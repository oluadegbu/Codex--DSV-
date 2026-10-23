# Bounded dedicated DEMO canary — DRAFT, NOT AUTHORIZED

No actual MT5 adapter/account isolation is independently certified yet. These are
two distinct future approval gates. Do not execute from this document or infer
permission from passed fixtures. Live accounts remain prohibited.

## Gate 1: explicit read-only broker preflight approval

Only after the operator identifies an existing dedicated demo account and isolated
terminal/data-folder pair privately, request approval for a **single supervised,
at-most-10-minute read-only session** to that exact account/server. No production
terminal, credentials, profile, account or execution authority may be reused.
If account enrollment, new credentials, installation or deployment is needed,
obtain separate approval for that action; none is granted now.

Proposed wording:

> Approve one supervised read-only preflight on the privately specified dedicated
> DEMO account/server and isolated terminal/build, for at most ten minutes. Permit
> terminal startup and operator-managed authentication only for that named session;
> no credentials are exposed to chat, source control or research logs. Verify
> account identity, broker-reported DEMO mode, currency, contract/lot/stop/margin/
> session/fill specifications, current quotes, account flatness and isolated
> controls. No order placement, modification, cancellation or position closing.

Approval must identify account/server/terminal exact private values (digest only
in public evidence), expiry, reviewer and reviewed adapter build. The preflight
interface must be independently verified read-only. Fail on REAL, CONTEST,
UNKNOWN, mismatch, account switch, stale quotes, existing unrelated positions,
unexpected EAs/services or missing contract evidence. Do not fall back to another
account, default terminal or cached credentials. Record no passwords/tokens.

Required evidence before Gate 2: independently reviewed adapter source/hash;
dedicated demo account/terminal identity and isolation; disabled default routing;
fresh per-action account verification; authenticated one-use approval mechanism
not reconstructed from old journals; durable intent/duplicate control; exact SL/TP
and retcode handling; gap/partial/unknown-result tests; reliable independent local
watchdog, emergency control and flat reconciliation. Existing DAT risk/kill controls
must be preserved and the stricter applicable bound enforced, never relaxed.

## Gate 2: fresh one-entry DEMO-only canary approval

Choose **one** verified broker EURUSD contract, exact suffix specified by preflight.
Candidate scope below is a proposal, not assumed broker support or a default grant:

| Item | Proposed strict envelope |
|---|---|
| Purpose | NON-EDGE / EXECUTION TEST only |
| Account | Exact independently verified dedicated DEMO login/server; no fallback |
| Instrument/direction | One approved EURUSD symbol, BUY only for this first canary |
| Entry | At most one accepted market entry; no pending order or retry/re-entry |
| Size | Exactly 0.01 lot only if actual verified minimum/step permits; otherwise abort |
| Protections | Valid attached SL and TP on initial request; no later widening/removal |
| Risk budget | At most USD 1 modeled loss including verified fees/spread/slippage; if not feasible at minimum volume/stops, abort rather than increase budget |
| Position cap | One owned exposure; dedicated account verified flat first |
| Duration | Maximum 30 seconds intended holding; ten-minute approval window for entry |
| Routing | Fresh one-use grant bound to account/server/symbol/volume/protections/build/expiry |
| Exit | Attached protective exit or at most one explicitly authorized owned close intent; no blind retry on ambiguous acknowledgement |
| Modifications | None for this first canary; no other order/account/settings mutations |

Final price/protection distances cannot be guessed here. Build a concrete reviewable
request after preflight using verified symbol/fee/stop rules and recent quotes;
if it cannot satisfy the envelope, do not trade. Submit once only after fresh
identity, data, risk, approval and emergency checks all pass.

Planned loss is **not a guaranteed maximum**: gaps, rejection and disconnect can
prevent expected closure. Broker-side protections and the watchdog must have
independent evidence. A 30-second plan is not proof of flatness under outage.

Risk-reducing cleanup of the **identified owned position** must be explicitly
included in approval and remain available until verified flat; entry expiry must
not strand an owned position. Read-only reconciliation is bounded and may continue
after entry is disabled. If close status is unknown, do not resend; inspect actual
orders/deals/positions and escalate to the supervising operator. Do not close
foreign positions or use a different account to compensate.

Completion evidence: initial and final account/position/order/deal snapshots,
intent/receipt/protection/exit IDs, costs, timestamps, duplicate count, stop state,
and actual flat confirmation. Failure to prove flat means **UNRESOLVED**, not PASS.
Archive private evidence separately; publish only sanitized execution mechanics.
No P&L inference, edge claim, live promotion or further canary authorization follows.

## Approval status now

**Gate 1 NOT REQUESTED/NOT APPROVED. Gate 2 NOT REQUESTED/NOT APPROVED.**
No terminal start, broker session, credential access or DEMO/live order occurred.
