"""One native Codex foreground effort; GitHub credential admission stays external.

Fixed existing DCI read-only review prompt. No persistent process, mailbox prompt,
Windows launch, auth enrollment, unrestricted shell or ambiguous-effect retry.
"""
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import time
from dci.bridge.hands import REVIEW_PROMPT
from dci.bridge.identity import require_non_admin
from dci.bridge.protocol import ProtocolError, canonical
from .windows_protocol import sha

TEMPLATE = 'codex_shadow_review_v1'


from .document_native_state import NativeReceiptBackend


class NativeForegroundBackend(NativeReceiptBackend):
    def __init__(self, store, pins, controller_workspace):
        if os.name != 'posix' or os.geteuid() == 0 or 0 in os.getgroups():
            raise PermissionError('Native foreground backend requires non-root Linux; Windows remains disabled')
        if set(pins) != {'workspace', 'git_commit', 'executable', 'executable_sha256', 'cli_version'}:
            raise PermissionError('Exact privately approved native pins required')
        self.store, self.pins = store, pins
        self.root = require_non_admin(pins['workspace'])
        controller = Path(controller_workspace).resolve(strict=True)
        if self.root == controller or self.root in controller.parents or controller in self.root.parents:
            raise PermissionError('Separate native worker clone required')
        self.executable = Path(pins['executable']).resolve(strict=True)
        if self.executable.is_symlink() or self.executable.stat().st_mode & 0o6022 or os.access(self.executable, os.W_OK):
            raise PermissionError('CLI must be non-setid, executable and not writable by worker')
        self.artifacts = self.root/'artifacts/ddb-native'
        with store.tx():
            store.db.execute('CREATE TABLE IF NOT EXISTS ddb_native_runs(task TEXT PRIMARY KEY,scope TEXT,state TEXT,evidence TEXT)')

    def preflight(self):
        self.store.verify_audit()
        if hashlib.sha256(self.executable.read_bytes()).hexdigest() != self.pins['executable_sha256']:
            raise PermissionError('Pinned native executable changed')
        version = subprocess.run([str(self.executable), '--version'], capture_output=True, text=True, timeout=5, check=True).stdout.strip()
        if version != self.pins['cli_version']: raise PermissionError('Pinned CLI version changed')
        login = subprocess.run([str(self.executable), 'login', 'status'], capture_output=True, text=True, timeout=5)
        if login.returncode or 'Logged in using ChatGPT' not in login.stdout+login.stderr:
            raise PermissionError('Existing supported ChatGPT authentication required; no API enrollment attempted')
        commit = subprocess.check_output(['git','rev-parse','HEAD'],cwd=self.root,timeout=5,text=True).strip()
        if commit != self.pins['git_commit'] or subprocess.check_output(['git','status','--porcelain'],cwd=self.root,timeout=5):
            raise PermissionError('Clean pinned development clone required')

    def _execute(self, task):
        directory = self.artifacts/task
        directory.mkdir(mode=0o700, parents=True, exist_ok=False)
        argv = [str(self.executable), 'exec', '--sandbox', 'read-only', '--json', '--ephemeral', '-C', str(self.root), '-']
        def limits():
            import resource
            resource.setrlimit(resource.RLIMIT_CPU,(10,10))
            resource.setrlimit(resource.RLIMIT_FSIZE,(1048576,1048576))
            resource.setrlimit(resource.RLIMIT_NOFILE,(128,128))
        with (directory/'stdout.log').open('xb') as output, (directory/'stderr.log').open('xb') as errors:
            process = subprocess.Popen(argv, cwd=self.root, stdin=subprocess.PIPE, stdout=output,
                                       stderr=errors, shell=False, start_new_session=True, preexec_fn=limits)
            try:
                owner = Path(f'/proc/{process.pid}').stat().st_uid
                if owner != os.geteuid(): raise PermissionError('Actual native process owner mismatch')
                process.communicate(REVIEW_PROMPT.encode(), timeout=20)
            finally:
                # Only this invocation's new process group; never unrelated workers.
                try: os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError: pass
                process.wait(timeout=3)
        for name in ('stdout.log','stderr.log'):
            if (directory/name).stat().st_size > 1048576: raise PermissionError('Native output exceeded fixed budget')
        events = []
        for line in (directory/'stdout.log').read_bytes().splitlines():
            try: events.append(json.loads(line))
            except ValueError: continue
        completed = any(e.get('type') == 'turn.completed' for e in events if isinstance(e,dict))
        failed = any(e.get('type') in {'turn.failed','error'} for e in events if isinstance(e,dict))
        response=any(e.get('type')=='item.completed' and isinstance(e.get('item'),dict) and e['item'].get('type')=='agent_message' and isinstance(e['item'].get('text'),str) and e['item']['text'].strip() for e in events if isinstance(e,dict))
        if process.returncode != 0 or not completed or failed or not response: raise PermissionError('No verified native Codex completion; private logs retained')
        self.preflight()
        return {'mode':'SHADOW','kind':'NATIVE_CODEX','task_id':task,'pid':process.pid,'uid':owner,
                'exit_code':0,'turn_completed':True,'git_commit':self.pins['git_commit'],
                'cli_sha256':self.pins['executable_sha256'],'cli_version':self.pins['cli_version'],
                'prompt_sha256':hashlib.sha256(REVIEW_PROMPT.encode()).hexdigest(),
                'files_sha256':{name:hashlib.sha256((directory/name).read_bytes()).hexdigest() for name in ('stdout.log','stderr.log')}}

    def verify(self, task, evidence):
        self.preflight()
        for name, expected in evidence['files_sha256'].items():
            if name not in {'stdout.log','stderr.log'}: raise ProtocolError('Unexpected native evidence path')
            p=self.artifacts/task/name
            if p.is_symlink() or hashlib.sha256(p.read_bytes()).hexdigest()!=expected: raise PermissionError('Native receipt artifact changed')
        if evidence['kind']!='NATIVE_CODEX' or evidence['uid']!=os.geteuid() or evidence['turn_completed'] is not True or evidence['exit_code']!=0:
            raise PermissionError('Native identity/completion mismatch')
