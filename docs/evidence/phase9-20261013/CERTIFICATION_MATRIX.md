# Phase 9 certification matrix

**DMB LOCAL SHADOW PASS / SINGLE REAL WORKER CERTIFICATION BLOCKED**. Full DMB: BLOCKED.

| Gate | Status | Scope and evidence |
| --- | --- | --- |
| baseline_preservation | PASS | Both immutable manifest sets and original source hashes match; original bundles verified. [BASELINE.json](BASELINE.json) |
| existing_tests | PASS | 100 regression and 17 authorization-fixture tests pass; original 84/100 cycles/1099 executions preserved. [LOCAL_VERIFICATION.json](LOCAL_VERIFICATION.json) |
| managed_host_identity | PASS | Linux agent UID1000; actual CLI UID1000 observed. Windows integrity level does not apply. [RUNTIME_IDENTITY.json](RUNTIME_IDENTITY.json) |
| failure_host_distinction | PASS | Read-only standalone runtime failure is Linux, not VPS. No Windows worker failure observed. [RUNTIME_IDENTITY.json](RUNTIME_IDENTITY.json) |
| windows_executor_token | BLOCKED | Connected executor is Administrator at High integrity; development invocation prohibited. [WINDOWS_IDENTITY.json](WINDOWS_IDENTITY.json) |
| existing_DirectiveCodex_account | PASS | Enabled existing account is not an Administrators member; session3 disconnected. No target process token certified. [WINDOWS_IDENTITY.json](WINDOWS_IDENTITY.json) |
| DirectiveCodex_actual_identity_integrity | NOT TESTED | No connected executor under target account; account membership cannot prove process integrity. [WINDOWS_IDENTITY.json](WINDOWS_IDENTITY.json) |
| DirectiveCodex_Codex_auth_and_compatibility | NOT TESTED | Target installation, existing login, writable state, policy-permitted sandbox and Server2022 compatibility unverified. [WINDOWS_IDENTITY.json](WINDOWS_IDENTITY.json) |
| actual_Codex_process_launch | PASS | One real CLI process launched in fresh pinned clone; this is not task completion certification. [CODEX_INVOCATION.json](CODEX_INVOCATION.json) |
| standalone_Codex_task_completion | BLOCKED | Exit1 on read-only initialization, zero JSON events/no completed turn. No synthetic replacement. [CODEX_INVOCATION.json](CODEX_INVOCATION.json) |
| worker_workspace_and_test_execution | NOT TESTED | Launcher clone/cwd exists; Codex never executes requested Git/tests or reports child identity. [CODEX_INVOCATION.json](CODEX_INVOCATION.json) |
| worker_Git_operations | NOT TESTED | Launcher and connector Git evidence cannot certify worker Git read/write/commit. [CODEX_INVOCATION.json](CODEX_INVOCATION.json) |
| worker_cancellation | NOT TESTED | No real turn began; natural initialization exit is not cancellation evidence. [CODEX_INVOCATION.json](CODEX_INVOCATION.json) |
| worker_restart_and_replay | NOT TESTED | No working turn/runtime available. Local verifier recovery remains separately scoped. [CODEX_INVOCATION.json](CODEX_INVOCATION.json) |
| current_layout_read_write_separation | BLOCKED | Both neighboring same-UID canary operations succeed. Distinct paths do not enforce separation. [LOCAL_VERIFICATION.json](LOCAL_VERIFICATION.json) |
| Codex_sandbox_canary_probe | BLOCKED | With managed requirements included, sandbox refuses socket-directory ownership/mode; no canary probe runs. Preliminary missing-profile argument error retained separately. [SANDBOX_DIAGNOSTIC.json](SANDBOX_DIAGNOSTIC.json) |
| Windows_worker_canary_read_denial | NOT TESTED | No non-admin worker token or independently enforced boundary provided. [WINDOWS_IDENTITY.json](WINDOWS_IDENTITY.json) |
| Windows_worker_canary_write_denial | NOT TESTED | No non-admin worker token or independently enforced boundary provided. Production ACLs untouched. [WINDOWS_IDENTITY.json](WINDOWS_IDENTITY.json) |
| signed_delivery_contract | PASS | Existing signatures/tampering/principal binding/dedup/retry/offline restart/audit tests pass. No external identity proof. [PRESERVED_TESTS.log](PRESERVED_TESTS.log) |
| inbox_outbox_preparation | PASS | Disabled MCP tools/events integration plan prepared; no network listener installed or route activated. [LOCAL_VERIFICATION.json](LOCAL_VERIFICATION.json) |
| authenticated_remote_delivery | BLOCKED | No DMB endpoint/issuer/principal/callback/subscription available. Fixture claims are not real authentication. [LOCAL_VERIFICATION.json](LOCAL_VERIFICATION.json) |
| remote_delivery_offline_recovery | NOT TESTED | Offline contract reopening passes; actual authenticated route outage/retry/recovery not available. [LOCAL_VERIFICATION.json](LOCAL_VERIFICATION.json) |
| HEG_real_approval_and_providers | BLOCKED | No real human approval inferred; WhatsApp/email remain disabled, approval/certification required. [AUTHORIZATION_TESTS.log](AUTHORIZATION_TESTS.log) |
| GitHub_draft_publication | PASS | PR1 open/draft/unmerged; baseline exact published tree; connector write evidence retained. [GITHUB_BASELINE.json](GITHUB_BASELINE.json) |
| GitHub_baseline_CI | PASS | Run38305725020 succeeds at f1d11c0; CI verifies shadow code, not Codex runtime/isolation. [GITHUB_BASELINE.json](GITHUB_BASELINE.json) |
| production_and_safety_preservation | PASS | No merge/main mutation, trading, secrets copying, notifications, Windows changes, identities, privileged ACLs, services or purchases. [CODEX_INVOCATION.json](CODEX_INVOCATION.json) |
| single_real_worker_certification | BLOCKED | Real turn/Windows token/worker Git/cancellation/restart/isolation gates have not passed. [CODEX_INVOCATION.json](CODEX_INVOCATION.json) |
| full_DMB_certification | BLOCKED | Multi-worker isolation, authenticated external delivery and actual external-project integrations remain unverified. [LOCAL_VERIFICATION.json](LOCAL_VERIFICATION.json) |

Process observations: Linux `agent` UID1000; Windows executor `WIN-HQAAFGGU1AM\Administrator`, High integrity. Existing `DirectiveCodex` is enabled/non-Administrators-member; its actual process integrity is NOT TESTED.

[Procedure](../../DMB_PHASE9.md) · [Inert communication plan](../../DMB_REMOTE_INTEGRATION.v1.json) · [Human prerequisite](../../../decisions/REQUEST-0007.md)

Manifest hashes bind evidence files. Local/synthetic PASS cannot promote the externally blocked gates. No main update, merge, provider activation or Windows security change occurred.
