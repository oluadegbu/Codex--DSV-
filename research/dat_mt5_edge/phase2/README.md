# Phase 2: multi-instrument research pilot

Research only. This package has no broker SDK, login, order API, terminal startup, service installation or production dependency. It extends PR #2; Phase 1 and DMB are unchanged.

## Data and reproducibility

`acquire_archive.populate` downloads public commit-pinned Dukascopy tick-mirror archives, selects plain CSV members in memory without extracting archive paths, and retains only January/April/July 2018. `acquire_mirror.run` validates every tick's date/hour, monotonic timestamp, finite positive noncrossed bid/ask, and nonnegative quote volume. Duplicate millisecond timestamps are permitted because multiple quote updates can share a millisecond. No missing minute is carried forward. Each observed minute has separate bid/ask OHLC. Empty minutes remain gaps. UTC is the upstream Dukascopy convention; `crosscheck.crosscheck` independently compares primary bid/ask daily candles where reachable. A failed check blocks qualification, rather than inferring timezone from market behavior.

`acquire_quotes.py` is a separate primary-feed daily downloader. Direct acquisition was unreliable and the bulk job was stopped; its partial cache is not silently merged into mirror research. Public source locks and normalized hashes are recorded with the results. Raw archives/ticks and private host inventories are not published. Read upstream redistribution terms before sharing raw data; no license is inferred.

Python 3.12 and IANA timezone data are required. Linux uses system TZif files. The isolated Windows research process uses copies of those same New York/London TZif files through `zoneinfo.reset_tzpath`, not a production Python package installation. Hashes are recorded in the report. A user running this elsewhere needs matching timezone rules (or the exact pinned files); fixed UTC offsets are not acceptable.

From the parent `research/dat_mt5_edge` directory:

```sh
python -m unittest discover -s tests_phase2 -v
python -m phase2.reproduce --root phase2/work/data --output phase2/work/results
```

Acquisition is explicit public HTTP. The offline simulator (`model`, `strategies`, `engine`, `research`) itself does no network I/O. To rerun offline, retain the normalized files plus source manifest and use `python -m phase2.research --data DATA_DIR --output OUTPUT_DIR`.

## Predeclared strategy grid

Gold mirror data failed the semantic price-scale/zero-volume check and are quarantined before simulation. No automatic scale correction is applied. EURUSD/GBPUSD are pilot quote-unit interpretations, with primary provenance and account execution still unverified.

All 1M/3M/5M entry signals use completed bars and are filled only at the next observed minute open. Complete 15M/1H context is available only at its close. No interpolation or centered pivots. One setup attempt per New York day per variant. Gaps reset setup/indicator history and cancel noncontiguous entries. Both directions are simulated as a hypothetical spot/CFD research model; executable account costs and contracts are NOT certified.

- **A:** default Asia 00:00–06:00 UTC plus a second instrument-specific range: EURUSD 22:00–06:00 UTC; GBPUSD 23:00–06:00 UTC; XAUUSD 18:00–00:00 New York. All range bars must be present. Compare NY 02:00–05:00, London 07:00–10:00, and NY 05:00–06:00 stall windows. Early entry requires sweep and close back inside; confirmation requires later opposite displacement/reclaim of sweep-bar structure within 15 minutes. Displacement >1.2 times the prior 20-body average. Stop tracks sweep extreme.
- **B:** NY 08:00–08:15 and 09:30–09:45 opening ranges (the latter is a comparative clock window for FX/gold, not a claim that those assets have an equity cash open). Breakout displacement >1.2 prior-body mean, one/two acceptance closes outside the range, then a later retest touching the broken boundary and closing in its direction. Setup expires after 20 minutes; all new entries stop 75 minutes after opening-range start. Opposite range extreme is stop. No entries at/after window expiry.
- **C:** external liquidity = preceding contiguous 60 minutes. Sweep/reclaim, then displacement breaks the opposite previous-three-entry-bar structure. First later retracement to displacement midpoint must close in intended direction; first invalid touch consumes the setup. Setup stages expire after 20 minutes. Compare reversal (against completed context-candle direction) versus continuation (with it), using separate closed 15M/1H context. Entry window 02:00–11:00 NY. This is an operational MSS/midpoint-retest variant, not a claim to reproduce discretionary order blocks or every FVG definition.

60 fixed variants per instrument. Thresholds are not optimized. Adjacent variant distributions and 1.5R/2R/2.5R exits are sensitivity diagnostics; no winner is chosen from these pilot holdouts. Model changes after inspecting holdouts require a new untouched period and trial-registry entry.

## Fills, risk and metrics

Execution replays observed 1-minute paired quotes for every entry timeframe. Long entry ask / exit bid; short entry bid / exit ask. Stops/targets trigger on the actual liquidation side's OHLC. Stop wins if both touch within the same minute. Gaps through a stop receive worse open execution. Missing-minute exits occur at the next observed opening quote and explicitly disqualify promotion because the unobserved path is unknown.

Hypothetical equity $100,000; 0.25% current-cash risk per trade; quantity rounded down. Commission scenario 0.35 bps per side on notional. FX: 1 currency unit point value, 1,000-unit increments, 10x maximum notional, 0.1 pip adverse slippage per fill. Gold: 1 oz units, 1 oz increments, 2x notional, $0.05/oz adverse slippage. These are research assumptions, not verified trading-account specifications, margins or historical fee tiers. Double-cost stress doubles commission/slippage and widens observed opening spread; no fee-free or overnight funding assumption. Trades exit after at most 90 minutes or at 16:00 NY; no late entries. Tick rounding is adverse.

Reports include trade count, frequency per observed 24h (not per calendar day), direction counts, win rate, expectancy USD, average R, PF, conservative marked drawdown, MAE/MFE price-excursion R bounds, daily-block bootstrap interval, IS/OOS degradation, forward-fold results and cost/target sensitivities. Spread-cost attribution uses opening quote spreads; exact intrabar spread at stop touch and exact MAE/MFE tick order cannot be recovered from minute OHLC. Net P&L uses side-aware fills and commissions. Drawdown uses conservative adverse minute-bar excursions. Each chronological fold starts a fresh $100,000 simulated account; pooled OOS P&L is not a single compounded portfolio.

January is fixed IS. April is forward validation after January; July is the next untouched fold after January+April. There is no fitting stage and no parameter chosen on a fold. Only these disjoint periods are covered; they are not continuous three-quarter history or proof across all regimes. Weekend/holiday/maintenance expectations are not equated with calendar minutes: coverage is explicitly measured in predeclared weekday NY 00:00–12:00 research windows, with holidays conservatively counted as unavailable. Complete exchange holiday/session and futures-roll calendars remain qualification gates.

## Controls and selection

A simple 08:00 NY prior-bar momentum baseline and ten seeded random-time/random-direction daily controls use the same execution costs, windows, risk model and historical periods. These are unconditioned controls, not perfectly frequency/volatility-matched causal inference. They cannot prove significance alone. Daily-block bootstrap resamples active-day blocks and omits no-trade days from the trade-mean estimate; insufficient days return no interval. No multiple-testing-adjusted edge claim is made across the 142 executed pilot/control trials (gold variants deferred by the semantic data gate).

Qualification requires >=99% research-window coverage, independent primary/timezone cross-check, verified executable account contract/costs, >=100 OOS trades and >=60 active days, >=30 trades and positive base/2x-cost expectancy in each forward fold, positive bootstrap lower bound, no unobserved gap exits, and <=10% OOS fold drawdown. Eligibility precedes any expectancy-based ranking. A pilot pass would still mean research review only, never trading permission.

ES/MES, NQ/MNQ, YM/MYM remain blocked until contract-specific timestamped bid/ask/trade data, expiries/roll policy, exchange sessions/holidays, tick/point values, and actual fee/slippage inputs are verified. Index CFDs, ETFs and generic continuous series are not substituted. No purchase or credential use occurs in this phase.
