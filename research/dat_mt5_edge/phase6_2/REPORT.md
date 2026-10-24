# DAT MT5 — Phase 6.2 Parallel Research Readiness

**Recorded:** 2026-10-19. **Mode:** RESEARCH ONLY / SHADOW / NON-TRADING / FAIL-CLOSED.
**Disposition:** Offline code prepared and locally tested; dataset certification **BLOCKED**;
live forward shadow **NOT STARTED**; trading authority **NONE**.

This update is additive to [Phase 6.1](../phase6_1/REPORT.md). Earlier
strategy definitions, sealed holdouts and Phase 3–6.1 evidence were not
overwritten. All files created or updated by this phase are isolated under
`phase6_2/` and `tests_phase6_2/`. No changes to main, DMB PR #1, production
DAT, MT5, user accounts, broker credentials, risk controls or terminals.

## Workstream A — rights and data inventory, repo evidence only

Read earlier entitlement/acquisition reports and the existing approved
file/export architecture; **did not** open live caches, credentials, MT5,
accounts or trading terminals. Historical manufacturer/provider claims do not
prove the requested organizational use or current coverage.

| Candidate | Existing recorded finding | Phase 6.2 decision |
|---|---|---|
| **EURUSD/GBPUSD** | Dukascopy advertises free historical CSV/ticks but DAT organizational database retention and bounded automation permission unresolved. Earlier 3-day EURUSD canary is historical only. | **NOT CERTIFIED**; ask for written applicable rights or supply already licensed primary paired quotes. |
| **XAUUSD (Gold)** | Dukascopy/HistData historical claims and existing broker-cache names are documented; exact provider↔broker mapping, size, units and complete BBO are not verified. | **NOT CERTIFIED**; source quotes and contract/swap metadata required. |
| **BTCUSD** | Existing public Bitfinex OHLCV proxy (2017–18) and one free first-of-month BTC quote sample from Tardis/Kraken; no continuous multiyear certified BBO. | **NOT CERTIFIED**; sample/proxy cannot substitute for true bid/ask history. |
| **Tickstory Lite** | Phase 6.1 reviewed vendor EULA and found personal-use scope unsuitable for DAT organizational research without explicit grant. | **RESTRICTION PRESERVED**; no installation or purchase. |
| **HistData / FXCM** | Strategy-testing description / historical free feeds exist but original source rights and DAT organizational retention/publication scope unresolved. | Secondary candidates only; no automatic certification. |
| **MT5 Market Watch built-in export** | Existing Phase 5 read-only documentation describes Bars/Ticks Request and CSV Export, subject to what server actually offers. | Capability documented, **not exercised**; no session or server history/fees inspected. |

No research-licensed, complete, reviewed 2021–2026 primary dataset was
located in the examined repository evidence. This is **not** an exhaustive audit
of every external provider account or local disk: neither was accessed.
Permission draft: [PERMISSION_REQUEST_DRAFT.md](PERMISSION_REQUEST_DRAFT.md)
(unsent, operator review only). No vendor contact, credentials, signup,
subscription, costs or external data acquisition.

## Workstream B — offline research engine additions

New `phase6_2/readiness.py` is a pure standard-library module. It implements:

1. **Deterministic walk-forward declarations:** explicit half-open UTC train/test
   ranges, strict chronology, no overlapping test folds, enforced embargo
   argument and sealed final holdout fence. The 2026-01-01 through 2026-09-30
   final holdout remains intentionally inaccessible to development folds.
2. **Minimum sample and calendar coverage:** defaults ≥100 hypothetical trades
   overall, ≥20 per fold, ≥60 active UTC days and ≥99% independently specified
   expected quote/calendar coverage *in each fold and in total*. Source-proof
   flag is required; missing or off-calendar quote records fail closed.
3. **Session and regime robustness:** predeclared Asia/London/New York and
   Trend/Range/Volatile slices; participation gates; full per-trade
   scenario-matrix completeness; missing, nonpositive or undersampled
   session/regime × scenario cells fail the exploratory screen.
4. **Cost sensitivity:** conservative side-correct bid/ask entry/exit,
   tick-grid outward rounding, spread 2×, slippage 1 vs 2 ticks,
   commission 2×, financing 2× and combined stress. Contract tick value,
   PnL currency and per-side charges are explicitly required. Financing
   nights are explicit instead of inventing broker rollover terms.
5. **Clock/contract restrictions:** aware UTC or fixed EST_NO_DST only;
   ambiguous timezone/naive-UTC denied. Crossed or off-tick quotes and
   unverified hypothetical contract specs denied.

These are **research readiness and exploratory screening functions**, not a
production backtester, independently validated strategy, proof of a
licensed/verified contract, dependence-adjusted inference or edge certificate.
No strategy performance is computed on synthetic data. Functions always
return `edge_certified=False` and `execution_authority=False`.

## Workstream C — prepared, not connected

New `phase6_2/shadow.py` composes the existing **quote-only**
`phase4.collector.PassiveCollector` and a local SQLite journal.
Transactions atomically enforce sequence/timestamp ordering and raw-payload
deduplication, with persistent restart state. Source identity, explicit
symbol, tick size, spread bound and age policy are bound to the journal.
Stale/future, duplicate, off-grid, crossed or unapproved messages are rejected
before commit; a missing/corrupted identity record fails closed.

Limitations: SQLite integrity does not independently authenticate an exporter
or protect against arbitrary filesystem tampering. Real streaming timing,
network partitions, high concurrency, production restart/load and broker quote
fidelity have **not** been evaluated. No real quote feed has been connected;
no terminal, scheduled job, DEMO account or order path exists in Phase 6.2.

## Verification evidence

Locally exercised in an isolated Python 3.13.5 standard-library workspace,
against **identical Git blob content** published on PR #2:

```text
cd research/dat_mt5_edge
python -m unittest discover -s tests_phase6_2 -q
Ran 32 tests — OK

python -m compileall -q phase6_2
No syntax errors reported
```

Relevant exact Git blob SHA identities:
- `phase6_2/readiness.py`: `487a6275bf755245fd44e733fc76ebc09f6766dd`
- `phase6_2/shadow.py`: `8091e3e9a3defb75f5e03fe62e5bc72753c0b77a`
- `tests_phase6_2/test_readiness.py`: `9b8457e1e0d2695a3948781ed0ec3527aec366df`

Fixture coverage includes monotonic walk-forward ordering and embargo,
sealed holdout, wrong calendar, missing trade/session/regime samples, complete
and incomplete stress grids, adverse bid/ask math for long and short,
financing, contract verification, invalid/future quotes, duplicate JSON keys,
stale rejection, persistent restart duplicate suppression, and malformed
journal identity. Synthetic eligibility assertions exercise control paths
only: **they are not actual data certification or a profitable-edge finding**.

Prior Phase 6.1's 84-test historical evidence is **not relabeled as 6.2**.
Previous Phase 3–6.1 certifier outputs were not rerun in this isolated
partial repository copy. Existing result files were not edited, compared
against new data or passed through a strategy optimizer.

## Remaining hard gates

1. **Operator choice:** supply an already licensed paired bid/ask primary
   export and proof of rights **OR** review/approve a permission message
   to a verified official provider channel. This draft is currently unsent.
2. **Provider response:** confirm organizational internal storage,
   normalization, backtesting, permitted automation/rate limits and
   aggregate-only publication; **Tickstory Lite remains off** absent
   explicit compatible permission.
3. **Source evidence:** immutable source/raw hashes, actual coverage,
   independent expected session calendar, UTC/broker-clock/DST provenance,
   exact symbol/contract IDs, tick size/value, lot/quantity rules,
   quote units and actual fee/slippage/financing schedule.
4. **Certified import:** run existing Phase 4 reviewed-bundle gate in
   offline/cloud context, then only after admissibility freeze 2024
   development and 2025 chronological walk-forward design. Do not touch
   2026-01-01–2026-09-30 final holdout until a separately authorized
   independent final validation.
5. **Forward shadow:** separately approve an exporter/feed provenance and
   a proper isolated quote-only connection. Any account login, terminal
   startup, SDK, actual quote streaming, installation, payment or
   production change remains outside this directive.

**Final status:** PHASE 6.2 OFFLINE RESEARCH DEVELOPMENT COMPLETE /
32 SYNTHETIC SOFTWARE TESTS PASS / CERTIFIED DATASETS 0 /
FORWARD SHADOW INACTIVE / ORDER INTERFACES DISABLED / DRAFT PR #2 UNMERGED.
