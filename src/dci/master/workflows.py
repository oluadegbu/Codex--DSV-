"""Transport-independent Temporal-compatible contracts; no SDK/server dependency.

Workflow input and signals are JSON-serializable. An eventual Temporal workflow
must call nonblocking claim/activity/result transitions; it must not run SQLite
or subprocesses inside workflow code. Activity retries reuse ID, scope and fence.
"""
from dataclasses import dataclass, asdict
from .planner import Job
from dci.bridge.protocol import identifier, ProtocolError


@dataclass(frozen=True)
class PortfolioWorkflowInput:
    job: Job
    registry_version: str
    scope_digest: str
    activity_fence: int
    schema_version: int = 1
    mode: str = 'SHADOW'

    def to_json(self):
        self.job.validate();identifier(self.registry_version)
        if self.schema_version!=1 or self.mode!='SHADOW' or type(self.activity_fence) is not int or self.activity_fence<1 or len(self.scope_digest)!=64 or any(c not in '0123456789abcdef' for c in self.scope_digest):
            raise ProtocolError('invalid durable workflow contract')
        return asdict(self)


SIGNALS=('PAUSE','RESUME','WORKER_LOST','APPROVAL_DECIDED','RECONCILIATION_REQUIRED')
ACTIVITIES=('registered_job_claim','fixed_shadow_worker','record_fenced_result','simulated_heg_delivery','portfolio_report')
PROTECTED_MILESTONE='Previously approved DAT Temporal Integration milestone'
# Completion uncertainty is never a retry permission. Durable keys and locks
# must survive worker/process outages. Real infrastructure migration is gated.
