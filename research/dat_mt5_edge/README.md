# DAT MT5 edge research — Phase 1

Phase 2 research: [quality-gated multi-instrument report](phase2/REPORT.md), [protocol and reproduction](phase2/README.md). Phase 1 results below remain preserved.

Independent offline research, with no DMEN, DAT service, OpenClaw, terminal, broker credentials or order API dependency. Production is not a research workspace. No execution authority is implemented or restored.

## Reproduce

Python 3.12+ with standard library and IANA timezone data (Linux normally includes it). Windows may need `tzdata` installed in the isolated research environment. No third-party backtest library is required for this small auditable event-driven baseline.

From `research/dat_mt5_edge`:

```sh
python -m unittest discover -s tests -v
# Explicit public HTTP download only; omit --download to use existing raw files.
python acquire.py --download
python -m edge.research --data data/BTCUSD_30m.csv --spec spec_bitfinex.json --output work/reproduced.json
# Must match the committed results byte for byte.
python -c "from pathlib import Path; assert Path('work/reproduced.json').read_bytes()==Path('results/phase1.json').read_bytes()"
```

All raw inputs are commit-pinned and SHA256 checked before normalization. Raw market data are excluded from Git; upstream provides the data as-is. See upstream README at https://github.com/Zombie-3000/Bitfinex-historical-data/blob/fc162575330dad255443a75137c67cee7d89be0d/README.md for provenance. No redistribution license is inferred. `data/source_manifest.json` records hashes, gaps, coverage and rejected aggregation buckets.

## Frozen definitions

All signals use completed 30-minute bars. Fill is at the next available contiguous bar open. Weekday windows use IANA timezone conversion, including historical daylight-saving time. One signal attempt per UTC day; one position per strategy; no simultaneous positions. These are explicit initial interpretations of the candidate ideas, not recovered DMEN strategies.

- **A:** local London 00:00–07:00 Asia range must contain all 14 bars. From 07:00–10:00, price sweeps a range extreme and closes back inside. A later bar, within four bars, must close past the sweep bar's opposite edge with opposite-direction body >1.2 times the previous 20-body mean. Stop beyond the tracked sweep extreme.
- **B:** New York 09:30–10:00 opening range. A later close breaks the range; a subsequent bar within four bars touches the broken boundary and closes beyond it. Entry window ends 12:00 local. Stop at the opposite opening-range extreme.
- **C:** external liquidity is the preceding 48 contiguous bars' extreme, excluding the signal bar. Sweep and close back inside, then within eight bars a displacement close breaks the preceding six-bar opposite structure. After that close, a later bar within eight bars retests the three-candle FVG if present or the causal EMA20 and closes in the intended direction. Stop at tracked sweep extreme. Window 07:00–16:00 New York; no centered or future-confirmed pivots.

Two-sided signals are implemented and tested. The Bitfinex spot baseline **rejects shorts** because borrow/funding execution was not verified. It does not silently simulate Vantage CFDs or assume free borrowing. Do not tune thresholds on the reported 2018 holdout and continue calling it out-of-sample; any revision requires a new untouched evaluation period and a recorded trial.

## Execution and cost model

`spec_bitfinex.json` is a research scenario, **not a verified broker contract**: 1 BTC per unit, 0.0001 unit granularity, $0.01 price tick, maximum 1x notional, $100,000 starting equity and 0.25% modeled risk per trade. Full spread 10 bps, commission 20 bps per side, adverse slippage 5 bps per side. Full cost sensitivity doubles all three. Prices round outward; sizes round down and include expected fees and stop execution in the risk budget. No overnight positions, so no assumed-free overnight funding. This example's granularity and fees require venue/date verification before any executable inference.

OHLC trade prices are treated as a midpoint **proxy**. Real bid/ask data are absent. Stop and target are midpoint triggers followed by adverse-side execution. Both hit within a bar: stop wins. Gaps through stops use worse opening prices. Targets receive no favorable gap improvement. Fixed 2R midpoint target. End-of-UTC-day, fold-end and final-sample closes flatten simulated positions. A missing bar cancels pending signals, resets indicator/setup history and exits existing risk at the next observed open. The unobserved path is unknowable, so gaps also disqualify promotion.

Drawdown includes conservative bar-level adverse excursions and modeled liquidation costs, using marked equity; the unknown tick path cannot be recovered. Stop/target event timestamps identify the containing bar's open, not an observed tick timestamp; session exits identify the bar's close. Cost figures include modeled spread/slippage/rounding and commissions. Average R uses initial modeled risk inclusive of costs; gap losses may exceed -1R.

Chronological protocol: 2017 IS; 2018 H1 OOS; 2018 H2 OOS. Each fold starts with $100,000; OOS metrics pool independent fold trades and are not a continuous compounded portfolio return. IS/OOS degradation = IS average R minus pooled OOS average R. Bull/bear year labels are descriptive context, not fitted filters. No optimization, candidate ranking or selection using holdout results. The 95% mean-R intervals are descriptive normal intervals, not dependence-adjusted statistical proof.

Promotion rejects unverified execution, OOS coverage below 99%, fewer than 100 OOS trades or 60 active days, nonpositive OOS expectancy, mean-R interval including zero, inadequate/negative half-year folds, failure under double costs, or OOS fold drawdown above 10%. Passing would permit research review only, never an order. Broader regimes, block-bootstrap inference, untouched recent data and multiple-testing controls remain required before claiming an edge.

## Future forward SHADOW

`edge.core.ReadOnlyBars` / `CsvBars` accept exported closed bars. `edge.shadow.FileShadowFeed` accepts a strictly whitelisted quote-only JSON snapshot; it rejects extra fields, stale/future quotes, out-of-order timestamps, replayed sequences, inverted/nonfinite prices and unapproved symbol mappings. Replay tracking is in-memory per instance; production-grade durable sequence state and authenticated exporter provenance remain future work. `contract_verified` is an input assertion, not proof that this reader can independently authenticate it.

The initial mapping is BTCUSD→BTCUSD, XAUUSD→XAUUSD.crp, NAS100→NAS100, SP500→SP500, based only on observed cache names. Every mapping, contract multiplier, tick value/size, volume limits, broker timezone, trade session/holiday calendar and bid/ask feed must be independently verified before use. No equity/metal session calendar or executable contract has been certified by this phase.

Shortest path: obtain a quote/bar-only export from a separately approved terminal session; verify contracts, timestamps and exporter provenance; feed the existing offline strategy classes to simulated fills and an append-only SHADOW ledger; record data gaps and compare simulated fills with bid/ask quotes. No relay, DMB or DMEN execution engine is needed. This phase does not start MT5, register a task, enable an EA or connect a broker SDK. Terminal startup and every new DEMO order require separate approval.

## Phase 3 certification review

[Phase 3 report](phase3/REPORT.md) records the empty certified inventory, reproduced pilot metrics, current data-access blockers and bounded acquisition plan. Qualifying candidates: **NONE**. The old pilot is not new independent OOS evidence. No execution authority is granted.

## Phase 4 verified-data readiness

[Phase 4 report](phase4/REPORT.md) adds source/cost comparison, recovery of three paired EURUSD 2022 canary days, deterministic evidence-bound certification and a passive quote-only consumer. No market dataset is certified, no new OOS result is claimed, and no terminal connectivity or execution is activated.

## Phase 5 acquisition route

[Phase 5 report](phase5/REPORT.md) ranks free and budget-limited routes, records a new 862,680-event free BTC/USD quote canary, and separates published prices from unquoted basket totals and authorization. Multi-year certification remains blocked; no spending, enrollment, terminal or execution authority is granted.

## Phase 6 Tickstory Lite gate

[Phase 6 feasibility report](phase6/REPORT.md) records the personal-use/EULA ambiguity and elevated Windows runner. No installer was downloaded or run; no CSV export or new certification is claimed. Resume only after readable permission evidence and an existing usable non-admin Windows context are established.

## Phase 6.1 acquisition fallback

[Phase 6.1 report](phase6_1/REPORT.md) resolves the readable Tickstory EULA, documents primary-data use restrictions, and confirms the active DirectiveCodex session without establishing a supported non-elevated runner. No new FX data is certified. Provider clarification drafts are prepared but unsent; prior evidence remains unchanged.

## Phase 6.2 parallel research readiness

[Phase 6.2 report](phase6_2/REPORT.md) documents offline walk-forward/coverage/robustness screening, paired bid/ask cost sensitivity, a durable quote-only replay journal, and 32 synthetic software tests. All new files remain in `phase6_2/` and `tests_phase6_2/`; provider rights remain unresolved and the [provider draft](phase6_2/PERMISSION_REQUEST_DRAFT.md) has not been sent. No new data, edge certification, MT5 startup, account connection or trading authority is claimed.

## Phase 6.3 read-only VPS cache survey

[Phase 6.3 report](phase6_3/REPORT.md) inventories 19 MT5 history/tick cache files from the already-authorized Windows VPS through **metadata-only** reads. It documents platform-supported HCC/TKC/ticks.dat semantics, per-instrument file sizes and modification dates, cross-server provenance warnings, legal/export gates and the gap to Phase 6.2 certification. No binary contents were read or decoded, no terminal or account opened, and no CSV was exported. History coverage, paired bid/ask and organizational reuse permission remain unverified; prior results and sealed holdouts are preserved.
