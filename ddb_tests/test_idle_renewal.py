"""Renewal cannot extend a dispatched grant, reset counters, or replay old authority."""
import copy
import unittest
from test_document_bridge import DDBTests, Policy, sha
from dci.master.document_bridge import renew_undispatched_policy, DocumentNode, verified_snapshot


class IdleRenewalTests(DDBTests):
    def test_only_neutral_history_survives_exact_grant_renewal(self):
        body=copy.deepcopy(self.policy.body);body.update(template='codex_shadow_review_v1',max_tasks=1,expires=self.now+30)
        old=Policy(body,sha(body));self.worker.store.close();self.root=self.root/'renewal';self.root.mkdir()
        self.policy=old;node=self.node('worker')
        node.enqueue('REPORT',{'effort_id':'idle','directive_id':None,'task_id':None,'status':'IDLE','evidence':None},'idle',self.now);node.flush(self.now)
        newbody=dict(body,expires=self.now+3631);new=Policy(newbody,sha(newbody),(old,))
        renew_undispatched_policy(node.store,'worker',old,new,self.now+31)
        updated=DocumentNode(node.store,'worker',new,self.keys['worker'],self.branch)
        verified_snapshot(self.branch.files,new,self.now+31)
        updated.enqueue('HEARTBEAT',{'state':'IDLE'},'new-heartbeat',self.now+31);updated.flush(self.now+31)
        self.assertEqual(updated.store.db.execute('SELECT count(*) FROM ddb_outbox').fetchone()[0],2)
    def test_any_execution_intent_forbids_renewal(self):
        body=copy.deepcopy(self.policy.body);body.update(template='codex_shadow_review_v1',max_tasks=1,expires=self.now+30)
        old=Policy(body,sha(body));newbody=dict(body,expires=self.now+3631);new=Policy(newbody,sha(newbody),(old,))
        db=self.worker.store
        db.db.execute('CREATE TABLE ddb_native_runs(task TEXT,state TEXT)');db.db.execute("INSERT INTO ddb_native_runs VALUES ('fixed','INTENT')")
        with self.assertRaises(PermissionError):renew_undispatched_policy(db,'worker',old,new,self.now+31)
        self.assertEqual(db.db.execute('SELECT state FROM ddb_native_runs').fetchone()[0],'INTENT')


def load_tests(loader,tests,pattern):
    return unittest.TestSuite(IdleRenewalTests(name) for name in ('test_only_neutral_history_survives_exact_grant_renewal','test_any_execution_intent_forbids_renewal'))
