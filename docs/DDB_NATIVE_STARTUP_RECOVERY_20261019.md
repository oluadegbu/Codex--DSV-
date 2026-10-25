# Native startup recovery — blocked, fail-closed

The pinned Codex binary is unchanged (SHA-256 `981ade7b03926534c654fd718ced3a9f378b7b2841271e29156f939462d176e9`). Diagnosis began at clean source commit `f95a612eb1130eb675d6c86dfba446cdb5c6d162`, under UID 1000. No application source changed.

A bounded startup-only `codex app-server --stdio` probe, with stdin closed, identifies SQLite state initialization under `/run/codex-environment/codex-home` as the first fatal failure. That directory inherits the read-only root mount. The inherited HOME and CODEX_HOME were not changed; credentials were not read or copied.

The supported `-c sqlite_home="/workspace/dmb-startup-recovery/sqlite"` override advances initialization and creates SQLite state only in authorized scratch. A subsequent EROFS remains. Adding a scratch `log_dir` does not resolve it. This is a partial diagnosis, not a working remediation. The exact failing syscall and final pathname remain unverified: platform policy denies PTRACE_TRACEME. No attempt was made to bypass tracing restrictions, trust the workspace, relax sandboxing, or change mount permissions.

No native research task, model request, network request, or quarantined task was executed. Original INTENT, signed failure, journals and quarantine remain intact. Startup probes are not genuine task certification.

Minimum next requirement: platform-provided sanitized filesystem-denial telemetry (operation and pathname), or a supported runtime configuration for every required writable startup dependency while retaining the protected credential mount. Do not blindly rerun the task or relocate/copy credential state. A fresh native task also requires explicit authorization; the previous single attempt is consumed.

Structured evidence: `evidence/ddb-startup-recovery-20261019/DIAGNOSIS.json`. Local probe artifacts remain under `/workspace/dmb-startup-recovery`; private startup traces are not published.
