# Supervisor policy

## Authority

The TRAD Research / Crypto supervisor owns architecture and strategy decisions.
The implementation worker can design within the approved pipeline, implement,
refactor, test, simulate, document, record decisions and commit/push safe work.
DSV/OpenClaw is an optional operator control plane. Temporal is the intended
durable orchestration layer. Neither belongs in the latency-sensitive data path.

## Hard gates

Separate explicit authorization is required before requesting/using/storing
private keys or seed phrases, production wallet signing, transferring real funds,
live trading, materially raising financial risk limits, destructive or
security-sensitive VPS changes, paid service purchases or DAT/DPM credential
reuse. DCI has no authorized live execution pathway. Fail closed on uncertainty.

## Decisions

Create decisions/REQUEST-<id>.md with CONTEXT, EVIDENCE, OPTIONS, RECOMMENDATION,
IMPACT, BLOCKING: YES/NO, HARD_GATE: YES/NO. Record status and response evidence;
never infer supervisor approval. Requests are durable files, not automatic
messages to the supervisor conversation. Continue unrelated safe development.

## Research discipline

Initial weights are hypotheses. Changing production strategy or promoting paper
results requires supervisor review. Preserve point-in-time inputs, versions,
provenance and observed outcomes. Include failed/dead tokens and unsuccessful
wallets to address survivorship bias. Separate training, validation and holdout
periods; model latency, fees, liquidity and adverse fills. Synthetic fixture gains
are plumbing checks only. Unknown safety or linkage evidence is not positive
safety or independent convergence evidence.

## Isolation and runtime

Use a dedicated runtime identity, database, configuration namespace and storage.
Only public/read-only adapters are currently allowed. Never share DAT/DPM secrets,
execution processes or service credentials. A future standalone worker must use
Temporal retry/idempotency policies, checkpoints and health reporting; operator
AI availability must not affect ingestion or paper state recovery.

## Directive Master Brain

The central strategic interface coordinates project registries and bounded
shadow workers. It cannot extend production authority across projects. Unknown
project history remains unverified. Shared infrastructure, deployment, privilege
and activation paths are serialized and approval gated; current implementations
are inert simulations. Simulated identities/delivery cannot authenticate or
authorize live actions. Only authenticated approval-gated requests, material
novel faults and unrecoverable failures belong in the escalation queue. Routine
safe work proceeds autonomously. No external notification is activated yet.
