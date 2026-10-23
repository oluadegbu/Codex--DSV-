"""Native read-only canary probes, opt-in on a separately approved isolated host.

No Codex, ACL/account changes, fixture creation, or production path access.
Default CI/Linux run records NOT TESTED through explicit skips.
"""
import ctypes
from ctypes import wintypes as w
import json
import os
from pathlib import Path
import unittest


class NativeCanaryDenialTests(unittest.TestCase):
    def test_existing_reviewed_canary_denial(self):
        if os.name != 'nt': self.skipTest('Native Windows isolated account unavailable')
        from dci.master.windows_native import require_identity, local_appdata, dll
        try: identity=require_identity()
        except PermissionError: self.skipTest('No approved non-admin DirectiveCodex token; no elevation')
        if os.environ.get('DMB_APPROVED_CANARY_TEST') != 'REQUEST-0011-ISOLATED-ONLY':
            self.skipTest('Separate exact harmless canary authorization absent')
        path=local_appdata()/'Directive/DMB-DDB-cert-0011/state/approved-canaries.json'
        from dci.master.document_windows import reject_links
        reject_links(path); plan=json.loads(path.read_text())
        self.assertEqual(set(plan),{'host','creator','canaries'});self.assertEqual(plan['host'],identity['host'])
        self.assertEqual(plan['creator'],identity['host']+'\\Administrator')
        self.assertEqual(set(plan['canaries']),{'read','write'})
        kernel=dll('kernel32');kernel.CreateFileW.argtypes=[w.LPCWSTR,w.DWORD,w.DWORD,ctypes.c_void_p,w.DWORD,w.DWORD,w.HANDLE];kernel.CreateFileW.restype=w.HANDLE
        kernel.CloseHandle.argtypes=[w.HANDLE];kernel.CloseHandle.restype=w.BOOL
        for operation,access in [('read',0x80000000),('write',0x40000000)]:
            item=plan['canaries'][operation]
            expected=Path(r'C:\Users\Administrator\AppData\Local\Directive\DMB-Isolation-Canary-v1\fixtures\v1')/(operation+'-canary.txt')
            self.assertEqual(set(item),{'path','creator_verified_exists'});self.assertEqual(Path(item['path']),expected)
            self.assertIs(item['creator_verified_exists'],True)
            handle=kernel.CreateFileW(str(expected),access,7,None,3,0,None) # OPEN_EXISTING only
            if handle != ctypes.c_void_p(-1).value:
                kernel.CloseHandle(handle);self.fail('Unsafe canary access succeeded; stop certification')
            self.assertEqual(ctypes.get_last_error(),5,'Only ERROR_ACCESS_DENIED counts; missing is not denial')
