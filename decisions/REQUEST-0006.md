# REQUEST-0006 — Phase 8 external certification prerequisites

STATUS: OPEN
BLOCKING: NO
HARD_GATE: YES

## CONTEXT

Full DMB certification now explicitly requires real external integration and
isolation evidence. Local safe development continues; no external authorization
is inferred from local PASS, synthetic signatures or old milestone records.

## EVIDENCE

See docs/DMB_PHASE8.md, docs/evidence/phase8/CERTIFICATION_MATRIX.json and
portfolio/RECONCILIATION.phase8.v1.json. Existing 84 tests/100 cycles/1,099 worker
executions remain preserved. Current 100 tests include 16 new offline fixtures.
Fresh GitHub writes fail403; installation scope cannot be inspected by the
available connector. Windows remains Administrator/high integrity. Actual Codex
startup fails read-only runtime initialization. Same-UID cross-root canary reads
succeed. No actual remote Brain/HEG route has been provided or certified.

## OPTIONS

1. Continue safe offline shadow development and keep all external gates blocked.
2. Operator reviews the existing GitHub installation for this exact repository
   and Contents write, provides an existing non-admin DirectiveCodex session and
   supported Codex runtime, plus isolated boundaries for synthetic denial probes.
3. Supervisor provides exact authorized external project evidence locations,
   remote Brain endpoint/identity/subscription references, and approves a bounded
   real HEG shadow test with exact channel, destination, consent, request scope,
   identity and expiry. Persistent installation/costs need their own explicit scope.

## RECOMMENDATION

Proceed with option 1 automatically. Minimum immediate human action is to review
and, if needed, restore the existing GitHub app's single-repository Contents-write
authorization. Keep all other grants unchanged; do not send tokens. Complete
option 2 before worker certification. Prepare option 3 using existing approved
interfaces; do not activate it from a synthetic fixture result.

## IMPACT

Full certification stays BLOCKED until real gates pass. No approval is needed
for the committed local contract lab or continued offline tests. This request
records material authorization prerequisites; it authorizes no accounts,
services, new credentials, elevated sessions, funds or production changes.
The original verified Git bundle is preserved. Publication of this request is
also blocked by the same GitHub authorization failure.
