import copy
import json
import tempfile
from pathlib import Path
import unittest
from dci.bridge.store import BridgeStore
from dci.bridge.protocol import ProtocolError
from dci.bridge.runner import Runner, DEGRADED
from dci.bridge.heg import HumanGateway, SimulationSession, SimulatedNotifications
from dci.bridge.brain import BrainTools
from dci.master.registry import PortfolioRegistry
from dci.master.planner import Job, PortfolioPlanner
from dci.master.workers import MasterRunner
from dci.master.brain import MasterBrainTools, MasterMcpPrototype
from dci.master.workflows import PortfolioWorkflowInput

ROOT=Path(__file__).resolve().parents[1]


class MasterTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.base=Path(self.temp.name)
        self.registry=PortfolioRegistry(ROOT/'portfolio/REGISTRY.v1.json')
        self.config=json.loads((ROOT/'portfolio/WORKERS.v1.json').read_text())
        for w in self.config['workers']:
            root=self.base/w['worker_id'];root.mkdir();w['workspace']=str(root)
        self.store=BridgeStore(self.base/'master.sqlite')
        self.planner=PortfolioPlanner(self.store,self.registry,self.config,ROOT)
        self.now=1000

    def tearDown(self):
        self.store.close();self.temp.cleanup()

    def submit(self, name='one', project='BHB', **kw):
        return self.planner.submit(Job(name,'corr-'+name,project,**kw),self.now)

    def evidence(self, job, **extra):
        return {'task_id':job['id'],'scope_digest':job['scope_digest'],'workspace':job['workspace'],'worker_id':job['worker'],'outcome':'COMPLETE','passed':True,**extra}

    def approve(self, task, decision='APPROVE', now=1001):
        row=self.store.db.execute('SELECT * FROM escalations WHERE task=? AND decision IS NULL',(task,)).fetchone()
        HumanGateway(self.store).decide(SimulationSession('synthetic-supervisor',True),row['id'],row['scope'],decision,now)
        return row

    def test_registry_covers_portfolio_without_promoting_unknown(self):
        self.assertEqual(len(self.registry.projects),13)
        self.assertEqual(self.registry.get('DAT_FUTURES')['verified_state'],'UNVERIFIED')
        self.assertIsNone(self.registry.get('DPM')['git_repository'])
        self.assertEqual(self.registry.data['protected_milestone']['implementation'],'UNVERIFIED')
        self.assertTrue(self.registry.graph()['edges'])

    def test_registry_rejects_cycle_and_unevidenced_pass(self):
        data=copy.deepcopy(self.registry.data);data['projects'][0]['evidence']=[]
        path=self.base/'bad.json';path.write_text(json.dumps(data))
        with self.assertRaises(ProtocolError):PortfolioRegistry(path)
        data=copy.deepcopy(self.registry.data);data['projects'][0]['dependencies']=[{'project_id':'DCI','kind':'integration','blocks_shadow_lab':False}];path.write_text(json.dumps(data))
        with self.assertRaises(ProtocolError):PortfolioRegistry(path)

    def test_dependency_priority_and_parallel_routes(self):
        self.submit('low',priority=1);self.submit('high',project='DAT_FUTURES',priority=90);self.submit('dependent',project='DPM',dependencies=('high',),priority=100)
        jobs=self.planner.claim(1001);self.assertEqual([j['id'] for j in jobs],['high','low'])
        for j in jobs:self.planner.finish(j,self.evidence(j),1002)
        self.assertEqual(self.planner.claim(1003)[0]['id'],'dependent')

    def test_three_independent_routes_resource_caps(self):
        for n,p in [('b','BHB'),('d','DAT_MT5'),('p','DPM')]:self.submit(n,p)
        jobs=self.planner.claim(1001);self.assertEqual(len(jobs),3)
        self.assertEqual(len({j['workspace'] for j in jobs}),3)
        self.assertEqual(sum(j['memory'] for j in jobs),768)
        self.submit('four','HEG');self.assertEqual(self.planner.claim(1002),[])

    def test_memory_budget_throttles(self):
        config=copy.deepcopy(self.config);config['max_memory_mb']=256
        other=BridgeStore(self.base/'limited.db')
        try:
            planner=PortfolioPlanner(other,self.registry,config,ROOT)
            for n,p in [('b','BHB'),('d','DAT_MT5'),('p','DPM')]:planner.submit(Job(n,'c-'+n,p),1000)
            self.assertEqual(len(planner.claim(1001)),1)
        finally:other.close()

    def test_workspace_overlap_duplicate_route_and_unbounded_rejected(self):
        for alteration in ('workspace','budget','route'):
            cfg=copy.deepcopy(self.config)
            if alteration=='workspace':cfg['workers'][1]['workspace']=cfg['workers'][0]['workspace']
            elif alteration=='budget':cfg['workers'][0]['max_seconds']=21
            else:cfg['workers'][1]['project_ids']=['BHB']
            with self.assertRaises(ProtocolError):PortfolioPlanner(self.store,self.registry,cfg,ROOT)

    def test_context_drift_fail_closed(self):
        cfg=copy.deepcopy(self.config);cfg['workers'][0]['expected_commit']='f'*40
        with self.assertRaises(ProtocolError):PortfolioPlanner(self.store,self.registry,cfg,ROOT)

    def test_arbitrary_shell_unknown_route_and_dependency_rejected(self):
        for kw in ({'operation':'sh -c whoami'},{'dependencies':('unknown',)},{'priority':True}):
            with self.assertRaises(ProtocolError):self.submit(**kw)
        with self.assertRaises(ProtocolError):self.submit(project='DSV')
        with self.assertRaises(ProtocolError):self.submit(project='unknown')
        self.assertEqual(self.store.db.execute('SELECT count(*) FROM tasks').fetchone()[0],0)

    def test_stable_task_replay_exact_retry_and_conflict(self):
        first=self.submit();self.assertEqual(self.submit()['id'],first['id'])
        with self.assertRaises(ProtocolError):self.submit(project='DPM')
        job=self.planner.claim(1001)[0];self.planner.finish(job,self.evidence(job),1002)
        with self.assertRaises(ProtocolError):self.planner.finish(job,self.evidence(job),1003)
        self.assertEqual(self.store.db.execute('SELECT count(*) FROM executions').fetchone()[0],1)

    def test_wrong_route_result_does_not_commit(self):
        self.submit();job=self.planner.claim(1001)[0]
        with self.assertRaises(ProtocolError):self.planner.finish(job,self.evidence(job,worker_id='dpm_simulation'),1002)
        self.assertEqual(self.store.task('one')['state'],'RUNNING')
        with self.assertRaises(ProtocolError):self.planner.finish(job,self.evidence(job,outcome='typo'),1002)

    def test_plain_bhb_runner_cannot_dispatch_portfolio(self):
        self.submit()
        with self.assertRaises(PermissionError):Runner(self.store,ROOT).claim(1001)

    def test_pause_and_expiry_survive_restart(self):
        self.submit(ttl_seconds=5);BrainTools(self.store).control('PAUSE',1001)
        self.assertEqual(self.planner.claim(1002),[])
        self.store.close();self.store=BridgeStore(self.base/'master.sqlite');self.planner=PortfolioPlanner(self.store,self.registry,self.config,ROOT)
        self.assertEqual(self.planner.claim(1006),[]);self.assertEqual(self.store.task('one')['state'],'EXPIRED')

    def test_crash_recovery_keeps_lock_and_other_worker_continues(self):
        self.submit();job=self.planner.claim(1001)[0]
        self.store.close();self.store=BridgeStore(self.base/'master.sqlite');self.planner=PortfolioPlanner(self.store,self.registry,self.config,ROOT)
        self.planner.recover(job['lease']);self.assertEqual(self.store.task('one')['state'],'NEEDS_HUMAN')
        self.submit('blocked','HEG');self.submit('independent','DPM')
        self.assertEqual([j['id'] for j in self.planner.claim(job['lease']+1)],['independent'])
        row=self.store.db.execute('SELECT * FROM escalations WHERE task=?',('one',)).fetchone()
        self.assertTrue(row['summary'].startswith(DEGRADED))
        with self.assertRaises(ProtocolError):HumanGateway(self.store).decide(SimulationSession('synthetic-supervisor',True),row['id'],row['scope'],'APPROVE',job['lease']+1)
        with self.assertRaises(ProtocolError):self.planner.finish(job,self.evidence(job),job['lease']+1)

    def test_shared_infrastructure_serialization_and_simulated_approval(self):
        self.submit('a','BHB',operation='simulate_shared_change');self.submit('b','DPM',operation='simulate_deployment')
        self.assertEqual(self.planner.claim(1001),[])
        row=self.approve('a');self.approve('b')
        jobs=self.planner.claim(1002);self.assertEqual(len(jobs),1)
        self.assertIn('GLOBAL_INFRASTRUCTURE_CHANGE',json.loads(jobs[0]['resources']))
        self.planner.finish(jobs[0],self.evidence(jobs[0],simulation=True,real_change=False),1003)
        self.assertEqual(len(self.planner.claim(1004)),1)
        with self.assertRaises(ProtocolError):HumanGateway(self.store).decide(SimulationSession('synthetic-supervisor',True),row['id'],row['scope'],'APPROVE',1005)

    def test_delivery_is_not_approval_fallback_denial_timeout(self):
        self.submit('deny',operation='simulate_activation');gateway=HumanGateway(self.store,SimulatedNotifications(whatsapp=False,email=True));gateway.tick(1001)
        self.assertEqual(self.store.task('deny')['state'],'NEEDS_HUMAN')
        channels=list(self.store.db.execute('SELECT channel,state FROM deliveries'))
        self.assertIn(('email','ACKNOWLEDGED'),[tuple(r) for r in channels])
        self.approve('deny','REJECT');self.assertEqual(self.planner.claim(1002),[])
        self.submit('timeout',operation='simulate_privileged',ttl_seconds=5);gateway.tick(1006)
        self.assertEqual(self.store.task('timeout')['state'],'HUMAN_TIMEOUT')

    def test_unauthenticated_wrong_scope_and_notification_outage(self):
        self.submit(operation='simulate_shared_change');row=self.store.db.execute('SELECT * FROM escalations').fetchone();gateway=HumanGateway(self.store,SimulatedNotifications(False,False))
        with self.assertRaises(PermissionError):gateway.decide(SimulationSession('synthetic-supervisor',False),row['id'],row['scope'],'APPROVE',1001)
        with self.assertRaises(ProtocolError):gateway.decide(SimulationSession('synthetic-supervisor',True),row['id'],'wrong','APPROVE',1001)
        for now in (1001,1003,1007,1020):gateway.tick(now)
        self.assertEqual(self.store.task('one')['state'],'NEEDS_HUMAN')
        self.assertTrue(all(r['attempts']<=3 for r in self.store.db.execute('SELECT * FROM deliveries')))
        self.submit('other','DAT_FUTURES');self.assertEqual(self.planner.claim(1021)[0]['id'],'other')

    def test_prestart_retry_bound_and_ambiguous_no_retry(self):
        self.submit()
        for start in (1001,1005,1011):
            job=self.planner.claim(start)[0];self.planner.finish(job,self.evidence(job,outcome='BEFORE_START_UNAVAILABLE',passed=False),start+1)
        self.assertEqual(self.store.task('one')['state'],'NEEDS_HUMAN');self.assertEqual(self.store.task('one')['attempts'],3)
        self.submit('ambiguous','DPM');job=self.planner.claim(1013)[0]
        self.planner.finish(job,self.evidence(job,outcome='AMBIGUOUS',passed=False),1014)
        self.assertEqual(self.store.task('ambiguous')['state'],'NEEDS_HUMAN')
        self.assertEqual(self.planner.claim(1015),[])

    def test_individual_worker_failure_does_not_block_safe_work(self):
        self.submit('b','BHB');self.submit('d','DPM')
        class Adapter:
            def execute(inner,job,barrier):
                if job['worker']=='bhb_heg':raise RuntimeError('simulated worker lost')
                return self.evidence(job)
        MasterRunner(self.planner,Adapter()).tick(1001)
        self.assertEqual(self.store.task('b')['state'],'NEEDS_HUMAN');self.assertEqual(self.store.task('d')['state'],'SUCCEEDED')

    def test_central_mcp_bidirectional_correlated_result(self):
        server=MasterMcpPrototype(MasterBrainTools(self.planner))
        with self.assertRaises(ProtocolError):server.request({'method':'tools/list'},1000)
        server.request({'method':'initialize'},1000);server.request({'method':'notifications/initialized'},1000)
        req=lambda name,args:{'method':'tools/call','params':{'name':name,'arguments':args}}
        server.request(req('dmb_submit_job',{'task_id':'central','correlation_id':'corr-central','project_id':'DPM'}),1000)
        job=self.planner.claim(1001)[0];self.planner.finish(job,self.evidence(job),1002)
        result=server.request(req('dmb_job_status',{'task_id':'central'}),1003)['structuredContent']
        self.assertEqual(result['correlation_id'],'corr-central');self.assertEqual(result['state'],'SUCCEEDED')
        report=server.request(req('dmb_portfolio_report',{}),1003)['structuredContent']
        self.assertEqual(len(report['projects']),13);self.assertTrue(report['audit_chain_valid'])
        self.assertTrue(any(m['kind']=='RESULT' for m in report['outbox']))
        with self.assertRaises(ProtocolError):server.request(req('dmb_submit_job',{'task_id':'x','correlation_id':'c','project_id':'BHB','shell':'whoami'}),1004)

    def test_temporal_contract_has_scope_and_fence(self):
        value=PortfolioWorkflowInput(Job('one','corr','BHB'),'dmb-portfolio-v1','a'*64,1).to_json()
        self.assertEqual(value['mode'],'SHADOW')
        with self.assertRaises(ProtocolError):PortfolioWorkflowInput(Job('one','corr','BHB'),'v1','a'*64,0).to_json()

    def test_100_synthetic_task_cycles_no_loss_duplicate_or_reexecution(self):
        for i in range(100):
            name='cycle-'+str(i);self.submit(name);self.submit(name)
            job=self.planner.claim(1001)[0];self.planner.finish(job,self.evidence(job,synthetic=True),1002)
            self.submit(name)
        self.assertEqual(self.store.db.execute('SELECT count(*) FROM executions').fetchone()[0],100)
        self.assertEqual(self.store.db.execute("SELECT count(*) FROM tasks WHERE state='SUCCEEDED'").fetchone()[0],100)
        self.store.verify_audit()

    def test_audit_tamper_detected(self):
        self.submit();self.store.verify_audit();self.store.db.execute("UPDATE audit SET hash='bad' WHERE seq=1")
        with self.assertRaises(ProtocolError):self.store.verify_audit()

    def test_uncertain_worker_still_reserves_parallel_and_memory(self):
        self.submit('b','BHB');self.submit('d','DAT_MT5');self.submit('p','DPM')
        jobs=self.planner.claim(1001)
        self.planner.recover(jobs[0]['lease'])
        self.assertEqual(len(list(self.store.db.execute('SELECT * FROM master_locks'))),3)
        self.submit('new','HEG')
        self.assertEqual(self.planner.claim(1032),[])
        self.assertEqual(self.store.db.execute("SELECT blocked FROM master_jobs WHERE task='new'").fetchone()[0],'RESOURCE_BUDGET')

    def test_proven_no_start_releases_reservation_after_bounded_retries(self):
        self.submit()
        for start in (1001,1005,1011):
            job=self.planner.claim(start)[0]
            self.planner.finish(job,self.evidence(job,outcome='BEFORE_START_UNAVAILABLE',passed=False),start+1)
        self.assertEqual(list(self.store.db.execute('SELECT * FROM master_locks')),[])
        self.submit('safe','HEG')
        self.assertEqual(self.planner.claim(1014)[0]['id'],'safe')

    def test_timeout_kills_worker_process_group(self):
        import os
        from dci.master.workers import WorkerAdapter
        runtime=self.base/'runtime';(runtime/'tools').mkdir(parents=True)
        (runtime/'tools/dmb_worker_entry.py').write_text('''import json, pathlib, subprocess, sys, time
request=pathlib.Path(sys.argv[1])
child=subprocess.Popen([sys.executable,'-c','import time; time.sleep(20)'])
(request.parent/'child.pid').write_text(str(child.pid))
time.sleep(20)
''')
        self.submit();job=self.planner.claim(1001)[0];job['worker_spec']={**job['worker_spec'],'max_seconds':1}
        result=WorkerAdapter(runtime).execute(job)
        self.assertEqual(result['outcome'],'AMBIGUOUS')
        child_pid=int((Path(result['artifact'])/'child.pid').read_text())
        status=Path('/proc')/str(child_pid)/'status'
        if status.exists():
            self.assertIn('State:\tZ',status.read_text())

    def test_live_codex_gate_cannot_be_promoted_by_simulation(self):
        from dci.master.workers import WorkerAdapter
        self.submit(operation='codex_review');job=self.planner.claim(1001)[0]
        result=WorkerAdapter(ROOT).execute(job)
        self.assertEqual(result['outcome'],'BEFORE_START_UNAVAILABLE')
        self.assertFalse(result['passed'])
        self.assertIn('no turn started',result['gate'])

    def test_independent_mcp_process_and_restart_without_operator_services(self):
        import os, subprocess, sys
        config=self.base/'workers.json';config.write_text(json.dumps(self.config))
        db=self.base/'independent.db'
        argv=[sys.executable,'-m','dci.master','--workspace',str(ROOT),'--database',str(db),'--workers',str(config)]
        env={'PATH':'/usr/bin:/bin','LANG':'C.UTF-8','PYTHONPATH':str(ROOT/'src')}
        messages=[{'jsonrpc':'2.0','id':1,'method':'initialize','params':{}},
                  {'jsonrpc':'2.0','method':'notifications/initialized'},
                  {'jsonrpc':'2.0','id':2,'method':'tools/call','params':{'name':'dmb_submit_job','arguments':{'task_id':'standalone','correlation_id':'corr-standalone','project_id':'DPM'}}},
                  {'jsonrpc':'2.0','id':3,'method':'tools/call','params':{'name':'dmb_job_status','arguments':{'task_id':'standalone'}}}]
        proc=subprocess.run(argv+['mcp'],input=''.join(json.dumps(m)+'\n' for m in messages),capture_output=True,text=True,env=env,timeout=5,check=True)
        replies=[json.loads(line) for line in proc.stdout.splitlines()]
        self.assertEqual(replies[-1]['result']['structuredContent']['state'],'QUEUED')
        proc=subprocess.run(argv+['report'],capture_output=True,text=True,env=env,timeout=5,check=True)
        report=json.loads(proc.stdout)
        self.assertEqual(report['jobs'][0]['task'],'standalone');self.assertTrue(report['audit_chain_valid'])
        self.assertEqual(report['jobs'][0]['correlation_id'],'corr-standalone')
