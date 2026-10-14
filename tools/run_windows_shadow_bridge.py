"""Foreground-only genuine Windows bridge certification. No installer or public listener."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import ssl
import subprocess
import sys
import threading
import time
from http.server import HTTPServer

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from dci.master.windows_native import require_identity, private_root
from dci.master.windows_bridge_cli import prepare, pair_windows, key_from_config, handler_factory
from dci.master.windows_controller import AtomicPeerStore, WindowsController
from dci.master.windows_worker import bridge_fingerprint
from dci.master.registry import PortfolioRegistry
from dci.master.planner import PortfolioPlanner
from dci.master.control_plane import atomic_json


def openssl_existing():
    found = shutil.which('openssl')
    if found:
        return found
    git = shutil.which('git')
    if git:
        candidate = Path(git).resolve().parent.parent / 'usr/bin/openssl.exe'
        if candidate.is_file():
            return str(candidate)
    raise PermissionError('Existing OpenSSL (including Git for Windows bundled OpenSSL) required; no installation attempted')


class ForegroundController:
    def __init__(self, config, manifest, database, certificate, tls_key, port):
        self.args = config, manifest, database, certificate, tls_key, port
        self.ready, self.stop = threading.Event(), threading.Event()
        self.error = None
        self.thread = threading.Thread(target=self.serve, name='DMB-foreground-loopback')

    def serve(self):
        config, manifest, database, certificate, tls_key, port = self.args
        server = store = None
        try:
            store = AtomicPeerStore(database)
            controller = WindowsController(PortfolioPlanner(store, PortfolioRegistry(ROOT / 'portfolio/REGISTRY.v1.json'), manifest, ROOT),
                                           key_from_config(config), config['expected_host'], config['bridge_sha256'])
            server = HTTPServer(('127.0.0.1', port), handler_factory(controller))
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER); context.load_cert_chain(certificate, tls_key)
            server.socket = context.wrap_socket(server.socket, server_side=True); server.timeout = .1
            self.ready.set()
            while not self.stop.is_set():
                server.handle_request(); controller.planner.recover(int(time.time()))
        except BaseException as exc:
            self.error = type(exc).__name__ + ': ' + str(exc); self.ready.set()
        finally:
            if server: server.server_close()
            if store: store.close()

    def __enter__(self):
        self.thread.start()
        if not self.ready.wait(5) or self.error:
            self.stop.set(); self.thread.join(5)
            raise RuntimeError(self.error or 'foreground controller did not start')
        return self

    def __exit__(self, *args):
        self.stop.set(); self.thread.join(5)
        if self.thread.is_alive(): raise RuntimeError('foreground controller did not stop')
        if self.error: raise RuntimeError(self.error)


def controller(config, manifest, database):
    store = AtomicPeerStore(database)
    instance = WindowsController(PortfolioPlanner(store, PortfolioRegistry(ROOT / 'portfolio/REGISTRY.v1.json'), manifest, ROOT),
                                 key_from_config(config), config['expected_host'], config['bridge_sha256'])
    return store, instance


def main():
    if sys.version_info < (3, 11): raise PermissionError('Existing Python 3.11+ required; no installation attempted')
    identity = require_identity()  # Before creating files or using authentication.
    from windows_package_runtime import verify_package, initialize_package_git, create_tls_certificate, verify_predecessor_unstarted
    package = verify_package(ROOT)
    private = private_root()
    predecessor = verify_predecessor_unstarted(private.parent) if package else None
    if package:
        initialize_package_git(ROOT, package)
    out = ROOT / 'artifacts/windows-foreground'
    out.mkdir(parents=True, exist_ok=True)
    settings = out / 'pairing.json'; manifest = out / 'workers.json'; database = out / 'controller.sqlite'
    certificate, tls_key = out / 'certificate.pem', out / 'private.key'
    port = 18443; origin = 'https://127.0.0.1:18443/v1/dmb/windows'
    if not settings.exists():
        if (private / 'pairing.dpapi').exists():
            raise PermissionError('Existing pairing retained; run its original procedure, do not replace it')
        if package:
            create_tls_certificate(certificate, tls_key)
        else:
            openssl = openssl_existing()
            subprocess.run([openssl, 'req', '-x509', '-newkey', 'rsa:2048', '-nodes', '-keyout', str(tls_key), '-out', str(certificate),
                            '-days', '1', '-subj', '/CN=localhost', '-addext', 'subjectAltName=IP:127.0.0.1,DNS:localhost'],
                           capture_output=True, check=True, timeout=15)
        prepare(ROOT, private / 'controller-route', manifest, settings, origin, identity['host'], 3600)
        pair_windows(settings, certificate)
    config = json.loads(settings.read_text())
    if config['endpoint'] != origin or config['bridge_sha256'] != bridge_fingerprint():
        raise PermissionError('Retain original paired source and endpoint; context drift rejected')
    source = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True, timeout=5).strip()
    if subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT, timeout=5):
        raise PermissionError('Reviewed checkout must be clean; runtime files remain ignored')
    store, bridge = controller(config, manifest, database)
    try:
        bridge.submit({'task_id': 'windows-shadow-001', 'correlation_id': 'corr-windows-shadow-001', 'project_id': 'DCI'}, int(time.time()))
        prior = store.task('windows-shadow-001')['state']
        if prior in {'RUNNING', 'NEEDS_HUMAN'}:
            raise PermissionError('Uncertain prior execution quarantined; no automatic re-execution')
    finally: store.close()
    child_env = dict(os.environ); child_env['PYTHONPATH'] = str(ROOT / 'src')
    runs = []
    # The second iteration closes/reopens both durable ends and polls again.
    # It certifies restart replay suppression, not an injected Windows crash.
    for iteration in range(2):
        with ForegroundController(config, manifest, database, certificate, tls_key, port):
            stdout, stderr = out / ('worker-' + str(iteration) + '.out'), out / ('worker-' + str(iteration) + '.err')
            with stdout.open('wb') as output, stderr.open('wb') as errors:
                proc = subprocess.Popen([sys.executable, '-m', 'dci.master.windows_bridge_cli', 'run', '--cycles', '1'],
                                        cwd=ROOT, env=child_env, stdout=output, stderr=errors)
                try:
                    code = proc.wait(timeout=45)
                finally:
                    if proc.poll() is None:
                        proc.terminate(); proc.wait(timeout=5)  # Only this owned bridge; Codex job kills on close.
            runs.append({'bridge_pid': proc.pid, 'exit_code': code, 'iteration': iteration})
            if code != 0:
                raise RuntimeError('Foreground worker failed; private logs retained at ' + str(out) + '; no blind retry')
        store, bridge = controller(config, manifest, database)
        try:
            store.verify_audit()
            task = store.task('windows-shadow-001')
            evidence = json.loads(task['result']) if task.get('result') else None
            if task['state'] != 'SUCCEEDED' or evidence is None or evidence['fixture'] is not False:
                raise RuntimeError('Genuine Windows completion not certified; durable state retained')
            if store.db.execute('SELECT count(*) FROM executions').fetchone()[0] != 1:
                raise RuntimeError('Lost or duplicate execution detected')
            if evidence['remote_report']['identity']['execution_kind'] != 'WINDOWS_CODEX':
                raise RuntimeError('Synthetic execution cannot pass this gate')
            report = bridge.report()
            if report['held_resources']: raise RuntimeError('Completion resources still held')
        finally: store.close()
    summary = {'schema_version': 1, 'mode': 'SHADOW', 'status': 'WINDOWS_SINGLE_TASK_LOCAL_BRIDGE_PASS',
               'source_commit': source, 'bridge_sha256': bridge_fingerprint(), 'identity': identity,
               'package_source_commit': package['source_commit'] if package else None,
               'package_version': package['package_version'] if package else None,
               'predecessor_evidence': predecessor,
               'transport': 'authenticated outbound HTTPS to foreground Windows loopback DMB; not remote cloud delivery',
               'genuine_completion': evidence, 'worker_runs': runs, 'durable_executions': 1, 'audit_valid': True,
               'restart_replay_suppression': 'PASS', 'injected_windows_crash': 'NOT TESTED',
               'windows_cancellation': 'NOT TESTED', 'OS_access_denial_isolation': 'NOT TESTED',
               'services_installed': False, 'public_listener': False, 'production_changes': False,
               'external_delivery': 'BLOCKED', 'full_dmb_certification': 'BLOCKED'}
    atomic_json(out / 'CERTIFICATION.json', summary)
    print(json.dumps(summary, indent=2))  # Only validated fixed artifact and non-secret evidence.


if __name__ == '__main__':
    main()
