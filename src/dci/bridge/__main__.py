"""Simulated one-shot scheduling. No daemon/service/task installation."""
import argparse
import json
import time
from .store import BridgeStore
from .runner import Runner
from .heg import HumanGateway
from .hands import HandsAdapter
from .identity import require_non_admin


def main():
    p = argparse.ArgumentParser(description='DCI deterministic shadow scheduler tick')
    p.add_argument('--database', required=True)
    p.add_argument('--workspace', required=True)
    p.add_argument('--now', type=int, help='simulation time; defaults to current epoch')
    p.add_argument("--hands", action="store_true", help="Enable fixed local verification/Codex read-only templates only")
    args = p.parse_args()
    require_non_admin(args.workspace)
    s = BridgeStore(args.database)
    try:
        now = args.now if args.now is not None else int(time.time())
        task = Runner(s, args.workspace, HandsAdapter() if args.hands else None).tick(now)
        HumanGateway(s).tick(now)
        print(json.dumps({'mode': 'SHADOW', 'task': task, 'heartbeat': now, 'providers': 'SIMULATED'}))
    finally:
        s.close()


if __name__ == '__main__':
    main()
