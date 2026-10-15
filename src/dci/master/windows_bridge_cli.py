"""Foreground HTTPS controller and outbound-only Windows bridge. No installation."""
import argparse
import base64
import ipaddress
import json
import os
from pathlib import Path
import re
import secrets
import ssl
import subprocess
import sys
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

from dci.bridge.identity import require_non_admin
from dci.bridge.protocol import ProtocolError, canonical
from .planner import PortfolioPlanner
from .registry import PortfolioRegistry
from .windows_controller import AtomicPeerStore, WindowsController
from .windows_protocol import MAX_BYTES, PeerKey, WORKSPACE_ID, endpoint, sha
from .windows_worker import (bridge_fingerprint, scratch_manifest_digest, SCRATCH_FILES, WorkerJournal,
                             HttpsTransport, OutboundWorker, NativeCodexExecutor)


def private_json(path, value):
    path = Path(path)
    with os.fdopen(os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), "w", encoding="utf-8") as stream:
        stream.write(canonical(value)); stream.flush(); os.fsync(stream.fileno())


def key_from_config(config):
    return PeerKey(config["worker_id"], config["key_id"], config["expires"], base64.b64decode(config["secret"], validate=True))


def prepare(root, route_root, workers_path, pairing_path, origin, host, ttl):
    root = require_non_admin(root)
    destination, workers_path, pairing_path = Path(route_root).resolve(), Path(workers_path).resolve(), Path(pairing_path).resolve()
    endpoint(origin)
    if not 60 <= ttl <= 28800 or not re.fullmatch(r"[A-Za-z0-9-]{1,63}", host):
        raise ProtocolError("bounded pairing TTL and exact Windows hostname required")
    if destination == root or root in destination.parents or destination in root.parents or destination.exists() or workers_path.exists() or pairing_path.exists():
        raise PermissionError("fresh dedicated controller route and files required")
    if root / "artifacts" not in pairing_path.parents:
        raise PermissionError("private pairing material must remain in ignored artifacts")
    destination.mkdir(parents=True)
    worker = "windows_codex_shadow"
    (destination / "CONTROLLER_ROUTE_ONLY.json").write_text(canonical({"mode": "SHADOW", "worker_id": worker,
                                                                   "note": "logical controller reservation; not a Windows filesystem/isolation claim"}))
    subprocess.run(["git", "init", "--quiet", str(destination)], check=True, timeout=5)
    subprocess.run(["git", "add", "."], cwd=destination, check=True, timeout=5)
    subprocess.run(["git", "-c", "user.name=DCI Shadow Worker", "-c", "user.email=shadow@example.invalid", "commit", "--quiet", "-m", "Bind outbound Windows controller route"], cwd=destination, check=True, timeout=5)
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=destination, text=True, timeout=5).strip()
    config = {"worker_id": worker, "key_id": "pair-" + secrets.token_hex(16), "expires": int(time.time()) + ttl,
              "secret": base64.b64encode(secrets.token_bytes(32)).decode(), "endpoint": origin,
              "expected_host": host, "bridge_sha256": bridge_fingerprint(), "workspace_id": WORKSPACE_ID}
    manifest = {"schema_version": 1, "mode": "SHADOW", "max_parallel": 1, "max_memory_mb": 256,
                "workers": [{"worker_id": worker, "project_ids": ["DCI"], "workspace": str(destination), "expected_commit": commit,
                             "source_sha256": {}, "max_seconds": 20, "memory_mb": 256, "cpu_seconds": 10, "max_output_bytes": 1048576,
                             "transport": "authenticated_outbound_windows_v1", "remote_workspace_id": WORKSPACE_ID,
                             "bridge_sha256": config["bridge_sha256"], "source_origin": "controller route only; physical Windows identity bound by authenticated HELLO"}]}
    workers_path.parent.mkdir(parents=True, exist_ok=True); pairing_path.parent.mkdir(parents=True, exist_ok=True)
    private_json(workers_path, manifest); private_json(pairing_path, config)
    return {"workers_manifest": str(workers_path), "private_pairing_file": str(pairing_path), "expires": config["expires"],
            "worker_id": worker, "bridge_sha256": config["bridge_sha256"], "note": "Transfer pairing file only through an approved secure channel; never paste it into chat or GitHub"}


def handler_factory(controller):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass  # Do not log authentication envelopes or provider/runtime output.

        def do_POST(self):
            if self.path != "/v1/dmb/windows":
                self.send_error(404); return
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if not 1 <= length <= MAX_BYTES or self.headers.get("Content-Type") != "application/json":
                    raise ProtocolError("bounded JSON POST required")
                self.connection.settimeout(2)
                packet = json.loads(self.rfile.read(length))
                response = controller.receive(packet, int(time.time()))
                body = canonical(response).encode()
            except (ValueError, KeyError, TypeError, PermissionError, OSError):
                self.send_error(403, "Bridge request rejected"); return
            self.send_response(200); self.send_header("Content-Type", "application/json"); self.send_header("Content-Length", str(len(body))); self.end_headers()
            self.wfile.write(body)
    return Handler


def pair_windows(bootstrap, ca_file=None, namespace="DMBWindowsWorker-v1-0.1.3"):
    if namespace != "DMBWindowsWorker-v1-0.1.3":
        raise PermissionError("Operations pairing requires the DPAPI-only pairing helper")
    from .windows_native import private_root, dpapi, require_identity
    identity = require_identity()
    root = private_root()
    config = json.loads(Path(bootstrap).read_text())
    key_from_config(config).check(int(time.time())); endpoint(config["endpoint"])
    if config["expected_host"] != identity["host"] or config["bridge_sha256"] != bridge_fingerprint() or config["workspace_id"] != WORKSPACE_ID:
        raise PermissionError("pairing host/code/scratch context mismatch")
    root.mkdir(parents=True, exist_ok=True)
    protected = root / "pairing.dpapi"
    if protected.exists():
        raise PermissionError("existing pairing retained; no silent overwrite/re-pair")
    if ca_file:
        config["ca_file"] = str(Path(ca_file).resolve(strict=True))
    with protected.open("xb") as stream:
        stream.write(dpapi(canonical(config).encode())); stream.flush(); os.fsync(stream.fileno())
    return {"paired_host": identity["host"], "worker_id": config["worker_id"], "state": str(root), "key_protection": "current-user DPAPI", "expires": config["expires"]}


def pair_windows_operations(protected_bootstrap):
    """Local approved provisioning only; no plaintext bootstrap or silent replacement."""
    from .windows_native import private_root, dpapi, require_identity
    identity = require_identity()
    config = json.loads(dpapi(Path(protected_bootstrap).read_bytes(), False))
    key_from_config(config).check(int(time.time())); endpoint(config['endpoint'])
    if config['expected_host'] != identity['host'] or config['bridge_sha256'] != bridge_fingerprint() or config['workspace_id'] != WORKSPACE_ID:
        raise PermissionError('Operations pairing host/code/scope mismatch')
    root = private_root('DMBWindowsWorker-ops-0.2.0-review1'); root.mkdir(parents=True, exist_ok=True)
    target = root/'pairing.dpapi'
    with target.open('xb') as stream:
        stream.write(dpapi(canonical(config).encode())); stream.flush(); os.fsync(stream.fileno())
    return {'worker_id': config['worker_id'], 'pairing': 'current-user DPAPI', 'old_state_changed': False}


def windows_run(cycles):
    from .windows_native import private_root, foreground_lock
    with foreground_lock(private_root()):
        return _windows_run_locked(cycles)


def _windows_run_locked(cycles, namespace="DMBWindowsWorker-v1-0.1.3"):
    from .windows_native import private_root, dpapi, require_identity, resolve_codex, WindowsJobProcess
    if not 1 <= cycles <= 100:
        raise ProtocolError("bounded foreground cycles required")
    identity, root = require_identity(), private_root(namespace)
    config = json.loads(dpapi((root / "pairing.dpapi").read_bytes(), False))
    key = key_from_config(config); key.check(int(time.time()))
    if config["bridge_sha256"] != bridge_fingerprint() or config["expected_host"] != identity["host"]:
        raise PermissionError("paired identity/code changed")
    scratch, state = root / "scratch", root / "state"
    state.mkdir(exist_ok=True)
    if not scratch.exists():
        scratch.mkdir()
        for name, contents in SCRATCH_FILES.items(): (scratch / name).write_bytes(contents.encode())
        subprocess.run(["git", "init", "--quiet", str(scratch)], check=True, timeout=5)
        subprocess.run(["git", "add", "."], cwd=scratch, check=True, timeout=5)
        subprocess.run(["git", "-c", "user.name=DCI Shadow Worker", "-c", "user.email=shadow@example.invalid", "commit", "--quiet", "-m", "Bind non-trading Windows scratch"], cwd=scratch, check=True, timeout=5)
    for name, content in SCRATCH_FILES.items():
        if (scratch / name).read_bytes() != content.encode(): raise PermissionError("scratch marker/content mismatch")
    if subprocess.check_output(["git", "status", "--porcelain"], cwd=scratch, timeout=5): raise PermissionError("scratch Git state not clean")
    identity.update(workspace_id=WORKSPACE_ID, scratch_manifest_sha256=scratch_manifest_digest(),
                    git_head=subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=scratch, text=True, timeout=5).strip(),
                    bridge_sha256=bridge_fingerprint(), execution_kind="WINDOWS_CODEX", codex_version="0.162.1")
    executable = resolve_codex()
    probe = state / ("startup-" + str(int(time.time())) + "-" + os.urandom(4).hex()); probe.mkdir()
    process = WindowsJobProcess(executable, ["--version"], scratch, probe)
    try:
        deadline = time.monotonic() + 5
        while process.active() and time.monotonic() < deadline: time.sleep(.02)
        if process.active(): raise PermissionError("bounded native CLI startup did not finish")
    finally:
        process.terminate(); process.close()
    version = (probe / "stdout.log").read_text().strip()
    if version != "codex-cli 0.162.1": raise PermissionError("native CLI differs from pinned verified version")
    journal = WorkerJournal(state / "bridge.sqlite", sha({"worker_id": key.worker_id, "key_id": key.key_id, "endpoint": config["endpoint"], "identity": identity}))
    worker = OutboundWorker(journal, key, identity, HttpsTransport(config["endpoint"], config.get("ca_file")),
                            NativeCodexExecutor(scratch, state, executable, identity), bridge_fingerprint())
    try:
        for _ in range(cycles):
            result = worker.step()
            if not result.get("idle"):
                print(json.dumps(result)); return
            time.sleep(.2)
        print(json.dumps({"idle": True, "cycles": cycles, "no_task_reexecuted": True}))
    finally:
        journal.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    create = sub.add_parser("prepare")
    for name in ("workspace", "route-root", "workers", "pairing", "endpoint", "host"): create.add_argument("--" + name, required=True)
    create.add_argument("--ttl", type=int, default=3600)
    pair = sub.add_parser("pair"); pair.add_argument("--bootstrap", required=True); pair.add_argument("--ca-file")
    run = sub.add_parser("run"); run.add_argument("--cycles", type=int, default=100)
    for command in ("serve", "submit", "report", "cancel"):
        action = sub.add_parser(command)
        for name in ("workspace", "database", "workers", "pairing"): action.add_argument("--" + name, required=True)
        if command == "serve":
            action.add_argument("--listen", default="127.0.0.1"); action.add_argument("--port", type=int, default=8443)
            action.add_argument("--cert", required=True); action.add_argument("--tls-key", required=True); action.add_argument("--seconds", type=int, default=300)
        if command == "cancel": action.add_argument("--task-id", required=True)
    args = parser.parse_args()
    if args.command == "prepare":
        result = prepare(args.workspace, args.route_root, args.workers, args.pairing, args.endpoint, args.host, args.ttl)
    elif args.command == "pair": result = pair_windows(args.bootstrap, args.ca_file)
    elif args.command == "run": windows_run(args.cycles); return
    else:
        root = require_non_admin(args.workspace)
        config = json.loads(Path(args.pairing).read_text()); key = key_from_config(config)
        store = AtomicPeerStore(args.database)
        try:
            planner = PortfolioPlanner(store, PortfolioRegistry(root / "portfolio/REGISTRY.v1.json"), args.workers, root)
            controller = WindowsController(planner, key, config["expected_host"], config["bridge_sha256"])
            if args.command == "serve":
                if not ipaddress.ip_address(args.listen).is_loopback or not 1 <= args.seconds <= 900:
                    raise PermissionError("foreground listener limited to loopback and 900 seconds; no public deployment")
                context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER); context.load_cert_chain(args.cert, args.tls_key)
                server = HTTPServer((args.listen, args.port), handler_factory(controller)); server.socket = context.wrap_socket(server.socket, server_side=True); server.timeout = .2
                try:
                    deadline = time.monotonic() + args.seconds
                    while time.monotonic() < deadline:
                        server.handle_request(); planner.recover(int(time.time()))
                finally: server.server_close()
                result = controller.report()
            elif args.command == "submit":
                raw = sys.stdin.read(65537)
                if len(raw) > 65536: raise ProtocolError("bounded intake required")
                result = controller.submit(json.loads(raw), int(time.time()))
            elif args.command == "cancel": result = controller.cancel(args.task_id, int(time.time()))
            else: result = controller.report()
        finally: store.close()
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
