# Independent runtime and future durable-workflow boundary

## Implemented now

The offline Python state machine runs synchronously with explicit synthetic quote
bytes, virtual time and two private local SQLite ledgers. One account owner,
sequential calls only. No scheduler, daemon, network transport, broker module,
terminal, secret lookup or dependency on chat/MCP/control products.

- `Controller`: admission checks, durable signal identity/intents, risk decisions,
  recovery, stop latch and local audit.
- `SimBroker`: separate synthetic acceptance/fill/position/cash state, deterministic
  availability/rejection/ack-loss fixtures. Availability is a Boolean, not a connection.
- Existing `PassiveCollector`: exact source/schema/symbol, replay, age, spread and
  tick-grid gate. Existing Decimal/Contract validators retain their original code.
- Explicit clock: no wall-time reads or random signals in decision code. A test
  driver supplies time and events. This is not an unattended execution worker.

The offline test strategy returns one stable NON-EDGE / EXECUTION TEST signal.
Repeated default calls deduplicate or conflict-halt if the payload changed. No
market thesis, martingale, grid, averaging or autonomous re-entry. Default lot is
the minimum synthetic 0.01 only if affordable; actual broker minimum is unknown.
Execution-test arithmetic must never be used to promote a live strategy.

## Future adapter contract — absent, disabled, approval-gated

Do not pass a real adapter into the current controller; it deliberately rejects
everything except the exact in-process SimBroker. A later separately reviewed
implementation must preserve durable intent-before-effect and add independent
admission/authorization, account pinning and real transport semantics. A JSON
configuration change cannot turn this fixture into a broker client.

Required operations: read verified account/contract/quote snapshots; read orders,
positions and deals; reconcile by local intent plus actual broker order/deal/
position identifiers; perform an individually approved bounded mutation. Account
identity must be verified before each mutation and after effects; no account
selection/autologin/fallback within a mutation path. Do not treat a broker comment
or magic number as an authenticated exactly-once key.

Official [trade requests](https://www.mql5.com/en/docs/constants/structures/mqltraderequest)
carry operation, volume, price, SL/TP, fill/time policy and order/position fields.
[Server retcodes](https://www.mql5.com/en/docs/constants/errorswarnings/enum_trade_return_codes)
distinguish placement, completion, partial completion, rejection and connection/
timeout conditions. The fixture's OPEN/REJECTED states do not implement that full
asynchronous lifecycle. Missing/ambiguous effects must quarantine the intent and
trigger reads, not resubmission or adoption of unrelated exposure.

## Temporal preparation — not a prerequisite or activated integration

Later workflow inputs: immutable command ID, exact private account identity digest,
approved operation/risk envelope, bounded validity window, fixture/transport type,
contract version and recorded quote/time snapshot. No credentials in history.

Workflow steps: persist intent → validate admission snapshot → one effect activity
attempt → persist receipt or UNKNOWN → reconcile actual order/deal/position state →
track protections → bounded owned cleanup → attest flat. Rejected/stale/conflicting
approval denies entry. Record decisions and IDs, not opaque broker credential state.

Non-idempotent broker effect activities must initially use **one attempt**, with no
generic retry/backoff across an ambiguous result. Read-only reconciliation may
retry within a bounded deadline. A retry policy is not broker idempotency. A future
single-account coordinator needs ownership/fencing and a dedicated account;
multi-worker exactly-once effects are not certified by local SQLite.

Emergency stop must latch durably independent of workflow/chat availability. A
dedicated local supervisor/watchdog and broker-side SL/TP must remain effective
through process or connectivity loss. No such production service is deployed in
Phase 7.0. A future deployment requires its own authorization and operational proof.

Desktop Commander, ChatGPT, DMB, DSV and OpenClaw are optional human interfaces,
never dependencies for position safety, reconciliation or shutdown. No outage of
those products may implicitly resume routing or remove an admission control.
