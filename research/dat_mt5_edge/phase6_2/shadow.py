"""Offline quote-only acceptance with durable replay protection.

Consumes only separately authorized exporter bytes. Never opens a terminal,
connects a broker, downloads quotes or exposes any trading/order interface.
"""
from __future__ import annotations
import hashlib
import sqlite3
from pathlib import Path
from phase4.collector import PassiveCollector

class ShadowJournal:
    """Single SQLite atomic replay register; process crashes never re-accept old quotes.

    initialize=True is allowed ONLY for a new, isolated SHADOW research journal.
    Existing DB missing, corrupt or mismatched identity -> fail closed.
    """
    def __init__(self, path: Path, *, source_id: str, symbol: str, tick_size: str,
                 max_spread: str, max_age_ms: int = 5000, initialize: bool = False):
        self.path=Path(path)
        new_file=not self.path.exists()
        if new_file and not initialize:
            raise ValueError('missing replay journal')
        if not self.path.parent.is_dir():
            raise ValueError('journal parent unavailable')
        self.collector=PassiveCollector(source_id,symbol,tick_size,max_spread,max_age_ms)
        self.identity=(source_id,symbol,str(self.collector.tick),str(self.collector.max_spread),str(max_age_ms))
        self.db=sqlite3.connect(str(self.path),timeout=1,isolation_level=None)
        try:
            self.db.execute('PRAGMA busy_timeout = 1000')
            self.db.execute('PRAGMA journal_mode = DELETE')
            self.db.execute('BEGIN IMMEDIATE')
            self.db.execute('CREATE TABLE IF NOT EXISTS identity(k INTEGER PRIMARY KEY CHECK(k=1), source TEXT, symbol TEXT, tick TEXT, spread TEXT, age TEXT)')
            self.db.execute('CREATE TABLE IF NOT EXISTS quotes(sequence INTEGER PRIMARY KEY, ts_ms INTEGER UNIQUE NOT NULL, bid TEXT NOT NULL, ask TEXT NOT NULL, digest TEXT UNIQUE NOT NULL)')
            identity=self.db.execute('SELECT source,symbol,tick,spread,age FROM identity WHERE k=1').fetchone()
            if identity is None and initialize and new_file and self.db.execute('SELECT COUNT(*) FROM quotes').fetchone()[0]==0:
                self.db.execute('INSERT INTO identity VALUES(1,?,?,?,?,?)',self.identity)
            elif identity != self.identity:
                raise ValueError('journal source/spec mismatch')
            last=self.db.execute('SELECT sequence,ts_ms FROM quotes ORDER BY sequence DESC LIMIT 1').fetchone()
            if last:
                self.collector.sequence,self.collector.timestamp=last
            self.db.execute('COMMIT')
        except Exception:
            self.db.execute('ROLLBACK');self.db.close();raise

    def accept(self, raw: bytes, now_ms: int) -> tuple:
        """Atomic validation and insertion. State advances only after durable commit."""
        self.db.execute('BEGIN IMMEDIATE')
        try:
            last=self.db.execute('SELECT sequence,ts_ms FROM quotes ORDER BY sequence DESC LIMIT 1').fetchone()
            v=PassiveCollector(self.collector.source_id,self.collector.symbol,
                               str(self.collector.tick),str(self.collector.max_spread),
                               self.collector.max_age_ms)
            if last:v.sequence,v.timestamp=last
            accepted=v.consume(raw,now_ms)
            symbol,t,b,a,seq=accepted
            digest=hashlib.sha256(raw).hexdigest()
            self.db.execute('INSERT INTO quotes VALUES(?,?,?,?,?)',(seq,t,b,a,digest))
            self.db.execute('COMMIT')
            self.collector.sequence,self.collector.timestamp=seq,t
            return accepted
        except Exception:
            self.db.execute('ROLLBACK')
            raise

    def close(self):
        self.db.close()
