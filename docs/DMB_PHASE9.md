# DMB Phase 9 — actual worker runtime and isolation

Outcome: **DMB LOCAL SHADOW PASS / SINGLE REAL WORKER CERTIFICATION BLOCKED**.
Full DMB certification remains blocked. Mode: SHADOW / NON-TRADING / FAIL-CLOSED.

## Observations, October 13, 2026

Draft [PR #1](https://github.com/oluadegbu/Codex--DSV-/pull/1) is open and unmerged.
Its baseline head is `f1d11c0f2bae6aaa07749c445173da1c079c1437` and its tree matches
local `fc3029f5cccbba76f421ad33461503a8712ae290` exactly. Baseline
[GitHub CI](https://github.com/oluadegbu/Codex--DSV-/actions/runs/38305725020)
passed. Remote main remains `0af1f4208da6d5f799ec68d48aab5fb4800159d0`.
New evidence is additive; old certificates, source hashes and bundles are retained.

The standalone Codex startup failure occurred on managed Linux host
`cb72e1cfc391`, kernel `6.18.44`, as `agent` UID 1000. It did **not** occur on
the Windows VPS. Codex CLI `0.159.0-alpha.3` reports existing ChatGPT login;
this does not establish a Windows login or a particular human identity. Windows
integrity levels do not apply to Linux. Codex Cloud repository initialization is
an operator-reported separate context, not proof that nested CLI execution works.

One actual `codex exec --sandbox read-only --json --ephemeral` process was
observed as UID 1000 in a fresh development clone pinned to the baseline commit.
It exited 1 after 0.042 seconds, with no turn or task execution. Startup reported
read-only filesystem error 30. The clone remained clean. Cancellation/restart
of a working Codex turn and worker Git operations are consequently **NOT TESTED**.
The Git clone performed by the diagnostic launcher is not worker Git evidence.

The [Codex maintainer response](https://github.com/openai/codex/issues/51293)
explains that initialization still needs writable runtime state in `CODEX_HOME`,
including an installation ID, even for ephemeral runs. Redirecting logs/SQLite
does not relocate all state. The exact failing operation in this local binary
was not traced. Authentication storage was not read, copied or redirected;
managed mounts and safety settings were not changed.

The connected Windows host is `WIN-HQAAFGGU1AM`, Server 2022 Standard
`10.0.20348`. Its current Desktop Commander executor has an Administrator token
at High integrity. `DirectiveCodex` exists, is enabled and is not a member of
Administrators; its session 3 is disconnected. No available executor has been
observed running with that account's token. Its effective integrity, Codex
installation, writable runtime state and authentication remain untested.
The Administrator context cannot resolve a Codex command; that observation says
nothing about the target account's installation. No Windows development worker
was launched, and no Windows files, permissions, accounts or services were changed.

## Supported non-elevated path and certification procedure

Minimum prerequisite: reconnect the **existing** `DirectiveCodex` session and
provide an existing foreground execution connection under that account. Use
normal supported Codex authentication there if it is not already present;
credentials must never be shared in this conversation or copied from another
account. An installation, service, account or privileged ACL change is a separate
approval gate if the existing environment cannot support this procedure.

Official [Windows sandbox documentation](https://learn.chatgpt.com/docs/windows/windows-sandbox)
describes MXC on compatible Windows 11 devices and legacy `unelevated` operation
with a restricted token. The latter cannot deny read paths and has weaker network
isolation. Server 2022 compatibility and existing sandbox provisioning are
unverified here. Use only an already provisioned, policy-permitted sandbox;
never select a weaker implementation to circumvent managed requirements or run
administrator-approved setup without separate authorization.

Execute these steps only after the remote connection is independently observed
as `DirectiveCodex`, with a non-admin token and integrity no higher than Medium:

1. Capture machine/OS, `whoami`, `whoami /groups`, resolved Codex binary/version,
   normal `codex login status` and authorized workspace accessibility. Keep raw
   local diagnostic logs private. Stop on an unexpected identity or policy error.
2. Prepare a fresh isolated development clone, record source HEAD/tree and clean
   status, and keep all runtime evidence out of Git. Do not touch production
   repositories. Verify the active sandbox/managed policy using supported CLI
   status/config diagnostics, without reading authentication files.
3. Run one fixed read-only task through supported `codex exec --json --ephemeral`
   in that clone: actual child identity/integrity/cwd, `git rev-parse HEAD`,
   `git status --porcelain`, and the 17 existing authorization-fixture tests.
   Require tool-execution records and `turn.completed`, not a self-reported PASS.
   Bound the invocation to 60 seconds; fence uncertain outcomes and retain locks.
4. Certify a fixed development task on a new local development branch in the
   clone, with workspace-write permissions only where already permitted. Capture
   the exact allowed diff, passing tests and actual worker commit. Do not push
   main or merge the draft PR. Current connector publication is independent
   evidence; it cannot substitute for worker Git tracing.
5. After a real turn starts, cancel a separate bounded read-only turn using the
   supported foreground interrupt or app-server `turn/interrupt`. Observe terminal
   state and cessation of child processes. Restart a fresh invocation, correlate
   task/result IDs, and reject replay of the completed task. If termination is
   ambiguous, quarantine that task; never retry its effects automatically.
6. Place harmless, non-secret read/write canaries in two disposable roots across
   an **existing** confinement boundary. First prove the boundary controller can
   access them. Probe from the actual sandboxed child and require OS errors for
   both read and write. Record policy, ownership, token and errors. Test that the
   worker cannot undo the boundary. A directory name, model refusal, missing
   file, read-only sandbox's write denial, or owner-editable ACL alone is not
   proof of separation. Stop if stronger confinement requires an approval gate.

This procedure is prepared, not executed on Windows. The Linux diagnostic
`tools/probe_phase9_worker.py` is deliberately limited to one observed startup
attempt; it cannot certify Windows, cancellation or isolation.

## Isolation evidence

Fresh same-UID cross-root canary read **and** write succeeded. The current trusted
workspaces therefore lack OS separation. Production permissions were not tested
or altered. A supported Codex sandbox wrapper with the built-in workspace profile
and managed requirements included also failed before running the probes: its
socket directory ownership/mode check rejected startup. No directory was changed
to bypass that check. These are separate observations; a launcher error is never
classified as a denied canary read or write.

## Inbox/outbox preparation

See [remote integration plan](DMB_REMOTE_INTEGRATION.v1.json). It is an inert,
disabled specification, not a live connector or authentication service. The
existing signed event lab and authorization fixtures remain unchanged and pass:
tampering, wrong routes, duplicate/conflicting identities, bounded retries, expiry,
durable restart, audit, revoked scope and non-approval delivery receipts.

The supported design uses authenticated MCP tools for inbox requests and
[MCP Events](https://developers.openai.com/plugins/build/mcp-events) subscriptions
for signed result callbacks. Callback verification, HTTPS destination validation,
receipt handling and durable replay must be certified on the actual route before
activation. No DMB endpoint, issuer, authenticated principal, callback or active
subscription is available. Offline signatures prove a contract only. Ordinary
ChatGPT conversations are not background workers. A persistent Brain fallback
requires separate installation/cost approval and retains the same gates.

No WhatsApp/email activation or notifications occurred. Delivery acknowledgements
cannot approve actions. Real HEG approvals require authenticated identity and the
exact request, scope and expiry. Preserve the separate DAT Temporal milestone;
the existing Temporal-compatible contracts are unchanged.

## Durable evidence and next actions

The [matrix](evidence/phase9-20261013/CERTIFICATION_MATRIX.md),
[artifact hashes](evidence/phase9-20261013/ARTIFACT_MANIFEST.json) and
[minimum human prerequisite](../decisions/REQUEST-0007.md) bind this milestone.
All 100 preserved tests and 17 separate fixture tests pass. Original 84-test,
100-cycle and 1,099-execution evidence is unchanged and remains scoped to the
original trusted shadow verifier, never recast as actual Codex execution.

Continue safe isolated contract/documentation work. Once the existing non-admin
connection is supplied, verify its actual token before running the procedure.
Retain **BLOCKED** for single-real-worker certification until all required gates
pass, and keep full DMB certification blocked independently.
