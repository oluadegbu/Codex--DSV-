# DAT MT5 Phase 2 research report

**Status: quality-gated pilot framework implemented; no candidate qualifies for an edge rank or forward-SHADOW promotion.** No broker orders, terminal startup, credentials, production modifications or automatic DEMO authority. All work belongs to draft PR #2.

## Evidence and validation

Final deterministic experiment: 142 executed trials (120 strategy variants + 2 baselines + 20 seeded controls), 2960 overlapping variant/control trades. These are not independent pooled samples. Raw ticks and broker caches are not published.

Experiment SHA256: `7e60b6d5456783f3d74abd593ea29c5330998cd88848b75d814387f91ec3c181`. Ledger SHA256: `bb3560923713a1b23a6076c9f365b5a6bce17a2a6c6089eb108c10830325ec7c`. Source pins, archive identities, normalized hashes and timezone-file hashes are in source_lock.json. Pinned archives were selected as plain data; no upstream code was executed.

Thirty-seven local tests pass: 20 retained Phase 1 and 17 Phase 2 tests, including actual paired-data prefix invariance, closed context alignment, DST, both-direction stop handling, adverse costs, sizing/fee accounting, MAE/MFE bounds, expiry, missing-minute denial, gold quarantine and futures separation. Reproducibility evidence is recorded in verification.json.

## Data-readiness matrix

| Data priority | Instrument | Observed minutes | Research-window availability | Evidence / gap | Edge rank |
|---:|---|---:|---:|---|---|
| 1 | EURUSD | 91,656 | 98.48% | Pinned paired ticks; January/April/July present; primary spot check failed; costs/contracts unverified | BLOCKED |
| 2 | GBPUSD | 58,245 | 65.15% | Pinned paired ticks; July absent; no final holdout; primary spot check failed; costs/contracts unverified | BLOCKED |
| 3 | XAUUSD | 55,850 | 65.15% | QUARANTINED: unverified quote scale and almost all volume fields zero; no economic performance inference | BLOCKED |
| 4 | ES | 0 | n/a | No licensed contract history, rolls/session/fees verified | BLOCKED |
| 4 | MES | 0 | n/a | No licensed contract history, rolls/session/fees verified | BLOCKED |
| 4 | MNQ | 0 | n/a | No licensed contract history, rolls/session/fees verified | BLOCKED |
| 4 | MYM | 0 | n/a | No licensed contract history, rolls/session/fees verified | BLOCKED |
| 4 | NQ | 0 | n/a | No licensed contract history, rolls/session/fees verified | BLOCKED |
| 4 | YM | 0 | n/a | No licensed contract history, rolls/session/fees verified | BLOCKED |

Availability is measured only over the frozen Jan/Apr/Jul weekday NY 00:00–12:00 windows, with holidays conservatively included. It is not continuous-year coverage, an exchange-calendar certification, or a claim that every unavailable minute is corrupt. No carry-forward or guessed bar is inserted.

1,321 of 4,752 requested hourly source files were unavailable or invalid. The locked gold mirror has raw prices approximately 13 rather than a verified USD/oz unit. No automatic 100x adjustment or liquidity inference from zero volume is made. The initial qualification pass was invalidated and gold removed before final performance selection; this was a data gate correction, not parameter tuning.

All six primary BID/ASK daily-candle checks failed with HTTP errors. UTC is the upstream convention used for pilot interpretation, not independently certified timezone provenance. FX quote-scale interpretation is recorded explicitly. Real executable fees, quantity rules and contract multipliers remain unverified. Futures are not represented by index CFDs, ETFs or generic continuous-price substitutes.

## Instrument x strategy matrix

Eligibility is evaluated before expectancy ranking. All cells fail evidence/sample gates, so there is no valid #1 edge. The table reports **medians across the predeclared family**, not a cherry-picked highest-performing variant. A/B/C remain separate hypotheses.

| Instrument | Family | Variants with OOS trades / total | Trades per variant range | Median OOS R | Median PF | Maximum fold DD | Positive OOS variants | Edge decision |
|---|---|---:|---:|---:|---:|---:|---:|---|
| EURUSD | A | 36/36 | 4–37 | -0.303 | 0.584 | 3.23% | 7/36 | REJECT |
| EURUSD | B | 12/12 | 5–34 | -0.239 | 0.597 | 3.23% | 1/12 | REJECT |
| EURUSD | C | 12/12 | 3–16 | -0.273 | 0.575 | 1.51% | 3/12 | REJECT |
| GBPUSD | A | 0/36 | 0–0 | n/a | n/a | 0.00% | 0/36 | REJECT |
| GBPUSD | B | 12/12 | 4–18 | -0.138 | 0.736 | 2.09% | 3/12 | REJECT |
| GBPUSD | C | 12/12 | 1–10 | -0.105 | 0.000 | 1.75% | 5/12 | REJECT |
| XAUUSD | A / B / C | 0 / deferred | n/a | n/a | n/a | n/a | n/a | DATA QUARANTINE |
| ES/MES, NQ/MNQ, YM/MYM | A / B / C | 0 / deferred | n/a | n/a | n/a | n/a | n/a | DATA BLOCKED |

GBPUSD A has no OOS trades under the strict complete Asia-range requirement. Zero trades is insufficient evidence, not zero expectancy. GBPUSD B/C results use April forward validation only; July is absent. EURUSD includes both forward months but no variant reaches the required 100 OOS trades / 60 active days. Thus positive-looking cells cannot be selected for forward SHADOW.

## Baseline and randomized-entry controls

| Instrument | Momentum baseline OOS N / R | Seeded random-time/direction median OOS R | Random R min/max |
|---|---|---|---|
| EURUSD | 43 / -0.177 | -0.062 | -0.268 / 0.142 |
| GBPUSD | 21 / -0.045 | -0.034 | -0.417 / 0.079 |

Controls use the same quote execution, costs, time limits and sizing. Random timing/direction is seeded and repeatable. They are not perfectly frequency/volatility matched to each candidate, and favorable comparison is not a significance test. Daily-block bootstrap intervals are unavailable below 20 active days and are not corrected for selection across trials.

## Entry-timeframe and parameter stability

| Instrument | Family | 1M median R | 3M median R | 5M median R |
|---|---|---:|---:|---:|
| EURUSD | A | -0.466 | -0.183 | -0.263 |
| EURUSD | B | -0.280 | -0.239 | -0.243 |
| EURUSD | C | -0.204 | -0.555 | 0.284 |
| GBPUSD | A | n/a | n/a | n/a |
| GBPUSD | B | -0.163 | -0.170 | -0.017 |
| GBPUSD | C | -0.259 | -0.415 | 0.098 |

Asia definitions, early/confirmation entry, NY/London/stall windows, OR clock/acceptance count, reversal/continuation and 15M/1H context are frozen grid dimensions. Full per-variant expectancy, frequency, win rate, PF, USD costs, drawdown, MAE/MFE, direction counts, IS–OOS degradation, forward folds, 2x-cost stress and 1.5/2/2.5R sensitivity are in results/phase2.json. No best parameter set is selected, and no optimization is performed while coverage remains inadequate.

MAE/MFE are conservative minute-bar price-excursion R bounds; exact tick ordering at exits is not claimed. Fees/slippage are explicit scenarios, not historical-account certification. Read README.md for fill semantics, cost-attribution limits and full definitions.

## Strongest forward-SHADOW candidates

**None qualify as an edge candidate.** EURUSD has the best data readiness of this collection, which makes it the first instrument for data-feed validation SHADOW. That is an engineering priority, not a profitable-strategy recommendation. GBPUSD needs a complete final holdout; gold needs independently verified units and usable quote-volume semantics. Futures require an existing licensed source or export; no purchase or credential activity was authorized.

## Next safe automated research actions

1. Re-run the locked public-data normalization and quote-only tests offline. Keep consumed dataset hashes and trial registry immutable; fail on changed source hashes.
2. Repair primary historical-feed access and independently verify timestamp/quote-scale correspondence. Collect complete recent multi-regime bid/ask periods spanning at least 60 active OOS days and adequate per-variant trades, including DST and holiday boundaries. Validate broker/session and FX/gold fee/quantity metadata without credentials or terminal startup.
3. Add existing licensed futures files only after contract ID, expiry, raw-vs-adjusted price, roll policy, Chicago/exchange clock, holiday/maintenance session, tick/point value and fees are verified. Simulate each contract before any declared continuous-series aggregation.
4. Run the same frozen variants and matched-frequency random controls on a new untouched holdout. Require stable positive base/2x-cost forward expectancy, adequate samples, conservative drawdown and selection-aware uncertainty before ranking candidates. Do not tune on these inspected pilot folds.
5. Feed approved market-data-only exports into file-based SHADOW and log simulated decisions, stale/missing feeds and bid/ask fill comparisons. This does not authorize terminal startup, a service/task, a broker order or DEMO execution.
