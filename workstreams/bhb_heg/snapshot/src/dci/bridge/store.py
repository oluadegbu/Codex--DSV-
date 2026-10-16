"""Dedicated single-host mailbox authority; SQLite atomicity and local writer ACLs."""
import hashlib
import json
import sqlite3
from contextlib import contextmanager
from uuid import uuid4
from .protocol import ProtocolError, canonical, envelope, validate


class BridgeStore:
    def __init__(self, path):
        self.db = sqlite3.connect(path, isolation_level=None, timeout=10)
        self.db.row_factory = sqlite3.Row
        try:
            with self.tx():
                version = self.db.execute("PRAGMA user_version").fetchone()[0]
                if version not in (0, 101):
                    raise ProtocolError("unrecognized bridge database")
                if version == 0:
                    if self.db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchone():
                        raise ProtocolError("dedicated empty bridge database required")
                    statements = [
                        "CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT NOT NULL)",
                        "CREATE TABLE messages (id TEXT PRIMARY KEY, sender TEXT, recipient TEXT, sequence INTEGER, task TEXT, correlation TEXT, kind TEXT, body TEXT, UNIQUE(sender,recipient,sequence))",
                        "CREATE TABLE sequences (sender TEXT, recipient TEXT, value INTEGER, PRIMARY KEY(sender,recipient))",
                        "CREATE TABLE tasks (id TEXT PRIMARY KEY, correlation TEXT, action TEXT, scope TEXT, state TEXT, expires INTEGER, attempts INTEGER DEFAULT 0, lease INTEGER, result TEXT, retry_at INTEGER)",
                        "CREATE TABLE executions (task TEXT PRIMARY KEY, evidence TEXT)",
                        "CREATE TABLE audit (seq INTEGER PRIMARY KEY, body TEXT, hash TEXT)",
                        "CREATE TABLE heartbeats (role TEXT PRIMARY KEY, at INTEGER)",
                        "CREATE TABLE escalations (id TEXT PRIMARY KEY, task TEXT, scope TEXT, expires INTEGER, category TEXT, summary TEXT, decision TEXT, identity TEXT, decided_at INTEGER)",
                        "CREATE TABLE deliveries (request TEXT, channel TEXT, attempts INTEGER, state TEXT, next_at INTEGER, acknowledgement TEXT, PRIMARY KEY(request,channel))"
                    ]
                    for sql in statements:
                        self.db.execute(sql)
                    self.db.execute("INSERT INTO meta VALUES ('policy','dci-bhb-shadow-v1')")
                    self.db.execute("INSERT INTO meta VALUES ('paused','0')")
                    self.db.execute("PRAGMA user_version=101")
                if self.db.execute("SELECT value FROM meta WHERE key='policy'").fetchone()[0] != 'dci-bhb-shadow-v1':
                    raise ProtocolError("bridge policy mismatch")
            self.db.execute("PRAGMA journal_mode=WAL")
            self.db.execute("PRAGMA synchronous=FULL")
            self.verify_audit()
        except BaseException:
            self.db.close()
            raise

    def close(self):
        self.db.close()

    @contextmanager
    def tx(self):
        self.db.execute("BEGIN IMMEDIATE")
        try:
            yield
            self.db.execute("COMMIT")
        except BaseException:
            self.db.execute("ROLLBACK")
            raise

    def audit(self, actor, event, detail, now):
        prior = self.db.execute("SELECT hash FROM audit ORDER BY seq DESC LIMIT 1").fetchone()
        previous = prior[0] if prior else "dci-bhb-shadow-v1"
        body = canonical({"actor": actor, "event": event, "detail": detail, "at": now})
        digest = hashlib.sha256((previous + body).encode()).hexdigest()
        self.db.execute("INSERT INTO audit(body,hash) VALUES (?,?)", (body, digest))

    def verify_audit(self):
        previous = "dci-bhb-shadow-v1"
        for expected, row in enumerate(self.db.execute("SELECT seq,body,hash FROM audit ORDER BY seq"), 1):
            if row['seq'] != expected or hashlib.sha256((previous + row['body']).encode()).hexdigest() != row['hash']:
                raise ProtocolError("audit integrity failure")
            previous = row['hash']

    def _next(self, actor, recipient):
        row = self.db.execute("SELECT value FROM sequences WHERE sender=? AND recipient=?", (actor, recipient)).fetchone()
        return row[0] + 1 if row else 1

    def _emit(self, kind, actor, recipient, task, correlation, payload, now, ttl=3600):
        message = envelope(kind, actor, recipient, task, correlation, payload, self._next(actor, recipient), now, ttl)
        self._insert(actor, message, now)
        return message

    def _insert(self, actor, message, now):
        validate(message, actor, now)
        body = canonical(message)
        existing = self.db.execute("SELECT body FROM messages WHERE id=?", (message['message_id'],)).fetchone()
        if existing:
            if existing[0] != body:
                raise ProtocolError("message identity conflict")
            return False
        if message['sequence'] != self._next(actor, message['recipient']):
            raise ProtocolError("replayed or out-of-order sequence")
        self.db.execute("INSERT INTO messages VALUES (?,?,?,?,?,?,?,?)", (message['message_id'], actor, message['recipient'], message['sequence'], message['task_id'], message['correlation_id'], message['kind'], body))
        self.db.execute("INSERT INTO sequences VALUES (?,?,?) ON CONFLICT(sender,recipient) DO UPDATE SET value=excluded.value", (actor, message['recipient'], message['sequence']))
        self.audit(actor, 'message', {'id': message['message_id'], 'kind': message['kind'], 'task': message['task_id']}, now)
        return True

    def submit(self, actor, message, now):
        # Public ingress is restricted to authenticated Brain session tools. Worker
        # messages are derived internally from the transition authority, never from text.
        if actor != 'brain' or message.get('kind') not in ('TASK', 'EVENT'):
            raise ProtocolError("ingress writer not permitted")
        with self.tx():
            return self._accept(actor, message, now)

    def _accept(self, actor, message, now):
        fresh = self._insert(actor, message, now)
        if not fresh:
            return False
        if message['kind'] == 'EVENT':
            paused = '1' if message['payload']['event'] == 'PAUSE' else '0'
            self.db.execute("UPDATE meta SET value=? WHERE key='paused'", (paused,))
        else:
            if self.db.execute("SELECT id FROM tasks WHERE id=?", (message['task_id'],)).fetchone():
                raise ProtocolError("task identity reused")
            scope = hashlib.sha256(canonical(message['payload']).encode()).hexdigest()
            self.db.execute("INSERT INTO tasks(id,correlation,action,scope,state,expires) VALUES (?,?,?,?,?,?)", (message['task_id'], message['correlation_id'], message['payload']['action'], scope, 'QUEUED', message['expires_at']))
            self._emit('ACK', 'runner', 'brain', message['task_id'], message['correlation_id'], {'accepted_message_id': message['message_id']}, now)
            self._status(message['task_id'], 'QUEUED', 'accepted', now)
        return True

    def create_task(self, action, now, ttl=3600, task_id=None, correlation_id=None):
        with self.tx():
            # Stable caller task/correlation identifiers make tool response-loss
            # retries idempotent. A changed scope/correlation is rejected.
            if task_id and correlation_id:
                existing = self.db.execute("SELECT body FROM messages WHERE task=? AND kind='TASK'", (task_id,)).fetchone()
                if existing:
                    prior = json.loads(existing[0])
                    if prior['correlation_id'] != correlation_id or prior['payload'] != {'action': action, 'parameters': {}} or prior['expires_at'] <= now:
                        raise ProtocolError('task retry changed scope/correlation or expired')
                    return prior
            m = envelope('TASK', 'brain', 'runner', task_id or str(uuid4()), correlation_id or str(uuid4()), {'action': action, 'parameters': {}}, self._next('brain', 'runner'), now, ttl)
            self._accept('brain', m, now)
        return m

    def task(self, task_id):
        row = self.db.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()
        if row is None:
            raise ProtocolError("unknown task")
        return dict(row)

    def _status(self, task, state, detail, now):
        row = self.task(task)
        self._emit('STATUS', 'runner', 'brain', task, row['correlation'], {'state': state, 'detail': detail}, now)
        self.audit('runner', 'transition', {'task': task, 'state': state, 'detail': detail}, now)

    def status_messages(self, recipient):
        if recipient not in ('brain', 'runner', 'heg'):
            raise ProtocolError("unknown recipient")
        return [json.loads(r[0]) for r in self.db.execute("SELECT body FROM messages WHERE recipient=? ORDER BY rowid", (recipient,))]
