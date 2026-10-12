"""Single local MCP inbox/outbox. Remote ChatGPT auth/delivery remains uncertified."""
import json
from dci.bridge.brain import BrainTools, LocalMcpPrototype
from dci.bridge.protocol import ProtocolError
from .planner import Job, OPERATIONS

TOOLS=[
 {'name':'dmb_submit_job','description':'Submit a bounded fixed shadow job to one registered worker; no commands or prompts',
  'inputSchema':{'type':'object','properties':{'task_id':{'type':'string'},'correlation_id':{'type':'string'},'project_id':{'type':'string'},'operation':{'enum':sorted(OPERATIONS)},'priority':{'type':'integer','minimum':0,'maximum':100},'dependencies':{'type':'array','items':{'type':'string'},'maxItems':100},'ttl_seconds':{'type':'integer','minimum':1,'maximum':86400}},'required':['task_id','correlation_id','project_id'],'additionalProperties':False}},
 {'name':'dmb_portfolio_report','description':'Consolidated verified portfolio, workers, tasks and human queue','inputSchema':{'type':'object','properties':{},'additionalProperties':False}},
 {'name':'dmb_job_status','description':'Correlated durable task results','inputSchema':{'type':'object','properties':{'task_id':{'type':'string'}},'required':['task_id'],'additionalProperties':False}},
 {'name':'dmb_control','description':'Pause/resume future dispatch','inputSchema':{'type':'object','properties':{'event':{'enum':['PAUSE','RESUME']}},'required':['event'],'additionalProperties':False}}
]


class MasterBrainTools:
    def __init__(self, planner):
        self.planner=planner
        self.bridge=BrainTools(planner.store)

    def status(self, task_id):
        s=self.planner.store
        task=s.task(task_id)
        return {'task_id':task['id'],'correlation_id':task['correlation'],'state':task['state'],'result':json.loads(task['result']) if task['result'] else None,'messages':[json.loads(row[0]) for row in s.db.execute("SELECT body FROM messages WHERE recipient='brain' AND task=? ORDER BY rowid LIMIT 100",(task_id,))]}

    def report(self):
        s=self.planner.store
        s.verify_audit()
        jobs=[{**dict(row),'state':s.task(row['task'])['state'],'correlation_id':s.task(row['task'])['correlation']} for row in s.db.execute('SELECT task,worker,workspace,operation,priority,blocked FROM master_jobs ORDER BY rowid DESC LIMIT 100')]
        outbox=[json.loads(row[0]) for row in reversed(list(s.db.execute("SELECT body FROM messages WHERE recipient='brain' ORDER BY rowid DESC LIMIT 100")))]
        totals={key:s.db.execute(query).fetchone()[0] for key,query in {'jobs':"SELECT count(*) FROM master_jobs",'outbox':"SELECT count(*) FROM messages WHERE recipient='brain'",'pending_human':"SELECT count(*) FROM escalations WHERE decision IS NULL"}.items()}
        worker_status=[]
        for worker in self.planner.workers.values():
            held=[dict(row) for row in s.db.execute("SELECT j.task,t.state,t.lease,t.attempts FROM master_jobs j JOIN tasks t ON t.id=j.task WHERE j.worker=? AND (t.state='RUNNING' OR EXISTS (SELECT 1 FROM master_locks l WHERE l.task=j.task))",(worker['worker_id'],))]
            worker_status.append({'worker_id':worker['worker_id'],'state':'QUARANTINED' if any(j['state']!='RUNNING' for j in held) else ('RUNNING' if held else 'IDLE'),'workspace':worker['workspace'],'reviewed_git_commit':worker['expected_commit'],'reservations':held})
        return {'schema_version':1,'mode':'SHADOW','registry_version':self.planner.registry.data['registry_version'],
                'projects':list(self.planner.registry.projects.values()),'dependency_graph':self.planner.registry.graph(),
                'jobs':jobs,'workers':list(self.planner.workers.values()),'worker_status':worker_status,
                'heartbeats':[dict(row) for row in s.db.execute('SELECT * FROM master_heartbeats')],
                'held_resources':[dict(row) for row in s.db.execute('SELECT * FROM master_locks')],
                'human_queue':[dict(row) for row in s.db.execute('SELECT * FROM escalations WHERE decision IS NULL ORDER BY rowid DESC LIMIT 100')],
                'notification_delivery':[dict(row) for row in s.db.execute('SELECT * FROM deliveries ORDER BY rowid DESC LIMIT 100')],
                'inbox':'messages where sender=brain; monotonic route sequence and stable task IDs',
                'outbox':outbox,'report_limits':{'latest_jobs':100,'latest_outbox':100,'latest_human_requests':100,'latest_deliveries':100},'total_counts':totals,'truncated':totals['jobs']>100 or totals['outbox']>100 or totals['pending_human']>100,'audit_chain_valid':True,
                'scope':'local trusted shadow prototype; live ChatGPT delivery/worker identities/provider certification blocked'}


class MasterMcpPrototype(LocalMcpPrototype):
    def __init__(self, tools):
        super().__init__(tools.bridge)
        self.master=tools

    def request(self, request, now):
        if request.get('method') in ('initialize','notifications/initialized') or not self.ready:
            result=super().request(request,now)
            if request.get('method')=='initialize':
                result['serverInfo']={'name':'directive-master-brain-shadow','version':'1.0.0'}
            return result
        if request.get('method')=='tools/list':
            return {'tools':TOOLS}
        params=request.get('params',{})
        if request.get('method')!='tools/call' or set(params)!={'name','arguments'} or not isinstance(params['arguments'],dict):
            raise ProtocolError('unsupported MCP request')
        args=params['arguments']; name=params['name']
        if name=='dmb_submit_job' and {'task_id','correlation_id','project_id'} <= set(args) <= {'task_id','correlation_id','project_id','operation','priority','dependencies','ttl_seconds'}:
            if 'dependencies' in args and type(args['dependencies']) is not list:
                raise ProtocolError('dependency array required')
            args={**args,'dependencies':tuple(args.get('dependencies',[]))}
            result=self.master.planner.submit(Job(**args),now)
        elif name=='dmb_portfolio_report' and not args:
            result=self.master.report()
        elif name=='dmb_job_status' and set(args)=={'task_id'}:
            if self.master.planner.store.db.execute('SELECT 1 FROM master_jobs WHERE task=?',(args['task_id'],)).fetchone() is None:
                raise ProtocolError('unregistered portfolio task')
            result=self.master.status(args['task_id'])
        elif name=='dmb_control' and set(args)=={'event'}:
            result=self.master.bridge.control(args['event'],now)
        else:
            raise ProtocolError('unsupported master tool or arguments')
        return {'content':[{'type':'text','text':json.dumps(result)}],'structuredContent':result,'isError':False}
