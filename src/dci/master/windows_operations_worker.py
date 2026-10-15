"""Bounded polling wrapper for an APPROVED user-mode supervisor. Installs nothing.

This foreground entry alone does not establish survival across RDP logoff/reboot.
Existing paired worker code/journals remain unchanged. No restart on uncertainty.
"""
import argparse
import json
from pathlib import Path
import time
from uuid import uuid4
from dci.bridge.store import BridgeStore
from .windows_protocol import sha


def run(seconds=300, isolation_manifest=None):
    from .windows_native import require_identity, private_root, foreground_lock
    from .windows_bridge_cli import _windows_run_locked
    from .windows_worker import bridge_fingerprint
    if type(seconds) is not int or not 1 <= seconds <= 3600:
        raise PermissionError('Bounded user-mode polling duration required')
    identity = require_identity()
    root = private_root()
    isolation = None
    if isolation_manifest is not None:
        from .windows_isolation import probe
        isolation = probe(isolation_manifest)
        if isolation['OS_canary_access_denial'] != 'PASS':
            raise PermissionError('Real canary denial did not pass; no worker activation')
    # Same exclusive native lock as the certified executor, held for the whole run.
    with foreground_lock(root):
        store = BridgeStore(root / 'operations-lifecycle.sqlite')
        instance = str(uuid4())
        try:
            binding = sha({'identity': identity, 'bridge': bridge_fingerprint(),
                           'wrapper_sha256': __import__('hashlib').sha256(Path(__file__).read_bytes()).hexdigest()})
            with store.tx():
                old = store.db.execute("SELECT value FROM meta WHERE key='worker_lifecycle_v1'").fetchone()
                if old is None:
                    store.db.execute('CREATE TABLE worker_runs(id TEXT PRIMARY KEY,state TEXT,heartbeat INTEGER,reason TEXT)')
                    store.db.execute("INSERT INTO meta VALUES ('worker_lifecycle_v1',?)", (binding,))
                elif old[0] != binding:
                    raise PermissionError('Wrapper/identity drift; preserve lifecycle evidence')
                # Recovery is delegated to the existing certified worker journal.
                # It reconciles cached receipts and quarantines uncertain started work.
                store.db.execute("UPDATE worker_runs SET state='INTERRUPTED',reason='Owner exited; reconcile worker journal before dispatch' WHERE state='ACTIVE'")
                store.db.execute("INSERT INTO worker_runs VALUES (?,'ACTIVE',?,NULL)", (instance, int(time.time())))
                store.audit('windows-supervisor', 'started', {'instance': instance}, int(time.time()))
            deadline = time.monotonic() + seconds
            polls = 0
            while time.monotonic() < deadline:
                with store.tx():
                    store.db.execute('UPDATE worker_runs SET heartbeat=? WHERE id=?', (int(time.time()), instance))
                _windows_run_locked(1)  # Same exact identity, version, pairing, task and sandbox gates.
                # Do not spin/retry a quarantined worker or create unrelated new tasks.
                journal = root / 'state/bridge.sqlite'
                if journal.exists():
                    # Existing worker has closed the DB; read-only inspection, no writes.
                    import sqlite3
                    with sqlite3.connect(journal.as_uri() + '?mode=ro', uri=True) as db:
                        reports = db.execute("SELECT report FROM win_local_jobs WHERE report IS NOT NULL").fetchall()
                        if any(json.loads(r[0]).get('status') == 'UNCERTAIN' for r in reports):
                            raise PermissionError('Uncertain worker outcome; supervisor must reconcile, not restart task')
                polls += 1
                time.sleep(min(2, max(0, deadline - time.monotonic())))
            with store.tx():
                store.db.execute("UPDATE worker_runs SET state='STOPPED',heartbeat=?,reason='Bounded run ended' WHERE id=?", (int(time.time()), instance))
                store.audit('windows-supervisor', 'bounded_stop', {'instance': instance, 'polls': polls}, int(time.time()))
            return {'mode': 'SHADOW', 'instance': instance, 'polls': polls, 'state': 'STOPPED',
                    'RDP_independence_certified': False, 'service_installed': False, 'isolation_probe': isolation}
        except BaseException as error:
            if not store.db.execute("SELECT 1 FROM sqlite_master WHERE name='worker_runs'").fetchone():
                raise
            with store.tx():
                store.db.execute("UPDATE worker_runs SET state='BLOCKED',heartbeat=?,reason=? WHERE id=?", (int(time.time()), type(error).__name__, instance))
                store.audit('windows-supervisor', 'blocked', {'instance': instance, 'reason': type(error).__name__, 'automatic_task_retry': False}, int(time.time()))
            raise
        finally:
            store.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seconds', type=int, default=300)
    parser.add_argument('--isolation-manifest')
    args = parser.parse_args()
    print(json.dumps(run(args.seconds, args.isolation_manifest)))


if __name__ == '__main__': main()
