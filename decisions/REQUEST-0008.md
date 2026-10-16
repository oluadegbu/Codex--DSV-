# REQUEST-0008 — One consolidated unattended shadow deployment gate

CONTEXT

The actual Windows0.1.3 foreground workflow passed under DirectiveCodex/Medium.
The operations implementation and local signed workflow are reviewable in
`docs/DMB_AUTONOMOUS_OPERATIONS.md`. No persistent startup or external relay is
installed. The current remote executor is Administrator/High and cannot launch
workers. The managed development environment has no durable host identity,
provider credentials or approved relay endpoint.

EVIDENCE

- docs/evidence/windows-genuine-completion/CERTIFICATION.json: real task/turn/PID,
  identity, exact artifact, one durable execution, audit and restart suppression.
- docs/evidence/autonomous-operations/: actual signed local process workflow,
  source hashes, tests and limitations (added at milestone completion).
- Existing certified bridge code/fingerprint and all0.1.x state remain unchanged.
- User directive explicitly forbids persistent services/scheduled tasks, ACL or
  firewall changes and costs without approval. Conversational/cloud execution
  does not establish RDP-independent or reboot-safe Windows operation.

OPTIONS

1. Approve one dedicated least-privilege Task Scheduler startup entry under the
   existing DirectiveCodex identity (RunLevel LeastPrivilege, never Administrator),
   configured to run without an interactive/RDP session, plus deployment to an
   existing approved durable controller/Brain host and HTTPS relay reachable by
   outbound requests only. Identify that existing host and relay endpoint; none
   is currently configured. No new account, public listener, paid service,
   production workspace, ACL/firewall change or notification activation included.
2. Keep foreground/manual startup. This preserves the baseline but cannot meet
   unattended, disconnect/logoff/reboot recovery acceptance.

RECOMMENDATION

Option1, limited initially to a one-hour shadow acceptance window and the compiled
connectivity task; the approved supervisor may restart only its owned process with
bounded retries. Deploy side by side; retain all existing keys/journals/receipts.
Any required Windows batch-logon right, credential-handling change or privilege
requirement discovered during setup remains separately blocked; do not grant it
implicitly. Passwords, if Windows requires them, are entered locally through the
supported OS interface and never sent to ChatGPT/Codex or stored in the repository.

Prepare approved harmless other-account canary fixtures under an existing account's
new non-production `AppData/Local/Directive/DMB-Isolation-Canary-v1/fixtures/v1`
directory using existing inherited permissions only. Record independent creation,
existence and fixed content hashes; do not change ACLs or production directories.
The supervised acceptance run automatically dispatches a real task, requests Codex
cancellation, kills only its owned test-worker process for crash recovery, checks
quarantine/no duplicate effects, and verifies read/write denial. No test outcome is
inferred before that actual run.

IMPACT

This is the sole requested deployment approval/action: approve the above bounded
startup and host deployment, and identify the existing approved durable host/relay.
It does not approve live trading, development tool access, credentials changes,
new identity, elevation, production access, paid API/model service, WhatsApp/email,
ACL/firewall modifications, a public listener or broader risk limits. Brain, worker
and relay keys must be distinct and privately paired/DPAPI protected. Provider
channels stay disabled until their own explicit approval and delivery certification.
If no suitable host/relay exists, report that access boundary; do not purchase one.

BLOCKING: YES
HARD_GATE: YES

Status: ARCHITECTURE APPROVED by the operator in Phase10, subject to FINAL CONFIGURATION REVIEW. Installation/activation NOT APPROVED. Exact review and remaining gates: REQUEST-0009.
Independent safe development and CI may continue; deployment remains disabled.
