# Windows DDB foreground certification — readiness review

Status: BLOCKED — exact runnable Windows DDB release is not yet available; no execution or enrollment approval requested against an incomplete package. Phase A read-only assessment is complete to the available executor boundary. Phase B has not started. REQUEST-0011 remains pending; REQUEST-0009 remains withheld.

## Verified host and package inspection

Read-only Desktop Commander inspection on October 20, 2026 reached device WIN-HQAAFGGU1AM. DirectiveCodex is enabled, SID S-1-5-21-3675741470-1525898003-3877381073-1000, and not a direct local Administrators member. Its RDP session 3 is disconnected. Observer runs as WIN-HQAAFGGU1AM\Administrator; this is not the worker identity and does not prove the current DirectiveCodex token or effective group membership. No impersonation, token duplication, RunAs, session injection or worker launch was attempted. The initial quoted observer command failed PowerShell parsing; the corrected encoded read-only command exited 0. Neither launched Codex. Observer integrity was not measured.

Official existing executable `C:\Users\DirectiveCodex\AppData\Local\Programs\OpenAI\Codex\bin\codex.exe` exists and hashes to `dd13bdb162a184fa04039488b234a8258ef9b76f84e926c505d5742b19249a6a`, matching pinned v0.162.1. No version/authentication subprocess was launched under Administrator. Historical non-admin Medium genuine receipt remains valid within its original scope.

Parent `C:\Users\DirectiveCodex\AppData\Local\Directive` exists. Its observed ACL grants inherited FullControl to DirectiveCodex, Administrators and SYSTEM; no ACL was changed. This establishes a relevant ACL grant, not a successful current-account write or cross-workspace denial. Proposed new root `C:\Users\DirectiveCodex\AppData\Local\Directive\DMB-DDB-cert-0011` does not exist and was not created by the Administrator observer.

REQUEST-0011 contained an architecture decision, not an executable deployment/enrollment package. Inspection confirms `document_native.py` explicitly rejects Windows and uses POSIX resource limits, /proc ownership and process groups. Existing `document_cli.py` selects that Linux backend; its current credential/signing loader is not a reviewed Windows DPAPI enrollment path. Therefore invoking it on Windows is prohibited, and historical v0.3.0 lifecycle packaging must not be advertised as Windows DDB-ready. Existing packaging already bundles Python, Git and cryptography dependencies; reuse that build approach rather than requiring manual dependency installation.

## Exact proposed boundaries (not activation authority)

Review manifest: `deployment/ddb/windows-request-0011/PACKAGE_REVIEW.json`. Only the fresh root above may receive a new release, controller/worker state, owner-protected DPAPI blobs and evidence after explicit package approval. Separate child directories: `package`, `worker-clone`, `state`, `artifacts`, `fixtures`. Worker review input is only pinned `src/dci/models.py` and `src/dci/scoring.py`; no document-supplied prompt/shell command. All creation must occur as DirectiveCodex, never through the Administrator observer. Require native account SID, non-admin membership, Medium token and no impersonation at every launch.

No DAT/DPM/DSV/OpenClaw/Pulse paths or service names are configured in the proposed manifest. This is configuration separation, not proof that all production paths are inaccessible. Do not enumerate or probe production contents. Use only pre-existing approved harmless canaries for negative read/write tests. Do not create users or change ACLs to manufacture a passing result. Missing safe denial targets are BLOCKED.

Network proposal: repository-scoped REST at https://api.github.com/repos/oluadegbu/Codex--DSV- and compiled documents-only branch `coordination/dmb-ddb-v1`; validated Codex service destinations must be captured from approved non-secret host/provider configuration before execution. The service allowlist is currently unresolved, so no exact network grant is requested. No inbound listener, remote shell, scheduler or new paid endpoint. GitHub Contents read/write plus Metadata read on this repository is the minimum publication grant; it is not server-side branch scoping. No admin, Actions, secrets, merge or bypass permission. Never reuse cloud/DAT/DPM/Pulse credentials or copy Linux private keys.

## Implementation gates before final package approval

1. Adapt the native backend to reuse Windows token/verified executable-handle/Job Object primitives and DDB INTENT→SEALED→REVIEWED storage. Keep Linux uncertain INTENT immutable; no migration/reset or task replay. Prove owned cancellation and process cleanup, no automatic retry of ambiguous effects.
2. Add reviewed Windows DPAPI-backed signer and GitHub credential provider, retaining exact identity/scope/expiry and no plaintext secret in files, arguments, documents or logs. Credential enrollment remains a separate explicit gate; first assess an existing dedicated approved credential under DirectiveCodex without displaying it.
3. Build a fresh self-contained native-Windows-validated release with full input/source/ZIP hashes and verify it under the target account. Current review manifest has no runnable release identifier or policy hash; these fields intentionally block execution. Do not approve substitutions or mutable latest downloads.
4. Produce the exact signed public one-task policy, signer fingerprints, clean source and executable pins, exact command/destinations, expiration and 420-second overall/20-second native bounds. Require review of these concrete values before Phase B. No auto-renewal, model switch or capacity retry.

## Bounded certification sequence after exact approval

Preflight identity/token, package/source/executable locks, clean dedicated clone, exclusive ownership, policy/signers/expiry, private DPAPI ownership and authenticated repository access. Preserve prior coordination history and all state. Refuse any conflicting directive/policy or uncertain publication.

DMB publishes one signed immutable DCI read-only review directive; worker retrieves and validates signatures/hash/sequence/expiry, writes durable INTENT, ACKs, executes one actual Codex task and verifies genuine completion/events and source unchanged. Publish signed receipt with artifact hash, identity and task/policy correlation. DMB independently reads it back, validates signature and artifact binding and records durable review. Only a verified completed receipt is success.

Then use separate state namespaces and harmless controlled fixtures for cancellation, termination before/after sealing, restart and duplicate delivery. Fixtures must not consume additional genuine research tasks or be reported as native Codex tests. Cancellation of an actual native process requires a separate exact bounded fixture grant if the single research run has completed; never disrupt production or unrelated Codex. Recovery must republish SEALED results without re-execution and quarantine an uncertain INTENT. Verify hash-chained audit and execution count. Test OS read/write denial only against existing authorized harmless canaries; absent safe authority means BLOCKED. Stop on any identity, permission, isolation or policy violation.

## Certification matrix

| Gate | Status | Evidence / limit |
|---|---|---|
| Existing executable availability/hash | PASS | Read-only live observer metadata; official pin matches |
| Account exists/enabled, direct admin membership | PASS | Read-only account/group metadata; no effective-token claim |
| Native worker execution | BLOCKED | Windows DDB adapter/release absent; historical bridge success is separate |
| Actual worker Medium token | BLOCKED | DirectiveCodex session disconnected; observer is Administrator |
| OS isolation / current account write | BLOCKED | Parent ACL grant observed; native denial/write probes not performed |
| Signed directive mechanism | PASS | Prior GitHub signed admission/failure readback; Windows route NOT TESTED |
| Windows GitHub read/write | BLOCKED | Dedicated credential/target-account validation pending |
| Windows durable signed completion | BLOCKED | No Windows DDB task started |
| Cancellation | BLOCKED | Controlled native fixture not executed |
| Crash recovery / duplicate suppression | BLOCKED | Windows DDB route not executed; prior receipts retained |
| Scheduler compatibility | BLOCKED | Existing XML/lifecycle preparation only; target-account batch context unverified |
| Production-system isolation | BLOCKED | No configured production paths; OS access denial not certified |
| No deployment/enrollment/activation | PASS | No package installed, credential enrolled, task/service registered or Codex launched in this assessment |

## Rollback and consolidated future approval

No deployment exists to undo. Preserve the observer evidence, Git branches, Linux quarantine and historical installations. For a future approved foreground package: STOP/drain only its owned worker/Job Object; verify child count zero, seal audit and retain the entire fresh root. Do not delete journals, pairing material or credentials and do not reset GitHub history. Credential revocation, if ever needed, belongs to the dedicated approved owner/lifecycle. Do not remove/change other schedules, services or ACLs. Uncertain effects remain quarantined.

The single future approval request must contain the actual release/hash, command, public policy hash/window/signers, exact endpoints, dedicated credential ownership/enrollment changes and controlled fixture grants. It must explicitly authorize one DirectiveCodex foreground session and no scheduler. This report does not ask the operator to run exploratory commands or approve an incomplete release. Until that package exists, continue only offline adapter/package preparation.
