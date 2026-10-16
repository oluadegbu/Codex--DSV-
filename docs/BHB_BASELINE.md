# BHB baseline — 2026-10-11

Overall baseline: BLOCKED for specified Windows deployment; PASS for isolated
cloud shadow development. No existing DCI component was restarted or replaced.

| Gate | Result | Observed evidence |
| --- | --- | --- |
| Cloud repository continuity | PASS | /workspace/dci, clean starting tree, 69bb12e and 2800b3c preserved |
| Existing tests | PASS | All 28 baseline tests passed before bridge changes |
| Cloud non-admin worker | PASS | uid/gid 1000 agent, group agent; no root group |
| Windows DirectiveCodex identity | BLOCKED | Desktop Commander whoami returned Administrator; Administrators enabled; High Mandatory Level |
| Windows Git/workspace access | BLOCKED | Directory listing shows .git and README; git reports not a repository; file realpath returns EPERM |
| Existing bridge certifications | BLOCKED | None in cloud checkout; Windows evidence inaccessible |
| Codex CLI | PASS for discovery | codex-cli 0.159.0-alpha.3; login status reports ChatGPT auth; exact account identity not returned |
| Live Codex task | BLOCKED | Read-only exec initialization fails with read-only runtime filesystem; no turn completed |
| GitHub read | PASS | Authenticated login oluadegbu; main remains 0af1f4208da6d5f799ec68d48aab5fb4800159d0 |
| GitHub write | BLOCKED | Fresh create_tree attempt returns HTTP 403 Resource not accessible by integration |

The Windows identity probe was read-only. After observing elevation, no Windows
implementation commands, writes, account changes, credential reads or attempts to
work around EPERM were performed. Implementation continues in /workspace/dci as
agent. Windows is the deployment target, not the workspace that was modified.
Exact Codex Remote account identity and its DirectiveCodex linkage remain
uncertified. No production DAT/DPM/Pulse/OpenClaw services were inspected or changed.
