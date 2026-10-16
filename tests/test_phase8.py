"""Additive offline checks. No remote providers, secrets, accounts or services."""
import base64
from dataclasses import replace
import hashlib
import hmac
import json
from pathlib import Path
import secrets
import tempfile
import unittest
from dci.bridge.protocol import ProtocolError
from dci.bridge.store import BridgeStore
from dci.bridge.runner import Runner
from dci.bridge.heg import HumanGateway, SimulationSession, SimulatedNotifications
from dci.master.event_contract import EventContractLab, LabSubscription, event_body, headers, signature


class Phase8ContractTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.path=Path(self.temp.name)/'lab.db'
        self.store=BridgeStore(self.path);self.lab=EventContractLab(self.store)
        self.sub=LabSubscription('synthetic-sub','synthetic-brain','dmb.shadow.result',2000,secrets.token_bytes(32))
        self.event={'eventId':'synthetic-event','name':'dmb.shadow.result','timestamp':'2026-10-11T12:00:00Z','data':{'task_id':'task','correlation_id':'corr','state':'SUCCEEDED','evidence':{'synthetic':True}}}

    def tearDown(self):self.store.close();self.temp.cleanup()

    def test_standard_webhooks_exact_byte_hmac_matches_independent_computation(self):
        body=json.dumps(self.event,indent=2).encode();got=headers(self.sub,body,1000)
        expected=base64.b64encode(hmac.new(self.sub.secret,b'synthetic-event.1000.'+body,hashlib.sha256).digest()).decode()
        self.assertEqual(got['webhook-signature'],'v1,'+expected)
        receipt=self.lab.receive(self.sub,body,got,1000)
        self.assertTrue(receipt.fresh);self.assertFalse(receipt.approval)

    def test_signature_body_tampering_and_missing_signature_fail_closed(self):
        body=event_body(self.event);got=headers(self.sub,body,1000)
        with self.assertRaises(PermissionError):self.lab.receive(self.sub,body+b' ',got,1000)
        with self.assertRaises(PermissionError):self.lab.receive(self.sub,body,{**got,'webhook-signature':''},1000)
        with self.assertRaises(PermissionError):self.lab.receive(self.sub,body,{**got,'webhook-signature':'\u00e9'},1000)
        self.assertEqual(self.store.db.execute('SELECT count(*) FROM event_lab_receipts').fetchone()[0],0)

    def test_wrong_subscription_identity_key_and_signed_event_id_rejected(self):
        body=event_body(self.event);got=headers(self.sub,body,1000)
        with self.assertRaises(PermissionError):self.lab.receive(self.sub,body,{**got,'X-MCP-Subscription-Id':'other'},1000)
        with self.assertRaises(PermissionError):self.lab.receive(replace(self.sub,secret=secrets.token_bytes(32)),body,got,1000)
        with self.assertRaises(ProtocolError):self.lab.receive(self.sub,body,{**got,'webhook-id':'other','webhook-signature':signature(self.sub.secret,'other',1000,body)},1000)

    def test_expiry_revocation_and_signed_time_window(self):
        body=event_body(self.event);got=headers(self.sub,body,1000)
        with self.assertRaises(PermissionError):self.lab.receive(self.sub,body,got,1301)
        with self.assertRaises(PermissionError):self.lab.receive(self.sub,body,got,699)
        with self.assertRaises(PermissionError):self.lab.receive(replace(self.sub,active=False),body,got,1001)
        with self.assertRaises(PermissionError):headers(self.sub,body,2000)
        with self.assertRaises(PermissionError):headers(replace(self.sub,principal='real-human'),body,1000)

    def test_duplicate_delivery_durable_across_restart(self):
        body=event_body(self.event);got=headers(self.sub,body,1000)
        self.assertTrue(self.lab.receive(self.sub,body,got,1000).fresh)
        self.store.close();self.store=BridgeStore(self.path);self.lab=EventContractLab(self.store)
        for now in (1001,1002,1100):self.assertFalse(self.lab.receive(self.sub,body,headers(self.sub,body,now),now).fresh)
        self.assertEqual(self.store.db.execute('SELECT count(*) FROM event_lab_receipts').fetchone()[0],1)
        self.store.verify_audit()

    def test_conflicting_and_rebound_duplicate_rejected(self):
        body=event_body(self.event);self.lab.receive(self.sub,body,headers(self.sub,body,1000),1000)
        changed={**self.event,'data':{**self.event['data'],'state':'FAILED'}};other=event_body(changed)
        with self.assertRaises(ProtocolError):self.lab.receive(self.sub,other,headers(self.sub,other,1001),1001)
        with self.assertRaises(PermissionError):self.lab.receive(replace(self.sub,principal='synthetic-other'),body,headers(self.sub,body,1001),1001)

    def test_out_of_order_distinct_events_are_correlated_not_executed(self):
        for name in ('event-2','event-1'):
            event={**self.event,'eventId':name};body=event_body(event);receipt=self.lab.receive(self.sub,body,headers(self.sub,body,1000),1000)
            self.assertEqual(receipt.event_id,name)
        self.assertEqual(self.store.db.execute('SELECT count(*) FROM tasks').fetchone()[0],0)

    def test_offline_outbox_restart_and_fresh_signature_preserve_event_identity(self):
        self.assertTrue(self.lab.enqueue(self.event,self.sub,1000));self.assertFalse(self.lab.enqueue(self.event,self.sub,1000))
        first=self.lab.claim(self.sub,1000);self.assertEqual(self.lab.response(first,503,1001),'RETRY_WAIT')
        self.store.close();self.store=BridgeStore(self.path);self.lab=EventContractLab(self.store)
        self.assertIsNone(self.lab.claim(self.sub,1002))
        second=self.lab.claim(self.sub,1003);self.assertEqual(first['body'],second['body']);self.assertEqual(first['event_id'],second['event_id'])
        self.assertNotEqual(first['headers']['webhook-signature'],second['headers']['webhook-signature'])
        self.assertEqual(self.lab.response(second,200,1004),'ACKNOWLEDGED');self.assertIsNone(self.lab.claim(self.sub,1005))

    def test_bounded_retries_and_nonretryable_410_413(self):
        self.lab.enqueue(self.event,self.sub,1000)
        for now in (1000,1003,1008):
            claim=self.lab.claim(self.sub,now);state=self.lab.response(claim,503,now+1)
        self.assertEqual(state,'FAILED');self.assertIsNone(self.lab.claim(self.sub,1020))
        for status in (410,413):
            event={**self.event,'eventId':'event-'+str(status)};self.lab.enqueue(event,self.sub,1000);claim=self.lab.claim(self.sub,1000)
            self.assertEqual(self.lab.response(claim,status,1001),'PERMANENT_FAILURE')
            self.assertIsNone(self.lab.claim(self.sub,1002))

    def test_crashed_claim_ambiguous_and_unrelated_delivery_continues(self):
        self.lab.enqueue(self.event,self.sub,1000);claim=self.lab.claim(self.sub,1000)
        self.store.close();self.store=BridgeStore(self.path);self.lab=EventContractLab(self.store);self.lab.recover(1010)
        self.assertEqual(self.store.db.execute('SELECT state FROM event_lab_outbox').fetchone()[0],'AMBIGUOUS')
        with self.assertRaises(ProtocolError):self.lab.response(claim,200,1011)
        self.lab.enqueue({**self.event,'eventId':'independent'},self.sub,1011)
        self.assertEqual(self.lab.claim(self.sub,1011)['event_id'],'independent')

    def test_outbox_conflict_corruption_and_stale_fence(self):
        self.lab.enqueue(self.event,self.sub,1000)
        with self.assertRaises(ProtocolError):self.lab.enqueue({**self.event,'data':{**self.event['data'],'state':'FAILED'}},self.sub,1001)
        claim=self.lab.claim(self.sub,1000);self.lab.response(claim,200,1001)
        with self.assertRaises(ProtocolError):self.lab.response(claim,200,1002)
        self.lab.enqueue({**self.event,'eventId':'corrupt'},self.sub,1001)
        self.store.db.execute("UPDATE event_lab_outbox SET body=x'00' WHERE id='corrupt'")
        with self.assertRaises(ProtocolError):self.lab.claim(self.sub,1002)

    def test_signed_notification_receipt_cannot_be_human_approval(self):
        root=Path(__file__).resolve().parents[1];task=self.store.create_task('gated_shadow_note',1000,task_id='gated',correlation_id='corr')
        Runner(self.store,root).tick(1001);row=self.store.db.execute('SELECT * FROM escalations').fetchone()
        sub=replace(self.sub,event_name='dmb.shadow.notification',principal='synthetic-email')
        event={'eventId':'notification','name':'dmb.shadow.notification','timestamp':'2026-10-11T12:00:00Z','data':{'request_id':row['id'],'task_id':'gated','correlation_id':'corr','scope_digest':row['scope'],'category':'APPROVAL','summary':'synthetic only','simulation':True}}
        body=event_body(event);receipt=self.lab.receive(sub,body,headers(sub,body,1002),1002)
        self.assertFalse(receipt.approval)
        with self.assertRaises(PermissionError):HumanGateway(self.store).decide(receipt,row['id'],row['scope'],'APPROVE',1002)
        self.assertEqual(self.store.task('gated')['state'],'NEEDS_HUMAN')
        self.lab.enqueue(event,sub,1002);claim=self.lab.claim(sub,1002);self.lab.response(claim,202,1003)
        self.assertEqual(self.store.task('gated')['state'],'NEEDS_HUMAN')

    def test_independent_channel_keys_and_simulated_email_fallback(self):
        primary=replace(self.sub,subscription_id='synthetic-whatsapp',principal='synthetic-whatsapp')
        backup=replace(self.sub,subscription_id='synthetic-email',principal='synthetic-email',secret=secrets.token_bytes(32))
        body=event_body(self.event);h=headers(primary,body,1000)
        with self.assertRaises(PermissionError):self.lab.receive(backup,body,{**h,'X-MCP-Subscription-Id':backup.subscription_id},1000)
        self.assertTrue(self.lab.receive(backup,body,headers(backup,body,1000),1000).fresh)
        self.store.create_task('gated_shadow_note',1000,task_id='fallback',correlation_id='corr')
        Runner(self.store,Path(__file__).resolve().parents[1]).tick(1001);HumanGateway(self.store,SimulatedNotifications(False,True)).tick(1002)
        self.assertEqual(self.store.db.execute("SELECT state FROM deliveries WHERE channel='email'").fetchone()[0],'ACKNOWLEDGED')
        self.assertEqual(self.store.task('fallback')['state'],'NEEDS_HUMAN')

    def test_payload_bounds_and_commands_approvals_forbidden(self):
        with self.assertRaises(ProtocolError):event_body({**self.event,'data':{**self.event['data'],'approval':'APPROVE'}})
        with self.assertRaises(ProtocolError):event_body({**self.event,'data':{**self.event['data'],'shell':'whoami'}})
        with self.assertRaises(ProtocolError):event_body({**self.event,'data':{**self.event['data'],'evidence':{'synthetic':'x'*262144}}})
        self.assertNotIn(self.sub.secret.hex(),repr(self.sub))

    def test_subscription_scope_is_pinned_across_restart_and_dispatch(self):
        self.lab.enqueue(self.event,self.sub,1000)
        self.store.close();self.store=BridgeStore(self.path);self.lab=EventContractLab(self.store)
        for changed in (replace(self.sub,principal='synthetic-other'),replace(self.sub,event_name='dmb.shadow.notification'),replace(self.sub,expires=3000)):
            with self.assertRaises(PermissionError):self.lab.claim(changed,1001)
        self.assertEqual(self.lab.claim(self.sub,1001)['event_id'],'synthetic-event')

    def test_same_event_independent_email_outbox_after_primary_failure(self):
        backup=replace(self.sub,subscription_id='synthetic-email',principal='synthetic-email',secret=secrets.token_bytes(32))
        self.lab.enqueue(self.event,self.sub,1000);self.lab.enqueue(self.event,backup,1000)
        primary=self.lab.claim(self.sub,1000);self.lab.response(primary,503,1001)
        email=self.lab.claim(backup,1001)
        self.assertEqual(primary['event_id'],email['event_id'])
        self.assertNotEqual(primary['headers']['webhook-signature'],email['headers']['webhook-signature'])
        self.assertEqual(self.lab.response(email,202,1002),'ACKNOWLEDGED')
        self.assertEqual(self.store.db.execute("SELECT state FROM event_lab_outbox WHERE subscription='synthetic-sub'").fetchone()[0],'RETRY_WAIT')
