# REQUEST-0007 — Existing non-admin worker execution connection

STATUS: OPEN
BLOCKING: NO
HARD_GATE: YES

Independent safe shadow development continues. Phase 9 real-worker certification
is blocked by execution prerequisites, not GitHub publication permission.

## CONTEXT

Phase 9 requires an actual standalone Codex turn under the existing DirectiveCodex
identity, cancellation/restart and OS-enforced canary read/write separation.
No Administrator token may be used to launch development workers or manufacture
the non-admin account's token. No account or privileged ACL change is authorized.

## EVIDENCE

`docs/evidence/phase9-20261013/WINDOWS_IDENTITY.json`: existing DirectiveCodex is
enabled and not an Administrators member, but disconnected session 3 has no
connected execution context. Current executor is Administrator/High.

`CODEX_INVOCATION.json`: actual Linux UID1000 CLI exits during read-only runtime
startup before any turn. `LOCAL_VERIFICATION.json`: cross-root same-UID canary
read/write succeed. `SANDBOX_DIAGNOSTIC.json`: managed Linux sandbox command
cannot initialize its socket boundary; probes never run. Prior tests/certs remain
intact. Draft PR #1 publication and baseline independent CI are PASS.

## OPTIONS

1. Reconnect the existing DirectiveCodex session on WIN-HQAAFGGU1AM and supply an
   existing foreground remote execution connection running as that user. Verify
   normal existing Codex login/runtime and pre-provisioned sandbox from that token.
2. Provide another already authorized non-elevated development environment with
   supported normal Codex authentication, writable runtime state, and an existing
   isolated canary boundary. This can certify that environment; it cannot certify
   the Windows DirectiveCodex gate by inference.
3. If the existing environment cannot supply read/write separation, review a
   specific disposable confinement proposal separately before any installation,
   new identity, privileged ACL/security change or cost. No such change is made
   or pre-approved by this request.

## RECOMMENDATION

Minimum human action now: option 1, providing the existing non-admin foreground
connection. Do not send credentials. No new GitHub grant is needed. After token
verification, continue the bounded procedure in `docs/DMB_PHASE9.md`. If setup
requires installation or security changes, submit the exact scoped proposal
before proceeding; do not weaken managed sandbox policy to achieve a PASS.

## IMPACT

Single-real-worker certification stays BLOCKED. Actual Windows process integrity,
Codex authentication/runtime, task completion, cancellation and restart remain
NOT TESTED. Existing account membership alone is insufficient. Legacy unelevated
Codex does not support denied read paths, so an actual existing stronger boundary
must also be demonstrated for the isolation gate. Full DMB certification remains
blocked for separate authenticated delivery and external-integration gates.
This request refines REQUEST-0003/0005/0006 without rewriting their historical
evidence; their GitHub 403 portions are historical and resolved for this connector.
