# DDB Phase 2 controlled foreground readiness

**BLOCKED — HUMAN AUTHORIZATION REQUIRED.** Option 1 authorization is recorded
for preparation and bounded, non-persistent certification only. Unattended
activation and REQUEST-0009 remain WITHHELD. No genuine Codex document cycle has
been completed, and paper results do not satisfy this certification.

| Gate | Result | Exact evidence / limit |
| --- | --- | --- |
| Existing cloud execution identity | PASS | Linux UID/GID1000, non-root, no group0; dedicated reviewed development workspace |
| Native CLI availability/authentication | PASS readiness only | `/opt/codex/bin/codex`, codex-cli0.159.0-alpha.3; supported `login status` reports ChatGPT authentication. No model task launched. |
| Binary pin | PASS observed | SHA256 `981ade7b03926534c654fd718ced3a9f378b7b2841271e29156f939462d176e9`, uid65534/mode0755, not writable by worker; distinct from Windows v0.162.1. |
| Windows executor | BLOCKED for worker launch | Existing connected executor is WIN-HQAAFGGU1AM\Administrator. No run-as, elevation or injection attempted. Existing DirectiveCodex evidence preserved. |
| Interactive GitHub connector | PASS scoped observation | Selected installation170722492 includes oluadegbu/Codex--DSV-. Connector can publish/read preparation documents. User permission projection is not proof of standalone App token scope. |
| Documents-only branch | PASS preparation | `coordination/dmb-ddb-v1`, commit `e25c4a5b135ad98ca15045acc7b832beb7bf3328`; exactly two JSON files, both the same signed BLOCKED heartbeat. Zero directives or executions. |
| Readback signature/hash/sequence | PASS preparation | Real GitHub blob readback verified against proposed public key/policy and expected sequence1. Connector-backed preparation is not worker authentication certification. |
| Dedicated signer preparation | PASS local ownership | Separate Ed25519 role keys, private root0700, files0600, UID1000, outside Git; public fingerprints/policy in PROPOSED_POLICY.json. No external credential enrollment or security-policy change. |
| Native foreground backend | IMPLEMENTED / NOT TESTED natively | One fixed DCI read-only review through official `codex exec`; actual child UID check, executable/version/Git pins,20s/10CPU seconds/1MiB file bounds, durable INTENT/SEALED/REVIEWED and no uncertain-effect retry. Not Windows certification. |
| Existing worker GitHub authentication | BLOCKED | Official gh auth status reports invalid token/account failure; managed runtime revision227 has no ready GitHub secret/outbound identity. No token value read, printed, exported or replaced. |
| Authenticated native GitHub intake/publication | NOT TESTED | No valid standalone credential; native launch is gated behind real signed publication and re-read with the worker's own selected authentication. |
| Genuine task/completion/replay/restart cycle | NOT TESTED | No native task dispatched. Local boundary tests/paper recovery are not substitutes. |
| Unattended scheduling | WITHHELD | No scheduler/service/task installed or activated; no batch-logon or security changes. |

## Prepared path

`NativeForegroundBackend` reuses the existing fixed Hands review prompt, existing
AtomicPeerStore and DDB signed document path. It only reviews public DCI models
and scoring code in a separate clean pinned clone. Mailbox text never becomes a
prompt, executable, path or argv. New template `codex_shadow_review_v1` permits
exactly one effort. Paper and native receipt kinds cannot be substituted; DMB
rejects a paper receipt under a native policy. Native intent without a sealed
receipt remains uncertain and is never rerun. An explicit `--foreground-certification` switch permits bounded manual handoff
steps without five-minute waits, only under the exact one-effort native policy;
it grants no additional task or scheduling authority. GitHub CLI transport uses official
`gh api` authentication without extracting its token; it is explicitly selected,
not a fallback after another credential fails. Windows native DDB remains disabled.

Prepared private worker and supervisor configurations are retained in the current
cloud workspace, outside Git, with the proposed policy and dedicated clone.
They have not been invoked. No private paths, keys, token values or raw logs are
needed from the operator. The native worker must prove signed branch publication
and re-read before launching Codex; this credential gate is not bypassed with
interactive connector operations or a paper worker.

Only a signed BLOCKED heartbeat has been published. Its expiry is liveness, not
execution authority; authenticated historical heartbeats may advance a cursor
without creating work. Expired reports/directives still block dispatch. Candidate
policy validity is finite; expiry never authorizes silent renewal, source reset,
re-pairing or historical rewriting. If it expires before access is repaired,
prepare a reviewed fresh policy/migration while preserving this attempt.

## One consolidated operator requirement

Repair or attach **standalone runtime GitHub authentication for the existing
non-root cloud foreground executor**, using an approved repository-selected
GitHub App credential or equivalent supported binding for only
`oluadegbu/Codex--DSV-`: Metadata read and Contents read/write. Deliver it through
the platform's protected runtime binding or supported official CLI authentication
mechanism; never paste a token into chat. The existing interactive connector
cannot be exported or assumed to authenticate `gh api`/the worker. No new account,
paid infrastructure, Administrator/Windows access or production credential is
required. No credential change has been attempted by this worker.

This is a specific credential/access gate under the user's explicit instruction
to stop if enrollment needs credential approval. It is not a renewed request for
routine implementation, and it does not authorize a scheduler. Proposed policy
hash and signer fingerprints are retained in
`docs/evidence/ddb-phase2/PROPOSED_POLICY.json` for exact review. Repository-wide
Contents write is the GitHub permission minimum; compiled branch checks do not
claim server-side branch-scoped authorization. Review existing main protection
without broadening App privileges or changing it under this phase.

After access is available: verify actual credential ownership/expiry/scope and
source pins, then perform one signed native handoff, verify sealed artifact and
DMB review, recover a lost publication/restart without another execution, and
check replay/stale/altered messages fail closed. Only genuine receipts may change
this report to FOREGROUND CERTIFIED. Scheduling review comes after that success.

## Verified rollback state

There is no running native task, scheduler, service, enrollment or production
change to undo. Leave the branch's immutable signed BLOCKED heartbeat and private
preparation journals/key files intact. Never force-reset branch history or delete
an uncertain journal. Stop only a newly owned foreground invocation if one is
subsequently approved and started. Existing keys/accounts, Windows installations,
PR#1/main, DAT/DPM/Pulse/DSV/OpenClaw and their schedules remain unchanged. Revocation
of a future dedicated runtime credential belongs to its authorized owner and
needs that credential's approved lifecycle, not production secret changes.

## Network/auth correction and resumed pre-dispatch state

This section supersedes the earlier credential-failure diagnosis. The explicitly
approved non-root diagnostic reached the repository API and received **HTTP200**
using existing authentication. Evidence:
`docs/evidence/ddb-network-auth/READ_ONLY_DIAGNOSTIC.json`. The real standalone
worker subsequently published its signed admission, idle report and heartbeat;
its durable outbox contains the GitHub commit receipts. No credential was changed,
exported, enrolled or rotated. Absence of a managed secret listing did not establish
absence of working SDK authentication. The earlier gh status output was not a
conclusive invalid-token result while execution-network access was blocked.

On resume, all four neutral documents were published, with zero directives,
zero native intents and no supervisor dispatch. The previous policy had expired.
An explicit pre-dispatch migration keeps its old signed documents, policy keys,
sequence numbers and audit; only expiry changes. It rejects any native intent,
job/plan, pending unknown publication or expanded task/signer authority. Retired
neutral history grants no work. Two targeted tests verify retention and refusal
when an execution intent exists;21 DDB boundary tests pass. This is not a reset
or an automatic renewal after task execution.

The resumed foreground network-permission request was aborted by the platform
interaction before an execution result. Journal inspection confirms that no new
messages or native task started. **One remaining human action:** approve the
platform's temporary network permission for the bounded foreground worker and
controller invocations. The earlier read-only diagnostic permission does not
bypass permission review for these different commands. No credential replacement,
Administrator access, security change, paid infrastructure or unattended schedule
is requested. Full native handoff/restart/replay certification remains NOT TESTED.

Current durable status: `docs/evidence/ddb-network-auth/STATUS.json`.
