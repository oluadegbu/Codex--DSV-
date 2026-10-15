"""Native access-denial probes for approved harmless canaries, never production ACLs.

Caller supplies a locally approved, independently recorded creator manifest.
No missing file counts as denial. No ACL/account mutation or write of denied data.
"""
import ctypes
from ctypes import wintypes as w
import hashlib
import json
from pathlib import Path
from .windows_native import require_identity, private_root, dll

CANARY = b'DMB harmless access probe v1\n'


def probe(manifest_file, namespace="DMBWindowsWorker-ops-0.2.0-review1"):
    identity = require_identity()
    plan = json.loads(Path(manifest_file).read_text())
    if set(plan) != {'version', 'host', 'creator_identity', 'canaries'} or plan['version'] != 1 or plan['host'] != identity['host'] or type(plan['creator_identity']) is not str or not plan['creator_identity'].casefold().startswith(identity['host'].casefold()+'\\') or plan['creator_identity'].casefold() == identity['user'].casefold() or type(plan['canaries']) is not list or len(plan['canaries']) != 2:
        raise PermissionError('Exact independently recorded canary creator plan required')
    kernel = dll('kernel32')
    kernel.CreateFileW.argtypes = [w.LPCWSTR,w.DWORD,w.DWORD,ctypes.c_void_p,w.DWORD,w.DWORD,w.HANDLE]
    kernel.CreateFileW.restype = w.HANDLE
    kernel.CloseHandle.argtypes = [w.HANDLE]; kernel.CloseHandle.restype = w.BOOL
    def attempt(path, access):
        handle = kernel.CreateFileW(str(path), access, 7, None, 3, 0, None)  # OPEN_EXISTING, never CREATE
        if handle == ctypes.c_void_p(-1).value:
            return ctypes.get_last_error()
        kernel.CloseHandle(handle)
        return 0
    own = private_root(namespace)/'operations-isolation'
    own.mkdir(exist_ok=True)
    positive = own/'own-canary.txt'
    if not positive.exists():
        with positive.open('xb') as file:file.write(CANARY)
    if positive.read_bytes() != CANARY or attempt(positive,0x80000000) or attempt(positive,0x40000000):
        raise PermissionError('Positive access control failed; negative tests cannot certify isolation')
    seen=set();results=[]
    for item in plan['canaries']:
        if type(item) is not dict or set(item) != {'path','operation','sha256','creator_verified_exists'} or item['operation'] not in {'read','write'} or item['operation'] in seen or item['sha256'] != hashlib.sha256(CANARY).hexdigest() or item['creator_verified_exists'] is not True:
            raise PermissionError('Independent harmless canary existence/hash evidence required')
        path = Path(item['path'])
        # A fixed non-production user-profile fixture location only; no mailbox paths.
        if not path.is_absolute() or path.drive.casefold() != 'c:' or len(path.parts) != 10 or tuple(p.casefold() for p in path.parts[1:2]) != ('users',) or tuple(p.casefold() for p in path.parts[3:-1]) != ('appdata','local','directive','dmb-isolation-canary-v1','fixtures','v1') or path.name != item['operation']+'-canary.txt' or path.parts[2].casefold() != plan['creator_identity'].split('\\')[-1].casefold() or path.parts[2].casefold() == 'directivecodex' or '..' in path.parts:
            raise PermissionError('Canary path outside fixed existing other-profile fixture boundary')
        seen.add(item['operation'])
        error = attempt(path,0x80000000 if item['operation']=='read' else 0x40000000)
        results.append({'operation':item['operation'],'path':str(path),'winerror':error,
                        'status':'PASS' if error==5 else ('FAIL' if error==0 else 'NOT TESTED')})
    return {'mode':'SHADOW','identity':identity,'positive_read_write':'PASS','negative_probes':results,
            'OS_canary_access_denial':'PASS' if all(r['status']=='PASS' for r in results) else 'BLOCKED',
            'scope':'Specific existing other-account harmless canaries only; not full hostile-code confinement',
            'ACLs_changed':False,'production_changes':False,'denied_files_modified':False}
