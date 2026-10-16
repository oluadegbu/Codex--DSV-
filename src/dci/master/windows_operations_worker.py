"""One bounded watchdog session; external five-minute scheduler installs separately."""
import argparse
import hashlib
import json
from pathlib import Path
import sqlite3
import time
from dci.bridge.protocol import ProtocolError
from .windows_protocol import sha
from .windows_lifecycle import Lifecycle

NAMESPACE = 'DMBWindowsWorker-ops-0.3.0'


def journal_uncertain(root):
    """Read-only pre-dispatch check; missing database is safe, corrupt evidence is not."""
    journal = Path(root) / 'state/bridge.sqlite'
    if not journal.exists(): return False
    with sqlite3.connect(journal.as_uri() + '?mode=ro', uri=True) as db:
        rows = db.execute('SELECT state,report FROM win_local_jobs').fetchall()
        return any(state == 'EXECUTING' or report and json.loads(report).get('status') == 'UNCERTAIN'
                   for state, report in rows)


def run(seconds=300, isolation_manifest=None, stop_file=None, namespace=NAMESPACE, authorized_until=None):
    from .windows_native import require_identity, private_root, foreground_lock
    from .windows_bridge_cli import _windows_run_locked
    from .windows_worker import bridge_fingerprint
    if type(seconds) is not int or not 1 <= seconds <= 3600:
        raise PermissionError('Bounded polling duration required')
    identity = require_identity()
    if namespace not in {NAMESPACE, 'DMBWindowsWorker-cert-0.3.0-success'}:
        raise PermissionError('Compiled operations or certification namespace required')
    root = private_root(namespace)
    # Fixed local control path, never mailbox-controlled. STOP is sticky in SQLite too.
    if stop_file is not None and Path(stop_file) != root/'STOP':
        raise PermissionError('Fixed local STOP path required')
    stop = root/'STOP'
    binding = sha({'identity': identity, 'bridge': bridge_fingerprint(),
                   'wrapper': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()})
    with foreground_lock(root):
        lifecycle = Lifecycle(root/'watchdog.sqlite', binding)
        owner = None
        try:
            uncertain = journal_uncertain(root)
            state = lifecycle.enter(int(time.time()), stopped=stop.exists(), uncertain=uncertain)
            if uncertain:
                # Deliver a sealed uncertainty receipt, NEVER poll or invoke another task.
                # If offline, its pending envelope remains durable for human reconciliation.
                try: _windows_run_locked(1, namespace, recover_only=True)
                except Exception: pass
            if state['state'] != 'ACTIVE':
                return {'mode': 'SHADOW', 'lifecycle': state, 'worker_started': False}
            owner = state['owner']
            if isolation_manifest is not None:
                from .windows_isolation import probe
                if probe(isolation_manifest, namespace)['OS_canary_access_denial'] != 'PASS':
                    raise PermissionError('Native canary denial required')
            deadline, polls, outcome = time.monotonic()+seconds, 0, 'NORMAL'
            while time.monotonic() < deadline:
                if stop.exists(): outcome = 'STOP'; break
                if not lifecycle.heartbeat(owner, int(time.time()), authorized_until):
                    owner = None
                    raise PermissionError('Authorization or clock boundary; lifecycle blocked')
                # Existing native identity, DPAPI, executable pins, authenticated route,
                # controller cancellation, Job Object and task/lease checks remain enforced.
                _windows_run_locked(1, namespace)
                polls += 1
                if journal_uncertain(root):
                    outcome = 'UNCERTAIN'; break
                time.sleep(min(2, max(0, deadline-time.monotonic())))
            if stop.exists(): outcome = 'STOP'
            state = lifecycle.finish(owner, int(time.time()), outcome); owner = None
            return {'mode': 'SHADOW', 'polls': polls, 'lifecycle': state,
                    'service_installed': False, 'RDP_independence_certified': False}
        except BaseException as error:
            if owner is not None:
                # Never recover automatically from uncertain task effects, authentication,
                # source/pairing/policy failures or corrupt journals.
                try: uncertain = journal_uncertain(root)
                except Exception: uncertain = True
                outcome = 'UNCERTAIN' if uncertain else ('STOP' if isinstance(error, KeyboardInterrupt)
                          else 'POLICY' if isinstance(error, (PermissionError, ProtocolError, ValueError, OSError))
                          else 'CRASH')
                lifecycle.finish(owner, int(time.time()), outcome)
            raise
        finally: lifecycle.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seconds', type=int, default=300)
    parser.add_argument('--isolation-manifest')
    args = parser.parse_args()
    print(json.dumps(run(args.seconds, args.isolation_manifest)))


if __name__ == '__main__': main()
