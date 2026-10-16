# Brain–Hands Bridge and Human Escalation Gateway

Mode: SHADOW / NON-TRADING / FAIL-CLOSED. Single-host local prototype.
The existing Solana research core and paper journal are preserved unchanged.

## Components

| Component | Authority and implementation |
| --- | --- |
| Brain tools | Submit fixed tasks, fetch correlated results, PAUSE/RESUME; local MCP stdio prototype |
| Mailbox authority | Dedicated SQLite DB, schema 101, WAL/FULL, atomic BEGIN IMMEDIATE transactions |
| Runner | One-shot simulated scheduling, heartbeat, claim leases, expiry and recovery; non-admin guard |
| Hands | Fixed tests, fixture replay and Codex read-only review templates; shell=False; local artifact/Git evidence |
| HEG | Durable NEEDS_HUMAN queue; simulated WhatsApp and independent simulated email delivery |
| Workflow boundary | Typed Temporal-compatible dispatch/reconcile/notify/read activity contracts; no Temporal deployment |

No mailbox-supplied prompts, command strings, paths, argv, environments or code
are executed. The initial Hands adapter permits verification/review tasks only.
Code-changing Hands jobs require a separately reviewed bounded template and scope;
this implementation deliberately does not accept arbitrary development requests.

## Contracts and ownership

Six versioned JSON Schema contracts live in schemas/bridge. Envelopes carry
message/task/correlation identities, writer, recipient, route sequence, issuance,
expiry and exact payload. Runtime additionally enforces authenticated-process
writer ownership, route, action allowlist, lifecycle, expiry and replay rules.
Schema validation alone is never authorization. Runtime does not require a
third-party JSON Schema package.

Brain is the sole TASK/control ingress writer. Runner owns task state, ACK,
STATUS and RESULT creation. HEG owns simulated decisions and delivery records.
Worker message creation is internal to transition APIs, never arbitrary external
message ingestion. The database provides the atomic mailbox and outbox; no
partial file rename protocol is needed for runtime state. A SHA-256 audit chain
preserves ordered transition/notification evidence.

The local process/account and its reviewed code are the trust boundary. Role
labels are local API authorization, not cryptographic cross-host authentication.
A user with direct DB/code write access can bypass them; this prototype is not a
hostile multi-user security boundary. External deployment requires an authenticated
service boundary, separate process identities/ACLs and a certified identity adapter.
Hash chaining detects accidental corruption; it does not prevent a privileged
attacker rewriting state, hashes or truncating the audit tail.

## Lifecycle and recovery

TASK → QUEUED + ACK → RUNNING → SUCCEEDED/FAILED + RESULT.
Only allowlisted actions with empty parameters can queue. Stable caller task and
correlation IDs make lost tool-response retries idempotent without extending TTL
or changing scope. Distinct message IDs with replayed route sequences, out-of-order
sequences, changed payloads and reused task scopes are rejected atomically.

PAUSE stops new claims; existing bounded work may finish. Task expiry prevents
new execution. Claim lease is 30 seconds; fixed external operations are bounded
at 20 seconds. Finish checks state, attempt fence, lease and task deadline.
A proven pre-start unavailability retries at most three attempts (2/4 second
backoff) then escalates. A started operation with an uncertain outcome is never
automatically retried. Lease expiry/crash puts it in NEEDS_HUMAN with control-plane
degradation classification. A generic approval cannot re-run ambiguous work;
reconciliation is required. No reconciliation bypass is currently implemented.

Synthetic operations have no external effect. Their execution count and result
commit in one transaction, supporting the tested exactly-once synthetic claim.
Exactly-once external Codex effects are not claimed. A crash can leave work
unexecuted/uncertain; safety takes precedence over silently re-running it.

## Human gateway

Requests retain ID, task, scope SHA-256, category, summary, expiry and decision.
Ordinary approval and control-plane degradation are distinct. Degradation starts
with the required banner:

🔴🔴🔴 HUMAN INPUT REQUIRED — CONTROL PLANE DEGRADED 🔴🔴🔴

Simulation tries WhatsApp, then an email adapter directly, with no DSV/OpenClaw
call. Delivery ACK, provider retry and human decision are separate records.
Once one delivery is acknowledged, further simulated deliveries stop. Each
channel permits at most three attempts. Failure preserves NEEDS_HUMAN while
unrelated work proceeds. Expiry becomes HUMAN_TIMEOUT, which cannot execute.

SimulationSession is a test-only authenticated identity model; it is not live
human authentication. Only synthetic-supervisor can decide; requests bind exact
ID/scope/expiry and reject replay. Approval can release only gated_shadow_note;
financial/account/credential/service operations are absent from the allowlist.
Notification delivery never grants approval. External providers are rejected
by the gateway; no credentials have been requested or network sends performed.
Pulse routing and provider receipts require independent certification first.

## Brain interfaces and independent operation

The prototype implements initialize, notifications/initialized, tools/list and
tools/call over local stdio. It proves local Brain→Runner→Hands/result→Brain
correlation, including real standalone subprocess tests. It has not been connected
to a ChatGPT conversation; do not label local tool tests as live ChatGPT delivery.

Official supported candidates, checked 2026-10-11:

- [Codex non-interactive execution](https://developers.openai.com/codex/noninteractive): sandboxed exec and JSONL events.
- [Codex app server](https://developers.openai.com/codex/app-server): supported stdio session/turn interface; not used to bypass CLI startup failures.
- [ChatGPT MCP server](https://developers.openai.com/plugins/build/mcp-server): tools for explicit task submission/result retrieval.
- [ChatGPT MCP Events](https://developers.openai.com/plugins/build/mcp-events): authenticated subscriptions and signed webhook updates are a supported candidate for result notifications; external endpoint/identity/subscription setup and live delivery remain uncertified.

An ordinary chat cannot be assumed to poll files or wake on its own. MCP Events
requires explicit subscription, authenticated endpoint, callback verification and
signed deliveries; it is not enabled here. The operational fallback is an
independent persistent Brain worker: durable plan/episode store, validated
allowlisted task proposals, result cursor/idempotency, bounded reasoning-provider
interface, and HEG on uncertainty. ChatGPT remains strategic reviewer. No paid API,
credentials, provider or Brain service has been activated. The fallback is designed,
not deployed or claimed as a reasoning engine.

Runner recovery and queued synthetic work require only Python and the dedicated
DB. The standalone CLI can run while ChatGPT, OpenClaw and DSV are absent. Continuous
uptime is not claimed: no service, scheduled task or daemon is installed.
