"""Separately approved non-admin preflight fixtures. NEVER launches Codex.

Not a worker/backend. Only exact bundled Python with fixed inlined fixtures.
No credentials, network, shell, service, account, ACL or production operation.
"""
import argparse
import ctypes
from ctypes import wintypes as w
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

CASES = ('identity', 'filesystem', 'containment', 'cancel', 'timeout', 'cpu', 'crash')
PACKAGE_SHA = '06a5eded7bcfc3ad2cbecf9140e47b88f6a65848c6929847f1de7dd8281791e0'
SID = 'S-1-5-21-3675741470-1525898003-3877381073-1000'


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def gate(case, approval_file, approved_hash):
    if os.name != 'nt': raise PermissionError('Native Windows required; no simulation substitutes')
    from dci.master.windows_native import require_identity, token_snapshot, local_appdata
    from dci.master.document_windows import reject_links
    identity=require_identity();token=token_snapshot()
    if identity['user'] != r'WIN-HQAAFGGU1AM\DirectiveCodex' or token['user_sid'] != SID:
        raise PermissionError('Reviewed host/SID required')
    base=local_appdata()/'Directive/DMB-DDB-cert-0011';reject_links(base)
    if Path(sys.executable) != base/'package/runtime/python/python.exe':raise PermissionError('Bundled interpreter required')
    if Path(approval_file) != base/'state/preflight-approval.json':raise PermissionError('Exact approval path required')
    reject_links(approval_file)
    if sha(approval_file) != approved_hash:raise PermissionError('Approval hash changed')
    grant=json.loads(Path(approval_file).read_text())
    fields={'version','approved','user_sid','starts','expires','cases','probe_sha256','package_sha256','canary_manifest_sha256'}
    if (set(grant)!=fields or grant['version']!=1 or grant['approved'] is not True
        or grant['user_sid']!=SID or grant['package_sha256']!=PACKAGE_SHA
        or grant['probe_sha256']!=sha(__file__) or type(grant['starts']) is not int or type(grant['expires']) is not int
        or not grant['starts']<=int(time.time())<grant['expires']<=grant['starts']+1800
        or type(grant['cases']) is not list or not set(grant['cases'])<=set(CASES) or case not in grant['cases']):
        raise PermissionError('No exact unexpired fixture approval')
    manifest=base/'package/DDB_PACKAGE_MANIFEST.json'
    if sha(manifest)!='8aa986c9a02f05fe1cd30fb18b957aa4610dd180e3e2866f23241197c33e5b0f':
        raise PermissionError('Reviewed package manifest required')
    inventory=json.loads(manifest.read_text())['files']
    for name in inventory:
        path=base/'package'/name;reject_links(path)
        if sha(path)!=inventory[name]:raise PermissionError('Package changed')
    actual={p.relative_to(base/'package').as_posix() for folder in ('app','runtime') for p in (base/'package'/folder).rglob('*') if p.is_file()}
    if actual!=set(inventory):raise PermissionError('Unlisted package/import file')
    out=base/'artifacts/preflight-10.5A'/case;reject_links(out)
    out.mkdir(parents=True,exist_ok=False) # Each case exactly once; never overwrite/retry.
    (out/'INTENT.json').write_text(json.dumps({'case':case,'approval_sha256':approved_hash,'identity':identity}))
    return base,out,identity,grant


def filesystem(base,out,grant):
    from dci.master.windows_native import dll
    from dci.master.document_windows import reject_links
    manifest=base/'state/approved-canaries.json';reject_links(manifest)
    if sha(manifest)!=grant['canary_manifest_sha256']:raise PermissionError('Exact independent canary manifest required')
    p=json.loads(manifest.read_text())
    if set(p)!={'host','creator','canaries'} or p['host']!='WIN-HQAAFGGU1AM' or p['creator']!=r'WIN-HQAAFGGU1AM\Administrator' or set(p['canaries'])!={'read','write'}:
        raise PermissionError('Existing harmless canary provenance required')
    own=out/'own-canary.txt';own.write_text('DMB harmless preflight\n')
    if own.read_text()!='DMB harmless preflight\n':raise PermissionError('Positive control failed')
    k=dll('kernel32');k.CreateFileW.argtypes=[w.LPCWSTR,w.DWORD,w.DWORD,ctypes.c_void_p,w.DWORD,w.DWORD,w.HANDLE];k.CreateFileW.restype=w.HANDLE
    k.CloseHandle.argtypes=[w.HANDLE];k.CloseHandle.restype=w.BOOL
    results={}
    for op,access in [('read',0x80000000),('write',0x40000000)]:
        item=p['canaries'][op];expected=Path(r'C:\Users\Administrator\AppData\Local\Directive\DMB-Isolation-Canary-v1\fixtures\v1')/(op+'-canary.txt')
        if set(item)!={'path','creator_verified_exists'} or Path(item['path'])!=expected or item['creator_verified_exists'] is not True:
            raise PermissionError('No approved existing canary; no production probes')
        h=k.CreateFileW(str(expected),access,7,None,3,0,None)
        if h!=ctypes.c_void_p(-1).value:k.CloseHandle(h);raise PermissionError('Isolation violation: canary open succeeded')
        code=ctypes.get_last_error();results[op]=code
        if code!=5:raise PermissionError('Only ACCESS_DENIED passes, never missing path')
    return {'positive_own_read_write':True,'canary_winerrors':results,'scope':'only exact independently evidenced canaries'}


def job(case,out):
    from dci.master.windows_native import dll,ExtendedLimits,Accounting,StartupInfo,ProcessInfo
    from dci.master.windows_codex_locator import native_handle,final_path,file_identity
    k=dll('kernel32')
    api={'CreateJobObjectW':([ctypes.c_void_p,w.LPCWSTR],w.HANDLE),
         'SetInformationJobObject':([w.HANDLE,ctypes.c_int,ctypes.c_void_p,w.DWORD],w.BOOL),
         'QueryInformationJobObject':([w.HANDLE,ctypes.c_int,ctypes.c_void_p,w.DWORD,ctypes.c_void_p],w.BOOL),
         'CreateProcessW':([w.LPCWSTR,w.LPWSTR,ctypes.c_void_p,ctypes.c_void_p,w.BOOL,w.DWORD,ctypes.c_void_p,w.LPCWSTR,ctypes.POINTER(StartupInfo),ctypes.POINTER(ProcessInfo)],w.BOOL),
         'AssignProcessToJobObject':([w.HANDLE,w.HANDLE],w.BOOL),'ResumeThread':([w.HANDLE],w.DWORD),
         'TerminateJobObject':([w.HANDLE,w.UINT],w.BOOL),'TerminateProcess':([w.HANDLE,w.UINT],w.BOOL),
         'GetExitCodeProcess':([w.HANDLE,ctypes.POINTER(w.DWORD)],w.BOOL),'CloseHandle':([w.HANDLE],w.BOOL),
         'QueryFullProcessImageNameW':([w.HANDLE,w.DWORD,w.LPWSTR,ctypes.POINTER(w.DWORD)],w.BOOL)}
    for name,(args,result) in api.items():getattr(k,name).argtypes=args;getattr(k,name).restype=result
    def check(ok):
        if not ok:raise ctypes.WinError(ctypes.get_last_error())
    handle=k.CreateJobObjectW(None,None);check(handle);pi=ProcessInfo();assigned=False
    def accounting():
        a=Accounting();check(k.QueryInformationJobObject(handle,1,ctypes.byref(a),ctypes.sizeof(a),None));return a
    start=time.monotonic();result={}
    try:
        limits=ExtendedLimits();limits.basic.flags=0x2000|0x200|0x4|0x8
        limits.basic.job_time=2*10000000;limits.basic.active_process_limit=2;limits.job_memory=64*1048576
        check(k.SetInformationJobObject(handle,9,ctypes.byref(limits),ctypes.sizeof(limits)))
        observed=ExtendedLimits();check(k.QueryInformationJobObject(handle,9,ctypes.byref(observed),ctypes.sizeof(observed),None))
        if observed.basic.flags!=limits.basic.flags or observed.basic.job_time!=limits.basic.job_time or observed.job_memory!=limits.job_memory or observed.basic.active_process_limit!=2:raise PermissionError('Job resource configuration differs')
        # Fixed code only; no command/prompt/path from a document is executed.
        code="import pathlib,time,sys,subprocess,json,os\nfrom dci.master.windows_native import require_identity,token_snapshot\nrequire_identity()\nt=token_snapshot()\nassert t['user_sid']=="+repr(SID)+"\np=pathlib.Path("+repr(str(out))+ ")\np.joinpath('started').write_text(json.dumps({'pid':os.getpid(),'user_sid':t['user_sid'],'integrity_sid':t['integrity_sid'],'elevated':t['elevated']}))\n"
        if case=='containment':code+="subprocess.Popen([sys.executable,'-I','-B','-c','import time;time.sleep(8)'])\ntime.sleep(8)\n"
        elif case=='cancel':code+="while not p.joinpath('STOP').exists():time.sleep(.02)\n"
        elif case=='cpu':code+="while True:pass\n"
        elif case=='crash':code+="sys.exit(73)\n"
        else:code+="time.sleep(8)\n"
        exe=Path(sys.executable)
        with native_handle(exe) as pinned:
            expected=file_identity(pinned);si=StartupInfo();si.cb=ctypes.sizeof(si)
            env={n:v for n,v in os.environ.items() if n.upper() in {'SYSTEMROOT','WINDIR','USERPROFILE','LOCALAPPDATA','TEMP','TMP'}}
            block=ctypes.create_unicode_buffer('\0'.join(n+'='+v for n,v in sorted(env.items()))+'\0\0')
            command=ctypes.create_unicode_buffer(subprocess.list2cmdline([str(exe),'-I','-B','-c',code]))
            check(k.CreateProcessW(str(exe),command,None,None,False,0x4|0x400|0x08000000,block,str(out),ctypes.byref(si),ctypes.byref(pi)))
            image=ctypes.create_unicode_buffer(32768);size=w.DWORD(len(image));check(k.QueryFullProcessImageNameW(pi.process,0,image,ctypes.byref(size)))
            with native_handle(image.value) as actual:
                if final_path(actual)!=final_path(pinned) or file_identity(actual)!=expected:raise PermissionError('Fixture image substituted')
            check(k.AssignProcessToJobObject(handle,pi.process));assigned=True
            if k.ResumeThread(pi.thread)==0xFFFFFFFF:raise ctypes.WinError(ctypes.get_last_error())
        deadline=start+(6 if case=='cpu' else 3);peak=0
        while time.monotonic()<deadline:
            a=accounting();peak=max(peak,a.active_processes)
            if (out/'started').exists() and case=='cancel':(out/'STOP').touch(exist_ok=True)
            if case=='containment' and peak>=2:break
            if case in {'cancel','cpu','crash'} and a.active_processes==0:break
            time.sleep(.02)
        if not (out/'started').exists():raise PermissionError('Fixture never started')
        if case=='containment' and peak<2:raise PermissionError('Descendant containment not observed')
        exitcode=w.DWORD();check(k.GetExitCodeProcess(pi.process,ctypes.byref(exitcode)))
        if case in {'cancel','cpu','crash'} and accounting().active_processes:raise PermissionError('Expected fixture stop not observed')
        if case=='timeout' and accounting().active_processes==0:raise PermissionError('Timeout fixture ended before containment deadline')
        if case=='cancel' and exitcode.value!=0:raise PermissionError('Cooperative fixture cancellation failed')
        if case=='cpu' and exitcode.value in (0,259):raise PermissionError('CPU-limited fixture did not terminate abnormally')
        if case=='crash' and exitcode.value!=73:raise PermissionError('Controlled crash exit differs')
        check(k.TerminateJobObject(handle,1));end=time.monotonic()+3
        while accounting().active_processes and time.monotonic()<end:time.sleep(.02)
        if accounting().active_processes:raise PermissionError('Owned job failed to drain')
        child_token=json.loads((out/'started').read_text())
        if child_token!={'pid':pi.pid,'user_sid':SID,'integrity_sid':'S-1-16-8192','elevated':False}:raise PermissionError('Fixture token mismatch')
        result={'child_token':child_token,'pid':pi.pid,'peak_active':peak,'active_after':0,'exit_before_cleanup':exitcode.value,'elapsed':round(time.monotonic()-start,3),'job_cpu_seconds':2,'job_memory_mib':64,'process_cap':2,'scope':'Python fixture only; not Codex/worker certification','memory_pressure_tested':False}
    finally:
        if pi.process and not assigned:k.TerminateProcess(pi.process,1)
        if assigned:k.TerminateJobObject(handle,1)
        for h in (pi.thread,pi.process,handle):
            if h:k.CloseHandle(h)
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('case',choices=CASES)
    p.add_argument('--approval-file',required=True);p.add_argument('--approval-sha256',required=True);a=p.parse_args()
    base,out,identity,grant=gate(a.case,a.approval_file,a.approval_sha256)
    try:
        evidence={'identity':identity,'case':a.case}
        if a.case=='filesystem':evidence.update(filesystem(base,out,grant))
        elif a.case!='identity':evidence.update(job(a.case,out))
        result={'status':'PASS_COMPONENT_SCOPE_ONLY','evidence':evidence}
    except Exception as e:result={'status':'BLOCKED_OR_FAILED_PRESERVED','category':type(e).__name__}
    temp=out/'RESULT.tmp';temp.write_text(json.dumps(result,indent=2));os.replace(temp,out/'RESULT.json')
    print(json.dumps(result));return 0 if result['status']=='PASS_COMPONENT_SCOPE_ONLY' else 1


if __name__=='__main__':
    try:raise SystemExit(main())
    except Exception as e:
        print(json.dumps({'status':'BLOCKED_PRESERVED','category':type(e).__name__}));raise SystemExit(1)
