"""Authentication/recovery integration uses actual bounded paper worker processes."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from dci.bridge.protocol import ProtocolError
from dci.master.windows_controller import AtomicPeerStore
from dci.master.planner import PortfolioPlanner
from dci.master.registry import PortfolioRegistry
from dci.master.control_plane import ShadowControlPlane
from dci.master.operations import BrainIdentity, Operations, signed, authenticated
from dci.master.operations_client import OperationsClient, OperationsHTTPS

ROOT = Path(__file__).resolve().parents[1]


class OperationsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix='dmb-ops-')
        cls.base = Path(cls.temp.name); cls.manifest = cls.base / 'workers.json'
        subprocess.run([sys.executable, str(ROOT / 'tools/prepare_shadow_research_worker.py'), '--destination', str(cls.base/'worker'), '--manifest', str(cls.manifest)], check=True, capture_output=True)
    @classmethod
    def tearDownClass(cls): cls.temp.cleanup()
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory(dir=self.base); self.root=Path(self.folder.name)
        self.store=AtomicPeerStore(self.root/'controller.sqlite')
        self.runtime=ShadowControlPlane(PortfolioPlanner(self.store,PortfolioRegistry(ROOT/'portfolio/REGISTRY.v1.json'),self.manifest,ROOT))
        self.now=int(time.time());self.key=BrainIdentity('test-brain','test-key',self.now+3600,frozenset({'intake','review','control','report'}),b'b'*32)
        self.ops=Operations(self.runtime,self.key);self.client_store=AtomicPeerStore(self.root/'client.sqlite')
        self.client=OperationsClient(self.client_store,self.key,lambda packet:self.ops.handle(packet,int(time.time())))
    def tearDown(self):self.store.close();self.client_store.close();self.folder.cleanup()
    def task(self,name='first'):return {'task_id':name,'correlation_id':'corr-'+name,'project_id':'DCI'}
    def test_real_worker_evidence_bound_review_and_followup(self):
        self.client.request('SUBMIT',self.task());self.runtime.tick()
        report=self.client.request('REPORT',{});review=report['reviews'][0]
        payload={'task_id':'first','scope_digest':review['scope'],'result_digest':review['result_digest'],'verdict':'ACCEPT','followup':{**self.task('second'),'dependencies':['first']}}
        self.client.request('REVIEW',payload);self.runtime.tick();self.ops.collect(int(time.time()))
        self.assertEqual(self.store.task('second')['state'],'SUCCEEDED')
        self.assertEqual(self.store.db.execute('SELECT count(*) FROM executions').fetchone()[0],2)
        self.assertTrue(self.client.request('REPORT',{})['audit_valid'])
    def test_lost_ack_offline_reopen_preserves_single_intake(self):
        def lost(packet):self.ops.handle(packet,int(time.time()));raise ConnectionError('lost reply')
        self.client.transport=lost
        with self.assertRaises(ConnectionError):self.client.request('SUBMIT',self.task())
        self.assertEqual(self.store.db.execute('SELECT count(*) FROM tasks').fetchone()[0],1)
        self.client_store.close();self.client_store=AtomicPeerStore(self.root/'client.sqlite')
        self.client=OperationsClient(self.client_store,self.key,lambda p:self.ops.handle(p,int(time.time())))
        self.client.recover();self.runtime.tick()
        self.assertEqual(self.store.db.execute('SELECT count(*) FROM executions').fetchone()[0],1)
    def test_replay_route_scope_and_approval_rejected(self):
        packet=signed(self.key,'SUBMIT',self.task(),1,'request-one',self.now)
        self.ops.handle(packet,self.now)
        changed=signed(self.key,'SUBMIT',self.task('other'),1,'request-one',self.now)
        with self.assertRaises(ProtocolError):self.ops.handle(changed,self.now)
        with self.assertRaises(PermissionError):self.ops.handle(signed(self.key,'SUBMIT',self.task('other'),2,'request-two',self.now,reply=True),self.now)
        with self.assertRaises(ProtocolError):self.ops.handle(signed(self.key,'APPROVE',{},2,'request-two',self.now),self.now)
        with self.assertRaises(PermissionError):self.ops.handle(packet,self.now+61)
        self.assertEqual(self.store.db.execute('SELECT count(*) FROM tasks').fetchone()[0],1)
    def test_wrong_review_result_rejected_atomically(self):
        self.client.request('SUBMIT',self.task());self.runtime.tick();self.ops.collect(self.now)
        review=self.store.db.execute('SELECT * FROM ops_reviews').fetchone()
        packet=signed(self.key,'REVIEW',{'task_id':'first','scope_digest':review['scope'],'result_digest':'0'*64,'verdict':'ACCEPT','followup':{**self.task('bad'),'dependencies':['first']}},2,'bad-review',self.now)
        with self.assertRaises(ProtocolError):self.ops.handle(packet,self.now)
        self.assertIsNone(self.store.db.execute("SELECT 1 FROM tasks WHERE id='bad'").fetchone())
    def test_event_delivery_ack_does_not_approve_and_scope_fails_closed(self):
        self.client.request('SUBMIT',self.task());r=self.client.request('REPORT',{})
        ack=self.client.request('ACK_EVENTS',{'events':[r['events'][0]['event_id']]})
        self.assertFalse(ack['human_approval'])
        self.assertEqual(self.store.db.execute('SELECT count(*) FROM ops_reviews').fetchone()[0],0)
        limited=BrainIdentity(self.key.principal,self.key.key_id,self.key.expires,frozenset({'report'}),self.key.secret)
        with self.assertRaises(PermissionError):authenticated(limited,signed(limited,'SUBMIT',self.task('bad'),4,'bad-scope',self.now),self.now)
    def test_actual_sealed_receipt_recovery_remains_reviewable(self):
        self.client.request('SUBMIT',self.task());job=self.runtime.planner.claim(self.now)[0]
        evidence=self.runtime.dispatch(job);self.assertTrue(evidence['passed'])
        self.store.close();self.store=AtomicPeerStore(self.root/'controller.sqlite')
        self.runtime=ShadowControlPlane(PortfolioPlanner(self.store,PortfolioRegistry(ROOT/'portfolio/REGISTRY.v1.json'),self.manifest,ROOT))
        self.ops=Operations(self.runtime,self.key);recovery=self.runtime.tick();self.ops.collect(self.now)
        self.assertEqual(recovery['recovered_without_reexecution'],['first'])
        self.assertEqual(self.store.db.execute("SELECT state FROM ops_reviews WHERE task='first'").fetchone()[0],'PENDING')
    def test_outbound_relay_crash_window_recovers_cached_authenticated_batch(self):
        from dci.master.operations_relay import OutboundRelayPump
        from dci.master.operations import semantic
        from dci.master.windows_protocol import sha
        carrier=BrainIdentity('controller-carrier','relay-key',self.now+3600,frozenset({'report'}),b'r'*32)
        delivered=[]
        request=signed(self.key,'SUBMIT',self.task(),1,'relay-task',self.now)
        def relay(packet):
            authenticated(carrier,packet,self.now)
            replies=packet['payload']['replies']
            value={'requests':[{'route':'brain','packet':request}] if not delivered else [],
                   'accepted_replies':[{k:item[k] for k in ('route','id','digest')} for item in replies]}
            delivered.append(packet['message_id'])
            return signed(carrier,'ACK',{'request_id':packet['message_id'],'request_digest':sha(semantic(packet)),'result':value},packet['sequence'],packet['message_id'],self.now,reply=True)
        pump=OutboundRelayPump(self.ops,carrier,relay)
        # Persist the actual carrier reply, then reopen before applying inner task.
        pump.client.request('REPORT',{'role':'controller','replies':[],'max_requests':10},self.now)
        self.assertEqual(self.store.db.execute('SELECT count(*) FROM tasks').fetchone()[0],0)
        self.store.close();self.store=AtomicPeerStore(self.root/'controller.sqlite')
        self.runtime=ShadowControlPlane(PortfolioPlanner(self.store,PortfolioRegistry(ROOT/'portfolio/REGISTRY.v1.json'),self.manifest,ROOT))
        self.ops=Operations(self.runtime,self.key);pump=OutboundRelayPump(self.ops,carrier,relay)
        self.assertFalse(pump.pump(self.now)['inbound_listener'])
        self.runtime.tick();self.ops.collect(self.now)
        self.assertEqual(self.store.db.execute('SELECT count(*) FROM executions').fetchone()[0],1)
        self.assertEqual(self.store.db.execute('SELECT count(*) FROM ops_relay_replies WHERE ack=0').fetchone()[0],0)

    def test_https_has_no_insecure_or_arbitrary_route(self):
        for url in ['http://localhost/v1/dmb/operations','https://localhost/else','https://user:secret@localhost/v1/dmb/operations']:
            with self.assertRaises(PermissionError):OperationsHTTPS(url)


if __name__=='__main__':unittest.main()
