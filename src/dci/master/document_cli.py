"""One foreground DDB invocation. No service, scheduler, key generation or enrollment."""
import argparse
from contextlib import contextmanager
import json
import os
from pathlib import Path
import time
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from .document_bridge import Policy, DocumentNode, Supervisor, Worker, PaperOperationsBackend, sha
from .document_github import GitHubDocuments, GitHubCLIDocuments
from .operations_cli import load_private_json, load_identity
from dci.bridge.protocol import canonical
from .operations import Operations
from .operations_client import OperationsClient
from .windows_bridge_cli import key_from_config
from .windows_controller import AtomicPeerStore
from .control_plane import ShadowControlPlane
from .planner import PortfolioPlanner
from .registry import PortfolioRegistry


@contextmanager
def exclusive(path):
    # Dedicated private directory is approved configuration, never document text.
    if path.is_symlink(): raise PermissionError('Lock link rejected')
    with path.open('a+b') as lock:
        if os.name == 'nt':
            import msvcrt
            lock.seek(0); lock.write(b'0'); lock.flush(); lock.seek(0)
            msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        try: yield
        finally:
            if os.name == 'nt':
                lock.seek(0); msvcrt.locking(lock.fileno(), msvcrt.LK_UNLCK, 1)
            else: fcntl.flock(lock.fileno(), fcntl.LOCK_UN)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--workspace', required=True)
    p.add_argument('--configuration', required=True)
    p.add_argument('--approved-policy-sha256', required=True)
    p.add_argument('--foreground-certification', action='store_true')
    p.add_argument('role', choices=['controller', 'worker'])
    a = p.parse_args()
    from dci.bridge.identity import require_non_admin
    root = require_non_admin(a.workspace)
    if os.name == 'nt':
        from .windows_native import require_identity
        require_identity()  # Existing exact DirectiveCodex/non-admin/Medium gate.
    config = load_private_json(a.configuration)
    retired=tuple(Policy(p,sha(p)) for p in config.get('retired_pre_dispatch_policies',[]))
    policy = Policy(config['policy'], a.approved_policy_sha256, retired)
    if a.foreground_certification and (policy.body['template']!='codex_shadow_review_v1' or policy.body['max_tasks']!=1):
        raise PermissionError('Foreground cadence override requires one native certification effort')
    role = 'supervisor' if a.role == 'controller' else 'worker'
    now = int(time.time()); policy.check(now)
    # Do not hold a network credential in GitHub documents or command arguments.
    configured_database = Path(config['database'])
    if configured_database.is_symlink(): raise PermissionError('Database link rejected')
    database = configured_database.resolve()
    if database.parent != Path(a.configuration).resolve().parent or not database.parent.is_dir(): raise PermissionError('Existing dedicated private state directory required')
    with exclusive(database.with_suffix('.ddb.lock')):
        store = AtomicPeerStore(database)
        client_store = None
        try:
            transport = (GitHubCLIDocuments(config['repository'], store) if config.get('github_auth')=='cli' else GitHubDocuments(config['repository'], lambda: load_private_json(config['github_credential_file'])['token'], store))
            private = load_private_json(config['document_signing_key_file'])
            node = DocumentNode(store, role, policy, Ed25519PrivateKey.from_private_bytes(bytes.fromhex(private['private_hex'])), transport)
            node.flush(now)  # Recover unknown publication before taking new work.
            if role == 'supervisor':
                changed = False
                if a.foreground_certification or node.due('watch', now):
                    _, snapshot = transport.snapshot()
                    head = sha(snapshot.get('reports/latest.json'))
                    with store.tx():
                        old = store.db.execute("SELECT value FROM meta WHERE key='ddb_watched_head'").fetchone()
                        changed = old is None or old[0] != head
                        store.db.execute("INSERT INTO meta VALUES ('ddb_watched_head',?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (head,))
                if a.foreground_certification or node.due('supervisor', now, evidence=changed): Supervisor(node).poll(now)
            else:
                if not a.foreground_certification and not node.due('worker', now): return
                if config.get('backend') == 'native-codex-foreground':
                    if policy.body['template']!='codex_shadow_review_v1' or policy.body['max_tasks']!=1:
                        raise PermissionError('One exact native foreground grant required')
                    # A real signed branch publication/re-read must establish
                    # worker-specific GitHub access before any native launch.
                    _, snapshot = transport.snapshot()
                    from .document_bridge import verified_snapshot
                    verified_snapshot(snapshot, policy, now)
                    admission_id='native-admission-'+str(now)
                    node.enqueue('HEARTBEAT', {'state':'IDLE'}, admission_id, now)
                    node.flush(now)
                    _, snapshot = transport.snapshot()
                    if snapshot.get('state/heartbeat.json') != canonical(json.loads(store.db.execute('SELECT body FROM ddb_outbox WHERE id=?',(admission_id,)).fetchone()[0])):
                        raise PermissionError('No verified native GitHub publication admission')
                    from .document_native import NativeForegroundBackend
                    worker = Worker(node, NativeForegroundBackend(store,config['native_pins'],root))
                else:
                    if os.name != 'posix' or config.get('backend') != 'paper' or policy.body['template']!='shadow_research':
                        raise PermissionError('Uncertified backend disabled')
                    pairing = key_from_config(load_private_json(config['existing_worker_pairing_file']))
                    if pairing.worker_id != policy.body['worker_id'] or pairing.key_id != policy.body['worker_key_id']:
                        raise PermissionError('Existing worker identity binding mismatch')
                    pairing.check(now)
                    operations = Operations(ShadowControlPlane(PortfolioPlanner(store, PortfolioRegistry(root/'portfolio/REGISTRY.v1.json'), config['workers'], root)), load_identity(config['operations_identity_file']))
                    if set(operations.controller.planner.workers) != {pairing.worker_id}:
                        raise PermissionError('Document signer/pairing must bind the exact runtime worker')
                    client_store = AtomicPeerStore(config['operations_client_database'])
                    client = OperationsClient(client_store, operations.identity, lambda packet: operations.handle(packet, int(time.time())))
                    worker = Worker(node, PaperOperationsBackend(operations, client))
                idle_id='initial-idle-'+policy.approved_sha256[:12] if policy.retired else 'initial-idle'
                if not store.db.execute('SELECT 1 FROM ddb_outbox WHERE id=?',(idle_id,)).fetchone():
                    node.enqueue('REPORT',{'effort_id':idle_id,'directive_id':None,'task_id':None,'status':'IDLE','evidence':None},idle_id,now)
                worker.poll(now); worker.execute_one(now)
                node.enqueue('HEARTBEAT', {'state': 'BLOCKED' if store.db.execute("SELECT 1 FROM meta WHERE key='ddb_blocked'").fetchone() or store.db.execute("SELECT 1 FROM tasks WHERE state='NEEDS_HUMAN'").fetchone() else 'IDLE'}, 'heartbeat-'+str(now), now)
            node.flush(int(time.time()))
            print(json.dumps({'mode': 'SHADOW', 'role': role, 'unattended_activated': False, 'audit_valid': True}))
        finally:
            if client_store is not None: client_store.close()
            store.close()


if __name__ == '__main__':
    try: main()
    except Exception as error:
        print(json.dumps({'mode': 'SHADOW', 'status': 'BLOCKED', 'category': type(error).__name__, 'details': 'Retained private state; no raw errors exported'}))
        raise SystemExit(1)
