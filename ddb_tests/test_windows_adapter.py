"""Offline contracts/fixtures only. Never launches Codex or enrolls credentials."""
import copy
import json
from pathlib import Path
import tempfile
import time
import unittest
from dci.master.document_windows import ReviewMachine, drive_review, check_layout, FILES, PIN_KEYS
from dci.master.document_native_state import NativeReceiptBackend
from dci.master.document_bridge import Policy, Supervisor, Worker
from dci.master.windows_protocol import sha
from dci.bridge.protocol import ProtocolError
from test_document_bridge import DDBTests


class FixtureProcess:
    def __init__(self, directory, scenario='complete'):
        self.directory, self.scenario = directory, scenario
        self.sent, self.closed, self.terminated = [], False, False
        self.pid = 123
        (directory/'stdout.log').write_bytes(b''); (directory/'stderr.log').write_bytes(b'')
    def send(self, msg):
        self.sent.append(msg)
        if 'id' not in msg: return
        i = msg['id']
        if i == 1: e = {'id':1,'result':{}}
        elif i == 2: e = {'id':2,'result':{'cwd':'scratch','approvalPolicy':'never','sandbox':{'type':'readOnly','networkAccess':False},'thread':{'id':'t'}}}
        elif i == 3:
            if self.scenario in ('timeout','dead'): return
            frames=[{'id':3,'result':{'turn':{'id':'u'}}}]
            if self.scenario == 'complete':
                frames += [{'method':'item/completed','params':{'threadId':'t','turnId':'u','item':{'type':'agentMessage','text':json.dumps({'mode':'SHADOW','review':'Fixture-only review'})}}}, {'method':'turn/completed','params':{'threadId':'t','turn':{'id':'u','status':'completed'}}}]
            for e in frames: self.append(e)
            return
        elif i == 4:
            self.append({'id':4,'result':{}})
            e={'method':'turn/completed','params':{'threadId':'t','turn':{'id':'u','status':'interrupted'}}}
        else: return
        self.append(e)
    def append(self, e):
        with (self.directory/'stdout.log').open('ab') as f: f.write(json.dumps(e).encode()+b'\n')
    def active(self): return 0 if self.scenario == 'dead' else 1
    def terminate(self): self.terminated=True; return 0
    def close(self): self.closed=True


class WindowsAdapterTests(unittest.TestCase):
    def machine(self): return ReviewMachine('scratch', {f:'fixture source' for f in FILES})
    def test_branch_isolation_and_original_protocol_unchanged(self):
        from dci.master.document_github import GitHubDocuments, WindowsGitHubDocuments
        self.assertEqual(GitHubDocuments.branch, 'coordination/dmb-ddb-v1')
        self.assertEqual(WindowsGitHubDocuments.branch, 'coordination/dmb-ddb-windows-0011')
        with self.assertRaises(PermissionError): WindowsGitHubDocuments('other/repo',lambda:'fixture')
    def test_fixed_context_and_schema(self):
        prompt,schema=self.machine().task_input();self.assertIn(FILES[0],prompt);self.assertFalse(schema['additionalProperties'])
        with self.assertRaises(PermissionError): ReviewMachine('scratch',{'C:/production':'no'})
    def test_workspace_rejection(self):
        with tempfile.TemporaryDirectory() as d:
            base=Path(d)
            for child in ('worker-clone','state','package/app'): (base/child).mkdir(parents=True)
            pins={k:None for k in PIN_KEYS};pins.update(workspace=str(base/'worker-clone'),state_directory=str(base/'state'),git_executable=str(base/'package/runtime/git/cmd/git.exe'),files_sha256={f:'0'*64 for f in FILES})
            check_layout(pins,base/'package/app',base)
            pins['workspace']=str(base/'other')
            with self.assertRaises(PermissionError):check_layout(pins,base/'package/app',base)
    def test_reparse_equivalent_rejected(self):
        from dci.master.document_windows import reject_links
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'real').mkdir();
            try: (root/'link').symlink_to(root/'real',target_is_directory=True)
            except OSError: self.skipTest('symlink creation unavailable; no privilege changes')
            with self.assertRaises(PermissionError):reject_links(root/'link')
    def test_tools_rejected(self):
        m=self.machine();out=m.receive({'id':99,'method':'item/commandExecution/requestApproval'})
        self.assertTrue(m.blocked);self.assertIn('error',out[0])
    def test_artifact_and_route_rejected(self):
        m=self.machine()
        for text in ('{}','{"mode":"LIVE","review":"x"}','{"mode":"SHADOW","review":"x","extra":1}'):
            with self.assertRaises(ProtocolError):m.accept_artifact(text)
        with self.assertRaises(ProtocolError):m.receive({'method':'turn/completed','params':{'threadId':'wrong','turn':{'id':'u','status':'completed'}}})
    def test_effective_sandbox_rejected(self):
        with self.assertRaises(PermissionError):self.machine().receive({'id':2,'result':{'cwd':'scratch','approvalPolicy':'never','sandbox':{'type':'dangerFullAccess'},'thread':{'id':'t'}}})
    def test_completion_cleanup(self):
        with tempfile.TemporaryDirectory() as d:
            p=FixtureProcess(Path(d));result=drive_review(p,self.machine(),Path(d),lambda:False,1)
            self.assertEqual(result['mode'],'SHADOW');self.assertTrue(p.closed and p.terminated)
    def test_timeout_cleanup(self):
        with tempfile.TemporaryDirectory() as d:
            p=FixtureProcess(Path(d),'timeout')
            with self.assertRaises(PermissionError):drive_review(p,self.machine(),Path(d),lambda:False,.12)
            self.assertTrue(p.closed and p.terminated)
    def test_cancel_acknowledgement_and_cleanup(self):
        with tempfile.TemporaryDirectory() as d:
            p=FixtureProcess(Path(d),'cancel');m=self.machine()
            with self.assertRaises(PermissionError):drive_review(p,m,Path(d),lambda:True,1)
            self.assertTrue(m.interrupt_acked and m.cancel_requested and p.closed)
    def test_process_failure_cleanup(self):
        with tempfile.TemporaryDirectory() as d:
            p=FixtureProcess(Path(d),'dead')
            with self.assertRaises(ProtocolError):drive_review(p,self.machine(),Path(d),lambda:False,1)
            self.assertTrue(p.closed and p.terminated)
    def test_non_windows_constructor_fails_before_launch(self):
        import os
        from dci.master.document_windows import WindowsForegroundBackend
        if os.name != 'nt':
            with self.assertRaises(PermissionError):WindowsForegroundBackend(None,{},'.')


class ReceiptFixture(NativeReceiptBackend):
    def __init__(self,store,fail=False):
        self.store,self.pins,self.calls,self.fail=store,{'fixture':True,'git_commit':'2'*40},0,fail
        with store.tx():store.db.execute('CREATE TABLE IF NOT EXISTS ddb_native_runs(task TEXT PRIMARY KEY,scope TEXT,state TEXT,evidence TEXT)')
    def preflight(self):self.store.verify_audit()
    def _execute(self,task):
        self.calls+=1
        if self.fail:raise RuntimeError('controlled fixture crash')
        return {'files_sha256':{'stdout.log':'1'*64},'git_commit':'2'*40}
    def verify(self,task,evidence):pass


class ReceiptContractTests(DDBTests):
    def setup_native(self):
        body=copy.deepcopy(self.policy.body);body.update(template='codex_shadow_review_v1',max_tasks=1)
        self.policy=Policy(body,sha(body));self.root=self.root/'native';self.root.mkdir()
        self.super=self.node('supervisor');self.worker=self.node('worker')
        self.s=Supervisor(self.super);self.backend=ReceiptFixture(self.worker.store);self.w=Worker(self.worker,self.backend)
    def test_signed_fixture_cycle_and_duplicate(self):
        self.setup_native();self.handoff();self.w.execute_one(self.now);self.worker.flush(self.now);self.s.poll(self.now);self.super.flush(self.now);self.w.poll(self.now);self.w.apply_reviews(self.now)
        self.assertEqual(self.backend.calls,1)
        self.assertEqual(self.worker.store.db.execute('SELECT state FROM ddb_native_runs').fetchone()[0],'REVIEWED')
        self.w.poll(self.now);self.w.execute_one(self.now);self.assertEqual(self.backend.calls,1)
    def test_sealed_recovery_no_second_effect(self):
        self.setup_native();d={'template':'codex_shadow_review_v1','task_id':'fixture'}
        a=self.backend.run(d,self.now);new=ReceiptFixture(self.worker.store);b=new.run(d,self.now)
        self.assertEqual(a,b);self.assertEqual(new.calls,0)
    def test_uncertain_intent_never_reruns(self):
        self.setup_native();self.backend.fail=True;d={'template':'codex_shadow_review_v1','task_id':'fixture'}
        with self.assertRaises(RuntimeError):self.backend.run(d,self.now)
        restarted=ReceiptFixture(self.worker.store);self.assertIsNone(restarted.run(d,self.now));self.assertEqual(restarted.calls,0)
        with self.assertRaises(PermissionError):restarted.run({**d,'extra':'rebound'},self.now)
    def test_signature_tampering_before_worker(self):
        self.setup_native();self.handoff()
        key=next(p for p in self.branch.files if p.startswith('directives/pending/'))
        value=json.loads(self.branch.files[key]);value['signature']='00'*64;self.branch.files[key]=json.dumps(value)
        with self.assertRaises((PermissionError, ProtocolError)):self.w.poll(self.now)
        self.assertEqual(self.backend.calls,0)


def load_tests(loader,tests,pattern):
    suite=unittest.TestSuite(loader.loadTestsFromTestCase(WindowsAdapterTests))
    for n in ('test_signed_fixture_cycle_and_duplicate','test_sealed_recovery_no_second_effect','test_uncertain_intent_never_reruns','test_signature_tampering_before_worker'):
        suite.addTest(ReceiptContractTests(n))
    return suite
