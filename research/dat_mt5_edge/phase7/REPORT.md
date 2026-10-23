# DAT MT5 Phase 7.0 — offline CFD execution mechanics

2026-10-23. **OFFLINE / RESEARCH / FAIL-CLOSED.**
**Offline result: PASS within the declared synthetic model. Actual MT5 DEMO
execution readiness: NOT CERTIFIED. Live trading: PROHIBITED.**

The isolated suite passes **88 tests: 56 new lifecycle tests and 32 reused Phase
6.2 tests**. No MT5 terminal, broker SDK, credential, account connection, real quote
feed or broker order was used. No profitability, edge or historical-data
certification is claimed. The historical-data workstream remains separate.

## Existing capability audit and reuse

Scope: the current PR #2 public research tree and previously recorded recovery
inventory, not a fresh inspection of private VPS runtimes or broker accounts.
[BACKUPS.md](../docs/BACKUPS.md) records missing original execution/controller/risk/
authorization source and primary audit chain in the inspected recovery scope.
Historical descriptions do not establish current runnable capability or fresh
authorization. No execution authority is reconstructed from those descriptions.

| Capability | Existing evidence | Phase 7.0 treatment / remaining gap |
|---|---|---|
| MT5 terminal integration | Earlier cache/export documentation; no verified runnable original adapter recovered | **No terminal integration activated or added.** Current terminal/account connectivity unknown |
| Broker adapter/account selection | Original implementation not established in available source | Add fixture-only SimBroker; exact synthetic account/server/type/transport checks. Real adapter absent |
| Market data | Phase 4 PassiveCollector, Phase 6.2 ShadowJournal | **Reuse PassiveCollector directly**; keep durable quote journal unchanged. Synthetic supplied bytes only; no exporter/feed |
| Order submission/ack | Backtest hypothetical fills exist, not a broker order lifecycle | Add durable intents, fixture acknowledgements/rejections and unknown-result reconciliation |
| SL/TP | Research stop/target models in edge/core.py | Preserve historical backtester; add atomic fixture protection attachment, automatic stop/target closure and tighten-only management |
| Sizing/risk | Phase 6.2 Decimal/Contract validators and hypothetical cost arithmetic | **Reuse Contract and Decimal validators**; add lot-grid sizing and local lifecycle exposure/daily-loss gates |
| Duplicate suppression | Durable quote deduplication already exists | Reuse principle, not the quote schema for orders; add persistent signal/client identity and conflict halt |
| Position reconciliation | No verified recovered live engine | Add two independent local fixture ledgers, owned-order comparison, unresolved intent quarantine |
| Restart/disconnect | Phase 6.2 SQLite quote replay handling | Keep existing implementation; add order/position restart scenarios, journal binding and ack recovery |
| Emergency stop/audit | Existing production controls must remain unchanged; original execution chain unavailable | Add separate persistent **fixture-only** stop latch and transactional event chains. No production changes |

Existing research, quote collector, replay journal, strategies, source data,
holdouts and earlier results are unchanged. New work is confined to `phase7/`.
The old OHLC backtester was not replaced by the lifecycle simulator.

## Implemented local lifecycle

`Controller` accepts only the exact in-process `SimBroker` type. There is no broker
transport selection, SDK import, network client, subprocess, credentials API or
dynamic plugin. Accounts must be explicit synthetic `FIXTURE-` / `OFFLINE-`
identities of type DEMO; real/unknown/type/server/account/transport or contract
mismatch fails closed. These are synthetic account checks, **not independent
verification of any actual demo account**.

Each intent is persisted before fixture dispatch. Duplicate IDs return the saved
state without resubmission; changed payloads halt. A lost acknowledgement is
resolved by comparing the actual fixture ledger to the saved intent. Missing or
conflicting results are quarantined, never retried blindly. Each process start
requires explicit fresh-market reconciliation before new entries. Missing or
incomplete existing state cannot silently initialize a new account/journal.

Market and pending limit/stop orders support both directions. Buy entry uses Ask
and sell entry Bid, with one adverse tick in the fixture; limit fills are capped at
their limit. Long exits use Bid and short exits Ask with adverse slippage. SL/TP
must be positive, tick-aligned and valid relative to actual fill. Invalid protection
at a gapped pending fill rejects it without an unprotected position. Pending
expiry and position holding limits use the explicitly supplied synthetic clock.

Stop tightening is journalled before dispatch. Unknown protection acknowledgements
can recover only when the actual fixture request exactly matches the intended
change. An unapplied/ambiguous change is not automatically resent. Foreign exposure
is not adopted or explicitly closed by the controller.

Risk tests cover min/step/max lots, downward rounding, spread/slippage/commissions,
per-trade risk, aggregate risk, pending position reservations, equity/daily-loss
checks and post-fill risk escalation. Defaults are deliberately tiny **synthetic
fixtures**, not changes to DAT production limits: minimum 0.01 lot, maximum one
open-or-pending exposure, nominal 1 USD per-trade and daily-loss limits. Default
test signals use minimum size only. All fixture contract economics are invented
test units with explicit labels, not broker specifications.

A daily-loss breach latches the stop, cancels owned pending orders and attempts
owned exposure reduction. It never automatically resumes, including next day or
restart. Stop persistence precedes cleanup. Disconnect/stale prices can prevent
flattening; unresolved exposure remains visible and blocked until fresh verified
fixture data/reconciliation. **A stop is not a guaranteed loss cap:** the gap-loss
test deliberately exceeds the nominal daily threshold and verifies entry shutdown.

## Verification evidence

Run from `research/dat_mt5_edge` using existing standard-library Python:

```sh
python -m phase7.certify
```

[Machine-readable results](results/offline_certification.json) contain every test
ID, source hashes, fixture policy/specification and preservation evidence.
The certificate generator checks all **113 prior public Git blobs** unchanged.
Two identical fixture runs compare order/effect event-chain heads and cash;
two complete certificate runs produced byte-identical JSON on the same Python
version (SHA256 `d29b39e124ec0cd2eb06205f2849a2ae6793c1de0a5cec3d716a02a48447c807`).
These checks are engineering evidence, not independent reviewer approval.

| Scenario group | Evidence |
|---|---|
| Market/pending | Buy/sell market; all four limit/stop direction combinations; limit price cap; expiry; invalid pending side |
| Protections | Initial attached SL/TP; side-correct exits; invalid/off-grid/zero/NaN stops; tighten; widening refusal; changed/unknown protection recovery |
| Risk | Cost-inclusive lot step; unaffordable minimum; aggregate risk; pending reservations; daily budget; post-fill risk breach; gap loss and persistent halt |
| Idempotency | Duplicate after restart; changed-ID payload halt; terminal rejection suppression; lost ack; unresolved pre-dispatch no-retry |
| Recovery | Startup reconciliation; quote-commit crash; replayed recovery with no duplicate fill; missing/config-mismatched/incomplete state refusal |
| Data/account safety | Stale/future/crossed/off-grid/replayed/wide quotes; source mismatch; backward time; real/unknown account modes; identity/contract change |
| Emergency | Fresh cleanup; disconnected/stale unresolved cleanup; pending cancellation; next-day/restart stop persistence; unowned exposure refusal |
| Isolation | Offline import allowlist; network/subprocess prohibition during a lifecycle; deterministic fixture event chains; existing Phase 6.2 checks |

## Dedicated demo isolation assessment

[demo_isolation.json](demo_isolation.json) is a **design-only disabled profile**:
empty actual-demo allowlist, no startup, credential, broker connection, demo order
or unattended authority. It is not a switch that enables routing; no connected
adapter exists in this phase. Offline fixture identity is not a broker login and
cannot grant access to a demo or live account.

Future admission requires an independently verified dedicated account, exact
server/login binding, broker-reported DEMO mode and contract/risk evidence. Never
infer demo status from a server/account name. Reject REAL, CONTEST, unknown or
changed identity; no fallback or live credential/configuration reuse. See official
[account properties](https://www.mql5.com/en/docs/constants/environment_state/accountinformation).
All actual credentials/identifiers stay operator-managed and private. New
credentials/enrollment require separate authorization, not this offline directive.

## Remaining security and operational blockers

- A reviewed real MT5 adapter and independently verified terminal/demo isolation
  do not exist in this available implementation. No actual read-only account
  verification, account-switch race controls or broker-enforced entitlement proof.
- Real margin, currency conversion, netting/hedging, FIFO, partial fills, async
  broker events, reconnect/backfill semantics, stop/freeze/fill modes, symbol
  permissions and actual server retcodes are **not certified by this simulator**.
  Full atomic fills are an explicit fixture assumption. Real prices are not
  guaranteed to fill within deviation or a loss budget.
- Holding expiry here runs on supplied quotes. An actual independent watchdog,
  stale-feed handling, terminal/process isolation, operator escalation and flat
  verification under disconnect must be demonstrated before a canary.
- SQLite is a single-writer local model, not multi-host exactly-once delivery.
  Event hashes detect event edits/corruption but do not authenticate an external
  broker or resist coordinated state edits/tail rollback. No original DMEN chain
  or signing/approval system is restored.
- No actual broker prices, specifications, historical data, financial edge or
  organizational data license is verified. This does not block the synthetic
  mechanics exercise but remains relevant before market research/forward use.
- No independent review has certified the real control path. Unit-test success
  cannot grant a demo order, runtime deployment or live authority.

## Runtime and next phase

[RUNTIME.md](RUNTIME.md) specifies a standalone local controller/ledger/clock and
future Temporal boundary. Initial offline tests need none of Desktop Commander,
ChatGPT, DMB, DSV, OpenClaw or Temporal. No service or unattended worker was installed.
Temporal may later schedule durable decisions and reconciliation; retries must
never blindly replay a non-idempotent broker submission.

Recommended Phase 7.1: independently review the offline lifecycle and controls,
define/test the missing adapter semantics using offline recorded/fixture events,
and prepare actual demo isolation evidence. Do not activate the adapter or terminal.
Then obtain **separate explicit approval for read-only broker preflight**, followed
by **fresh approval for one bounded demo canary only after admission controls pass**.
[DEMO_CANARY_APPROVAL_DRAFT.md](DEMO_CANARY_APPROVAL_DRAFT.md) gives exact scope and
abort/cleanup rules. It is not executable authorization and no canary ran.

**Final: offline modeled lifecycle VERIFIED BY TESTS; actual demo NOT CERTIFIED;
live PROHIBITED; real execution authority OFF; no merge/main/production changes.**
