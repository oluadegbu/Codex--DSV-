"""Deterministic one-tick scheduler; no services or conversation dependency."""
from uuid import uuid4
import math
import time
from .identity import require_non_admin
from .protocol import canonical

DEGRADED = '🔴🔴🔴 HUMAN INPUT REQUIRED — CONTROL PLANE DEGRADED 🔴🔴🔴'


class BeforeStartUnavailable(RuntimeError):
    """Only use when the adapter proves no operation was started."""


class Runner:
    def __init__(self, store, workspace, hands=None):
        self.store = store
        self.workspace = require_non_admin(workspace)
        self.hands = hands

    def _human(self, task_id, now, category='APPROVAL', summary='Shadow review required'):
        s = self.store
        task = s.task(task_id)
        existing = s.db.execute("SELECT id FROM escalations WHERE task=? AND decision IS NULL", (task_id,)).fetchone()
        if existing:
            return existing[0]
        request_id = str(uuid4())
        if category == 'CONTROL_PLANE_DEGRADED':
            summary = DEGRADED + ' ' + summary
        expires = min(task['expires'], now + 300)
        # Expired tasks may still need reconciliation; notification envelope remains
        # transport-valid while approval cannot revive an expired task.
        s.db.execute("UPDATE tasks SET state='NEEDS_HUMAN',lease=NULL WHERE id=?", (task_id,))
        s.db.execute("INSERT INTO escalations(id,task,scope,expires,category,summary) VALUES (?,?,?,?,?,?)", (request_id, task_id, task['scope'], expires, category, summary))
        s._emit('APPROVAL_REQUEST', 'runner', 'heg', task_id, task['correlation'], {'request_id': request_id, 'scope_digest': task['scope'], 'category': category, 'summary': summary}, now)
        s._status(task_id, 'NEEDS_HUMAN', category, now)
        return request_id

    def recover(self, now):
        s = self.store
        with s.tx():
            s.db.execute("INSERT INTO heartbeats VALUES ('runner',?) ON CONFLICT(role) DO UPDATE SET at=excluded.at", (now,))
            for row in list(s.db.execute("SELECT id FROM tasks WHERE state='RUNNING' AND lease<=?", (now,))):
                self._human(row[0], now, 'CONTROL_PLANE_DEGRADED', 'Execution outcome uncertain; automatic retry prohibited')
            for row in list(s.db.execute("SELECT id FROM tasks WHERE state IN ('QUEUED','RETRY_WAIT') AND expires<=?", (now,))):
                s.db.execute("UPDATE tasks SET state='EXPIRED' WHERE id=?", (row[0],))
                s._status(row[0], 'EXPIRED', 'task deadline passed', now)

    def claim(self, now):
        if self.store.db.execute("SELECT 1 FROM meta WHERE key='dmb_version'").fetchone():
            raise PermissionError("DMB database requires PortfolioPlanner; ordinary Runner prohibited")
        self.recover(now)
        s = self.store
        with s.tx():
            if s.db.execute("SELECT value FROM meta WHERE key='paused'").fetchone()[0] == '1':
                return None
            row = s.db.execute("SELECT * FROM tasks WHERE state='QUEUED' OR (state='RETRY_WAIT' AND retry_at<=?) ORDER BY rowid LIMIT 1", (now,)).fetchone()
            if row is None:
                return None
            task = dict(row)
            if task['action'] == 'gated_shadow_note':
                approved = s.db.execute("SELECT id FROM escalations WHERE task=? AND decision='APPROVE' AND expires>?", (task['id'], now)).fetchone()
                if not approved:
                    self._human(task['id'], now)
                    return None
            s.db.execute("UPDATE tasks SET state='RUNNING',attempts=attempts+1,lease=? WHERE id=?", (now+30, task['id']))
            s._status(task['id'], 'RUNNING', 'claimed bounded operation', now)
            return s.task(task['id'])

    def finish(self, task, now, evidence):
        s = self.store
        with s.tx():
            current = s.task(task['id'])
            if current['state'] != 'RUNNING' or current['attempts'] != task['attempts'] or current['lease'] <= now or current['expires'] <= now:
                raise RuntimeError('stale/expired execution fence')
            # A synthetic operation has no external effects; count + result are one
            # transaction. External effects never inherit this exactly-once claim.
            s.db.execute("INSERT INTO executions VALUES (?,?)", (task['id'], canonical(evidence)))
            state = 'SUCCEEDED' if evidence.get('passed') is True else 'FAILED'
            s.db.execute("UPDATE tasks SET state=?,result=?,lease=NULL WHERE id=?", (state, canonical(evidence), task['id']))
            s._emit('RESULT', 'runner', 'brain', task['id'], task['correlation'], {'state': state, 'evidence': evidence}, now)
            s._status(task['id'], state, 'bounded operation complete', now)

    def tick(self, now):
        task = self.claim(now)
        if task is None:
            return None
        started = time.monotonic()
        try:
            if task['action'] in ('synthetic_check', 'gated_shadow_note'):
                evidence = {'passed': True, 'operation': task['action'], 'synthetic': True}
            elif self.hands is None:
                raise BeforeStartUnavailable('Hands adapter absent; no operation started')
            else:
                evidence = self.hands.execute(task['action'], self.workspace)
            completed_at = now + math.ceil(time.monotonic() - started)
            if task['action'] == 'codex_review' and evidence.get('turn_completed') is not True:
                with self.store.tx():
                    current = self.store.task(task['id'])
                    if current['state'] != 'RUNNING' or current['attempts'] != task['attempts']:
                        raise RuntimeError('stale control-plane result fence')
                    self.store.db.execute("UPDATE tasks SET result=? WHERE id=?", (canonical(evidence), task['id']))
                    self._human(task['id'], completed_at, 'CONTROL_PLANE_DEGRADED', 'Codex turn not completed; runtime certification blocked')
            else:
                self.finish(task, completed_at, evidence)
        except BeforeStartUnavailable as exc:
            with self.store.tx():
                current = self.store.task(task['id'])
                if current['state'] != 'RUNNING' or current['attempts'] != task['attempts']:
                    raise RuntimeError('stale retry fence')
                if current['attempts'] < 3:
                    self.store.db.execute("UPDATE tasks SET state='RETRY_WAIT',lease=NULL,retry_at=? WHERE id=?", (now+2**current['attempts'], task['id']))
                    self.store._status(task['id'], 'RETRY_WAIT', str(exc), now)
                else:
                    self._human(task['id'], now, 'CONTROL_PLANE_DEGRADED', str(exc))
        except Exception as exc:
            with self.store.tx():
                current = self.store.task(task['id'])
                if current['state'] == 'RUNNING' and current['attempts'] == task['attempts']:
                    self._human(task['id'], now, 'CONTROL_PLANE_DEGRADED', type(exc).__name__ + ': uncertain outcome')
        return self.store.task(task['id'])
