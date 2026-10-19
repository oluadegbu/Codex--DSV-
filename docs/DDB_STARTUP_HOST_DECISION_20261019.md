# DDB native startup: host decision

Recommendation: use the existing restricted DirectiveCodex Windows host as the native execution fallback, subject to a reviewed Windows DDB integration package and explicit approval before host changes or another task. This is an architecture recommendation, not a deployment or certification claim. Stop local Linux remediation until the platform supplies the exact remaining denial and a supported correction.

## Supported diagnostic assessment

Read-only assessment on October 19, 2026 (UTC evidence dates). Current managed environment status reports running/connected, current observations, empty capabilities and no network diagnostic snapshot. The exposed status API describes network/credential readiness; it has no filesystem-denial feed or worker runtime-path contract. No supported filesystem-telemetry tool is exposed in this session. This establishes an available-interface limit, not that the provider has no internal telemetry. No tracing, native startup, network diagnostic or model execution was attempted in this assessment.

Installed public help already captured in prior diagnosis supports TOML `-c` overrides. Read-only static binary inspection confirms `sqlite_home`, `log_dir`, `CODEX_HOME` and `CODEX_SQLITE_HOME` identifiers; identifiers alone do not constitute permission or a complete runtime-location contract. No complete writable-runtime configuration is documented in inspected installed resources. Protected Codex home contains a private auth file and tmp directory; no auth contents were inspected. HOME/CODEX_HOME, inherited guards, credentials and mount policy remain unchanged.

Previous startup-only evidence establishes SQLite initialization under `/run/codex-environment/codex-home` as the first fatal stage. The supported `sqlite_home` override created databases under authorized `/workspace/dmb-startup-recovery/sqlite`; retain this verified partial remediation. The second EROFS persists even with `log_dir` redirected. Exact second operation/path remains UNKNOWN. Do not infer sessions, cache, aliases, history or credentials as its cause. No additional directory guesses or retries are proposed. SQLite override is not deployed into the native task backend or represented as a complete fix.

## Comparison

| Property | Current restricted Linux host | Existing DirectiveCodex Windows host |
|---|---|---|
| Isolation | Read-only protected root; writable workspace. Native task sandbox configured read-only; successful execution not established. | Receipt proves non-admin Medium token; dedicated scratch and sandbox controls implemented. OS access-denial certification remains NOT TESTED. |
| Credentials | Existing inherited auth unchanged, protected read-only mount; no copying/re-enrollment. | Existing CLI authentication previously passed; retain DPAPI/account boundaries. Dedicated DDB signer and repository credential availability/ownership need host-specific review; do not transfer Linux credentials. |
| Persistence | No DDB scheduler activated; process continuity unproven. | Foreground execution proven; RDP-independent lifecycle and REQUEST-0009 activation withheld. |
| GitHub | Signed directive/ACK/failure readback proven in approved network context; not genuine completion. | Local bridge receipt does not prove remote GitHub DDB access. Existing-host scoped auth/connectivity still require certification. |
| Startup | First SQLite write diagnosed and partially corrected; second EROFS unobservable. | Genuine pinned historical v0.1.3 worker completed DCI_SHADOW_OK; current live session/binary not revalidated here. |
| Effort | Small correction only if provider reveals supported remaining dependency; currently blocked. | Reuse existing Windows bridge/package and DDB contracts; native DDB backend currently Linux-only and needs reviewed adaptation/package plus a fresh bounded test. No new platform needed. |

## Certification and next gate

PASS: historical Windows genuine execution, audit and restart replay suppression (receipt scope only); unchanged Linux binary and preserved source/evidence. BLOCKED: current Linux startup; Windows signed DDB execution; live host access/credential review. NOT TESTED: Windows OS access-denial isolation, genuine cancellation/injected crash, remote DDB successful completion, unattended continuity. Do not declare foreground or full DMB certification.

A platform owner can provide sanitized failing operation/path and supported runtime requirements without granting broad filesystem access. Otherwise prepare the reviewed Windows adapter package offline; before deployment, consolidate exact host paths, source/binary/package hashes, one-task signed policy, credential ownership/enrollment changes and bounded execution into REQUEST-0011. Approval must precede security-sensitive enrollment or a fresh task. No services/schedulers, batch rights, ACL/firewall changes or production access are requested here.

Rollback is preservation-only at this stage: no runtime change was deployed. Leave original INTENT/quarantines, signed GitHub failure/ACK/directive, policy history, journals, keys and old Windows installations untouched. Do not reinterpret failure as completion or reset the task budget. PRs remain draft; main is unchanged.

## Evidence provenance

- `docs/evidence/ddb-startup-recovery-20261019/DIAGNOSIS.json` SHA-256 `437aaf4ff255732df60ca3361632931dec16b7a184047c6c0c983268f3e8259b`.
- `docs/evidence/windows-genuine-completion/CERTIFICATION.json` SHA-256 `eeb58f4dbdc2dd9fab35cf55e528575e713022621a70230bbd4dc46fa69853e6`.
- `docs/evidence/phase10-lifecycle/CERTIFICATION.json` SHA-256 `1480026422391ca774f8a8206ac49b8b4f22bd0995a457627a4e544624681eb4`.
- Pinned Linux binary SHA-256 `981ade7b03926534c654fd718ced3a9f378b7b2841271e29156f939462d176e9`; application source untouched. Current assessment changes documentation/state only; no synthetic test is substituted for native evidence.
