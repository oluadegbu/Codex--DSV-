"""Independent bounded foreground Runner/MCP facade, never installs a service."""
import argparse
import json
from pathlib import Path
import sys
import time
from dci.bridge.store import BridgeStore
from dci.bridge.heg import HumanGateway
from .registry import PortfolioRegistry
from .planner import PortfolioPlanner, Job, OPERATIONS
from .workers import MasterRunner
from .brain import MasterBrainTools, MasterMcpPrototype


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace',required=True);parser.add_argument('--database',required=True);parser.add_argument('--workers')
    sub=parser.add_subparsers(dest='command',required=True)
    sub.add_parser('report');sub.add_parser('tick');sub.add_parser('mcp')
    task=sub.add_parser('submit');task.add_argument('--task-id',required=True);task.add_argument('--correlation-id',required=True);task.add_argument('--project',required=True);task.add_argument('--operation',choices=sorted(OPERATIONS),default='verify_lab');task.add_argument('--depends',action='append',default=[]);task.add_argument('--priority',type=int,default=50)
    loop=sub.add_parser('foreground');loop.add_argument('--ticks',type=int,default=10);loop.add_argument('--interval',type=float,default=1)
    args=parser.parse_args();root=Path(args.workspace).resolve()
    store=BridgeStore(args.database)
    try:
        planner=PortfolioPlanner(store,PortfolioRegistry(root/'portfolio/REGISTRY.v1.json'),args.workers or root/'portfolio/WORKERS.v1.json',root)
        tools=MasterBrainTools(planner);runner=MasterRunner(planner)
        now=lambda:int(time.time())
        if args.command=='report': result=tools.report()
        elif args.command=='submit': result=planner.submit(Job(args.task_id,args.correlation_id,args.project,args.operation,args.priority,tuple(args.depends)),now())
        elif args.command=='tick': result=runner.tick(now());HumanGateway(store).tick(now())
        elif args.command=='foreground':
            if not 1<=args.ticks<=100 or not 0.01<=args.interval<=1:
                raise ValueError('bounded shadow foreground ticks/interval required')
            for _ in range(args.ticks):
                runner.tick(now());HumanGateway(store).tick(now());time.sleep(args.interval)
            result=tools.report()
        else:
            server=MasterMcpPrototype(tools)
            for line in sys.stdin:
                request={}
                try:
                    if len(line)>65536: raise ValueError('oversized request')
                    request=json.loads(line)
                    if request.get('jsonrpc')!='2.0': raise ValueError('JSON-RPC 2.0 required')
                    reply={'jsonrpc':'2.0','id':request.get('id'),'result':server.request(request,now())}
                except (ValueError,KeyError,TypeError,PermissionError) as exc:
                    reply={'jsonrpc':'2.0','id':request.get('id'),'error':{'code':-32602,'message':str(exc)}}
                if 'id' in request: print(json.dumps(reply),flush=True)
            return
        print(json.dumps(result,indent=2))
    finally:store.close()


if __name__=='__main__':main()
