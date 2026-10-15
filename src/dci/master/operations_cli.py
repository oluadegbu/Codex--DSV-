"""Non-admin signed exchange/tick CLI. No listener, installer or arbitrary shell."""
import argparse
import json
import os
from pathlib import Path
import sys
import time
from .operations import BrainIdentity, Operations
from .windows_controller import AtomicPeerStore, WindowsController
from .planner import PortfolioPlanner
from .registry import PortfolioRegistry
from .control_plane import ShadowControlPlane


def load_private_json(path):
    path = Path(path)
    if path.is_symlink() or not path.is_file(): raise PermissionError('Private identity file required')
    if os.name == 'nt':
        from .windows_native import dpapi, require_identity
        require_identity()
        raw = dpapi(path.read_bytes(), False)
    else:
        if path.stat().st_uid != os.getuid() or path.stat().st_mode & 0o077:
            raise PermissionError('Current-user-only operations identity required')
        raw = path.read_bytes()
    return json.loads(raw)


def load_identity(path):
    value = load_private_json(path)
    if set(value) != {'principal', 'key_id', 'expires', 'scopes', 'secret_hex'}:
        raise PermissionError('Exact scoped Brain identity required')
    return BrainIdentity(value['principal'], value['key_id'], value['expires'], frozenset(value['scopes']), bytes.fromhex(value['secret_hex']))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('workspace', 'database', 'workers', 'identity-file'): p.add_argument('--' + name, required=True)
    p.add_argument('--backend', choices=['paper', 'windows'], required=True)
    p.add_argument('--pairing')
    p.add_argument('--relay-identity-file')
    p.add_argument('--relay-url')
    p.add_argument('command', choices=['exchange', 'tick', 'relay-once'])
    args = p.parse_args()
    root = Path(args.workspace).resolve(strict=True)
    from dci.bridge.identity import require_non_admin
    require_non_admin(root)
    identity = load_identity(args.identity_file); identity.check(int(time.time()))
    store = AtomicPeerStore(args.database)
    try:
        planner = PortfolioPlanner(store, PortfolioRegistry(root / 'portfolio/REGISTRY.v1.json'), args.workers, root)
        if args.backend == 'windows':
            if not args.pairing: raise PermissionError('Separate Windows worker pairing required')
            from .windows_bridge_cli import key_from_config
            cfg = load_private_json(args.pairing)
            controller = WindowsController(planner, key_from_config(cfg), cfg['expected_host'], cfg['bridge_sha256'])
        else: controller = ShadowControlPlane(planner)
        ops = Operations(controller, identity)
        if args.command == 'exchange':
            raw = sys.stdin.read(131073)
            if len(raw.encode()) > 131072: raise PermissionError('One bounded signed request required')
            response = ops.handle(json.loads(raw), int(time.time()))
        elif args.command == 'relay-once':
            if not args.relay_identity_file or not args.relay_url: raise PermissionError('Approved relay endpoint and separate carrier pairing required')
            from .operations_relay import OutboundRelayPump
            from .operations_client import OperationsHTTPS
            response = OutboundRelayPump(ops, load_identity(args.relay_identity_file), OperationsHTTPS(args.relay_url)).pump(int(time.time()))
        else:
            response = controller.tick() if args.backend == 'paper' else {'worker_dispatch': 'outbound poll only'}
            ops.collect(int(time.time()))
        print(json.dumps(response))
    finally: store.close()


if __name__ == '__main__': main()
