# Phase 1 research readiness

Offline engine operational; all candidates REJECTED for promotion. No broker/terminal startup, credentials, execution or production changes. Research branch is based directly on main, separate from DMB.

## Data available

| Instrument | Observed data | Research status |
|---|---|---|
| BTCUSD | Vantage proprietary cache; public Bitfinex 2017–2018 minute OHLCV | Public proxy structurally validated, complete 30m buckets only; gaps disqualify promotion |
| XAUUSD | Vantage `XAUUSD.crp` ticks.dat | Mapping/contract/timestamps/coverage unverified; no backtest |
| NAS100 | Vantage ticks.dat | Contract/timestamps/coverage unverified; no backtest |
| SP500 | Vantage ticks.dat | Contract/timestamps/coverage unverified; no backtest |

Broker caches for the requested symbols were observed but remain quarantined. Their proprietary formats, coverage, timezone and executable contract specifications were not certified. No unsupported decoder, guessed epoch or invented contract specification is used. No terminal startup was performed. Internal file locations and recovery details are excluded from this public report.

Public data provenance is pinned in acquire.py and source_manifest.json; hashes and content validation independently reproduced in the isolated Windows research directory and matched the Linux transfer.

- 2017: 505,209 minutes, 20,391 missing minutes; zero invalid OHLCV/non-increasing timestamps. 12,615 complete 30m bars; 4,904 incomplete buckets excluded.
- 2018: 520,499 minutes, 5,101 missing minutes; zero invalid OHLCV/non-increasing timestamps. 15,363 complete 30m bars; 2,153 incomplete buckets excluded.

Total 27,978 bars; normalized SHA256 `0390982c2b8c4489a287a8a5259c6d56cce424e0c6daa7266661a0a2964b2c1c`. UTC open timestamps from upstream epoch milliseconds; zero fill/interpolation. First/last: 2017-01-01T10:30:00+00:00 / 2018-12-31T23:00:00+00:00. OOS 30m coverage 87.69%, below required 99%. Source completeness does not prove fidelity to the exchange or executability at Vantage.

## Verified results

20 tests passed, including actual-data prefix invariance, each candidate event sequence, winter/summer NY session conversion, weekend rejection, next-open fills, stop/target ambiguity, stop gaps, cost accounting/stress, sizing, drawdown, invalid-data denial and SHADOW snapshot gates. Two final experiment runs produced byte-identical JSON.

Final results SHA256 `076c9c9e7165aef9f07a61bf8a822001a08741e806cef2d0cf9ab8b3fc639b12`.

OOS below pools two independently capitalized 2018 half-year folds. Long-only spot proxy; no borrowing assumptions. Fixed modeled costs: full spread 10bps, per-side commission 20bps, per-side adverse slippage 5bps. Additional 2x-cost results and per-session/per-fold metrics are in phase1.json.

| Candidate | OOS trades | Win rate | Expectancy USD | Avg R | PF | Max fold DD | Costs USD | IS–OOS degradation R |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| A | 8 | 25.0% | -60.44 | -0.2414 | 0.595 | 0.85% | 532.64 | 0.45767571733816154 |
| B | 36 | 25.0% | -125.78 | -0.5081 | 0.196 | 2.79% | 3544.28 | 0.1909133243944074 |
| C | 1 | 0.0% | -0.35 | -0.0014 | 0.000 | 0.17% | 14.31 | n/a |

All three fail sample, stable OOS and verified-price gates. Candidate C has only one OOS trade; its estimates carry no statistical weight. These are initial engineering results, not evidence of profitability. The fixed weekday session rule was corrected during implementation verification before freezing final results; no search for better parameters occurred. Only two old regimes and one proxy instrument are represented.

## Next steps

1. Obtain complete recent bid/ask history with source provenance; verify all four broker contracts, symbol mappings, broker-time conversion and actual calendars. This needs data, not execution-engine recovery.
2. Freeze a new untouched holdout and test higher-resolution setup/stop behavior; record every additional strategy/parameter trial and use dependence-aware uncertainty analysis. Do not reuse 2018 as fresh holdout after looking at these results.
3. Separately approved terminal startup may provide market-data-only exports. Connect those files to ReadOnlyBars/FileShadowFeed, validate clock/freshness and authentic exporter provenance, add durable replay state, and log simulated decisions/fills in SHADOW. No terminal startup was authorized or attempted here.
4. Recover DMEN originals independently per BACKUPS.md. Never recreate execution grants from historical descriptions.

No new DEMO/live order is authorized; any future DEMO order requires separate explicit approval.
