"""Bounded trusted worker execution; durable planner owns authorization, not text."""
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import os
import signal
from pathlib import Path
import subprocess
import sys
import time
from uuid import uuid4
from dci.bridge.protocol import ProtocolError
from .planner import PROTECTED


class WorkerAdapter:
    def __init__(self, workspace):
        self.workspace=Path(workspace).resolve()

    def execute(self, job, barrier=None):
        evidence={k:job[v] for k,v in [('task_id','id'),('scope_digest','scope_digest'),('workspace','workspace'),('worker_id','worker')]}
        if job['operation'] in PROTECTED:
            return {**evidence,'outcome':'COMPLETE','passed':True,'simulation':True,'operation':job['operation'],'real_change':False}
        if job['operation']=='codex_review':
            # Existing officially supported HandsAdapter is the live prototype.
            # No DMB delegation until its identity/runtime/resource gate passes.
            return {**evidence,'outcome':'BEFORE_START_UNAVAILABLE','passed':False,'gate':'live Codex execution not certified; no turn started','interface':'codex exec --sandbox read-only --json --ephemeral'}
        artifact=self.workspace/'artifacts'/'dmb'/str(uuid4())
        artifact.mkdir(parents=True)
        worker=job['worker_spec']
        request={**worker,**evidence,'operation':job['operation'],'barrier':str(barrier) if barrier else None}
        request_path=artifact/'request.json';request_path.write_text(json.dumps(request))
        script=self.workspace/'tools/dmb_worker_entry.py'
        if os.name!='posix':
            return {**evidence,'outcome':'BEFORE_START_UNAVAILABLE','passed':False,'gate':'non-admin process group/resource enforcement unverified on this OS'}
        if not script.is_file() or not Path(job['workspace']).is_dir():
            return {**evidence,'outcome':'BEFORE_START_UNAVAILABLE','passed':False,'gate':'workspace/entry missing; no process started'}
        # No inherited provider/trading credentials or free-form environment input.
        env={'PATH':'/usr/bin:/bin','LANG':'C.UTF-8','PYTHONDONTWRITEBYTECODE':'1','GIT_CONFIG_NOSYSTEM':'1'}
        try:
            with (artifact/'stdout.log').open('wb') as out,(artifact/'stderr.log').open('wb') as err:
                proc=subprocess.Popen([sys.executable,'-I',str(script),str(request_path)],cwd=job['workspace'],env=env,stdout=out,stderr=err,shell=False,start_new_session=True)
                try:
                    proc.wait(timeout=worker['max_seconds'])
                except subprocess.TimeoutExpired:
                    os.killpg(proc.pid,signal.SIGKILL)
                    proc.wait(timeout=3)
                    raise
        except FileNotFoundError:
            return {**evidence,'outcome':'BEFORE_START_UNAVAILABLE','passed':False,'gate':'executable missing'}
        except (subprocess.TimeoutExpired,OSError):
            return {**evidence,'outcome':'AMBIGUOUS','passed':False,'gate':'process termination/IO outcome uncertain','artifact':str(artifact)}
        report=artifact/'report.json'
        if proc.returncode!=0 or not report.is_file() or report.stat().st_size>worker['max_output_bytes']:
            return {**evidence,'outcome':'AMBIGUOUS','passed':False,'gate':'no valid completion; inspect local-only logs','exit_code':proc.returncode,'artifact':str(artifact)}
        data=json.loads(report.read_text())
        if any(data.get(k)!=v for k,v in evidence.items()):
            raise ProtocolError('worker report route mismatch')
        return {**data,'artifact':str(artifact)}


class MasterRunner:
    def __init__(self, planner, adapter=None):
        self.planner=planner
        self.adapter=adapter or WorkerAdapter(planner.workspace)

    def tick(self, now, concurrent_barrier=False):
        jobs=self.planner.claim(now)
        if not jobs:
            return []
        started=time.monotonic()
        barrier=None
        if concurrent_barrier:
            if len({j['worker'] for j in jobs})!=len(jobs) or any(j['operation']!='verify_lab' for j in jobs):
                raise ProtocolError('barrier requires distinct fixed verifier workers')
            barrier=self.planner.workspace/'artifacts'/'barriers'/str(uuid4());barrier.mkdir(parents=True)
        records=[]
        with ThreadPoolExecutor(max_workers=self.planner.config['max_parallel']) as pool:
            futures={pool.submit(self.adapter.execute,j,barrier):j for j in jobs}
            if barrier:
                limit=time.monotonic()+3
                while len(list(barrier.glob('ready-*')))<len(jobs) and time.monotonic()<limit and not any(f.done() for f in futures):
                    time.sleep(.005)
                (barrier/'GO').write_text('concurrent shadow tests only')
            for future in as_completed(futures):
                job=futures[future]
                try:
                    evidence=future.result()
                except Exception as exc:
                    evidence={'task_id':job['id'],'scope_digest':job['scope_digest'],'workspace':job['workspace'],'worker_id':job['worker'],'outcome':'AMBIGUOUS','passed':False,'gate':type(exc).__name__}
                completed=now+int(time.monotonic()-started)+1
                try:
                    self.planner.finish(job,evidence,completed)
                except ProtocolError:
                    # Deadline/fence mismatch: retain locks for reconciliation.
                    from dci.bridge.runner import Runner
                    with self.planner.store.tx():
                        current=self.planner.store.task(job['id'])
                        if current['state']=='RUNNING' and current['attempts']==job['attempts']:
                            Runner(self.planner.store,self.planner.workspace)._human(job['id'],completed,'CONTROL_PLANE_DEGRADED','Completion fence/route invalid; reconciliation required')
                records.append(evidence)
        return records
