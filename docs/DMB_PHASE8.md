# DMB Phase 8 — external integration assessment

Outcome: **DMB LOCAL SHADOW PASS / FULL CERTIFICATION BLOCKED**.
User-facing assessment date: October 11, 2026, America/New_York. Machine evidence
uses UTC capture times. Original DMB evidence and Git bundle remain unchanged.

## Baseline and provenance

Baseline HEAD `2adcf00c3d8ed991eaf16668762a97f78355c2e3`; certified implementation
`a3d85e45de16231e7cfcea092abbe21c6dcc0a1b`. All 35 recorded source hashes match
both that commit and current files. Three lab Git heads/bundle hashes verify.
The original 84 tests, 100 actual verifier cycles and 1,099 worker test executions
retain their exact historical evidence. Phase 8 adds 16 offline contract tests;
all 100 regression tests pass. Previous certificate files are not rewritten.
Original BUILD_STATE bytes are retained before the milestone update.

[Baseline hashes](evidence/phase8/BASELINE.json),
[current test log](evidence/phase8/TESTS.log),
[local resilience](evidence/phase8/LOCAL_RESILIENCE.json),
[complete certification matrix](evidence/phase8/CERTIFICATION_MATRIX.json) and
[artifact hash manifest](evidence/phase8/ARTIFACT_MANIFEST.json).

## GitHub diagnosis and minimum human action

The connected identity is `oluadegbu`; repository ID is `1409360122` and the
verified repository is `oluadegbu/Codex--DSV-`, default branch `main`. Metadata
reports user push permission. README read succeeds. ChatGPT's GitHub action
setting is already permissive, but collaborator-permission lookup and fresh
branch creation both return integration HTTP403. Installation scope/permissions
and response headers are not exposed by the available connector; they are
**NOT TESTED**, not assumed. Empty inventory does not prove repository absence.
See [diagnosis](evidence/phase8/GITHUB_AUTHORIZATION.json).

**HUMAN REQUIRED:** inspect the existing ChatGPT/Codex GitHub App installation in
GitHub settings. Confirm this exact repository is selected and Contents is
read/write; approve an outstanding permission update or reauthorize the existing
connection if needed. Keep other repository and organization grants unchanged.
If the app cannot support writes, provide a supported already-authorized write
runtime for this repository. No tokens, administrator access or all-repository
grant is requested. Do not change the already permissive ChatGPT action setting.
This is a minimum action conditional on the installation review, not a claim
that an unseen installation setting was diagnosed precisely.

GitHub documents this error as insufficient integration authorization and the
ref creation endpoint requires Contents write. Sources:
[REST troubleshooting](https://docs.github.com/en/rest/using-the-rest-api/troubleshooting-the-rest-api#resource-not-accessible),
[create reference](https://docs.github.com/en/rest/git/refs#create-a-reference).
No branch was created and no successful publication/read-back is claimed.

## Worker invocation and isolation

[Codex invocation](evidence/phase8/CODEX_INVOCATION.json) records an actual
supported `codex exec --sandbox read-only --json --ephemeral` attempt, fixed
no-tools prompt, 15-second timeout, Git evidence and raw-log hashes. CLI version
is 0.159.0-alpha.3; normal login status says ChatGPT, but exact account mapping is
unverified. Startup fails on read-only runtime storage before any completed turn.
No runtime/authentication relocation or sandbox bypass was attempted. Actual
Codex retries, cancellation and sandbox denial remain NOT TESTED.

Fresh [Windows identity](evidence/phase8/RUNTIME_IDENTITY.json) remains
Administrator, enabled Administrators membership and High integrity. The stated
Windows README read returns EPERM from Desktop Commander resolution. Development
and Codex execution were not run through that privileged identity. The tool's
EPERM is not evidence of a non-admin OS sandbox.

The [negative isolation probe](evidence/phase8/ISOLATION_PROBE.json) uses only a
synthetic canary in two distinct temporary roots under uid1000. A neighboring
read succeeds. Consequently, path separation is VERIFIED locally while OS
access-denial isolation is BLOCKED. Do not generalize the outer managed sandbox
or Desktop Commander path policy to isolation between workers.

**HUMAN REQUIRED:** provide an existing supported non-admin DirectiveCodex
connection with accessible DCI workspace and normally configured Codex runtime
storage. Provide independently enforced worker boundaries and authorize exact
synthetic cross-boundary read/write probes. No account/service installation,
privilege inheritance or permissions relaxation has been performed.

## External project reconciliation

[Assessment ledger](../portfolio/RECONCILIATION.phase8.v1.json) keeps the original
registry pinned. DCI/BHB/HEG/DMB are verified in their scoped local capabilities;
external activation/publication is blocked. DSV, Pulse, actual DAT Futures/MT5,
DPM, Temporal deployment and VMA/DAR remain UNKNOWN because no authorized exact
artifact locations were available. Synthetic DAT/DPM labs are historical lab
evidence, never evidence of their actual repositories. The user's DAT Temporal
Integration approval is HISTORICAL; its unchanged interfaces are VERIFIED LOCAL,
and its implementation/deployment remains UNKNOWN. No inferred paths, secrets
or production service stores were inspected.

## Supported Brain path and authenticated shadow contract

The documented remote path is Streamable HTTP MCP with server-side authorization
and OAuth 2.1 user identity; MCP Events supplies subscription callbacks signed
using Standard Webhooks. No DCI remote endpoint, OAuth issuer/audience or active
subscription is available, so real inbox/outbox delivery is BLOCKED/NOT TESTED.
An ordinary conversation is not assumed to poll files, self-wake or host a service.
Sources: [MCP server](https://developers.openai.com/plugins/build/mcp-server),
[authentication](https://developers.openai.com/plugins/build/auth),
[MCP Events](https://developers.openai.com/plugins/build/mcp-events).

`event_contract.py` is a **local, ephemeral synthetic contract lab**, not OAuth,
a network server, a provider adapter or remote identity certification. It models
signed result/notification events, durable receipts/outbox, immutable public
subscription scope, exact event bytes, fresh signatures on retry, bounded attempts
and nonretryable failures. It reuses the existing BridgeStore/audit authority in
isolated test databases. Keys are generated in memory for tests, hidden from
representations and never placed in SQLite or Git. Sender/recipient principals
must be explicitly synthetic. JSON text is data; no commands or approvals execute.

The v1 HMAC formula is checked against an independent computation of the public
[Standard Webhooks specification](https://github.com/standard-webhooks/standard-webhooks/blob/main/spec/standard-webhooks.md).
This proves the local formula/contract, not external endpoint interoperability.
No production certificate, subscription secret, wallet key or credential is used.

A local HTTP status supplied by a fixture does not prove real delivery. Unknown
started-delivery outcome is quarantined rather than blindly retried. Missing live
OAuth, client identity and callback ownership must be certified before activation.
Persistent endpoint/service deployment still requires explicit installation scope.

## HEG and resilience

Authenticated synthetic signatures do not authenticate a real supervisor. A
`ShadowReceipt` cannot pass the existing HEG approval interface; successful
receipt/HTTP acknowledgement leaves the task blocked. Separate ephemeral channel
keys and queues model WhatsApp failure/email fallback. Gmail discovery identifies
an available unconnected plugin; no installation, provider activation or message
was sent. WhatsApp/Pulse's actual route remains uncertified. Provider, destination,
consent and identity approvals are still required before a real shadow test.

Phase 8 checks actual independent process restart, a newly launched synthetic
child SIGKILL, preserved uncertain-task locks/reservations, audit and unrelated
safe continuation. The combined absent-control-plane fixture passes with minimal
environment and no DSV/OpenClaw/ChatGPT connections. Actual outages of connected
production services and live ChatGPT delivery are NOT TESTED: none were interrupted.
Temporal-compatible contracts and the separate DAT milestone are preserved.

No production trading/control changes, broker orders, wallet/fund actions,
elevation, paid services, credential exposure or persistent service installation
occurred. Remaining approvals are recorded in REQUEST-0002 through REQUEST-0006.
Next safe work: offline OAuth/subscription validation fixtures, explicit shadow
reconciliation contracts, and read-only review of exact authorized project evidence.
