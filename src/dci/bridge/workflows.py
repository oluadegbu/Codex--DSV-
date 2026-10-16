"""Temporal-compatible activity boundary; no Temporal client/service installed."""
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class ActivityInput:
    version: int
    task_id: str
    correlation_id: str
    idempotency_key: str
    scope_digest: str
    deadline: int


class BridgeActivities(Protocol):
    def dispatch(self, command: ActivityInput) -> dict: ...
    def reconcile(self, command: ActivityInput) -> dict: ...
    def notify_human(self, command: ActivityInput) -> dict: ...
    def read_result(self, command: ActivityInput) -> dict: ...


# Host workflow supplies deterministic time, not wall-clock reads inside workflows.
# Retry only provably pre-start failures. Unknown effects -> reconciliation and HEG.
# Activity retries use the same idempotency key, never a new execution identity.
RETRY_POLICY = {'maximum_attempts': 3, 'initial_interval_seconds': 2,
                'non_retryable_errors': ('AmbiguousOutcome', 'Unauthorized', 'Expired', 'WrongScope')}
