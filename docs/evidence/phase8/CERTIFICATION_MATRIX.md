# Phase 8 certification matrix

Outcome: **DMB LOCAL SHADOW PASS / FULL CERTIFICATION BLOCKED**.

Every PASS is scoped; local, synthetic, documented or historical checks do not certify external activation.

| Gate | Status | Evidence scope | Evidence |
|---|---|---|---|
| baseline_git_and_bundle_integrity | PASS | LOCAL | [BASELINE.json](../../../docs/evidence/phase8/BASELINE.json) |
| baseline_artifact_and_source_hashes | PASS | LOCAL | [BASELINE.json](../../../docs/evidence/phase8/BASELINE.json) |
| prior_test_cycle_provenance | PASS | PRESERVED_HISTORICAL_LOCAL | [BASELINE.json](../../../docs/evidence/phase8/BASELINE.json) |
| current_regression_suite | PASS | LOCAL | [LOCAL_RESILIENCE.json](../../../docs/evidence/phase8/LOCAL_RESILIENCE.json) |
| github_authenticated_identity | PASS | EXTERNAL_READ_ONLY | [GITHUB_AUTHORIZATION.json](../../../docs/evidence/phase8/GITHUB_AUTHORIZATION.json) |
| github_repository_read_access | PASS | EXTERNAL_READ_ONLY | [GITHUB_AUTHORIZATION.json](../../../docs/evidence/phase8/GITHUB_AUTHORIZATION.json) |
| github_chatgpt_action_permission_check | PASS | EXTERNAL_SETTINGS_READ_ONLY | [GITHUB_AUTHORIZATION.json](../../../docs/evidence/phase8/GITHUB_AUTHORIZATION.json) |
| github_collaborator_permission_endpoint | BLOCKED | EXTERNAL_DENIAL | [GITHUB_AUTHORIZATION.json](../../../docs/evidence/phase8/GITHUB_AUTHORIZATION.json) |
| github_installation_scope_and_grant_introspection | NOT TESTED | UNAVAILABLE_SUPPORTED_INTERFACE | [GITHUB_AUTHORIZATION.json](../../../docs/evidence/phase8/GITHUB_AUTHORIZATION.json) |
| github_write_authorization | BLOCKED | EXTERNAL_DENIAL | [GITHUB_AUTHORIZATION.json](../../../docs/evidence/phase8/GITHUB_AUTHORIZATION.json) |
| github_publication_and_readback | NOT TESTED | DEPENDENCY_BLOCKED | [GITHUB_AUTHORIZATION.json](../../../docs/evidence/phase8/GITHUB_AUTHORIZATION.json) |
| codex_supported_cli_available | PASS | LOCAL_INTERFACE | [CODEX_INVOCATION.json](../../../docs/evidence/phase8/CODEX_INVOCATION.json) |
| codex_standalone_turn_completion | BLOCKED | ACTUAL_INVOCATION | [CODEX_INVOCATION.json](../../../docs/evidence/phase8/CODEX_INVOCATION.json) |
| codex_live_bounded_development_task | NOT TESTED | DEPENDENCY_BLOCKED | [CODEX_INVOCATION.json](../../../docs/evidence/phase8/CODEX_INVOCATION.json) |
| codex_live_retry_and_cancellation | NOT TESTED | DEPENDENCY_BLOCKED | [CODEX_INVOCATION.json](../../../docs/evidence/phase8/CODEX_INVOCATION.json) |
| cloud_non_admin_identity | PASS | LOCAL | [RUNTIME_IDENTITY.json](../../../docs/evidence/phase8/RUNTIME_IDENTITY.json) |
| windows_directivecodex_non_admin_identity | BLOCKED | EXTERNAL_IDENTITY_PROBE | [RUNTIME_IDENTITY.json](../../../docs/evidence/phase8/RUNTIME_IDENTITY.json) |
| windows_dci_workspace_access | BLOCKED | EXTERNAL_TOOL_POLICY | [RUNTIME_IDENTITY.json](../../../docs/evidence/phase8/RUNTIME_IDENTITY.json) |
| distinct_worker_workspaces_and_git_traceability | PASS | LOCAL | [BASELINE.json](../../../docs/evidence/phase8/BASELINE.json) |
| os_cross_workspace_access_denial | BLOCKED | ACTUAL_NEGATIVE_PROBE | [ISOLATION_PROBE.json](../../../docs/evidence/phase8/ISOLATION_PROBE.json) |
| codex_sandbox_access_denial | NOT TESTED | DEPENDENCY_BLOCKED | [ISOLATION_PROBE.json](../../../docs/evidence/phase8/ISOLATION_PROBE.json) |
| external_project_reconciliation | PASS | EVIDENCE_RECORDING_ONLY | [RECONCILIATION.phase8.v1.json](../../../portfolio/RECONCILIATION.phase8.v1.json) |
| actual_dat_dpm_dsv_pulse_vma_temporal_integration | NOT TESTED | NO_AUTHORIZED_ARTIFACT_LOCATIONS | [RECONCILIATION.phase8.v1.json](../../../portfolio/RECONCILIATION.phase8.v1.json) |
| supported_remote_brain_path_identification | PASS | DOCUMENTED_ONLY | [DMB_PHASE8.md](../../../docs/DMB_PHASE8.md) |
| remote_brain_oauth_and_client_identity | BLOCKED | MISSING_EXTERNAL_CONFIGURATION | [DMB_PHASE8.md](../../../docs/DMB_PHASE8.md) |
| real_remote_inbox_outbox_delivery | NOT TESTED | DEPENDENCY_BLOCKED | [DMB_PHASE8.md](../../../docs/DMB_PHASE8.md) |
| signed_event_identity_scope_and_tamper_rejection | PASS | LOCAL_EPHEMERAL_CONTRACT | [LOCAL_RESILIENCE.json](../../../docs/evidence/phase8/LOCAL_RESILIENCE.json) |
| event_dedup_audit_retry_and_offline_recovery | PASS | LOCAL_EPHEMERAL_CONTRACT | [LOCAL_RESILIENCE.json](../../../docs/evidence/phase8/LOCAL_RESILIENCE.json) |
| heg_whatsapp_primary_activation_approval | BLOCKED | APPROVAL_NOT_PRESENT | [DMB_PHASE8.md](../../../docs/DMB_PHASE8.md) |
| heg_independent_email_activation_approval | BLOCKED | APPROVAL_NOT_PRESENT | [DMB_PHASE8.md](../../../docs/DMB_PHASE8.md) |
| heg_real_authenticated_supervisor_approval | NOT TESTED | NO_AUTHENTICATED_LIVE_IDENTITY | [DMB_PHASE8.md](../../../docs/DMB_PHASE8.md) |
| heg_receipt_is_not_approval | PASS | LOCAL_SYNTHETIC | [LOCAL_RESILIENCE.json](../../../docs/evidence/phase8/LOCAL_RESILIENCE.json) |
| heg_independent_fallback_and_channel_dedup | PASS | LOCAL_SYNTHETIC | [LOCAL_RESILIENCE.json](../../../docs/evidence/phase8/LOCAL_RESILIENCE.json) |
| isolated_process_restart_and_worker_crash | PASS | ACTUAL_LOCAL_FAULT | [LOCAL_RESILIENCE.json](../../../docs/evidence/phase8/LOCAL_RESILIENCE.json) |
| local_task_retry_resource_fencing_and_cancellation | PASS | LOCAL | [LOCAL_RESILIENCE.json](../../../docs/evidence/phase8/LOCAL_RESILIENCE.json) |
| combined_controlplane_absence_continuation | PASS | LOCAL_ABSENCE_FIXTURE | [LOCAL_RESILIENCE.json](../../../docs/evidence/phase8/LOCAL_RESILIENCE.json) |
| dsv_connected_service_outage | NOT TESTED | NO_CERTIFIED_CONNECTED_ROUTE | [LOCAL_RESILIENCE.json](../../../docs/evidence/phase8/LOCAL_RESILIENCE.json) |
| openclaw_connected_service_outage | NOT TESTED | NO_CERTIFIED_CONNECTED_ROUTE | [LOCAL_RESILIENCE.json](../../../docs/evidence/phase8/LOCAL_RESILIENCE.json) |
| chatgpt_live_delivery_disconnect | NOT TESTED | NO_CERTIFIED_CONNECTED_ROUTE | [LOCAL_RESILIENCE.json](../../../docs/evidence/phase8/LOCAL_RESILIENCE.json) |
| temporal_contract_and_dat_milestone_preservation | PASS | LOCAL_INTERFACE_AND_HISTORICAL_APPROVAL | [BASELINE.json](../../../docs/evidence/phase8/BASELINE.json) |
| temporal_live_server_integration | NOT TESTED | NO_AUTHORIZED_DEPLOYMENT | [RECONCILIATION.phase8.v1.json](../../../portfolio/RECONCILIATION.phase8.v1.json) |
| no_live_trading_elevation_or_provider_service_activation | PASS | CURRENT_WORK_SCOPE | [RUNTIME_IDENTITY.json](../../../docs/evidence/phase8/RUNTIME_IDENTITY.json) |

Exact SHA-256 hashes are attached to every gate in CERTIFICATION_MATRIX.json and indexed in ARTIFACT_MANIFEST.json.

HUMAN REQUIRED: existing single-repository GitHub Contents-write review; non-admin Windows/runtime and worker boundaries; exact authorized project references and separately scoped remote Brain/HEG shadow activation. No tokens or broad privilege grants requested.
