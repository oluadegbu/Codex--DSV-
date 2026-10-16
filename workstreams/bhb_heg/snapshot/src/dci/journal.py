"""Single-host SQLite paper journal; atomic append and deterministic recovery.

This is local persistence, not a substitute for Temporal orchestration.
"""
import hashlib
import json
import sqlite3
from decimal import Decimal
from pathlib import Path

from .models import Opportunity
from .shadow import ShadowBook


class JournalError(RuntimeError):
    pass


def canonical(value) -> str:
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)


def digest(previous: str, event_id: str, payload: str) -> str:
    return hashlib.sha256(canonical([previous, event_id, payload]).encode()).hexdigest()


def apply_command(book: ShadowBook, command: dict):
    if command['type'] == 'entry':
        raw = command['opportunity']
        opportunity = Opportunity(raw['token'], raw['as_of'], Decimal(raw['score']), raw['eligible'],
                                  tuple(raw['reasons']), {k: Decimal(v) for k, v in raw['features'].items()},
                                  tuple(raw['events']), raw['config_version'])
        book.enter(opportunity, Decimal(command['price']))
    elif command['type'] == 'mark':
        book.mark(command['token'], Decimal(command['price']), command['at'], command['force_exit'])
    else:
        raise JournalError('unknown journal command')


class DurableShadowBook:
    """Serialized, idempotent commands; reloads ledger from committed evidence.

    Replaying is O(n); suitable for bounded local research only. Use a dedicated
    database path. No credential discovery or execution adapter is present.
    """
    def __init__(self, path: str | Path):
        self.db = sqlite3.connect(path, timeout=10, isolation_level=None)
        self.db.execute('PRAGMA journal_mode=WAL')
        self.db.execute('PRAGMA synchronous=FULL')
        try:
            self.db.execute('BEGIN IMMEDIATE')
            version = self.db.execute('PRAGMA user_version').fetchone()[0]
            if version not in (0, 1):
                raise JournalError('unsupported journal schema')
            if version == 0:
                # Reject unrelated DBs rather than reusing another application's storage.
                if self.db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchone():
                    raise JournalError('database is not an empty dedicated DCI journal')
                self.db.execute('CREATE TABLE events (seq INTEGER PRIMARY KEY, event_id TEXT UNIQUE NOT NULL, payload TEXT NOT NULL, chain TEXT NOT NULL)')
                self.db.execute('CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL)')
                self.db.execute('INSERT INTO metadata VALUES (?, ?)', ('policy', 'dci-synthetic-shadow-v1'))
                self.db.execute('PRAGMA user_version=1')
            if self.db.execute("SELECT value FROM metadata WHERE key='policy'").fetchone() != ('dci-synthetic-shadow-v1',):
                raise JournalError('journal policy mismatch')
            self.db.execute('COMMIT')
            self.load()
        except BaseException:
            if self.db.in_transaction:
                self.db.execute('ROLLBACK')
            self.db.close()
            raise

    def close(self):
        self.db.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def _recover(self) -> tuple[ShadowBook, str]:
        book = ShadowBook()
        previous = 'dci-synthetic-shadow-v1'
        expected_seq = 1
        for seq, event_id, payload, chain in self.db.execute('SELECT seq, event_id, payload, chain FROM events ORDER BY seq'):
            if seq != expected_seq or digest(previous, event_id, payload) != chain:
                raise JournalError('journal integrity failure')
            try:
                apply_command(book, json.loads(payload))
            except (ValueError, KeyError, TypeError) as exc:
                raise JournalError('invalid persisted command') from exc
            previous = chain
            expected_seq += 1
        return book, previous

    def load(self) -> ShadowBook:
        return self._recover()[0]

    def append(self, event_id: str, command: dict) -> ShadowBook:
        if not event_id:
            raise ValueError('event identity required')
        payload = canonical(command)
        self.db.execute('BEGIN IMMEDIATE')
        try:
            book, previous = self._recover()
            existing = self.db.execute('SELECT payload FROM events WHERE event_id=?', (event_id,)).fetchone()
            if existing:
                if existing[0] != payload:
                    raise JournalError('conflicting payload for event identity')
            else:
                apply_command(book, command)
                self.db.execute('INSERT INTO events (event_id,payload,chain) VALUES (?,?,?)',
                                (event_id, payload, digest(previous, event_id, payload)))
            self.db.execute('COMMIT')
            return book
        except BaseException:
            self.db.execute('ROLLBACK')
            raise

    def enter(self, opportunity: Opportunity, price: Decimal):
        raw = {'token': opportunity.token, 'as_of': opportunity.as_of, 'score': str(opportunity.score),
               'eligible': opportunity.eligible, 'reasons': list(opportunity.reasons),
               'features': {k: str(v) for k, v in opportunity.features.items()},
               'events': list(opportunity.events), 'config_version': opportunity.config_version}
        event_id = canonical(['entry', opportunity.token, opportunity.as_of, opportunity.config_version])
        return self.append(event_id, {'type': 'entry', 'opportunity': raw, 'price': str(price)}).positions[opportunity.token]

    def mark(self, token: str, price: Decimal, at: int, force_exit: bool = False):
        event_id = canonical(['mark', token, at])
        return self.append(event_id, {'type': 'mark', 'token': token, 'price': str(price),
                                    'at': at, 'force_exit': force_exit}).positions[token]

    @property
    def cash(self):
        return self.load().cash

    @property
    def audit(self):
        return self.load().audit
