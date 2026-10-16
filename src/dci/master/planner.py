"""Atomic dependency/resource-aware scheduling using the existing BHB authority."""
import hashlib
import json
from dataclasses import dataclass, asdict, field
from pathlib import Path
from dci.bridge.protocol import ProtocolError, canonical, envelope, identifier
from dci.bridge.runner import Runner
from dci.bridge.identity import require_non_admin

OPERATIONS = {'verify_lab','codex_review','simulate_shared_change','simulate_deployment','simulate_privileged','simulate_activation'}
PROTECTED = OPERATIONS - {'verify_lab','codex_review'}


@dataclass(frozen=True)
class Job:
    task_id: str
    correlation_id: str
    project_id: str
    operation: str = 'verify_lab'
    priority: int = 50
    dependencies: tuple[str, ...] = field(default_factory=tuple)
    ttl_seconds: int = 3600

    def validate(self):
        for value in (self.task_id,self.correlation_id,self.project_id):
            identifier(value)
        if self.operation not in OPERATIONS or type(self.priority) is not int or not 0 <= self.priority <= 100 or type(self.ttl_seconds) is not int or not 1 <= self.ttl_seconds <= 86400:
            raise ProtocolError('invalid operation, priority or deadline')
        if len(self.dependencies) > 100 or len(set(self.dependencies)) != len(self.dependencies) or self.task_id in self.dependencies:
            raise ProtocolError('invalid job dependencies')
        for dependency in self.dependencies:
            identifier(dependency)


class PortfolioPlanner:
    def __init__(self, store, registry, workers, workspace):
        self.store, self.registry = store, registry
        self.workspace = require_non_admin(workspace)
        self.config = json.loads(Path(workers).read_text()) if not isinstance(workers, dict) else workers
        if self.config.get('schema_version') != 1 or self.config.get('mode') != 'SHADOW':
            raise ProtocolError('unsupported worker manifest')
        if type(self.config['max_parallel']) is not int or self.config['max_parallel'] not in (1,2,3) or type(self.config['max_memory_mb']) is not int or not 64 <= self.config['max_memory_mb'] <= 768:
            raise ProtocolError('shadow resource limits exceeded')
        if not 1 <= len(self.config['workers']) <= 3:
            raise ProtocolError('bounded shadow worker registry required')
        self.workers = {}
        self.binding = hashlib.sha256(canonical({'registry':registry.data,'workers':self.config}).encode()).hexdigest()
        roots = set()
        for worker in self.config['workers']:
            identifier(worker['worker_id'])
            if len(worker['expected_commit'])!=40 or any(c not in '0123456789abcdef' for c in worker['expected_commit']):
                raise ProtocolError('invalid reviewed Git commit')
            if any(type(worker[k]) is not int for k in ('max_seconds','memory_mb','cpu_seconds','max_output_bytes')):
                raise ProtocolError('integer resource limits required')
            root = Path(worker['workspace']).resolve(strict=True)
            if root == self.workspace or self.workspace in root.parents or root in self.workspace.parents or root in roots or worker['worker_id'] in self.workers:
                raise ProtocolError('overlapping worker workspace')
            if any(root in p.parents or p in root.parents for p in roots):
                raise ProtocolError('nested worker workspace')
            if not 1 <= worker['max_seconds'] <= 20 or not 64 <= worker['memory_mb'] <= 256 or not 1 <= worker['cpu_seconds'] <= 10 or not 1 <= worker['max_output_bytes'] <= 1048576:
                raise ProtocolError('unbounded worker resource budget')
            if any(set(worker['project_ids']) & set(w['project_ids']) for w in self.workers.values()):
                raise ProtocolError('duplicate project route')
            for project in worker['project_ids']:
                registry.get(project)
            roots.add(root)
            self.workers[worker['worker_id']] = {**worker,'workspace':str(root)}
        with store.tx():
            version = store.db.execute("SELECT value FROM meta WHERE key='dmb_version'").fetchone()
            if version is not None and version[0] != '1':
                raise ProtocolError('unsupported DMB database extension')
            if version is None:
                store.db.execute("CREATE TABLE master_jobs(task TEXT PRIMARY KEY, spec TEXT, scope TEXT, worker TEXT, workspace TEXT, operation TEXT, priority INTEGER, dependencies TEXT, resources TEXT, memory INTEGER, attempt INTEGER DEFAULT 0, blocked TEXT)")
                store.db.execute("CREATE TABLE master_locks(resource TEXT PRIMARY KEY, task TEXT, fence INTEGER)")
                store.db.execute("CREATE TABLE master_heartbeats(worker TEXT PRIMARY KEY, at INTEGER, task TEXT)")
                store.db.execute("INSERT INTO meta VALUES ('dmb_version','1')")
                store.db.execute("INSERT INTO meta VALUES ('dmb_registry_version',?)", (registry.data['registry_version'],))
                store.db.execute("INSERT INTO meta VALUES ('dmb_binding',?)", (self.binding,))
            elif store.db.execute("SELECT value FROM meta WHERE key='dmb_registry_version'").fetchone()[0] != registry.data['registry_version']:
                raise ProtocolError('registry migration/review required')
            elif store.db.execute("SELECT value FROM meta WHERE key='dmb_binding'").fetchone()[0] != self.binding:
                raise ProtocolError('registry/worker context drift; migration required')

    def _worker(self, project):
        matches = [w for w in self.workers.values() if project in w['project_ids']]
        if len(matches) != 1:
            raise ProtocolError('no unique certified shadow workspace for project')
        return matches[0]

    def submit(self, job: Job, now):
        job.validate()
        self.registry.get(job.project_id)
        worker = self._worker(job.project_id)
        full = {**asdict(job),'registry_version':self.registry.data['registry_version'],'worker':worker}
        spec = canonical(full)
        scope = hashlib.sha256(spec.encode()).hexdigest()
        resources = ['workspace:'+worker['workspace']]
        if job.operation in PROTECTED:
            resources += ['GLOBAL_INFRASTRUCTURE_CHANGE']
        s = self.store
        with s.tx():
            prior = s.db.execute('SELECT spec FROM master_jobs WHERE task=?',(job.task_id,)).fetchone()
            if prior:
                if prior[0] != spec or s.task(job.task_id)['expires'] <= now:
                    raise ProtocolError('job identity conflict or expired retry')
                return s.task(job.task_id)
            for dep in job.dependencies:
                if s.db.execute('SELECT task FROM master_jobs WHERE task=?',(dep,)).fetchone() is None:
                    raise ProtocolError('dependency must be a previously registered job')
            action = 'gated_shadow_note' if job.operation in PROTECTED else 'synthetic_check'
            m = envelope('TASK','brain','runner',job.task_id,job.correlation_id,{'action':action,'parameters':{}},s._next('brain','runner'),now,job.ttl_seconds)
            s._accept('brain',m,now)
            # The immutable portfolio context is part of the authorization scope;
            # ordinary BHB Runner must not be used on this dedicated DMB database.
            s.db.execute('UPDATE tasks SET scope=? WHERE id=?',(scope,job.task_id))
            s.db.execute('INSERT INTO master_jobs(task,spec,scope,worker,workspace,operation,priority,dependencies,resources,memory) VALUES (?,?,?,?,?,?,?,?,?,?)',
                         (job.task_id,spec,scope,worker['worker_id'],worker['workspace'],job.operation,job.priority,canonical(job.dependencies),canonical(resources),worker['memory_mb']))
            s._emit('EVENT','runner','brain',job.task_id,job.correlation_id,{'event':'PORTFOLIO_JOB_REGISTERED','detail':spec},now)
            if job.operation in PROTECTED:
                Runner(s,self.workspace)._human(job.task_id,now,summary='Approval for exact simulated infrastructure scope; no real changes')
        return s.task(job.task_id)

    def recover(self, now):
        s = self.store
        with s.tx():
            s.db.execute("INSERT INTO heartbeats VALUES ('master',?) ON CONFLICT(role) DO UPDATE SET at=excluded.at",(now,))
            for row in list(s.db.execute("SELECT t.id FROM tasks t JOIN master_jobs j ON j.task=t.id WHERE t.state='RUNNING' AND (t.lease<=? OR t.expires<=?)",(now,now))):
                Runner(s,self.workspace)._human(row[0],now,'CONTROL_PLANE_DEGRADED','Worker outcome uncertain; retain locks and require reconciliation')
            for row in list(s.db.execute("SELECT t.id FROM tasks t JOIN master_jobs j ON j.task=t.id WHERE t.state IN ('QUEUED','RETRY_WAIT') AND t.expires<=?",(now,))):
                s.db.execute("UPDATE tasks SET state='EXPIRED' WHERE id=?",(row[0],))
                s._status(row[0],'EXPIRED','portfolio deadline expired',now)

    def claim(self, now):
        self.recover(now)
        s = self.store
        selected = []
        with s.tx():
            if s.db.execute("SELECT value FROM meta WHERE key='paused'").fetchone()[0] == '1':
                return selected
            running = list(s.db.execute("SELECT j.memory FROM master_jobs j JOIN tasks t ON t.id=j.task WHERE t.state='RUNNING' OR EXISTS (SELECT 1 FROM master_locks l WHERE l.task=j.task)"))
            occupied = len(running)
            memory = sum(row[0] for row in running)
            rows = list(s.db.execute("SELECT j.*,t.state,t.expires,t.retry_at FROM master_jobs j JOIN tasks t ON t.id=j.task WHERE t.state='QUEUED' OR (t.state='RETRY_WAIT' AND t.retry_at<=?) ORDER BY j.priority DESC,j.rowid",(now,)))
            for row in rows:
                job = dict(row)
                task = s.task(job['task'])
                if occupied >= self.config['max_parallel'] or memory + job['memory'] > self.config['max_memory_mb']:
                    s.db.execute("UPDATE master_jobs SET blocked='RESOURCE_BUDGET' WHERE task=?",(job['task'],));continue
                if any(s.task(dep)['state'] != 'SUCCEEDED' for dep in json.loads(job['dependencies'])):
                    s.db.execute("UPDATE master_jobs SET blocked='DEPENDENCY_NOT_SUCCEEDED' WHERE task=?",(job['task'],));continue
                locks = json.loads(job['resources'])
                if any(s.db.execute('SELECT task FROM master_locks WHERE resource=?',(key,)).fetchone() for key in locks):
                    s.db.execute("UPDATE master_jobs SET blocked='RESOURCE_LOCK' WHERE task=?",(job['task'],));continue
                if job['operation'] in PROTECTED and s.db.execute("SELECT id FROM escalations WHERE task=? AND scope=? AND decision='APPROVE' AND expires>?",(job['task'],job['scope'],now)).fetchone() is None:
                    Runner(s,self.workspace)._human(job['task'],now,summary='Simulated approval missing/expired');continue
                fence = task['attempts']+1
                timeout = self.workers[job['worker']]['max_seconds']
                s.db.execute("UPDATE tasks SET state='RUNNING',attempts=?,lease=? WHERE id=?",(fence,now+timeout+10,job['task']))
                s.db.execute('UPDATE master_jobs SET attempt=?,blocked=NULL WHERE task=?',(fence,job['task']))
                for key in locks:
                    s.db.execute('INSERT INTO master_locks VALUES (?,?,?)',(key,job['task'],fence))
                s.db.execute('INSERT INTO master_heartbeats VALUES (?,?,?) ON CONFLICT(worker) DO UPDATE SET at=excluded.at,task=excluded.task',(job['worker'],now,job['task']))
                s._status(job['task'],'RUNNING','DMB worker claim with resource fence',now)
                selected.append({**job,**s.task(job['task']),'scope_digest':job['scope'],'worker_spec':self.workers[job['worker']]})
                occupied+=1;memory+=job['memory']
        return selected

    def finish(self, job, evidence, now):
        s = self.store
        with s.tx():
            current = s.task(job['id'])
            if current['state'] != 'RUNNING' or current['attempts'] != job['attempts'] or current['lease'] <= now or current['expires'] <= now:
                raise ProtocolError('stale portfolio completion')
            if evidence.get('task_id') != job['id'] or evidence.get('scope_digest') != job['scope_digest'] or evidence.get('workspace') != job['workspace'] or evidence.get('worker_id') != job['worker']:
                raise ProtocolError('wrong-route worker evidence')
            if evidence.get('outcome') == 'AMBIGUOUS':
                s.db.execute('UPDATE tasks SET result=? WHERE id=?',(canonical(evidence),job['id']))
                Runner(s,self.workspace)._human(job['id'],now,'CONTROL_PLANE_DEGRADED','External worker outcome uncertain; locks retained')
                return
            if evidence.get('outcome') == 'BEFORE_START_UNAVAILABLE':
                if current['attempts'] >= 3:
                    s.db.execute('DELETE FROM master_locks WHERE task=? AND fence=?',(job['id'],job['attempts']))
                    Runner(s,self.workspace)._human(job['id'],now,'CONTROL_PLANE_DEGRADED','Worker unavailable after bounded pre-start retries; no execution began')
                else:
                    s.db.execute("UPDATE tasks SET state='RETRY_WAIT',retry_at=?,lease=NULL WHERE id=?",(now+2**current['attempts'],job['id']))
                    s.db.execute('DELETE FROM master_locks WHERE task=? AND fence=?',(job['id'],job['attempts']))
                    s._status(job['id'],'RETRY_WAIT','Proven worker not started',now)
                return
            if evidence.get('outcome') != 'COMPLETE' or type(evidence.get('passed')) is not bool:
                raise ProtocolError('unsupported completion outcome')
            state = 'SUCCEEDED' if evidence['passed'] else 'FAILED'
            s.db.execute('INSERT INTO executions VALUES (?,?)',(job['id'],canonical(evidence)))
            s.db.execute('UPDATE tasks SET state=?,result=?,lease=NULL WHERE id=?',(state,canonical(evidence),job['id']))
            s.db.execute('DELETE FROM master_locks WHERE task=? AND fence=?',(job['id'],job['attempts']))
            s._emit('RESULT','runner','brain',job['id'],current['correlation'],{'state':state,'evidence':evidence},now)
            s._status(job['id'],state,'Portfolio workstream complete',now)
