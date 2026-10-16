"""Local HTTP-adapter/SQLite contracts; no external host or genuine Windows claim."""
from contextlib import contextmanager
import io
import json
from pathlib import Path
import tempfile
import time
import unittest

from dci.master.https_gateway import DMBHTTPSApplication
from dci.master.operations import BrainIdentity, Operations, signed, authenticated
from dci.master.windows_protocol import PeerKey
from dci.master.windows_controller import AtomicPeerStore, WindowsController
from dci.master.windows_worker import bridge_fingerprint
from dci.master.planner import PortfolioPlanner
from dci.master.registry import PortfolioRegistry

ROOT=Path(__file__).resolve().parents[1]


class GatewayTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.path=Path(self.tmp.name)
        self.database=self.path/'controller.sqlite';route=self.path/'route';route.mkdir()
        self.now=int(time.time());self.openings=0
        self.key=PeerKey('windows_codex_shadow','contract-worker-key',self.now+3600,b'w'*32)
        self.brain=BrainIdentity('contract-brain','contract-brain-key',self.now+3600,frozenset({'intake','review','control','report'}),b'b'*32)
        self.workers={'schema_version':1,'mode':'SHADOW','max_parallel':1,'max_memory_mb':256,
                      'workers':[{'worker_id':self.key.worker_id,'project_ids':['DCI'],'workspace':str(route),
                                  'expected_commit':'a'*40,'source_sha256':{},'max_seconds':20,
                                  'memory_mb':256,'cpu_seconds':10,'max_output_bytes':1048576}]}
        self.app=DMBHTTPSApplication(self.factory,'https://relay.example.invalid')
    def tearDown(self):self.tmp.cleanup()
    @contextmanager
    def factory(self):
        self.openings+=1;store=AtomicPeerStore(self.database)
        try:
            planner=PortfolioPlanner(store,PortfolioRegistry(ROOT/'portfolio/REGISTRY.v1.json'),self.workers,ROOT)
            controller=WindowsController(planner,self.key,'CONTRACT-WINDOWS',bridge_fingerprint())
            yield controller,Operations(controller,self.brain)
        finally:store.close()
    def task(self,project='DCI'):
        return {'task_id':'gateway-one','correlation_id':'gateway-corr','project_id':project}
    def packet(self,action='SUBMIT',payload=None):
        return signed(self.brain,action,self.task() if payload is None else payload,1,'gateway-message',self.now)
    def call(self,packet=None,raw=None,**changes):
        body=json.dumps(self.packet() if packet is None else packet).encode() if raw is None else raw
        env={'wsgi.url_scheme':'https','HTTP_HOST':'relay.example.invalid','PATH_INFO':'/v1/dmb/operations',
             'REQUEST_METHOD':'POST','CONTENT_TYPE':'application/json','CONTENT_LENGTH':str(len(body)),
             'wsgi.input':io.BytesIO(body)};env.update(changes);headers=[]
        data=b''.join(self.app(env,lambda status,h:headers.append((status,h))))
        return headers[0][0],json.loads(data)
    def test_signed_intake_reopens_and_replays_one_durable_task(self):
        status,reply=self.call();self.assertEqual(status,'200 OK')
        authenticated(self.brain,reply,int(time.time()),reply=True)
        self.app=DMBHTTPSApplication(self.factory,'https://relay.example.invalid')
        status,duplicate=self.call();self.assertEqual(status,'200 OK')
        self.assertEqual(reply['payload'],duplicate['payload'])
        with self.factory() as (controller,ops):
            self.assertEqual(controller.store.db.execute('SELECT count(*) FROM tasks').fetchone()[0],1)
            self.assertEqual(controller.store.db.execute('SELECT count(*) FROM executions').fetchone()[0],0)
            controller.store.verify_audit()
    def test_worker_route_retains_original_authenticated_protocol(self):
        from dci.master.windows_protocol import sign,verify,WORKSPACE_ID
        from dci.master.windows_worker import scratch_manifest_digest
        identity={'host':'CONTRACT-WINDOWS','user':'CONTRACT-WINDOWS\\DirectiveCodex','administrator':False,
                  'integrity':'Medium','workspace_id':WORKSPACE_ID,'scratch_manifest_sha256':scratch_manifest_digest(),
                  'git_head':'b'*40,'bridge_sha256':bridge_fingerprint(),'execution_kind':'WINDOWS_CODEX','codex_version':'0.162.1'}
        packet=sign(self.key,'worker_to_controller','HELLO',1,identity,self.now)
        status,reply=self.call(packet,PATH_INFO='/v1/dmb/windows')
        self.assertEqual(status,'200 OK');verify(self.key,reply,'controller_to_worker',int(time.time()))
        self.assertEqual(reply['payload']['data'],{'ready':True})
        # This is an authenticated message fixture, never evidence of a real process.
    def test_no_forwarded_header_can_invent_tls_or_cross_host(self):
        for changes in ({'wsgi.url_scheme':'http','HTTP_X_FORWARDED_PROTO':'https'},
                        {'HTTP_HOST':'different.example.invalid'}, {'QUERY_STRING':'override=shell'}):
            status,_=self.call(**changes);self.assertEqual(status,'403 Forbidden')
        self.assertEqual(self.openings,0)
    def test_route_method_size_and_duplicate_json_fail_before_authority(self):
        for changes,expected in [({'PATH_INFO':'/shell'},'404'),({'REQUEST_METHOD':'GET'},'405'),
                                 ({'CONTENT_TYPE':'text/plain'},'415'),({'CONTENT_LENGTH':'131073'},'413')]:
            status,_=self.call(**changes);self.assertTrue(status.startswith(expected))
        status,_=self.call(raw=b'{"action":"REPORT","action":"SUBMIT"}')
        self.assertEqual(status,'403 Forbidden');self.assertEqual(self.openings,0)
    def test_auth_failure_no_shell_approval_or_project_authority(self):
        wrong=self.packet();wrong['mac']='0'*64
        for packet in (wrong,self.packet('SHELL',{}),self.packet('APPROVE',{}),self.packet(payload=self.task('DAT_FUTURES'))):
            status,body=self.call(packet);self.assertEqual(status,'403 Forbidden')
            self.assertNotIn('secret',json.dumps(body))
        status,_=self.call();self.assertEqual(status,'200 OK')  # Rejections consumed no sequence.
    def test_backend_outage_has_no_false_ack_and_same_request_recovers(self):
        @contextmanager
        def unavailable():
            raise ConnectionError('private fixture detail must never appear in response')
            yield
        self.app=DMBHTTPSApplication(unavailable,'https://relay.example.invalid')
        status,body=self.call();self.assertEqual(status,'503 Service Unavailable')
        self.assertNotIn('private',json.dumps(body));self.assertFalse(self.database.exists())
        self.app=DMBHTTPSApplication(self.factory,'https://relay.example.invalid')
        self.assertEqual(self.call()[0],'200 OK');self.assertEqual(self.call()[0],'200 OK')
        with self.factory() as (controller,ops):
            self.assertEqual(controller.store.db.execute('SELECT count(*) FROM tasks').fetchone()[0],1)
    def test_audit_corruption_is_preserved_and_never_acknowledged(self):
        self.assertEqual(self.call()[0],'200 OK')
        with self.factory() as (controller,ops):
            controller.store.db.execute("UPDATE audit SET hash='corrupt' WHERE seq=1")
        self.assertNotEqual(self.call()[0],'200 OK')
        import sqlite3
        with sqlite3.connect(self.database) as db:
            self.assertEqual(db.execute('SELECT hash FROM audit WHERE seq=1').fetchone()[0],'corrupt')
    def test_missing_or_invalid_operator_origin_cannot_activate(self):
        for origin in (None,'http://relay.example.invalid','https://user:password@relay.example.invalid',
                       'https://relay.example.invalid/path','https://relay.example.invalid:8443'):
            with self.assertRaises((PermissionError,ValueError)):DMBHTTPSApplication(self.factory,origin)


if __name__=='__main__':unittest.main()
