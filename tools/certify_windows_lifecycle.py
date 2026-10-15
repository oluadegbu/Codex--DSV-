"""One foreground native certification run, never registers a task or edits security.

Real wall time, genuine Codex only. Failed scenarios are preserved and never rerun.
Loopback delivery is not remote or RDP-independent certification.
"""
import argparse
import ctypes
from ctypes import wintypes as w
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
SCENARIOS = ('success', 'cancel', 'crash')


def namespace(scenario):
    if scenario not in SCENARIOS: raise PermissionError('Compiled certification scenario required')
    return 'DMBWindowsWorker-cert-0.3.0-'+scenario


def private_config(path):
    from dci.master.windows_native import dpapi
    return json.loads(dpapi(path.read_bytes(), False))


def turn_started(root, child, task):
    """Read private logs locally; expose only owned PID and actual turn presence."""
    for receipt in (root/'state/attempts').glob('*/process-started.json'):
        value=json.loads(receipt.read_text())
        if value['bridge_pid'] != child.pid or value['task_id'] != task: continue
        log=receipt.parent/'stdout.log'
        if not log.exists(): continue
        with log.open('rb') as stream:
            for line in stream.read(1048577).splitlines():
                try: event=json.loads(line)
                except ValueError: continue
                if event.get('method')=='turn/started': return value['pid']
    return None


def observe_owned_exit(pid):
    # Hold an actual process handle BEFORE crashing its known parent; no PID reuse.
    from dci.master.windows_native import dll
    kernel=dll('kernel32')
    kernel.OpenProcess.argtypes=[w.DWORD,w.BOOL,w.DWORD];kernel.OpenProcess.restype=w.HANDLE
    kernel.WaitForSingleObject.argtypes=[w.HANDLE,w.DWORD];kernel.WaitForSingleObject.restype=w.DWORD
    kernel.CloseHandle.argtypes=[w.HANDLE];kernel.CloseHandle.restype=w.BOOL
    handle=kernel.OpenProcess(0x100000,False,pid)  # SYNCHRONIZE only; no terminate/access escalation.
    if not handle: raise PermissionError('Cannot observe owned Codex exit safely')
    def wait():
        try:
            if kernel.WaitForSingleObject(handle,5000)!=0: raise RuntimeError('Owned Codex did not exit after parent crash')
        finally: kernel.CloseHandle(handle)
    return wait


def launch(scenario, out, seconds=None, recovery=False, ownership_probe=False):
    argv=[sys.executable,'-I',str(Path(__file__).resolve()),'--child',scenario]
    if seconds is not None: argv+=['--seconds',str(seconds)]
    if recovery: argv+=['--recover-only']
    if ownership_probe: argv+=['--ownership-probe']
    # Exclusive create preserves all failed-run logs, no raw output in public evidence.
    index=len(list(out.glob('child-*.out')))
    with (out/('child-'+str(index)+'.out')).open('xb') as stdout, (out/('child-'+str(index)+'.err')).open('xb') as stderr:
        return subprocess.Popen(argv,cwd=ROOT,stdout=stdout,stderr=stderr)


def result(config, manifest, database, task):
    from run_windows_shadow_bridge import controller
    store, bridge=controller(config,manifest,database)
    try:
        store.verify_audit(); row=store.task(task)
        evidence=json.loads(row['result']) if row['result'] else None
        return {'state':row['state'],'attempts':row['attempts'],'evidence':evidence,
                'executions':store.db.execute('SELECT count(*) FROM executions').fetchone()[0],
                'held_resources':bridge.report()['held_resources'],'audit_valid':True}
    finally: store.close()


def scenario(name, full_hour, identity, out):
    from windows_package_runtime import create_tls_certificate
    from run_windows_shadow_bridge import ForegroundController,controller
    from dci.master.windows_native import private_root,dpapi
    from dci.master.windows_bridge_cli import prepare
    from dci.master.windows_worker import bridge_fingerprint
    private=private_root(namespace(name))
    # Never re-pair/retry a failed scenario or bypass its quarantine.
    if private.exists() and any(private.iterdir()): raise PermissionError('Prior certification namespace retained; inspect its evidence')
    private.mkdir(parents=True,exist_ok=True)
    folder=out/name;folder.mkdir()
    settings=folder/'pairing.dpapi';manifest=folder/'workers.json';database=folder/'controller.sqlite'
    cert=folder/'certificate.pem';key=folder/'private.key';create_tls_certificate(cert,key)
    prepare(ROOT,private/'controller-route',manifest,settings,'https://127.0.0.1:18443/v1/dmb/windows',identity['host'],28800,protected=True)
    config=private_config(settings);config['ca_file']=str(cert)
    with (private/'pairing.dpapi').open('xb') as stream:
        stream.write(dpapi(json.dumps(config).encode()));stream.flush();os.fsync(stream.fileno())
    task='native-'+name
    store,bridge=controller(config,manifest,database)
    try: bridge.submit({'task_id':task,'correlation_id':'corr-'+task,'project_id':'DCI'},int(time.time()))
    finally: store.close()
    start=time.monotonic();runs=[];actions=[]
    with ForegroundController(config,manifest,database,cert,key,18443):
        first_seconds=3300 if name=='success' and full_hour else 1
        child=launch(name,folder,seconds=first_seconds if name=='success' else None)
        try:
            if name=='success' and full_hour:
                limit=time.monotonic()+20
                while time.monotonic()<limit and child.poll() is None:
                    try:
                        with sqlite3.connect((private/'watchdog.sqlite').as_uri()+'?mode=ro',uri=True) as db:
                            if db.execute('SELECT state FROM watchdog WHERE id=1').fetchone()[0]=='ACTIVE': break
                    except sqlite3.Error: pass
                    time.sleep(.05)
                else: raise RuntimeError('Actual native lifecycle owner not observed')
                competitor=launch(name,folder,ownership_probe=True)
                try:
                    if competitor.wait(15)!=75: raise RuntimeError('Native competing owner was not denied')
                finally:
                    if competitor.poll() is None: competitor.terminate();competitor.wait(5)
                actions.append('Actual second DirectiveCodex process denied by held native exclusive byte lock')
            if name in ('cancel','crash'):
                deadline=time.monotonic()+35;pid=None
                while child.poll() is None and time.monotonic()<deadline:
                    pid=turn_started(private,child,task)
                    if pid is not None: break
                    time.sleep(.02)
                if pid is None: raise RuntimeError('Actual turn not observed; no retry or cancellation claim')
                if name=='cancel':
                    store,bridge=controller(config,manifest,database)
                    try: bridge.cancel(task,int(time.time()))
                    finally: store.close()
                    actions.append('Authenticated controller cancellation after actual turn/started')
                else:
                    wait=observe_owned_exit(pid)
                    try: child.terminate();child.wait(5)
                    finally: wait()
                    actions.append('Owned bridge terminated; actual owned Codex process handle signaled exit')
                    runs.append({'pid':child.pid,'exit':child.returncode,'injected_crash':True})
                    child=launch(name,folder,recovery=True)
            code=child.wait(timeout=first_seconds+45)
            runs.append({'pid':child.pid,'exit':code})
            if code: raise RuntimeError('Native certification child failed; private logs preserved')
            if name=='success':
                first=result(config,manifest,database,task)
                if first['state']!='SUCCEEDED' or first['executions']!=1: raise RuntimeError('Genuine completion absent')
                if full_hour:
                    # A real five-minute minimum gap and actual elapsed > one hour.
                    deadline=max(start+3605,time.monotonic()+300)
                    while time.monotonic()<deadline: time.sleep(min(5,deadline-time.monotonic()))
                    store,bridge=controller(config,manifest,database)
                    try: bridge.submit({'task_id':'native-after-hour','correlation_id':'corr-native-after-hour','project_id':'DCI'},int(time.time()))
                    finally: store.close()
                child=launch(name,folder,seconds=1);code=child.wait(45)
                runs.append({'pid':child.pid,'exit':code})
                if code: raise RuntimeError('Native normal rotation failed')
        finally:
            if child.poll() is None: child.terminate();child.wait(5)
    receipt=result(config,manifest,database,task)
    if name=='success':
        expected=2 if full_hour else 1
        if receipt['executions']!=expected or receipt['state']!='SUCCEEDED' or receipt['held_resources']:
            raise RuntimeError('Normal continuation/replay verification failed')
        if receipt['evidence']['fixture'] is not False or receipt['evidence']['remote_report']['identity']['execution_kind']!='WINDOWS_CODEX':
            raise RuntimeError('Only genuine Windows Codex may certify')
        if full_hour and (time.monotonic()-start<=3600 or result(config,manifest,database,'native-after-hour')['state']!='SUCCEEDED'):
            raise RuntimeError('Real hour boundary not passed')
    elif name=='cancel':
        report=receipt['evidence']['remote_report'] if receipt['evidence'] else {}
        if receipt['state']!='FAILED' or report.get('status')!='CANCELLED' or not report.get('interrupt_acknowledged') or report.get('job_active_processes')!=0:
            raise RuntimeError('Actual cancellation not certified; preserve evidence without retry')
    elif receipt['state']!='NEEDS_HUMAN' or not receipt['held_resources']:
        raise RuntimeError('Crash did not retain uncertainty quarantine')
    with sqlite3.connect((private/'state/bridge.sqlite').as_uri()+'?mode=ro',uri=True) as db:
        intents=sum(json.loads(row[0]).get('event')=='execution_intent' for row in db.execute('SELECT body FROM audit'))
    if intents != (2 if name=='success' and full_hour else 1): raise RuntimeError('Execution replay detected')
    return {'status':'PASS','scenario':name,'elapsed_seconds':time.monotonic()-start,'runs':runs,
            'actions':actions,'execution_intents':intents,'controller':receipt,'bridge_sha256':bridge_fingerprint()}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--full-hour',action='store_true');parser.add_argument('--isolation-manifest',type=Path,default=ROOT/'deployment/phase10/lifecycle-v0.3.0/CANARY_CREATOR.json')
    parser.add_argument('--child',choices=SCENARIOS);parser.add_argument('--seconds',type=int,default=1)
    parser.add_argument('--recover-only',action='store_true');parser.add_argument('--ownership-probe',action='store_true');args=parser.parse_args()
    from dci.master.windows_native import require_identity,private_root,foreground_lock
    identity=require_identity()  # Before using auth or modifying any file.
    from run_windows_lifecycle_host import HOST,USER_SID
    from dci.master.windows_native import token_snapshot
    if identity['host']!=HOST or token_snapshot()['user_sid']!=USER_SID:
        raise PermissionError('Exact approved host and existing local SID required')
    from windows_package_runtime import verify_package,initialize_package_git
    manifest=verify_package(ROOT,'0.3.0')
    if manifest is None: raise PermissionError('Pinned self-contained package required')
    if args.ownership_probe:
        if args.child!='success': raise PermissionError('Compiled ownership probe route required')
        from dci.master.windows_native import WorkerOwnershipError
        try:
            with foreground_lock(private_root(namespace('success'))):
                raise RuntimeError('Native owner unexpectedly absent')
        except WorkerOwnershipError: sys.exit(75)
    if args.child:
        from dci.master.windows_bridge_cli import _windows_run_locked
        if args.child=='success' and not args.recover_only:
            from dci.master.windows_operations_worker import run
            print(json.dumps(run(args.seconds,namespace=namespace(args.child))))
        else:
            with foreground_lock(private_root(namespace(args.child))):
                _windows_run_locked(1,namespace(args.child),recover_only=args.recover_only)
        return
    isolation=None
    expected_plan=ROOT/'deployment/phase10/lifecycle-v0.3.0/CANARY_CREATOR.json'
    if args.isolation_manifest.read_bytes()!=expected_plan.read_bytes():
        raise PermissionError('Exact independently verified bundled canary plan required')
    if args.isolation_manifest:
        from dci.master.windows_isolation import probe
        isolation=probe(args.isolation_manifest,'DMBWindowsWorker-ops-0.3.0')
        if isolation['OS_canary_access_denial']!='PASS':
            raise PermissionError('Independent real canary denial failed; no certification worker launched')
        local_plan=private_root('DMBWindowsWorker-ops-0.3.0')/'isolation-creator-manifest.json'
        if local_plan.exists():
            if local_plan.read_bytes()!=expected_plan.read_bytes(): raise PermissionError('Existing private canary plan preserved')
        else:
            with local_plan.open('xb') as stream:stream.write(expected_plan.read_bytes())
    initialize_package_git(ROOT,manifest)
    out=ROOT/'artifacts/windows-lifecycle-0.3.0';out.mkdir(parents=True,exist_ok=False)
    from dci.master.control_plane import atomic_json
    from dci.master.windows_worker import bridge_fingerprint
    evidence={'mode':'SHADOW','identity':identity,'package_source_commit':manifest['source_commit'],
              'bridge_sha256':bridge_fingerprint(),'RDP_independence':'NOT TESTED',
              'remote_delivery':'BLOCKED_APPROVED_ENDPOINT_REQUIRED','scheduled_task_registered':False,
              'production_changes':False,'gates':{},'status':'INCOMPLETE'}
    try:
        for name in SCENARIOS:
            evidence['gates'][name]=scenario(name,args.full_hour,identity,out)
            atomic_json(out/'CERTIFICATION.json',evidence)
        if isolation is not None:
            evidence['OS_access_denial']=isolation
        else: evidence['OS_access_denial']={'OS_canary_access_denial':'BLOCKED_INDEPENDENT_CANARY_REQUIRED'}
        evidence['beyond_one_hour']='PASS' if args.full_hour else 'NOT TESTED'
        evidence['status']='LOCAL_FOREGROUND_GATES_COMPLETE_NOT_UNATTENDED_CERTIFIED'
        if args.full_hour and evidence['OS_access_denial']['OS_canary_access_denial']=='PASS':
            acceptance={'identity':identity,'bridge_sha256':bridge_fingerprint(),
                        'genuine_task':'PASS','cancellation':'PASS','owned_worker_crash_recovery':'PASS',
                        'OS_access_denial':'PASS','beyond_one_hour':'PASS','exclusive_owner':'PASS',
                        'certification_sha256':hashlib.sha256(json.dumps(evidence,sort_keys=True).encode()).hexdigest(),
                        'scheduled_task_registered':False,'remote_delivery':'BLOCKED'}
            target=private_root('DMBWindowsWorker-ops-0.3.0')/'WINDOWS_ACCEPTANCE.json'
            with target.open('x',encoding='utf-8') as stream:
                json.dump(acceptance,stream,indent=2);stream.flush();os.fsync(stream.fileno())
    except BaseException as error:
        evidence['status']='BLOCKED';evidence['failure_class']=type(error).__name__
        raise
    finally:
        atomic_json(out/'CERTIFICATION.json',evidence)
        print(json.dumps({'status':evidence['status'],'evidence':str(out/'CERTIFICATION.json'),
                          'sha256':hashlib.sha256((out/'CERTIFICATION.json').read_bytes()).hexdigest()}))


if __name__=='__main__': main()
