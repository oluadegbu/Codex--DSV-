# REQUEST-0005 — DMB live portfolio and isolation certification boundary

STATUS: OPEN
BLOCKING: NO

Full DMB certification is blocked; independent local shadow development is not.
HARD_GATE: YES

## CONTEXT

The Directive Master Brain extends BHB/HEG to 13 portfolio records and three
concurrent trusted shadow labs. Existing records do not establish access to
actual DAT Futures, DAT MT5, DPM, DSV, Pulse, Temporal or VMA/DAR repositories.
No production integration is authorized by an unknown repository or old PASS.

## EVIDENCE

- Registry: portfolio/REGISTRY.v1.json. Unknown workspaces/repos remain null.
- Local certification: docs/evidence/DMB_CERTIFICATION.json and DMB_TESTS.log.
- Three non-admin uid1000 labs have distinct paths and pinned commits; they share
  an OS identity and lack hostile-code confinement.
- REQUEST-0002: GitHub writes still 403 on fresh branch creation.
- REQUEST-0003: Windows remote identity/access and actual Codex runtime blocked.
- REQUEST-0004: authenticated remote Brain and live providers not activated.
- Simulated HEG approvals are not real human authentication or authority.

## OPTIONS

1. Continue trusted local shadow development, preserving unknown external states.
2. Supervisor supplies verified repository/workspace/certification references
   and approves an independently certified non-admin worker environment.
3. Later approve separately scoped provider/remote MCP/Temporal service changes
   after reviewed deployment and authenticated approval-binding evidence exist.

## RECOMMENDATION

Continue option 1 now. Use option 2 to establish exact project identity and a
supported worker runtime. Keep option 3 behind separate explicit approvals.
Do not reuse credentials, install services, incur costs, alter production
controls or elevate privileges to clear a certification gate.

## IMPACT

DMB local shadow evidence can pass, but the required complete DMB SHADOW
CERTIFIED label cannot be issued yet. Existing DAT Temporal Integration approval
is preserved; implementation and deployment are not inferred. No routine
implementation action waits on this request. The request remains local until
GitHub integration write access permits publication.
