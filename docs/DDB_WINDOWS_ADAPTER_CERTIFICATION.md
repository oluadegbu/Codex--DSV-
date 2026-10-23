# Windows DDB adapter — Phase 10.2 offline certification

Mode: SHADOW / NON-TRADING / FAIL-CLOSED. This report supersedes the earlier statement that no Windows adapter exists; historical live evidence is unchanged. Adapter implementation and offline contracts pass. Full offline release certification is BLOCKED pending native-Windows CI/package artifacts and the existing loopback regression's sandbox permission gate. Native Windows isolation is NOT TESTED. Not ready for execution approval until those concrete release gates close.

## Architecture and implemented boundaries

`document_native_state.NativeReceiptBackend` is the portable native INTENT/SEALED/REVIEWED contract extracted without changing the Linux task path or signed document format. Linux keeps /proc ownership, POSIX limits and owned process-group cleanup. Windows supplies `document_windows.WindowsForegroundBackend`, using the existing exact non-admin/Medium token gate, reviewed host/SID, official v0.162.1 executable verification and suspended-image check, and Win32 owned Job Object. Job limits remain 10 CPU seconds, 256 MiB job memory, eight processes and kill-on-close. Protocol execution is limited to 20 seconds; pipe writes have bounded waits and the foreground driver caps the full cycle at 420 seconds. Cancellation sends turn/interrupt; all exits terminate/drain/close the owned job. An uncertain execution is never relaunched.

Only `C:\Users\DirectiveCodex\AppData\Local\Directive\DMB-DDB-cert-0011` is allowed for this Windows deployment. Controller must be `package\app`, clone `worker-clone`, private configuration/journals `state`, output `artifacts`. Reparse/symlink paths are rejected. Pinned bundled Git runs with system/global config disabled, fsmonitor disabled and hooks disabled; source commit must be clean and both allowlisted source hashes unchanged. The fixed DCI review template receives only `src/dci/models.py` and `src/dci/scoring.py` as bounded JSON context; no mailbox prompt, shell, model-selected tools, MCP or web search. Effective app-server read-only/no-network sandbox and approvalPolicy never are checked. Tool/approval requests and unexpected artifacts/routes fail closed.

These are application/protocol boundaries. Read-only sandbox does NOT prove that every other file is unreadable by the Windows account. Existing account filesystem authority, Codex runtime/auth initialization and inherited proxy/CA handling are not an OS-isolation certificate. Production and other-account negative access tests remain NOT TESTED; do not deploy until the exact intended scope is approved. No tests probed DAT/DPM/DSV/Pulse/OpenClaw contents or modified ACLs. The account's existing `.codex` state is the only permitted explicit CODEX_HOME; no cloud keys or trading credentials are copied. Default profile/runtime authority must be checked during separately approved host preflight.

Existing `load_private_json` DPAPI loading is reused for Windows configuration, Ed25519 key file and dedicated repository credential. No enrollment/rotation code runs. Files must be in the dedicated state root and token identity is verified before private loading. DPAPI is current-user protection, not proof that every same-account process is isolated. No credential or private signer appears in the package, policy example, tests or logs.

## Branch, signer and policy changes requiring approval

Original `coordination/dmb-ddb-v1`, its signed failure/ACK/directive, consumed policy, audit and uncertain INTENT remain untouched. A fresh policy cannot reinterpret that stream's non-neutral history. The proposed Windows carrier has one compiled branch: **`coordination/dmb-ddb-windows-0011`** in `oluadegbu/Codex--DSV-`. It has not been created or trusted. Linux transport retains its original branch. No arbitrary branch parameter, force update or branch-creation API is exposed by the worker. The owner must explicitly approve creation of an empty documents-only branch before a future foreground attempt; do not fork it from main or populate it with code.

Enrollment proposal: two fresh dedicated Ed25519 role keys, one supervisor and one Windows worker, generated/protected under their approved identities. Bind their public keys/fingerprints, worker_id `windows_codex_ddb_0011`, worker_key_id `ddb-windows-0011`, and exact public policy hash. Do not reuse or move Linux/DAT/DPM/Pulse signer material. Windows DPAPI files: `state\worker.dpapi`, `state\controller.dpapi`, `state\worker-signing.dpapi`, `state\controller-signing.dpapi`, `state\github.dpapi`. No credential value belongs in an argument or GitHub document. If the strategic controller stays on another host, its key remains there; running both roles as DirectiveCodex only certifies role separation, not separate OS identities.

Proposed repository permission: Metadata read, Contents read/write for this repository only, no Actions/admin/secrets/merge/bypass grant. GitHub grant is repository-scoped; compiled branch enforcement is not server-enforced branch restriction. Native Codex uses the existing account's supported authentication unchanged. Actual credential availability, owner and expiry must be reviewed before enrollment is requested. HTTPS repository API is `api.github.com`; exact Codex service endpoints/proxy behavior remain a host preflight gate, not an invented allowlist.

Policy schema remains unchanged: version1, mode SHADOW, policy_id `ddb-windows-0011-foreground`, max_tasks1, template `codex_shadow_review_v1`, report_max_age600, document_ttl900, worker identity above and both actual public signer keys. Expiry is proposed 60 minutes from the approved verified start, no automatic renewal. Because no keys are enrolled, the public signer fingerprints, signed policy and final policy hash do not yet exist. No placeholder grants authority. One native research turn only; cancellation/crash fixtures do not silently authorize extra native Codex turns.

## Offline evidence and limits

43 DDB tests pass, preserving the original 38 plus four real harmless subprocess protocol fixtures and a branch-isolation assertion. Fixtures cover completion, cancellation acknowledgement, timeout, process crash/cleanup, wrong sandbox/route/tool/artifact, exact workspace pins, malformed signature, duplicate suppression, recovered sealed receipt and uncertain-intent refusal. Controlled subprocesses are ordinary Python fixtures, not Codex and not Win32 Job validation. Package tests verify deterministic ZIP ordering/timestamps and rejection of an unpinned base archive.

Historical Linux regressions in `docs/evidence/ddb-windows-adapter-20261020/OFFLINE_TESTS.json`: 100 core,17 certification,9 control-plane,13 package,16 operations and17 lifecycle tests pass. The Windows bridge suite ran22 tests with21 passing and its real loopback TLS fixture blocked by sandbox bind PermissionError. The subsequent narrowly scoped permission request was aborted; no retry or bypass. This is a blocked regression gate, not evidence that all tests pass. Updated adapter run and source pins are in `docs/evidence/ddb-windows-adapter-20261022/`.

The proposed native CI workflow runs offline protocol/controlled-process tests on a Windows runner and builds the review ZIP. It never launches Codex, enrolls signers, changes ACLs or impersonates DirectiveCodex. CI is not the VPS account and cannot certify its OS authority. Native canary tests should reuse existing harmless approved canary manifests through the established Windows isolation probe only after a non-admin isolated executor is available; no new identities or ACLs are authorized. Current environment is Linux, and the known VPS remote observer is Administrator. Therefore native Windows access denial is NOT TESTED, not simulated PASS.

## Package and reproducibility

`tools/build_windows_ddb_package.py` assembles committed bytes deterministically. Version `0.4.0-ddb-review1`. Complete Windows ZIP reuses runtime files only from certified baseline ZIP SHA256 `38b395f3609900d1c5423fc9ed4f02413397db8728c2c27d66ae576308ead5f6`. Dependencies: CPython3.12.10, MinGit2.51.0.windows.1, cryptography46.0.2, cffi2.0.0, pycparser2.23; existing Codex0.162.1 is not bundled. No Git/Python installation is required on the VPS. `DDB_PACKAGE_MANIFEST.json` enumerates every packaged file/hash; RELEASE.json and SHA256SUMS bind ZIP/source/manifest. Fixed ZIP timestamps/order make the same committed inputs reproducible. A source-only archive is explicitly non-runnable. The complete Windows ZIP/hash is pending native CI, so a source ZIP must never be substituted for deployment.

Offline build commands (development host only):

```text
python tools/build_windows_ddb_package.py --source-only --output <fresh-source-output>
python tools/build_windows_ddb_package.py --base-zip <exact-certified-base.zip> --output <fresh-windows-output>
```

After separate approval and exact ZIP/policy/network review, foreground command shape under the existing DirectiveCodex session is:

```powershell
& 'C:\Users\DirectiveCodex\AppData\Local\Directive\DMB-DDB-cert-0011\package\runtime\python\python.exe' -I 'C:\Users\DirectiveCodex\AppData\Local\Directive\DMB-DDB-cert-0011\package\app\tools\run_windows_ddb.py' --certify-cycle --foreground-certification --configuration-directory 'C:\Users\DirectiveCodex\AppData\Local\Directive\DMB-DDB-cert-0011\state' --approved-policy-sha256 '<ACTUAL_APPROVED_POLICY_HASH>' --output 'C:\Users\DirectiveCodex\AppData\Local\Directive\DMB-DDB-cert-0011\artifacts\foreground-001'
```

This is review-only command shape, not an instruction to execute. First verify the full ZIP SHA256 independently, Python Authenticode, package manifest and fresh root/non-admin token; prepare a clean pinned worker clone using bundled Git, with exact source hashes. No deployment/config generator is authorized to guess policy keys, source hashes or token material. Policy, signing and credential files must already be separately approved/enrolled as DPAPI. The driver reopens durable state between each role, verifies a single native reviewed receipt, signed completion and audit. Successful Windows handoff status explicitly keeps additional isolation/resilience/scheduler gates blocked.

## Readiness matrix and rollback

| Gate | Status |
|---|---|
| Portable/Linux and Windows offline DDB contracts | PASS (43 tests) |
| Controlled-process cancellation/timeout/crash/recovery | PASS fixture scope only |
| Original signed protocol/Linux transport preserved | PASS offline regressions |
| Full regression suite | BLOCKED loopback permission gate |
| Reproducible source archive | PASS once built; exact release record attached |
| Complete native-Windows ZIP and native CI | BLOCKED pending actual artifacts |
| Native Windows OS isolation | NOT TESTED |
| Native Windows Codex/DDB/GitHub completion | NOT TESTED |
| Fresh branch/signers/policy/deployment | BLOCKED separate approval |
| One bounded foreground attempt | NOT READY until exact release, enrollment/policy/endpoints and isolation scope reviewed |
| Unattended scheduling | WITHHELD REQUEST-0009 |

No deployed state exists to roll back. Preserve all previous files, pairing, journals and Linux quarantine. For a subsequently approved foreground attempt, create STOP only in the new dedicated state root; driver cancels/drains only its owned job. Seal evidence and retain the entire new installation on any failure. Restart with an uncertain INTENT must stay blocked; never remove/reset it. Do not alter original coordination history, other services/schedules or production credentials. Revocation of a future dedicated credential needs its separately approved owner/lifecycle. No automated rollback deletes keys or branch history.

Source review archive was built twice from local commit `cc16d48000eb4d1be5116f97711f92e25aa30394`; both ZIPs match SHA256 `8055d06d70f625851e237d549ff8cc4152329735097d0ce5085ee8133bbf7c47` (149727 bytes). Exact per-file/dependency manifest is attached in evidence. This archive is **not** the complete runnable Windows package. Native CI result remains pending.
