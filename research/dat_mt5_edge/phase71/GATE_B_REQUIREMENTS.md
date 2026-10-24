# Gate B — independent future order-canary approval, NOT APPROVED

Gate A authorizes only inspection. A successful Gate A result cannot enable the
Phase 7.0 simulator, modify its type guard, issue a trading credential or authorize
an order. There is no connected order adapter in Phase 7.1.

Before even requesting Gate B, retain independently reviewed Gate A evidence and:

1. Implement/review the missing real order adapter and its actual asynchronous
   acknowledgement/retcode, partial-fill, margin, netting/hedging, stop/freeze,
   account-pin and unknown-result semantics. Keep default routing OFF. No blind
   retry or authority reconstruction from historical records.
2. Independently verify dedicated DEMO isolation, exact identity and contract,
   current risk/kill controls, broker-side SL/TP, local watchdog, durable one-use
   authorization, journaling, single-account ownership and actual flat recovery.
   Account- or terminal-name inference and fixture success are insufficient.
3. Independently resolve server clock/quote freshness, actual costs, minimum volume/
   margin/fill rules and the feasibility of the exact proposed risk envelope.
   A reported zero stop level or estimated margin does not prove order acceptance.
4. Obtain a **fresh human approval** for one exact reviewed mutation envelope.
   Trading-capable authentication, if needed, is a distinct privilege from the
   investor session and must be explicitly authorized. No live credentials or
   account may be reused. Do not switch permission modes within Gate A.

## Proposed separate Gate B wording, after those conditions pass

> Approve one supervised NON-EDGE / EXECUTION TEST canary on the exact privately
> identified dedicated DEMO account/server/terminal/build. Permit at most one
> EURUSD BUY market entry, exact verified symbol and 0.01 lot only if supported,
> valid initial SL/TP and at most USD 1 modeled all-in loss or abort. No risk or
> volume increase to make the order feasible. Maximum one owned exposure, intended
> holding at most 30 seconds, no re-entry, blind retry, pending order or protection
> widening. Entry must occur within the ten-minute one-use approval window. Include
> at most one owned close intent if protective exit has not already closed it,
> read-only reconciliation until actual flat confirmation and operator escalation
> on an unknown result. No foreign position cleanup, live routing, unattended
> operation, production or security-permission changes.

Use the stricter of the final approval and existing DAT risk/kill controls. Final
SL/TP/prices/costs must be concrete and reviewed after actual contract evidence;
no broker price or parameter is invented here. Gaps can exceed planned loss and
connectivity loss can prevent timely closure. If flatness cannot be proven, report
UNRESOLVED and stop further entries, not PASS or automatic retries.

This is a **separate future request**, not part of Gate A and not requested now.
See [the preserved Phase 7.0 draft](../phase7/DEMO_CANARY_APPROVAL_DRAFT.md).
