# DMB autonomous operations integration — SHADOW

The original Windows0.1.3 core, pairing and journals are unchanged. The actual
VPS receipt is retained at `docs/evidence/windows-genuine-completion/`:
WINDOWS_SINGLE_TASK_LOCAL_BRIDGE_PASS, DirectiveCodex/Medium/non-admin, PID4196,
DCI_SHADOW_OK, one durable execution, audit valid, both worker runs exit0 and
restart replay suppression PASS. This certifies local foreground execution;
RDP independence, Windows cancellation/crash and OS isolation remain untested.

## Shortest practical path

1. Use the existing durable planner and compiled Windows connectivity task.
   Add signed Brain intake/review and outbound relay delivery, not another executor.
2. An existing approved HTTPS relay carries `/v1/dmb/windows` worker requests and
   `/v1/dmb/operations` Brain/carrier exchanges. Both controller and worker initiate
   outbound HTTPS; neither opens an inbound/public listener. No relay provider is
   configured or activated by this milestone. The relay must implement the documented
   bounded contract and pass identity, timeout, redelivery and offline certification.
3. A dedicated independently running Brain policy process reviews exact controller
   evidence, permits at most three dependent follow-up generations/ten jobs per
   root, and emits durable exceptions. This is deterministic policy supervision;
   ChatGPT remains a strategic reviewer. No ordinary conversation is assumed to
   self-wake. No model/provider key or paid API is required for this bounded policy.
4. Following REQUEST-0008 approval, register one least-privilege startup task for
   the existing DirectiveCodex identity, without interactive-logon dependence.
   Deploy a pinned operations package/config separately from all failed and
   successful0.1.x installations. No re-pairing, state deletion or journal migration
   occurs automatically. The separate controller/Brain/carrier and worker pairing
   expires fail closed; key rotation requires a reviewed state-preserving transition.
5. Run the actual signed remote workflow and automatic cancellation/owned-worker
   crash tests under that non-admin task. Inspect the actual batch token and
   prove RDP disconnect/logoff/reboot recovery. Keep uncertain starts quarantined.
   Run harmless canary read/write-denial probes using independently recorded
   creator evidence. Only then certify unattended Windows operation or isolation.

## Delivered code

`operations.py` adds a versioned HMAC domain, principal/key/scopes, TTL, sequence,
message identity and exact action allowlist: SUBMIT, REVIEW, CANCEL, PAUSE, RESUME,
REPORT, ACK_EVENTS. There is deliberately no human APPROVE action, remote shell,
mailbox prompt, arbitrary operation, workspace or executable. Worker, Brain and
report-only relay carrier keys must differ. Signed claims are not hardware or
human identity attestation; real endpoint/identity provisioning remains gated.

`Operations` uses the existing AtomicPeerStore and planner. Authenticated request,
intake, review/follow-up and audit commit atomically. Reviews bind exact task scope
and durable result digest; changed/replayed evidence cannot authorize another job.
Follow-ups require successful reviewed completion and the parent dependency.
Durable NEEDS_HUMAN review states/events distinguish supervisory exceptions from
control-plane degradation. Degraded events contain the required red banner.
Ordinary acknowledged cancellation is an event, not an approval escalation.

`operations_client.py` durably records an outbound request before sending. Replies
must authenticate and bind its exact digest/message/sequence. Up to three transient
attempts reuse the same semantic identity. Authentication, TLS and policy failures
stop; no redirects or TLS bypass. Response-loss recovery reuses the durable outbox.
No later request can overtake an uncertain pending one. Expired credentials or
stale signed tasks stay blocked; offline recovery cannot extend authorization.

`operations_relay.py` pulls bounded signed batches using a separate report-only
carrier identity. Incoming Brain and Windows packets still authenticate end to end
through the existing authorities. Received carrier ACKs are durable before inner
messages apply; reopening replays unapplied batches without losing or duplicating
work. Controller replies remain durable until exact relay acknowledgements, and
are freshly signed for retransmission. Delivery acknowledgements never approve
human requests. No external endpoint was contacted in local integration tests.

`operations_cli.py` offers signed stdio exchange, paper tick and outbound
`relay-once`. CLI paths/keys are local operator configuration, never mailbox data.
POSIX identity files require current-user ownership and0600-style permissions;
Windows configurations require current-user DPAPI/native identity validation.
No keys, raw logs, private configs or runtime databases are committed/uploaded.

`windows_operations_worker.py` wraps the existing executor in a bounded polling
loop, exclusive native lock and separate lifecycle heartbeat/audit database. Every
poll preserves native identity, pinned executable/version, sandbox and journal
checks. It delegates receipt reconciliation to the existing worker and stops on
uncertainty, expired pairing or policy failure. It installs nothing and alone does
not prove survival across RDP disconnect. The old certified bridge fingerprint is
unchanged. No service/task has been registered or activated.

`windows_isolation.py` prepares native OPEN_EXISTING probes against fixed harmless
other-account canary fixtures with independent creator existence/hash evidence.
It first requires own-canary positive read/write access, counts only WinError5 as
access denial, never counts missing files, and never modifies denied files or ACLs.
It remains NOT TESTED on DirectiveCodex until the approved real integration run.
Its receipt describes only those canaries, never full hostile-code confinement.

## Local integration evidence and certification scope

`tools/run_operations_workflow.py` launches independent real controller and paper
worker processes, authenticates intake, drops committed replies, reopens the
client, verifies one execution per task, reviews exact evidence, submits and
executes a dependent task, acknowledges delivery and verifies no duplicate work.
The paper market data is synthetic. This is actual process execution over signed
local stdio, not externally certified HTTPS or genuine Windows unattended execution.
`operations_tests` additionally exercises sealed real-receipt recovery and the
relay crash window between durable carrier receipt and applying an inner request.

Existing Linux certification remains, including real controller crash/receipt
recovery. All historical evidence bytes remain intact. Normal CI builds no new
Windows prerelease: publication now requires an explicit reviewed commit marker
`[publish-windows-shadow]`; the certified0.1.3 release stays pinned.

| Gate | State |
| --- | --- |
| Genuine Windows single local task, artifact and durable replay suppression | PASS; actual VPS receipt |
| Signed local intake → real paper execution → review → follow-up → durable reporting | PASS; local integration |
| Client response loss/reopen, deduplication, evidence binding and relay crash window | PASS; local integration/tests |
| Outbound HTTPS adapter and relay contract | IMPLEMENTED; external delivery NOT TESTED |
| Windows bounded wrapper/native canary probes | IMPLEMENTED; actual runtime NOT TESTED |
| RDP-independent startup/reboot, Windows cancellation and crash recovery | BLOCKED; approved installation/context required |
| Windows OS canary denial | BLOCKED; real fixtures/context required |
| Durable remote relay and independent Brain policy host | BLOCKED; approved host/endpoint/pairing absent |
| WhatsApp primary and independent email backup | DISABLED; provider approval/certification absent |
| LLM strategic Brain service | DISABLED; no provider/cost authorization |
| Full DMB certification/development worker with tools | BLOCKED; isolation and bounded development scope not certified |

Temporal-compatible activity boundaries are intake(message ID), execute(task ID,
fence), reconcile(receipt digest), review(scope/result digest) and deliver(event ID).
A Temporal retry must preserve identity/fence and must never re-run an uncertain
started worker. No Temporal deployment or DAT Temporal milestone changes occurred.

Milestone evidence: [operations certificate](evidence/autonomous-operations/CERTIFICATION.json),
[real process workflow](evidence/autonomous-operations/WORKFLOW.json),
[CI166 tests](evidence/autonomous-operations/CI.json), and
[hash manifest](evidence/autonomous-operations/ARTIFACT_MANIFEST.json).
The certified Windows core and107 prior evidence files remain byte-identical.
