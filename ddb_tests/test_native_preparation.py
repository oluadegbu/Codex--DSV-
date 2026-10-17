"""Native boundary checks only. Never substitutes fixtures for genuine execution."""
import copy
import unittest
from test_document_bridge import DDBTests, sha, Policy
from dci.master.document_bridge import Supervisor, Worker
from dci.master.document_native import NativeForegroundBackend


class NativePreparationTests(DDBTests):
    # Reuse setup helpers; inherited tests deliberately excluded by loader below.
    def test_native_policy_is_exactly_one_effort(self):
        body=copy.deepcopy(self.policy.body);body['template']='codex_shadow_review_v1'
        with self.assertRaises(PermissionError):Policy(body,sha(body))
        body['max_tasks']=1;Policy(body,sha(body))
    def test_native_scope_rejects_paper_evidence(self):
        body=copy.deepcopy(self.policy.body);body.update(template='codex_shadow_review_v1',max_tasks=1)
        # Separate policy namespace; never mutate an enrolled binding.
        self.super.store.close();self.worker.store.close()
        self.policy=Policy(body,sha(body))
        self.root=self.root/'native-policy';self.root.mkdir()
        self.super=self.node('supervisor');self.worker=self.node('worker')
        self.s=Supervisor(self.super);self.w=Worker(self.worker,self.backend)
        self.handoff();self.w.execute_one(self.now);self.worker.flush(self.now)
        with self.assertRaises(PermissionError):self.s.poll(self.now)
        self.assertEqual(self.super.store.db.execute('SELECT count(*) FROM ddb_plan WHERE completed=1').fetchone()[0],0)
    def test_expired_heartbeat_does_not_authorize_or_block_fresh_report(self):
        self.worker.enqueue('HEARTBEAT',{'state':'BLOCKED'},'blocked-preparation',self.now)
        self.worker.flush(self.now);self.assertEqual(self.s.poll(self.now+901),1)
        self.assertEqual(self.super.store.db.execute('SELECT count(*) FROM ddb_plan').fetchone()[0],0)
        self.w.idle(self.now+901);self.worker.flush(self.now+901)
        self.assertEqual(self.s.poll(self.now+901),1)
        self.assertEqual(self.super.store.db.execute('SELECT count(*) FROM ddb_plan').fetchone()[0],1)
    def test_native_constructor_rejects_unreviewed_pin_shape(self):
        with self.assertRaises(PermissionError):NativeForegroundBackend(self.worker.store,{},self.root)


def load_tests(loader,tests,pattern):
    suite=unittest.TestSuite()
    for name in ('test_native_policy_is_exactly_one_effort','test_native_scope_rejects_paper_evidence','test_native_constructor_rejects_unreviewed_pin_shape','test_expired_heartbeat_does_not_authorize_or_block_fresh_report'):
        suite.addTest(NativePreparationTests(name))
    return suite
