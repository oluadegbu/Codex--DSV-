"""Durable watchdog authority. Caller MUST hold the native foreground lock.

No task registration, shell execution, credential renewal or quarantine reset.
Wall-clock regression blocks instead of evading a recovery cooldown.
"""
from uuid import uuid4
from pathlib import Path
import os
from dci.bridge.store import BridgeStore

CADENCE = 300
CRASH_LIMIT = 3


class Lifecycle:
    def __init__(self, path, binding):
        path=Path(path)
        marker=path.with_name(path.name+'.initialized')
        if path.exists()!=marker.exists():
            raise PermissionError('Missing lifecycle authority/marker; never reset the crash budget')
        if marker.exists():
            if marker.read_text(encoding='utf-8')!=binding:
                raise PermissionError('Lifecycle marker binding drift')
        else:
            # Marker first: an interrupted initialization remains blocked for review.
            with marker.open('x',encoding='utf-8') as stream:
                stream.write(binding);stream.flush();os.fsync(stream.fileno())
        self.store = BridgeStore(path)
        try:
            with self.store.tx():
                db = self.store.db
                prior = db.execute("SELECT value FROM meta WHERE key='watchdog_v1'").fetchone()
                if prior is None:
                    db.execute('CREATE TABLE watchdog (id INTEGER PRIMARY KEY CHECK(id=1), state TEXT, crashes INTEGER, eligible INTEGER, clock INTEGER, owner TEXT, heartbeat INTEGER, reason TEXT)')
                    db.execute("INSERT INTO watchdog VALUES (1,'READY',0,0,0,NULL,0,NULL)")
                    db.execute("INSERT INTO meta VALUES ('watchdog_v1',?)", (binding,))
                elif prior[0] != binding:
                    raise PermissionError('Watchdog context drift; preserve original authority')
        except BaseException:
            self.store.close()
            raise

    def close(self): self.store.close()

    def snapshot(self):
        return dict(self.store.db.execute('SELECT * FROM watchdog WHERE id=1').fetchone())

    def _event(self, event, now):
        self.store.audit('windows-watchdog', event, self.snapshot(), now)

    def _block(self, reason, now, state='BLOCKED'):
        self.store.db.execute('UPDATE watchdog SET state=?,owner=NULL,reason=?,clock=max(clock,?) WHERE id=1', (state, reason, now))
        self._event(reason, now)

    def _crash(self, now):
        self.store.db.execute("UPDATE watchdog SET crashes=crashes+1,owner=NULL,eligible=?,state='COOLDOWN',reason='unexpected_owner_exit',clock=? WHERE id=1", (now+CADENCE, now))
        if self.snapshot()['crashes'] >= CRASH_LIMIT:
            self._block('three_crash_circuit_open', now)
        else:
            self._event('crash_recovery_delayed', now)

    def enter(self, now, *, stopped=False, uncertain=False):
        with self.store.tx():
            row = self.snapshot()
            if row['state'] in ('BLOCKED', 'PAUSED'):
                return self.snapshot()
            if now < row['clock']:
                self._block('clock_regressed', now)
            elif stopped:
                self._block('local_STOP', now, 'PAUSED')
            elif uncertain:
                self._block('uncertain_worker_quarantined', now)
            elif row['state'] == 'ACTIVE':
                # Exclusive native lock proves that the old owner no longer holds it.
                self._crash(now)
            elif now < row['eligible']:
                pass
            else:
                owner = str(uuid4())
                self.store.db.execute("UPDATE watchdog SET state='ACTIVE',owner=?,heartbeat=?,clock=?,reason=NULL WHERE id=1", (owner, now, now))
                self._event('owner_acquired', now)
            return self.snapshot()

    def heartbeat(self, owner, now, authorized_until=None):
        with self.store.tx():
            row = self.snapshot()
            if row['state'] != 'ACTIVE' or row['owner'] != owner:
                raise PermissionError('Watchdog owner mismatch')
            if authorized_until is not None and (type(authorized_until) is not int or now+120 >= authorized_until):
                self._block('authorization_drain_boundary', now)
                return False
            if now < row['clock']:
                self._block('clock_regressed', now)
                return False
            self.store.db.execute('UPDATE watchdog SET heartbeat=?,clock=? WHERE id=1', (now, now))
            return True

    def finish(self, owner, now, outcome):
        if outcome not in ('NORMAL', 'STOP', 'POLICY', 'UNCERTAIN', 'CRASH'):
            raise PermissionError('Unrecognized lifecycle outcome')
        with self.store.tx():
            row = self.snapshot()
            if row['state'] != 'ACTIVE' or row['owner'] != owner:
                raise PermissionError('Watchdog owner mismatch')
            if now < row['clock']:
                self._block('clock_regressed', now)
            elif outcome == 'NORMAL':
                self.store.db.execute("UPDATE watchdog SET state='READY',owner=NULL,clock=?,reason='normal_rotation' WHERE id=1", (now,))
                self._event('normal_rotation', now)
            elif outcome == 'CRASH': self._crash(now)
            else: self._block(outcome, now, 'PAUSED' if outcome == 'STOP' else 'BLOCKED')
            return self.snapshot()
