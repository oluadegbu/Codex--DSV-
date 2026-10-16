"""Standalone foreground shadow control plane. No service installation or shell intake."""
import argparse
import json
from pathlib import Path
import sys
import time

from dci.bridge.store import BridgeStore
from dci.bridge.protocol import ProtocolError
from .registry import PortfolioRegistry
from .planner import PortfolioPlanner
from .brain import MasterBrainTools, MasterMcpPrototype, TOOLS
from .control_plane import ShadowControlPlane


class RuntimeMcp(MasterMcpPrototype):
    def __init__(self, runtime):
        super().__init__(MasterBrainTools(runtime.planner))
        self.runtime = runtime

    def request(self, request, now):
        if not self.ready or request.get("method") in ("initialize", "notifications/initialized"):
            return super().request(request, now)
        if request.get("method") == "tools/list":
            tools = json.loads(json.dumps(TOOLS))
            tools[0]["inputSchema"]["properties"]["operation"] = {"enum": ["shadow_research"]}
            return {"tools": tools}
        params = request.get("params", {})
        if request.get("method") == "tools/call" and type(params) is dict and set(params) == {"name", "arguments"}:
            name, arguments = params["name"], params["arguments"]
            if name == "dmb_submit_job":
                result = self.runtime.submit(arguments, now)
            elif name == "dmb_portfolio_report" and arguments == {}:
                result = self.runtime.report()
            else:
                return super().request(request, now)
            return {"content": [{"type": "text", "text": json.dumps(result)}], "structuredContent": result, "isError": False}
        return super().request(request, now)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--database", required=True)
    parser.add_argument("--workers", required=True)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("intake")
    sub.add_parser("tick")
    sub.add_parser("report")
    sub.add_parser("mcp")
    cancel = sub.add_parser("cancel"); cancel.add_argument("--task-id", required=True)
    status = sub.add_parser("status"); status.add_argument("--task-id", required=True)
    foreground = sub.add_parser("foreground")
    foreground.add_argument("--ticks", type=int, default=10)
    foreground.add_argument("--interval", type=float, default=.2)
    args = parser.parse_args()
    root = Path(args.workspace).resolve(strict=True)
    # Validate identity before touching the dedicated database.
    from dci.bridge.identity import require_non_admin
    require_non_admin(root)
    with_store = BridgeStore(args.database)
    try:
        planner = PortfolioPlanner(with_store, PortfolioRegistry(root / "portfolio/REGISTRY.v1.json"), args.workers, root)
        runtime = ShadowControlPlane(planner)
        now = lambda: int(time.time())
        if args.command == "intake":
            line = sys.stdin.readline(65537)
            if len(line) > 65536 or sys.stdin.read(1):
                raise ProtocolError("one bounded JSON intake request required")
            result = runtime.submit(json.loads(line), now())
        elif args.command == "tick":
            result = runtime.tick()
        elif args.command == "report":
            result = runtime.report()
        elif args.command == "status":
            result = MasterBrainTools(planner).status(args.task_id)
        elif args.command == "cancel":
            result = runtime.cancel(args.task_id, now())
        elif args.command == "foreground":
            if not 1 <= args.ticks <= 100 or not .01 <= args.interval <= 1:
                raise ProtocolError("bounded foreground scheduling required")
            for _ in range(args.ticks):
                runtime.tick()
                time.sleep(args.interval)
            result = runtime.report()
        else:
            server = RuntimeMcp(runtime)
            while True:
                line = sys.stdin.readline(65537)
                if not line:
                    break
                request = {}
                try:
                    if len(line) > 65536:
                        # Do not parse subsequent chunks as independent commands.
                        raise ProtocolError("oversized MCP request; transport closed")
                    request = json.loads(line)
                    if type(request) is not dict or request.get("jsonrpc") != "2.0":
                        raise ProtocolError("JSON-RPC 2.0 required")
                    reply = {"jsonrpc": "2.0", "id": request.get("id"), "result": server.request(request, now())}
                except (ValueError, KeyError, TypeError, PermissionError) as exc:
                    reply = {"jsonrpc": "2.0", "id": request.get("id") if type(request) is dict else None,
                             "error": {"code": -32602, "message": str(exc)}}
                if type(request) is dict and "id" in request:
                    print(json.dumps(reply), flush=True)
                if len(line) > 65536:
                    return
            return
        print(json.dumps(result, indent=2))
    finally:
        with_store.close()


if __name__ == "__main__":
    main()
