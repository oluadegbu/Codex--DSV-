"""Additive local evidence checks. Never rewrites prior DMB certification/bundle."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from uuid import uuid4
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from dci.bridge.store import BridgeStore
from dci.master.registry import PortfolioRegistry
from dci.master.planner import PortfolioPlanner, Job
from dci.master.workers import MasterRunner, WorkerAdapter


def main():
    out=ROOT/'docs/evidence/phase8';out.mkdir(parents=True,exist_ok=True)
    baseline=json.loads((out/'BASELINE.json').read_text())
    for relative,evidence in baseline['artifacts'].items():
        if relative=='BUILD_STATE.json':continue # retained separately before milestone update
        if hashlib.sha256((ROOT/relative).read_bytes()).hexdigest()!=evidence['sha256']:
            raise RuntimeError('preserved baseline artifact changed: '+relative)
    original=Path(baseline['bundle']['path'])
    if hashlib.sha256(original.read_bytes()).hexdigest()!=baseline['bundle']['sha256']:
        raise RuntimeError('original portable Git bundle changed')
    for relative,expected in json.loads((ROOT/'docs/evidence/DMB_CERTIFICATION.json').read_text())['source_sha256'].items():
        if hashlib.sha256((ROOT/relative).read_bytes()).hexdigest()!=expected:
            raise RuntimeError('previously certified source changed: '+relative)
    env={'PATH':'/usr/bin:/bin','LANG':'C.UTF-8','PYTHONPATH':str(ROOT/'src')}
    proc=subprocess.run([sys.executable,'-m','unittest','discover','-s','tests','-v'],cwd=ROOT,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=20,check=True)
    (out/'TESTS.log').write_bytes(proc.stdout)
    count=int(re.search(rb'Ran (\d+) tests?',proc.stdout).group(1))
    if count!=100:raise RuntimeError('expected preserved 84 plus 16 additive tests')
    artifact=ROOT/'artifacts/phase8'/str(uuid4());artifact.mkdir(parents=True)
    registry=PortfolioRegistry(ROOT/'portfolio/REGISTRY.v1.json');workers=ROOT/'portfolio/WORKERS.v1.json'
    db=artifact/'independent.sqlite';store=BridgeStore(db);planner=PortfolioPlanner(store,registry,workers,ROOT)
    now=int(datetime.now(timezone.utc).timestamp())
    for i,p in enumerate(('BHB','DAT_FUTURES','DPM')):planner.submit(Job('independent-'+str(i),'correlation-'+str(i),p),now)
    store.close()
    argv=[sys.executable,'-m','dci.master','--workspace',str(ROOT),'--database',str(db)]
    proc=subprocess.run(argv+['foreground','--ticks','1','--interval','.01'],cwd=ROOT,env=env,capture_output=True,text=True,timeout=25,check=True)
    report=json.loads(proc.stdout)
    if not all(j['state']=='SUCCEEDED' for j in report['jobs']) or len(report['jobs'])!=3:raise RuntimeError('independent runner continuation failed')
    restarted=json.loads(subprocess.check_output(argv+['report'],cwd=ROOT,env=env,text=True,timeout=5))
    if restarted['total_counts']['jobs']!=3 or not restarted['audit_chain_valid']:raise RuntimeError('process restart audit failed')
    evidence={'schema_version':1,'status':'PASS','scope':'isolated local process checks; actual connected-service outages NOT TESTED','tests':{'original_preserved':84,'new_offline_contract':16,'total_passed':count,'failed':0,'log':'docs/evidence/phase8/TESTS.log'},'prior_certification_preserved':True,'prior_source_files_unchanged':35,'prior_bundle_unchanged':True,'independent_process':{'argv':argv+['foreground','--ticks','1','--interval','.01'],'env_variable_names':sorted(env),'job_states':{j['task']:j['state'] for j in report['jobs']},'all_controlplane_connections_absent':['DSV','OpenClaw','ChatGPT'],'process_restart_audit':'PASS','actual_connected_services_stopped':False,'interpretation':'Combined control-plane absence fixture; no live DSV/OpenClaw outage or ChatGPT webhook disconnect induced'},'worker_crash':{}}
    # Actual SIGKILL of a synthetic child, never another service or worker.
    crashdb=artifact/'crash.sqlite';store=BridgeStore(crashdb);planner=PortfolioPlanner(store,registry,workers,ROOT)
    for i,p in enumerate(('BHB','DAT_FUTURES','DPM')):planner.submit(Job('crash-'+str(i),'crash-correlation-'+str(i),p),now)
    observed={}
    class CrashAdapter:
        def execute(self,job,barrier=None):
            if job['worker']!='bhb_heg':return WorkerAdapter(ROOT).execute(job)
            child=subprocess.run([sys.executable,'-I','-c','import os, signal; os.kill(os.getpid(), signal.SIGKILL)'],cwd=job['workspace'],env={'PATH':'/usr/bin:/bin'},timeout=3)
            observed['exit_code']=child.returncode
            return {'task_id':job['id'],'scope_digest':job['scope_digest'],'workspace':job['workspace'],'worker_id':job['worker'],'outcome':'AMBIGUOUS','passed':False,'fault':'synthetic child SIGKILL; not actual Codex process','exit_code':child.returncode}
    MasterRunner(planner,CrashAdapter()).tick(now+1)
    store.close();store=BridgeStore(crashdb);planner=PortfolioPlanner(store,registry,workers,ROOT)
    state={row['id']:row['state'] for row in store.db.execute('SELECT id,state FROM tasks')}
    locks=[dict(row) for row in store.db.execute('SELECT * FROM master_locks')]
    if state!={'crash-0':'NEEDS_HUMAN','crash-1':'SUCCEEDED','crash-2':'SUCCEEDED'} or len(locks)!=1 or observed['exit_code']!=-9:
        raise RuntimeError('worker crash/restart fencing failed')
    planner.submit(Job('unrelated','unrelated-corr','DAT_MT5'),now+10)
    result=MasterRunner(planner).tick(now+11)
    if store.task('unrelated')['state']!='SUCCEEDED':raise RuntimeError('unrelated safe continuation failed')
    store.verify_audit()
    evidence['worker_crash']={'fault':'SIGKILL only a newly started synthetic child','actual_exit_code':observed['exit_code'],'job_states_after_restart':state,'retained_locks':locks,'unrelated_continuation':'SUCCEEDED','reservation_retained':True,'audit':'PASS','automatic_uncertain_retry':False,'actual_codex_cancellation':'NOT TESTED; Codex initialization blocked'}
    evidence['new_sources_sha256']={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in ('src/dci/master/event_contract.py','tests/test_phase8.py','tools/verify_phase8.py')}
    evidence['generated_at']=datetime.now(timezone.utc).isoformat();evidence['observed_git_head']=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT).decode().strip()
    evidence['identity']={'uid':os.geteuid(),'groups':os.getgroups()};store.close()
    (out/'LOCAL_RESILIENCE.json').write_text(json.dumps(evidence,indent=2)+'\n')
    print(json.dumps({'regressions_passed':count,'preserved_regressions':84,'new_contract_tests':16,'independent_worker_jobs':3,'crash_outcome':state,'full_certification':'BLOCKED'}))


if __name__=='__main__':main()
