"""Signed intake/review/follow-up across real processes; no RDP or external service.

Actual paper worker execution, local signed stdio transport. This is not remote
HTTPS delivery, Windows service survival, LLM supervision or human notification.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from dci.master.operations import BrainIdentity
from dci.master.operations_client import OperationsClient
from dci.master.windows_controller import AtomicPeerStore


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--workers',required=True);p.add_argument('--output',required=True);a=p.parse_args()
    out=Path(a.output).resolve()
    if out.exists() or ROOT in out.parents:raise PermissionError('Fresh isolated evidence directory outside repository required')
    out.mkdir(parents=True)
    now=int(time.time());secret=secrets.token_bytes(32)
    identity=BrainIdentity('shadow-brain-policy','ops-test',now+3600,frozenset({'intake','review','control','report'}),secret)
    private=out/'brain-identity.json'
    fd=os.open(private,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
    with os.fdopen(fd,'w') as f:json.dump({'principal':identity.principal,'key_id':identity.key_id,'expires':identity.expires,'scopes':sorted(identity.scopes),'secret_hex':secret.hex()},f)
    argv=[sys.executable,'-m','dci.master.operations_cli','--workspace',str(ROOT),'--database',str(out/'controller.sqlite'),'--workers',a.workers,'--identity-file',str(private),'--backend','paper']
    env={'PATH':'/usr/bin:/bin','LANG':'C.UTF-8','PYTHONDONTWRITEBYTECODE':'1','PYTHONPATH':str(ROOT/'src')}
    calls=[]
    def cli(command,packet=None):
        proc=subprocess.run(argv+[command],input=None if packet is None else json.dumps(packet),text=True,capture_output=True,env=env,timeout=30)
        if proc.returncode:raise RuntimeError('Operations process failed: '+proc.stderr[-1500:])
        calls.append({'command':command,'exit_code':proc.returncode})
        return json.loads(proc.stdout)
    store=AtomicPeerStore(out/'brain-client.sqlite')
    client=OperationsClient(store,identity,lambda packet:cli('exchange',packet))
    job={'task_id':'ops-first','correlation_id':'corr-ops-first','project_id':'DCI'}
    # Drop an actual committed reply. Retry twice and then restart Brain process state.
    def lost(packet):cli('exchange',packet);raise ConnectionError('Injected response loss after commit')
    client.transport=lost
    try:client.request('SUBMIT',job)
    except ConnectionError:pass
    else:raise RuntimeError('Expected isolated lost-reply fault did not occur')
    store.close();store=AtomicPeerStore(out/'brain-client.sqlite')
    client=OperationsClient(store,identity,lambda packet:cli('exchange',packet));client.recover()
    first=cli('tick');report=client.request('REPORT',{})
    review=report['reviews'][0]
    followup={'task_id':'ops-followup','correlation_id':'corr-ops-followup','project_id':'DCI','dependencies':['ops-first']}
    # This deterministic, bounded policy uses verified controller evidence only.
    # It is not an LLM/human strategic approval.
    client.request('REVIEW',{'task_id':review['task'],'scope_digest':review['scope'],'result_digest':review['result_digest'],'verdict':'ACCEPT','followup':followup})
    second=cli('tick');report=client.request('REPORT',{})
    for review in report['reviews']:
        client.request('REVIEW',{'task_id':review['task'],'scope_digest':review['scope'],'result_digest':review['result_digest'],'verdict':'ACCEPT'})
    report=client.request('REPORT',{})
    assert not report['reviews']
    events=[e['event_id'] for e in report['events']]
    ack=client.request('ACK_EVENTS',{'events':events});assert ack['human_approval'] is False
    client.request('SUBMIT',job);idle=cli('tick');assert not idle['executed']
    from dci.master.planner import PortfolioPlanner
    from dci.master.registry import PortfolioRegistry
    from dci.master.control_plane import ShadowControlPlane
    from dci.master.operations import Operations
    controller_store=AtomicPeerStore(out/'controller.sqlite')
    runtime=ShadowControlPlane(PortfolioPlanner(controller_store,PortfolioRegistry(ROOT/'portfolio/REGISTRY.v1.json'),a.workers,ROOT))
    ops=Operations(runtime,identity);controller_store.verify_audit()
    assert controller_store.db.execute('SELECT count(*) FROM executions').fetchone()[0]==2
    assert not controller_store.db.execute('SELECT 1 FROM master_locks').fetchone()
    result={'schema_version':1,'mode':'SHADOW','status':'LOCAL_AUTHENTICATED_OPERATIONS_WORKFLOW_PASS',
        'scope':'Actual independent Linux controller/worker processes over signed local stdio; synthetic paper data. No remote/Windows unattended certification.',
        'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        'completed_workers':first['executed']+second['executed'],'durable_executions':2,
        'lost_reply_recovered_from_outbox':True,'duplicate_executions':0,
        'review_bound_to_exact_result_and_scope':True,'automatic_bounded_followup':True,'delivery_ack_is_human_approval':False,
        'controller_process_invocations':len(calls),'audit_valid':True,'reservations_released':True,
        'remote_HTTPS_delivery':'BLOCKED_APPROVED_HOST_AND_PAIRING_REQUIRED','Windows_RDP_independence':'BLOCKED_INSTALLATION_APPROVAL_REQUIRED',
        'LLM_Brain':'DISABLED_NO_APPROVED_PROVIDER_COST','HEG_external_notifications':'DISABLED_APPROVAL_AND_CERTIFICATION_REQUIRED',
        'services_installed':False,'production_changes':False,
        'new_source_sha256':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in ['src/dci/master/operations.py','src/dci/master/operations_client.py','src/dci/master/operations_cli.py','src/dci/master/windows_operations_worker.py']}}
    (out/'WORKFLOW.json').write_text(json.dumps(result,indent=2)+'\n')
    controller_store.close();store.close()
    # Private runtime identity stays outside repository/evidence publication.
    print(json.dumps({k:result[k] for k in ['status','durable_executions','duplicate_executions','automatic_bounded_followup','audit_valid']}))


if __name__=='__main__':main()
