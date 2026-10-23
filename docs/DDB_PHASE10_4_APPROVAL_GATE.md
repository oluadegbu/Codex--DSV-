# Phase 10.4 — native Windows certification decision package

Decision: **GO for owner review of the bounded preparation approvals below;
NO-GO for native Codex execution today.** Offline package review passes. Native
DirectiveCodex isolation/containment and genuine signed Windows handoff are not
certified. All proposed approvals remain WITHHELD. This is documentation only;
no package, worker source, credentials, branch trust or production system changed.

## Immutable package and entry points

Reviewed publication: draft PR#3 commit `9206fc29b3cfda3569b98c70e33357747218a7aa`.
Runtime code commit `f528274914cfe0ccb3743294d29ab6b6bf5e0b9a`; code tree
`c78bcd31b498bdfea9499f688fca08dd6acaa988`. Package source is PR test-merge commit
`c7574b2757b48f5e167ee8135c3c70913f5908b3`, with that same code tree. This is not
an actual merge or approval to merge. Later documentation commits do not rebuild
or replace this pinned binary package.

Package `DMB-DDB-0.4.0-ddb-review1-c7574b2757b4-windows-amd64.zip`,58475044 bytes.
SHA256 `06a5eded7bcfc3ad2cbecf9140e47b88f6a65848c6929847f1de7dd8281791e0`.
DDB_PACKAGE_MANIFEST.json SHA256
`8aa986c9a02f05fe1cd30fb18b957aa4610dd180e3e2866f23241197c33e5b0f`.
[Artifact12498015215](https://github.com/oluadegbu/Codex--DSV-/actions/runs/39944383870/artifacts/12498015215)
was rechecked available/not expired. The Actions outer artifact digest is
`fd8e8d80085ee3ce5116e8f2558f9f4feaff839529440171b94c033464d87e6e`;
it differs from the inner package ZIP digest above. The full per-file manifest,
RELEASE.json and checksums are inside the artifact. Windows CI built the inner
ZIP twice identically. This review rechecks records/metadata, not a new local
binary download or Authenticode signature on the DCI ZIP. The DCI ZIP is hash
verified through authenticated GitHub provenance, not independently Authenticode signed.

Final launcher, after separately approved deployment:
`C:\Users\DirectiveCodex\AppData\Local\Directive\DMB-DDB-cert-0011\package\runtime\python\python.exe`
with `-I`, running `package\app\tools\run_windows_ddb.py`. No new bridge EXE or
Git/Python installation is needed. Bundled dependencies: CPython3.12.10,
MinGit2.51.0.windows.1, cryptography46.0.2, cffi2.0.0 and pycparser2.23. Runtime
comes from pinned baseline ZIP SHA256
`38b395f3609900d1c5423fc9ed4f02413397db8728c2c27d66ae576308ead5f6`.
The existing official native executable is
`C:\Users\DirectiveCodex\AppData\Local\Programs\OpenAI\Codex\bin\codex.exe`,
v0.162.1 SHA256 `dd13bdb162a184fa04039488b234a8258ef9b76f84e926c505d5742b19249a6a`.
It is not bundled or reinstalled. Native Windows final-path/file-identity locks,
official hash/version and suspended process image are checked before execution.

Only host WIN-HQAAFGGU1AM, account DirectiveCodex, SID
S-1-5-21-3675741470-1525898003-3877381073-1000, non-admin Medium token, no thread
impersonation. No Administrator/SYSTEM worker or session injection. Keep inherited
supported authentication/proxy/CA context; reject alternate CODEX_HOME outside
`C:\Users\DirectiveCodex\.codex`. Exact non-secret runtime endpoint/hook/MCP
configuration remains a narrow preflight item, not permission to inspect secrets.

## What CI established and skipped

Linux workflow39944383888 passed238 tests with one skip, including the previously
locally blocked loopback test;100 verifier cycles/1099 worker checks retained.
Windows workflow39944383870 passed42 of44 tests, with two explicit skips:

| Skipped test | Reason | Consequence |
|---|---|---|
| `DDBTests.test_real_paper_artifact_and_crash_after_execution_recover_once` | Existing worker is Linux-only | Linux real paper recovery remains tested on Linux; this is not native Windows recovery evidence. |
| `NativeCanaryDenialTests.test_existing_reviewed_canary_denial` | CI lacks approved non-admin DirectiveCodex token/explicit canary authority | No OS access-denial or production filesystem isolation claim. Must run under the separately approved target token with existing harmless canaries. |

Native Windows protocol/controlled Python subprocess fixtures are genuine Windows
CI tests but are not Codex, Job Object containment or target-account certification.
Legacy package workflow39944383893 also passes. No tests need repeating merely
because this document changed; package/code changes would require targeted regression.

## Trust, policy and authority boundaries

Proposed carrier: exactly `oluadegbu/Codex--DSV-`, branch
`coordination/dmb-ddb-windows-0011`, initialized once with an empty documents-only
root. Worker has no branch-creation route; fixed transport only CAS-publishes
compiled JSON paths under reports/,directives/,state/. Single-writer signed role
ownership, immutable IDs, sequence/previous hashes, expiry, bounded retry and
no-force publication remain unchanged. Keep original `coordination/dmb-ddb-v1`,
its signed failure, ACK, policy history and Linux INTENT/quarantine intact. No
history import, forced reset, policy renewal or replay into the Windows stream.

Dedicated supervisor and worker Ed25519 role keys, worker_id
`windows_codex_ddb_0011`, worker_key_id `ddb-windows-0011`. Current-user DPAPI
protects Windows config/signing/credential files inside the new root's state/.
No new keys or tokens have been enrolled. Same-account DPAPI separates storage
from other accounts, not hostile processes using the same account. Two keys in
one account provide protocol role separation, not independent security principals.
An independently hosted supervisor would need its own exact deployment review;
this package does not assume a continuously running ChatGPT conversation.

Proposed policy: version1,mode SHADOW,policy_id `ddb-windows-0011-foreground`,
template `codex_shadow_review_v1`,max_tasks1,report_max_age600,document_ttl900,
expiry60 minutes from verified approved start. Actual public key fingerprints,
canonical signed policy hash and absolute validity timestamps are unavailable
until enrollment is separately approved. They must be reviewed before the execution
row below becomes executable; no placeholder is valid authority.

Repository credential minimum: Metadata read,Contents read/write, this repository
only. No admin,Actions,secrets,merge or bypass permission. Prefer a dedicated
existing approved GitHub App installation credential with at most60-minute
lifetime. Availability is not assumed; no new App/account or credential is created.
If the provider cannot support the reviewed owner/scope/TTL, remain BLOCKED and
review that exact deviation. A repository-scoped token can potentially write
other branches outside this program. Compiled branch enforcement is not server-side
permission scoping or proof of main protection. Never transfer cloud/DAT/DPM/Pulse
credentials. Revocation is explicit provider-side invalidation by the authorized
owner; notification delivery or simulated acknowledgement cannot grant authority.

Controller root: new package\app only. Worker root: new worker-clone only.
Source context: pinned src/dci/models.py and src/dci/scoring.py, each at most64KiB.
No caller-selected workspace, prompt, arbitrary shell, external tool, MCP, web
search, signing, orders or funds. Private files: state/worker.dpapi,
controller.dpapi,worker-signing.dpapi,controller-signing.dpapi,github.dpapi;
separate worker/controller SQLite journals and locks. Outputs: artifacts/ddb-native/
<immutable-task-id>/{stdout.log,stderr.log,review.json}; one fresh foreground
certification output directory. Raw model/stdout/stderr and credentials remain
private; signed GitHub reports carry sanitized status/digests, not raw model text.

DAT,DPM,DSV,OpenClaw,Pulse and all production/trading paths, credentials, controls,
schedules and services are explicitly out of scope. No direct negative test may
open their content. App-server read-only/no-network/never-approve policy is verified;
client tool-event rejection is reactive and not proof of no prior tool effect.
Startup hooks/config and same-account credential authority remain limitations.
OS access denial is therefore a mandatory native gate, not an offline PASS.

## Approval matrix — proposed, not granted

Each new grant must name its approver, verified start and absolute expiry in its
approval record. Below are proposed maximum windows; elapsed time is never consent.
No grant renews automatically or implies any other row.

| ID / decision | Exact scope and permissions | Proposed expiry / budget | Rollback or revocation |
|---|---|---|---|
| A0 Offline review | Current authorized documentation, code review and offline fixtures; no host action | This bounded effort; no persistent authority | Preserve committed review/evidence. |
| A1 Branch creation | Once, empty coordination/dmb-ddb-windows-0011 in this repo; no main/old-stream change | Creation action within60 minutes of approval; branch existence grants no execution | Disable new dispatch; retain immutable history rather than delete/reset. |
| A2 Enrollment | Two dedicated role signers and one repository-only credential; DPAPI under approved account; publish public fingerprints only | Enrollment within60 minutes of approval; execution policy/credential at most60 minutes from verified test start | Stop dispatch; expire policy; owner revokes only dedicated credential. Preserve encrypted files/audit; no production rotation. |
| A3 Deployment/preflight without Codex | Verify exact ZIP/manifest, unpack once to the new root, prepare clean pinned clone; inspect token and own permissions; existing approved canary OPEN_EXISTING tests only | One foreground preparation session, at most30 minutes; no Codex subprocess, service or ACL change | Stop preparation and retain complete new root; no overwrites or old-state deletion. |
| A4 One native DDB research attempt | One fixed read-only task; signed GitHub handoff; actual package/source/policy hash, signer fingerprints and exact service destinations must be attached | Policy window60 minutes; foreground420 seconds; native20 seconds,CPU10 seconds,job256MiB/eight processes; no model/capacity retry | STOP/drain owned job only; retain INTENT if uncertain, signed failure and audit; no budget reset or rerun. |
| A5 Extra native fixture tests | Separate exact fixture list required for Win32 Job startup/crash/timeout and actual turn cancellation; no arbitrary executable/shell | No grant proposed for unnamed fixtures. Owner must approve explicit invocation count, deadline and whether any additional model turn is allowed | Terminate only fixture-owned Job/handles; retain fixture journals; no effect on the one research-task namespace. |
| A6 Unattended scheduling | WITHHELD REQUEST-0009; no task/service/batch-right changes | No lifetime or activation permission | Nothing installed/enabled; separate final review required. |

A3 may be approved without A2/A4 so account/canary isolation is checked before new
DDB credentials or a model turn. A1/A2/A3 preparation approval does not imply A4.
A4 cannot be approved against missing policy/source-clone pins or unknown endpoints.
These are exact bounded inputs to capture during preparation, not a request for
broad infrastructure discovery. A5 is deliberately separate: a single successful
research turn cannot simultaneously prove interruption of another native turn.

## Native evidence sequence and stop rules (NOT EXECUTED)

| Order | No Codex launch? | Required evidence and acceptance |
|---|---|---|
| 1 Package/token/preflight | Yes | ZIP/manifest and file inventory, Python signature, official executable hash, effective SID/groups/integrity, no impersonation; identity mismatch stops before auth/child use. |
| 2 Filesystem gate | Yes | Own workspace positive read/write and independently proven existing harmless read/write canaries; exact approved manifest digest. Only WinError5 passes. Missing/unknown is BLOCKED; unexpected access is FAIL and stop. No production probes. |
| 3 Signed carrier negatives | Yes | Real scoped repository read/write after A1/A2, exact branch, signed role/policy/ID/sequence/expiry validation; tampered, stale, duplicate and wrong-workspace fixtures rejected before native dispatch. Preserve CAS/audit. |
| 4 Genuine DDB research | No — A4 | Native process identity/image/job evidence, fixed source/prompt digest, completion/artifact/source unchanged; durable INTENT→SEALED, signed report/ACK/GitHub readback, independent supervisor review to REVIEWED; exactly one native execution. |
| 5 Receipt recovery | No additional model launch | Reopen SEALED/REVIEWED store, recover lost publication and replay with zero extra execution; hash-chain audit valid; INTENT-only state remains quarantined. Controlled crash fixtures use separate journals. |
| 6 Native containment/cancel/timeout | A5 only | Job-owned process count returns zero; timeout evidence and, if separately authorized, actual turn/interrupt ACK plus interrupted terminal status. Python fixtures/process startup alone cannot pass actual Codex turn cancellation. |
| 7 Production preservation | Yes | Only owned-root/process/GitHub mutations in audit; compare approved pre/post metadata/hashes without reading production contents, changing controls or claiming exhaustive host proof. Any unexpected mutation stops and escalates. |

Driver command shape remains in DDB_WINDOWS_ADAPTER_CERTIFICATION.md. It is not
runnable approval until the above concrete pins and A4 grant exist. There is no
unattended invocation, automatic renewal or model fallback. Remote ChatGPT does
not self-wake; foreground controller role and any future persistent Brain service
have distinct authority.

## Fail-closed recovery and decision

Before launch, invalid policy/expiry/token/package/route yields BLOCKED. After an
uncertain start, keep durable INTENT and worker/controller quarantine; publish
sanitized NEEDS_HUMAN when safe. Never treat receipt delivery as approval. Recover
only a verified SEALED receipt without re-executing; a changed artifact/source or
scope stays blocked. Revocation/expiry prevents dispatch; an active job is stopped
only through its owned drain path, not by killing unrelated processes.

Rollback is preservation-first: set STOP in the new state root, drain the owned
job and verify zero active children, retain all logs/journals/keys/evidence and new
branch history. STOP can prevent subsequent receipt verification; removing it and
resuming review is an explicit evidence-based recovery action, never permission to
rerun an INTENT. Revoke only the dedicated provider credential through its owner.
Do not delete installations, clear counters, alter old pairing, merge PRs or modify
DAT/DPM/DSV/Pulse/OpenClaw/production schedules or security settings.

**Recommendation:** GO for evaluating A1/A2/A3 preparation; NO-GO for A4/A5 until
actual fingerprints/policy/pins/endpoints and native isolation evidence are reviewed.
A6 remains withheld. Native certification is NOT TESTED. Passing CI/package checks
are sufficient for this review package, not production readiness.
