"""Offline DDB contracts; one test uses a real existing Linux paper worker."""
import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization
from dci.bridge.protocol import ProtocolError, canonical
from dci.master.document_bridge import (Policy, DocumentNode, Supervisor, Worker, PaperOperationsBackend,
    validate_document, verified_snapshot, document_files, sha, DOMAIN)
from dci.master.document_github import GitHubDocuments
from dci.master.document_cli import exclusive
from dci.master.windows_controller import AtomicPeerStore

ROOT = Path(__file__).resolve().parents[1]


class MemoryBranch:
    """Fault-injected branch CAS contract, not a real GitHub certification."""
    def __init__(self):
        self.files = {}; self.head = '0'*40; self.offline = False; self.lost = False; self.conflicts = 0
    def snapshot(self):
        if self.offline: raise ConnectionError('offline fixture')
        return self.head, dict(self.files)
    def publish(self, expected_head, changes):
        if self.offline: raise ConnectionError('offline fixture')
        if self.conflicts:
            self.conflicts -= 1; raise ConnectionError('competing CAS fixture')
        if expected_head != self.head: raise ConnectionError('non-fast-forward')
        self.files.update(changes); self.head = hashlib.sha1(canonical(self.files).encode()).hexdigest()
        if self.lost:
            self.lost = False; raise ConnectionError('ACK lost after branch commit')
        return self.head


class CountingBackend:
    def __init__(self): self.calls = 0
    def review(self, report, now): pass
    def run(self, directive, now):
        self.calls += 1
        return {'kind': 'VERIFIED_LOCAL_PAPER', 'scope_digest': '1'*64, 'result_digest': '2'*64,
                'artifact_sha256': '3'*64, 'git_commit': '4'*40, 'audit_valid': True, 'exit_code': 0}


class DDBTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.root = Path(self.tmp.name); self.now = int(time.time())
        self.keys = {role: Ed25519PrivateKey.generate() for role in ('supervisor', 'worker')}
        body = {'version': 1, 'mode': 'SHADOW', 'policy_id': 'offline-fixture-only', 'expires': self.now+3600,
                'max_tasks': 2, 'template': 'shadow_research', 'report_max_age': 600, 'document_ttl': 900,
                'worker_id': 'dci_shadow_research', 'worker_key_id': 'existing-offline-key',
                'signers': {r: k.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw).hex() for r,k in self.keys.items()}}
        self.policy = Policy(body, sha(body)); self.branch = MemoryBranch(); self.stores = []
        self.super = self.node('supervisor'); self.worker = self.node('worker')
        self.backend = CountingBackend(); self.w = Worker(self.worker, self.backend); self.s = Supervisor(self.super)
    def tearDown(self):
        for store in self.stores:
            try: store.close()
            except Exception: pass
        self.tmp.cleanup()
    def node(self, role):
        store = AtomicPeerStore(self.root/(role+'.sqlite')); self.stores.append(store)
        return DocumentNode(store, role, self.policy, self.keys[role], self.branch)
    def handoff(self):
        self.w.idle(self.now); self.worker.flush(self.now)
        self.s.poll(self.now); self.super.flush(self.now)
        self.w.poll(self.now)
    def test_e2e_handoff_receipts_review_and_budget(self):
        self.handoff(); self.w.execute_one(self.now); self.worker.flush(self.now)
        self.s.poll(self.now); self.super.flush(self.now)
        self.w.poll(self.now); self.w.execute_one(self.now); self.worker.flush(self.now)
        self.s.poll(self.now); self.super.flush(self.now)
        self.assertEqual(self.backend.calls, 2)
        self.assertEqual(len([p for p in self.branch.files if p.startswith('directives/completed/')]), 2)
        self.assertEqual(self.super.store.db.execute('SELECT count(*) FROM ddb_plan WHERE completed=1').fetchone()[0], 2)
        self.assertEqual(self.s.poll(self.now), 0)
        self.assertIsNone(self.w.execute_one(self.now)); self.assertEqual(self.backend.calls, 2)
        verified_snapshot(self.branch.files, self.policy, self.now)
    def test_lost_publication_ack_reopens_without_overwrite(self):
        doc = self.w.idle(self.now); self.branch.lost = True
        self.worker.flush(self.now)
        self.worker.store.close(); self.worker = self.node('worker')
        self.assertEqual(self.worker.flush(self.now), 0)
        self.assertEqual(json.loads(self.branch.files['reports/latest.json']), doc)
    def test_disconnection_retains_outbox_and_restart_delivers_once(self):
        self.w.idle(self.now); self.branch.offline = True
        with self.assertRaises(ConnectionError): self.worker.flush(self.now)
        self.assertIsNone(self.worker.store.db.execute('SELECT published FROM ddb_outbox').fetchone()[0])
        self.worker.store.close(); self.worker = self.node('worker'); self.branch.offline = False
        self.assertEqual(self.worker.flush(self.now), 1)
        self.assertEqual(Supervisor(self.super).poll(self.now), 1)
        self.assertEqual(Supervisor(self.super).poll(self.now), 0)
    def test_bounded_cas_retry_and_atomic_document_set(self):
        self.w.idle(self.now); self.branch.conflicts = 3
        with self.assertRaises(ConnectionError): self.worker.flush(self.now)
        self.assertEqual(self.branch.files, {})
        self.worker.flush(self.now)
        self.assertEqual(len(self.branch.files), 3)
    def test_stale_report_and_expired_directive_cannot_execute(self):
        self.w.idle(self.now); self.worker.flush(self.now)
        self.s.poll(self.now); self.super.flush(self.now)
        with self.assertRaises(PermissionError): self.w.poll(self.now+901)
        self.assertEqual(self.backend.calls, 0)
    def test_wrong_signature_and_worker_cannot_sign_directive(self):
        with self.assertRaises(PermissionError): self.worker.enqueue('DIRECTIVE', {'directive_id':'d','task_id':'t','correlation_id':'c','template':'shadow_research','source_report':'1'*64}, 'wrong', self.now)
        doc = copy.deepcopy(self.w.idle(self.now)); doc['signature'] = '0'*128
        with self.assertRaises(PermissionError): validate_document(doc,self.policy,self.now)
        with self.assertRaises(PermissionError): DocumentNode(self.worker.store,'worker',self.policy,self.keys['supervisor'],self.branch)
    def test_policy_pin_and_exceptional_directive_are_closed(self):
        with self.assertRaises(PermissionError): Policy(copy.deepcopy(self.policy.body), '0'*64)
        bad = copy.deepcopy(self.policy.body); bad['template']='shell'
        with self.assertRaises(PermissionError): Policy(bad,sha(bad))
        self.handoff()
        doc=json.loads(self.worker.store.db.execute('SELECT body FROM ddb_jobs').fetchone()[0]);doc['body']['command']='whoami'
        with self.assertRaises(ProtocolError): self.worker.enqueue('ACK', {'directive_id':'d','directive_digest':'1'*64,'state':'APPROVED'}, 'approval',self.now)
        self.policy.body['max_tasks']=3
        with self.assertRaises(PermissionError): self.w.execute_one(self.now)
    def test_stream_gap_mirror_tamper_and_rollback_are_rejected(self):
        self.handoff()
        original = dict(self.branch.files); self.branch.files['reports/latest.json']='{}'
        with self.assertRaises(PermissionError): self.s.poll(self.now)
        self.branch.files = original
        self.branch.files = {p:v for p,v in original.items() if not p.startswith(('reports/','state/events/worker/'))}
        with self.assertRaises(PermissionError): self.super._consume(self.now,self.s.handle)
    def test_conflicting_directive_rolls_back_whole_batch(self):
        self.handoff()
        first = json.loads(self.worker.store.db.execute('SELECT body FROM ddb_jobs').fetchone()[0])['body']
        other = dict(first,directive_id='different',task_id='different-task')
        self.super.enqueue('DIRECTIVE',other,'different-directive',self.now);self.super.flush(self.now)
        with self.assertRaises(PermissionError): self.w.poll(self.now)
        self.assertEqual(self.worker.store.db.execute('SELECT count(*) FROM ddb_jobs').fetchone()[0],1)
    def test_unexpected_worker_failure_reports_without_followup(self):
        self.handoff()
        class Failing:
            def run(self,*args): raise ConnectionError('private details')
        report=Worker(self.worker,Failing()).execute_one(self.now);self.worker.flush(self.now)
        self.assertEqual(report['body']['status'],'NEEDS_HUMAN')
        self.assertNotIn('private',canonical(report))
        self.s.poll(self.now)
        self.assertEqual(self.super.store.db.execute('SELECT count(*) FROM escalations').fetchone()[0],1)
        with self.assertRaises(PermissionError):self.s.poll(self.now)
        self.assertEqual(self.super.store.db.execute('SELECT count(*) FROM ddb_plan').fetchone()[0],1)
    def test_cadence_clock_and_exclusive_foreground_owner(self):
        self.assertTrue(self.super.due('watch',self.now))
        self.assertFalse(self.super.due('watch',self.now+179));self.assertTrue(self.super.due('watch',self.now+180))
        self.assertTrue(self.super.due('supervisor',self.now));self.assertFalse(self.super.due('supervisor',self.now+299))
        self.assertTrue(self.super.due('supervisor',self.now+1,evidence=True))
        with self.assertRaises(PermissionError):self.super.due('supervisor',self.now)
        with exclusive(self.root/'owner.lock'):
            with self.assertRaises(OSError):
                with exclusive(self.root/'owner.lock'):pass
    def test_corrupt_audit_prevents_publication_and_execution(self):
        self.handoff();self.worker.store.db.execute("UPDATE audit SET hash='bad' WHERE seq=1")
        with self.assertRaises(ProtocolError):self.worker.flush(self.now)
        with self.assertRaises(ProtocolError):self.w.execute_one(self.now)
        self.assertEqual(self.backend.calls,0)
    def test_github_transport_has_fixed_branch_no_redirect_and_no_force(self):
        calls=[]
        class Fake(GitHubDocuments):
            def request(self,method,path,value=None):
                calls.append((method,path,value))
                if '/git/trees' in path:return {'sha':'a'*40}
                if '/git/commits' in path:return {'sha':'b'*40}
                return {}
        api=Fake('oluadegbu/Codex--DSV-',lambda:'not-a-real-credential');api.head_trees['0'*40]='c'*40
        api.publish('0'*40,{'reports/latest.json':'{}'})
        self.assertEqual(calls[-1][1],'/git/refs/heads/coordination/dmb-ddb-v1')
        self.assertIs(calls[-1][2]['force'],False)
        with self.assertRaises(PermissionError):api.publish('0'*40,{'../main.json':'{}'})
        self.assertTrue(any(type(h).__name__=='NoRedirect' for h in api.opener.handlers))
    def test_stale_report_preserves_durable_needs_human(self):
        self.w.idle(self.now);self.worker.flush(self.now)
        with self.assertRaises(PermissionError):self.s.poll(self.now+601)
        self.assertEqual(self.super.store.db.execute('SELECT count(*) FROM ddb_plan').fetchone()[0],0)
        self.assertEqual(self.super.store.db.execute('SELECT count(*) FROM escalations').fetchone()[0],1)
        self.super.store.close();self.super=self.node('supervisor')
        with self.assertRaises(PermissionError):Supervisor(self.super).poll(self.now+602)

    @unittest.skipUnless(os.name == 'posix', 'Existing paper worker is Linux-only; not Windows certification')
    def test_real_paper_artifact_and_crash_after_execution_recover_once(self):
        manifest=self.root/'workers.json'
        proc=subprocess.run([sys.executable,str(ROOT/'tools/prepare_shadow_research_worker.py'),'--destination',str(self.root/'paper-worker'),'--manifest',str(manifest)],capture_output=True,text=True,timeout=30)
        self.assertEqual(proc.returncode,0,proc.stderr[-800:])
        from dci.master.operations import Operations, BrainIdentity
        from dci.master.operations_client import OperationsClient
        from dci.master.control_plane import ShadowControlPlane
        from dci.master.planner import PortfolioPlanner
        from dci.master.registry import PortfolioRegistry
        identity=BrainIdentity('ddb-paper-fixture','ddb-ops-fixture',self.now+3600,frozenset({'intake','review','control','report'}),b'x'*32)
        def backend(node):
            ops=Operations(ShadowControlPlane(PortfolioPlanner(node.store,PortfolioRegistry(ROOT/'portfolio/REGISTRY.v1.json'),manifest,ROOT)),identity)
            client_store=AtomicPeerStore(self.root/'ops-client.sqlite');self.stores.append(client_store)
            return PaperOperationsBackend(ops,OperationsClient(client_store,identity,lambda p:ops.handle(p,int(time.time()))))
        real=backend(self.worker)
        class CrashAfterReceipt:
            def run(self,directive,now):
                real.run(directive,now)
                raise SystemExit('injected isolated crash after sealed receipt')
        self.handoff()
        with self.assertRaises(SystemExit):Worker(self.worker,CrashAfterReceipt()).execute_one(self.now)
        self.assertEqual(self.worker.store.db.execute('SELECT count(*) FROM executions').fetchone()[0],1)
        self.worker.store.close();self.worker=self.node('worker');real=backend(self.worker)
        report=Worker(self.worker,real).execute_one(int(time.time()))
        self.assertEqual(report['body']['status'],'SUCCEEDED')
        self.assertEqual(report['body']['evidence']['kind'],'VERIFIED_LOCAL_PAPER')
        self.assertEqual(self.worker.store.db.execute('SELECT count(*) FROM executions').fetchone()[0],1)
        self.worker.flush(int(time.time()));self.s.poll(int(time.time()));self.super.flush(int(time.time()))
        self.assertEqual(self.super.store.db.execute('SELECT count(*) FROM ddb_plan WHERE completed=1').fetchone()[0],1)
        native_worker=Worker(self.worker,real);native_worker.poll(int(time.time()));native_worker.apply_reviews(int(time.time()))
        self.assertEqual(self.worker.store.db.execute("SELECT state FROM ops_reviews").fetchone()[0],'ACCEPT')
        self.worker.store.verify_audit();self.super.store.verify_audit()
        if os.environ.get('DDB_EVIDENCE_DIR'):
            receipt={'scope':'REAL_LOCAL_LINUX_PAPER_PROCESS_NOT_CODEX_OR_GITHUB',
                     'offline_fixture_policy_not_human_approval':self.policy.body,'signed_report':report,'durable_executions':self.worker.store.db.execute('SELECT count(*) FROM executions').fetchone()[0],
                     'restart_after_sealed_receipt':'PASS_NO_SECOND_EXECUTION','operations_review':'ACCEPT','audit_valid':True}
            (Path(os.environ['DDB_EVIDENCE_DIR'])/'REAL_PAPER_RECOVERY.json').write_text(json.dumps(receipt,indent=2)+'\n')


if __name__=='__main__':unittest.main()
