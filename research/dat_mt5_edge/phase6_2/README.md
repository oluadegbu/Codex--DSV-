# DAT MT5 Phase 6.2 — parallel research readiness

**Offline / research-only / hypothetical / fail-closed.** No MT5 terminal,
broker client, account, order, SDK, service/scheduler or external quote-download
dependency is imported or started. Phase 3–6.1 evidence, strategies, frozen
historical outputs and the 2026 sealed holdout remain untouched.

See [Phase 6.2 report](REPORT.md) and the
[unsent provider permission draft](PERMISSION_REQUEST_DRAFT.md).

## Reproduce the software checks

From `research/dat_mt5_edge` using Python 3.12+ (standard library only):

```sh
python -m unittest discover -s tests_phase6_2 -v
python -m compileall -q phase6_2
```

The isolated software fixtures validate 32 cases. All test data are synthetic
and are prohibited from being cited as evidence of any market edge, profitability
or contract validity. Historic prior-phase suite results are **not** counted as
new Phase 6.2 executions.

## Modules

- `readiness.py`: explicit UTC/fixed-EST conversion, immutable chronological
  fold declarations, minimum embargo and sealed holdout fence, per-fold coverage
  versus an **independently reviewed expected trading calendar**, minimum
  active-day/trade/session/regime gates, exploratory robustness across every
  predeclared cost-sensitivity scenario, Decimal side-specific bid/ask hypothetical
  fill arithmetic, commission, slippage, spread and explicit financing-night
  inputs. No simulated edge is ever certified by these functions.
- `shadow.py`: consumes bytes with the existing `phase4.collector.PassiveCollector`
  schema; an isolated SQLite journal atomically retains source/symbol
  identity, sequence, clock, prices and raw message digest. Replayed,
  stale, future, crossed, off-grid or malformed quote fixtures are rejected.
  Existing or corrupt journals cannot silently reset from missing identity.
  Create a new journal only with `initialize=True` in a new isolated research
  directory; reopen with the default `initialize=False`.
- `tests_phase6_2/test_readiness.py`: chronological, structural, pricing,
  permission-assumption and crash/restart-software regression checks.

## Hard separation

`research_gate(..., evidence_certified=True)` and
`Contract(...,verified=True)` are only caller-provided flags for an
**already independently reviewed** dataset/contract. They do not grant access,
prove provenance, establish licensing, or authorize order simulation on actual
unverified exports. Production integration must derive these assertions from the
existing Phase 4 reviewed-bundle trust registry, not from raw-file metadata.
The `edge_certified` and `execution_authority` outputs remain False.

For source data, preserve 2024 development, 2025 walk-forward and
2026-01-01 through 2026-09-30 sealed final holdout. The full Phase 6.2
module uses no real quote downloads and makes no new historical claims.

The quote-only journal is **not** an authenticated producer, cryptographically
tamper-proof ledger, privileged Windows session bridge or deployed forward feed.
It handles single-file SQLite transactions but has not undergone a multi-process
load/recovery campaign. These interfaces must not be interpreted as an MT5
connector or order endpoint.

## Next certified-data gate

Obtain a provider's applicable organizational-use grant **or** provide
pre-existing licensed primary bid/ask exports and proof of rights; include
calendar, source clocks/DST, symbol/contract metadata and historical fee/
financing rules. Inspect files with the existing Phase 4 `certify_package`
offline gate before any strategy performance evaluation. No credentials,
terminal startup, purchases, source automation or account changes are approved.
