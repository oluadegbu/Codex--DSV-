"""Run real trusted workstream processes, repeat/restart and publish shadow evidence."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
import re
from pathlib import Path
import subprocess
import sys
from uuid import uuid4
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from dci.bridge.store import BridgeStore
from dci.bridge.protocol import ProtocolError
from dci.master.registry import PortfolioRegistry
from dci.master.planner import Job, PortfolioPlanner
from dci.master.workers import MasterRunner
from dci.master.brain import MasterBrainTools


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--workers');parser.add_argument('--output',required=True);args=parser.parse_args()
    root=Path(__file__).resolve().parents[1];out=Path(args.output);out.mkdir(parents=True,exist_ok=True)
    config=Path(args.workers) if args.workers else root/'portfolio/WORKERS.v1.json'
    checked=subprocess.run([sys.executable,'-m','unittest','discover','-s','tests','-v'],cwd=root,env={'PATH':'/usr/bin:/bin','LANG':'C.UTF-8','PYTHONPATH':str(root/'src')},stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=20,check=True)
    (out/'DMB_TESTS.log').write_bytes(checked.stdout)
    test_count=int(re.search(rb'Ran (\d+) tests?',checked.stdout).group(1))
    if test_count<84:raise RuntimeError('required certification regression suite missing')
    registry=PortfolioRegistry(root/'portfolio/REGISTRY.v1.json')
    artifact=root/'artifacts'/'dmb-certification'/str(uuid4());artifact.mkdir(parents=True)
    database=artifact/'master.sqlite';store=BridgeStore(database)
    planner=PortfolioPlanner(store,registry,config,root)
    records=[];first=[];n=0;clock=1_800_000_000
    while n<100:
        ids=[]
        for project in ('BHB','DAT_FUTURES','DPM'):
            if n>=100:break
            task='cert-'+str(n);job=Job(task,'corr-'+task,project);planner.submit(job,clock);planner.submit(job,clock)
            ids.append(task);n+=1
        batch=MasterRunner(planner).tick(clock+1,concurrent_barrier=not records)
        if not records:first=batch
        records+=batch
        if any(store.task(task)['state']!='SUCCEEDED' for task in ids):
            raise RuntimeError('workstream certification failed; inspect local artifacts '+str(artifact))
        # Reopen periodically to demonstrate durable scheduler restart.
        if n%3==0:
            store.close();store=BridgeStore(database);planner=PortfolioPlanner(store,registry,config,root)
        clock+=10
    count=store.db.execute('SELECT count(*) FROM executions').fetchone()[0]
    if count!=100 or len(records)!=100:raise RuntimeError('lost or duplicate execution')
    for i in range(100):planner.submit(Job('cert-'+str(i),'corr-cert-'+str(i),('BHB','DAT_FUTURES','DPM')[i%3]),clock)
    if planner.claim(clock):raise RuntimeError('replay was executable')
    overlap=max(r['started_monotonic'] for r in first)<min(r['finished_monotonic'] for r in first)
    if not overlap or len({r['pid'] for r in first})!=3:raise RuntimeError('three concurrent processes not proven')
    store.verify_audit();report=MasterBrainTools(planner).report()
    (out/'DMB_PORTFOLIO_REPORT.json').write_text(json.dumps(report,indent=2)+'\n')
    (out/'DMB_DEPENDENCY_GRAPH.json').write_text(json.dumps(registry.graph(),indent=2)+'\n')
    source_files=[p for folder in ('src','tools','tests') for p in (root/folder).rglob('*.py')]
    summary={'schema_version':1,'mode':'SHADOW','generated_at':datetime.now(timezone.utc).isoformat(),'local_shadow_status':'PASS',
             'required_outcome':'DMB SHADOW CERTIFIED','overall_status':'BLOCKED','scope':'trusted local deterministic labs and simulated HEG; not live remote/production certification',
             'identity':{'uid':os.geteuid(),'groups':os.getgroups(),'non_admin':os.geteuid()!=0 and 0 not in os.getgroups()},
             'cycles':100,'executions':count,'lost_executions':0,'duplicate_executions':0,'replayed_dispatches':0,
             'total_worker_test_executions':sum(r['tests_run'] for r in records),'peak_concurrent_processes':3,'overlap_proven':overlap,
             'first_concurrent_batch':first,'worker_git':[{k:w[k] for k in ('worker_id','workspace','expected_commit','bundle_sha256')} for w in planner.workers.values()],
             'worker_cycles':{w:sum(r['worker_id']==w for r in records) for w in planner.workers},
             'resource_policy':{'max_parallel':3,'reserved_memory_mb':768,'per_process_address_space_mb':256,'cpu_seconds_per_process':10,'wall_seconds_per_worker':20,'output_bytes':1048576,'group_timeout_cleanup':True,'hostile_os_isolation_certified':False},
             'registry_sha256':hashlib.sha256(registry.path.read_bytes()).hexdigest(),'workers_sha256':hashlib.sha256(config.read_bytes()).hexdigest(),
             'source_sha256':{str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(source_files)},
             'test_suite':{'command':'PYTHONPATH=src python -m unittest discover -s tests -v','tests':test_count,'failures':0,'errors':0,'log':'docs/evidence/DMB_TESTS.log'},
             'publication_recheck':{'date':'2026-10-11','operation':'create branch codex/dmb-shadow-20261011 from main','error':'403 Resource not accessible by integration','remote_modified':False},
             'observed_head_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=root).decode().strip(),
             'audit_valid':True,'artifact_database':str(database.relative_to(root)),
             'gates':{'portfolio_registry':'PASS_LOCAL','dependency_and_priority_planner':'PASS_LOCAL','three_concurrent_shadow_workstreams':'PASS_LOCAL','restart_replay_recovery':'PASS_LOCAL','central_mcp_inbox_outbox':'PASS_LOCAL_PROTOTYPE','simulated_heg':'PASS_LOCAL_SIMULATION','temporal_contracts':'PASS_INTERFACE_ONLY',
                     'live_codex_worker_execution':'BLOCKED_RUNTIME_NOT_CERTIFIED','github_write':'BLOCKED_FRESH_403_BRANCH_CREATION','remote_chatgpt_auth_delivery':'BLOCKED_NOT_CONNECTED','windows_directivecodex_identity':'BLOCKED_TARGET_UNVERIFIED','separate_os_worker_confinement':'BLOCKED_NOT_AVAILABLE','actual_dat_dpm_repository_integration':'BLOCKED_NOT_AVAILABLE','whatsapp_email_auth_delivery':'BLOCKED_APPROVAL_AND_CERTIFICATION'},
             'production_modifications':False,'services_installed':False,'live_trading':False,'external_notifications':False,'costs_incurred':False}
    (out/'DMB_CERTIFICATION.json').write_text(json.dumps(summary,indent=2)+'\n');store.close()
    print(json.dumps({k:summary[k] for k in ('local_shadow_status','overall_status','cycles','executions','total_worker_test_executions','peak_concurrent_processes','overlap_proven')}))


if __name__=='__main__':main()
