# Interim DMB Document Bridge v1

Status: offline implementation; **activation withheld**. No coordination branch,
credential enrollment, service or scheduled task is activated by this change.
The deterministic supervisor is a standalone policy engine, not this ChatGPT
conversation, an LLM, or a source of human approval/hidden conversation context.

## Carrier and document ownership

Proposed repository: `oluadegbu/Codex--DSV-`; compiled mailbox branch:
`coordination/dmb-ddb-v1`. It must be a documents-only tree, initialized only after
approval. Development source goes to its own draft PR stacked on existing draft
PR #1. No updates to main, automatic merges or modifications to PR #1 are needed.

| Path | Single writer | Meaning |
| --- | --- | --- |
| `reports/latest.json` | worker | Latest signed execution/idle report |
| `reports/history/<id>.json` | worker | Immutable reports, including sanitized failures |
| `directives/pending/<id>.json` | supervisor | Immutable, bounded authorized directive |
| `directives/completed/<id>.json` | supervisor | Exact report-bound shadow review, not human approval |
| `state/heartbeat.json` | worker | Liveness only; never task or approval authority |
| `state/events/<role>/<sequence>-<id>.json` | corresponding role | Complete append-only signed sequence/hash chain |
| `state/acks/<id>.json` | worker | Durable receipt, not completion or authorization |

Every document is versioned SHADOW JSON with an ID, per-role monotonic sequence,
previous-document hash, issued/expiry timestamps, human-pinned policy hash,
content hash and Ed25519 signature. Runtime validation enforces exact fields and
compiled payload types; JSON Schemas are in `schemas/ddb/`. No shell, arbitrary
prompt, URL, argv, source path or policy override is accepted from a directive.

The existing worker ID/key ID must match its approved private pairing. Existing
non-admin Windows DirectiveCodex/Medium and DPAPI guards are retained before any
private use; Linux requires non-root. Dedicated document signer public keys are
bound to that worker identity in the human-approved policy. Private signing keys
are separate per role. Workers hold the supervisor PUBLIC key, not its signing
key or Brain HMAC secret. New signer enrollment remains approval gated. Optional
cryptography dependency is pinned to `cryptography==50.0.0`; Windows package
v0.3.0 is not rebuilt/replaced and is not claimed to include the DDB dependency.

GitHub credentials remain distinct from document and worker keys. GitHub writes
alone cannot authenticate a directive. The transport uses HTTPS certificate
verification, rejects redirects, reads only the fixed mailbox branch and writes
only bounded JSON paths. One Git tree/commit publishes the event and all mirrors
atomically; the branch update is fast-forward only. A concurrent sibling update
fails, so the publisher rereads instead of overwriting it. Unknown publication
outcomes retain the exact signed document in the existing SQLite outbox; restart
checks the branch before acknowledging delivery. Three CAS attempts per document,
ten documents per flush, a 60-second network budget per invocation, 32KiB per
document and a 512-file mailbox cap prevent uncontrolled processing. Immutable
blob caching in the existing SQLite store avoids downloading history every poll.
Reaching capacity stops processing; archive/rotation needs reviewed maintenance.

## Runtime and cadence

`dci.master.document_cli` performs **one foreground invocation and exits**. It
installs nothing and contains no indefinite polling loop. An approved scheduler
would invoke controller mode once per minute and worker mode once per five
minutes. Durable due times implement report-watch checks every 180 seconds,
supervisory evaluation every 300 seconds or when the watcher sees a new report,
and worker intake every 300 seconds. There is no catch-up burst after downtime.
Local exclusive file ownership prevents overlapping invocations; SQLite retains
sequence/cadence/audit state. Clock rollback blocks processing.

Manual command shape (not an activation or provisioning procedure):

```
python -m dci.master.document_cli --workspace <reviewed-DCI-root> --configuration <private-config> --approved-policy-sha256 <human-approved-exact-pin> controller
python -m dci.master.document_cli --workspace <reviewed-DCI-root> --configuration <private-config> --approved-policy-sha256 <human-approved-exact-pin> worker
```

The private configuration supplies `policy`, approved `repository`, dedicated
`database`, `document_signing_key_file`, and `github_credential_file`. Worker mode
also needs `backend=paper`, reviewed `workers`, `existing_worker_pairing_file`,
`operations_identity_file`, and `operations_client_database`. The DDB database
must share the private configuration directory. Secret files are current-user
DPAPI blobs on Windows or owner-only files on POSIX, loaded through existing
private-file functions. No credential appears in a command or document. No key
creation, credential enrollment, task registration or service installer is
provided or invoked here.

The initial enabled template is **only existing `shadow_research` for DCI**:
fixed paper fixture, reviewed Git/source hashes, 20-second process budget and
existing resource limits. Human-pinned policy caps a run at 1–10 efforts. A fresh
signed IDLE report permits initial selection; a fresh verified successful report
permits one follow-up while budget remains. One directive may be active at a
time. A policy revision cannot silently extend a live budget.

Worker intake records intent and ACK in existing AtomicPeerStore. The backend
uses existing signed OperationsClient/Operations and ShadowControlPlane; mailbox
latency never carries the runtime's short execution lease. Artifact/receipt/Git
verification happens locally before reporting. The supervisor accepts an
**authenticated worker attestation**, not an independent read of the worker
filesystem. Its completion is bound to the exact report digest. Worker applies
that signed review through existing evidence-bound Operations REVIEW before
executing follow-up. No review is an authenticated human approval.

The implementation is not a general Codex development-task executor. Native
Windows/Codex DDB dispatch stays **disabled** until a reviewed native backend,
its packaged dependency, real signed GitHub handoff and existing native safety
checks are certified. Previous genuine Windows v0.1.3 execution is preserved but
does not certify this new document route. Offline fixture signers do not establish
real identity enrollment. This interim milestone does not solve RDP-independent
Windows activation by implication.

## Failure, policy and human authority

Stable directive/task IDs and durable controller receipts suppress duplicates.
A crash after execution recovers the same sealed completion; it never resets a
lease or re-executes ambiguous effects. Disconnection retains outbox and task
state. Reports are fresh for the pinned 300–900-second maximum; documents expire
within 600–900 seconds. Disconnection beyond expiry blocks rather than silently
refreshing authority. Stale reports, altered audit/streams/mirrors, authentication
failures, rollback and conflicting directives stop progress. Authentication or
semantic failure records durable NEEDS_HUMAN where the audit is intact. An
uncertain effort emits a sanitized failure report, blocks local dispatch and
creates an escalation in the existing durable queue. Notifications remain OFF.
Audit corruption is preserved, not rewritten to clear the gate.

Human policy mechanism: propose the complete versioned policy and any exceptional
template change in a reviewable PR; human approves its exact canonical SHA256,
public signer fingerprints, task budget, expiry and runtime scope through an
independently authenticated operator channel. Operator pins that digest in private
launch configuration/arguments. GitHub document edits, signatures by the ordinary
supervisor and receipt delivery cannot update the pin or approve exceptions.
Policy/signer drift is rejected against durable binding. For a revision, stop and
drain, preserve old branch/journals and review an explicit versioned migration;
there is deliberately no unattended policy-migration/reset command. Exceptional
directives outside the compiled catalog require code review and a new human pin;
they are not executable free text. Do not delete a database to clear a block.

## Certification and activation

`python tools/certify_ddb.py --output <fresh-external-directory>` runs the offline
suite and retains actual Linux paper-process recovery evidence. Tests cover
handoff/review/budget, lost publication ACK, bounded CAS conflicts, disconnection,
deduplication, restart, expired/stale evidence, role signatures, policy pins,
conflicting routes, audit corruption, cadence and exclusive ownership. The real
paper test crashes after a sealed receipt and verifies exactly one execution,
then applies the supervisory review through Operations. GitHub transport/CAS and
outages use a local fault-injected branch; **real GitHub delivery is NOT TESTED**.
No new native Windows certification is claimed.

Minimum scheduler: an already approved non-admin durable scheduler with the two
cadences and exclusive ownership; no such host/scheduler authorization has been
verified for DDB. Existing Temporal may provide this only after endpoint/queue
ownership is verified. The prior Windows Scheduled Task remains REQUEST-0009
WITHHELD and must not be repurposed or activated. Do not use the interactive
Administrator OpenClaw task or DAT/Pulse schedules.

Minimum GitHub authorization: a separately approved repository-selected GitHub
App installation credential (Metadata read, Contents read/write), or equivalently
narrow existing supported credential, with private secure storage/renewal.
Contents write is **repository-scoped, not branch-scoped**: compiled branch checks
are application controls, not a GitHub permission boundary. Existing main
protection/no-bypass guarantees must be independently reviewed before enrollment;
never broaden privileges silently. No Actions/secrets/admin/merge permission is
needed. ChatGPT's connector authorization is not a standalone worker credential.
No new paid subscription, account, public listener or remote relay is required.

Single consolidated activation request: `decisions/REQUEST-0010.md`, retaining
REQUEST-0009. Rollback stops only the approved DDB scheduler/owned invocation,
retains signed documents/SQLite/DPAPI artifacts, and disables the private DDB
credential through the authorized owner if approved. No main merge, production
restart, ACL/firewall/right change or deletion of historical evidence is involved.
