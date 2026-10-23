# REQUEST-0011: Restricted native worker host fallback

CONTEXT
Current Linux Codex startup is blocked by a second unlocalized read-only filesystem failure after a demonstrated supported SQLite-state relocation. Local remediation stops; no task retry or new path guesses are authorized by this decision.

EVIDENCE
See docs/DDB_STARTUP_HOST_DECISION_20261019.md and docs/evidence/ddb-startup-recovery-20261019/. Existing Windows genuine receipt SHA-256 eeb58f4dbdc2dd9fab35cf55e528575e713022621a70230bbd4dc46fa69853e6 proves non-admin Medium execution, not signed DDB delivery or OS isolation. Available platform status exposes no filesystem-denial telemetry. Exact remaining syscall/path is UNKNOWN.

OPTIONS
1. Wait for platform-supported sanitized filesystem-denial telemetry and a documented minimum-scope runtime configuration, keeping protected credentials and sandbox unchanged.
2. Prepare the existing DirectiveCodex Windows host as the native worker fallback; authorize deployment/enrollment and a single bounded signed foreground certification only after reviewing exact host configuration, policy, source/binary pins and credential scope. No scheduler authorization is implied.

RECOMMENDATION
Option 2 for the execution architecture; retain Option 1 as a platform support request. Reuse existing Windows bridge security and durable DDB contracts. Do not run the Linux-only backend on Windows, transfer Linux keys/auth state, reset quarantines, or imply existing Windows receipt certifies the new route.

IMPACT
Approval gate, before any host deployment/enrollment/execution: review one consolidated Windows DDB preparation package identifying exact artifact/hash, DirectiveCodex scratch paths, dedicated signer/GitHub authentication ownership, policy fingerprint and one-task limits; approve only the necessary host/enrollment changes and fresh foreground attempt. No new paid host, ACL/firewall changes, production access or persistent process is proposed. No approval is required merely to review this report. REQUEST-0009 remains WITHHELD. Original task remains quarantined; use a fresh explicitly approved identity-bound task and preserve its predecessor evidence.

BLOCKING: YES
HARD_GATE: YES

## October 20 readiness assessment (supersedes any implication of a runnable package)
Phase A permits read-only inspection and preparation, not enrollment or execution.
Live observer metadata verifies the existing account and official executable hash;
the observer is Administrator and DirectiveCodex is disconnected. No worker was
launched. The existing DDB native backend remains Linux-only. The exact reviewed
release/command/policy cannot yet be approved because the Windows adaptation is
not built. See docs/DDB_WINDOWS_FOREGROUND_CERTIFICATION_PLAN.md and
 deployment/ddb/windows-request-0011/PACKAGE_REVIEW.json. Null release/policy/command
fields are deliberate blockers, never default values. Continue offline preparation;
consolidate approval only after native release validation and exact pins are ready.

## Phase 10.2 offline adapter implementation (activation still WITHHELD)
The Windows native adapter now shares portable native receipt state with Linux;
see docs/DDB_WINDOWS_ADAPTER_CERTIFICATION.md. Existing Linux protocol/branch and
quarantine are unchanged. Proposed fresh compiled Windows branch is exactly
`coordination/dmb-ddb-windows-0011`; it has NOT been created/trusted. Two dedicated
role signers, exact public fingerprints/one-task policy and dedicated DPAPI
repository credential require review/enrollment approval; no enrollment occurred.
The review package version is 0.4.0-ddb-review1. Source-only archive is not a
Windows deployment ZIP. Native CI/full ZIP/hash, current isolated non-admin
executor, actual service destinations and OS-denial evidence remain pending.
Readiness is BLOCKED, not production-ready. Consolidated approval must identify
actual ZIP/source/policy hashes, branch creation, signer/credential ownership,
exact destinations and one bounded command; no placeholder is authorization.
No privilege, ACL, production, scheduler, main merge or VPS launch is approved.
