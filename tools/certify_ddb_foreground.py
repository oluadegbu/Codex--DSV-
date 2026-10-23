"""One approved foreground cycle; no scheduler or credential changes.

Network permission must cover this exact invocation. Existing private policy,
keys and SDK authentication are used unchanged. Any failed stage stops, retaining
journals. No blind retries, automatic expiry renewal, or shell/mailbox execution.
"""
import argparse
from datetime import datetime,timezone
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from dci.bridge.identity import require_non_admin
from dci.master.operations_cli import load_private_json
from dci.master.document_bridge import Policy,sha,validate_document
from dci.master.windows_controller import AtomicPeerStore


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--configuration-directory',required=True)
    p.add_argument('--approved-policy-sha256',required=True)
    p.add_argument('--output',required=True)
    args=p.parse_args();require_non_admin(ROOT)
    directory=Path(args.configuration_directory).resolve(strict=True)
    output=Path(args.output).resolve()
    if output.exists() or ROOT in output.parents:raise PermissionError('Fresh external evidence directory required')
    if os.name == 'nt':
        from dci.master.windows_native import require_identity, local_appdata
        from dci.master.document_windows import NAMESPACE, reject_links
        identity=require_identity(); base=local_appdata()/'Directive'/NAMESPACE
        if directory != base/'state' or output.parent != base/'artifacts':
            raise PermissionError('Only reviewed Windows state/evidence paths permitted')
        reject_links(directory); reject_links(output)
        configs={'worker':directory/'worker.dpapi','supervisor':directory/'controller.dpapi'}
    else:
        configs={r:directory/(r+'-config-renewed.json') for r in ('worker','supervisor')}
    values={r:load_private_json(path) for r,path in configs.items()}
    if values['worker']['policy']!=values['supervisor']['policy']:raise PermissionError('Exact paired policy required')
    config=values['worker'];policy=Policy(config['policy'],args.approved_policy_sha256,
        tuple(Policy(v,sha(v)) for v in config.get('retired_pre_dispatch_policies',[])))
    policy.check(int(time.time()))
    if policy.body['max_tasks']!=1 or policy.body['template']!='codex_shadow_review_v1':raise PermissionError('One native foreground effort only')
    if policy.body['expires']-int(time.time())<480:raise PermissionError('Insufficient grant lifetime; never renew silently')
    output.mkdir(mode=0o700)
    result={'schema_version':1,'started_at_utc':datetime.now(timezone.utc).isoformat(),
            'status':'FAILED_PRESERVED_FAIL_CLOSED','mode':'SHADOW','stages':[],
            'scheduler_installed':False,'credentials_changed':False,'production_changes':False}
    deadline=time.monotonic()+420
    try:
        # Each CLI invocation reopens durable state. The final worker invocation
        # is restart/replay: it must apply review without another native launch.
        for role in ('worker','supervisor','worker','supervisor','worker','supervisor'):
            remaining=deadline-time.monotonic()
            if remaining<=0:raise TimeoutError('Foreground deadline exhausted')
            argv=[sys.executable,'-B','-m','dci.master.document_cli','--workspace',str(ROOT),
                  '--configuration',str(configs[role]),'--approved-policy-sha256',args.approved_policy_sha256,
                  '--foreground-certification','controller' if role=='supervisor' else 'worker']
            env=dict(os.environ);env['PYTHONPATH']=str(ROOT/'src')
            process=subprocess.run(argv,cwd=ROOT,env=env,capture_output=True,text=True,timeout=min(90,remaining),shell=False)
            result['stages'].append({'role':role,'exit_code':process.returncode})
            if process.returncode:raise RuntimeError('Bounded stage failed; retain original journals; no retry')
            reply=json.loads(process.stdout)
            if reply.get('mode')!='SHADOW' or reply.get('audit_valid') is not True:raise PermissionError('Stage did not certify its audit')
        stores={r:AtomicPeerStore(values[r]['database']) for r in values}
        try:
            for store in stores.values():store.verify_audit()
            worker=stores['worker'];supervisor=stores['supervisor']
            runs=worker.db.execute('SELECT * FROM ddb_native_runs').fetchall()
            plans=supervisor.db.execute('SELECT * FROM ddb_plan').fetchall()
            if len(runs)!=1 or runs[0]['state']!='REVIEWED' or len(plans)!=1 or plans[0]['completed']!=1:
                raise PermissionError('One reviewed genuine execution and completed directive required')
            native=json.loads(runs[0]['evidence'])
            identity_valid = (native.get('kind')=='WINDOWS_NATIVE_CODEX' and native.get('identity')==identity) if os.name=='nt' else (native.get('kind')=='NATIVE_CODEX' and native.get('uid')==os.geteuid())
            if not identity_valid or native.get('turn_completed') is not True or native.get('exit_code')!=0:
                raise PermissionError('Paper/synthetic evidence cannot certify native task')
            root=base if os.name=='nt' else Path(config['native_pins']['workspace'])
            for name,checksum in native['files_sha256'].items():
                if name not in ({'stdout.log','stderr.log','review.json'} if os.name=='nt' else {'stdout.log','stderr.log'}):raise PermissionError('Unexpected artifact path')
                if hashlib.sha256((root/'artifacts/ddb-native'/runs[0]['task']/name).read_bytes()).hexdigest()!=checksum:
                    raise PermissionError('Native artifact changed')
            row=worker.db.execute("SELECT body FROM ddb_outbox WHERE json_extract(body,'$.kind')='REPORT' AND json_extract(body,'$.body.status')='SUCCEEDED'").fetchone()
            if row is None:raise PermissionError('Signed completion receipt required')
            receipt=json.loads(row[0]);validate_document(receipt,policy,int(time.time()))
            altered=dict(receipt,signature='0'*128)
            try:validate_document(altered,policy,int(time.time()))
            except PermissionError:pass
            else:raise PermissionError('Altered signature was accepted')
            try:validate_document(receipt,policy,receipt['expires_at'])
            except PermissionError:pass
            else:raise PermissionError('Expired receipt was accepted')
            result.update(status='WINDOWS_DDB_SINGLE_HANDOFF_PASS_ADDITIONAL_GATES_BLOCKED' if os.name=='nt' else 'FOREGROUND_CERTIFIED_READY_FOR_SCHEDULER_REVIEW',native_receipt=native,
                          signed_completion=receipt,duplicate_executions=0,native_executions=1,
                          restarted_worker_without_reexecution=True,audit_valid=True,
                          altered_signature_rejected=True,expired_receipt_rejected=True)
        finally:
            for store in stores.values():store.close()
    except Exception as error:
        result['failure_category']=type(error).__name__
    result['completed_at_utc']=datetime.now(timezone.utc).isoformat()
    (output/'CERTIFICATION.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'status':result['status'],'evidence':str(output/'CERTIFICATION.json')}))
    raise SystemExit(0 if result['status'] in {'FOREGROUND_CERTIFIED_READY_FOR_SCHEDULER_REVIEW','WINDOWS_DDB_SINGLE_HANDOFF_PASS_ADDITIONAL_GATES_BLOCKED'} else 1)


if __name__=='__main__':main()
