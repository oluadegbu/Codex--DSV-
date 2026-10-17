# Phase 3 — data certification and edge discovery

**Decision: NONE. No instrument is certified and no strategy qualifies for promotion.** Evidence collected: 2026-10-16; publication finalized: 2026-10-17. This is a conclusive assessment of currently available evidence, not a claim that no market edge exists. The blocking primary-data path now has a concrete credential/billing gate; silently substituting secondary data would not meet the directive.

No orders, broker credentials, terminal startup, paid requests, execution reconstruction, production changes or main merge occurred. Everything in this phase is isolated offline research in draft PR #2. DMB PR #1 is outside scope.

## Certified data inventory

**Certified inventory: empty.** The following are revalidated, hash-locked pilot inputs, not certified primary quotes. Historical raw and normalized data remain excluded from the public repository; source pins and hashes are in Phase 2. Broker cache presence is not evidence of research quality.

| Instrument | Observed paired 1M bars | Historical period available | Pilot session availability | Certification decision |
|---|---:|---|---:|---|
| EURUSD | 91,656 | Selected Jan/Apr/Jul 2018 windows | 98.48% | BLOCKED: primary/time conversion, calendar gaps, recent history and executable costs |
| GBPUSD | 58,245 | Selected Jan/Apr 2018 windows; July absent | 65.15% | BLOCKED: same issues plus missing final pilot fold |
| XAUUSD | 55,850 | Selected Jan/Apr 2018 windows | 65.15% | QUARANTINED: price scale, metadata and broker mapping unresolved |
| ES/MES, NQ/MNQ, YM/MYM | 0 | No acquired contract-aware history | N/A | DATA BLOCKED |

The pilot denominator counts weekday NY 00:00–12:00 minutes in its selected months, including holidays conservatively. It is **not a certified provider calendar**. Wall-clock gaps include normal closures and cannot all be called missing market data. No interpolation/remediation has been applied. Future certification must classify closures separately, retry missing objects within bounds and exclude unresolved research sessions with fold-level disclosure.

The files contain separate bid/ask OHLC, pass the existing structural checks, and match their frozen normalized SHA256s. This proves file consistency, not simultaneous tick executability, primary quote correspondence or correct original timezone conversion. Minute extrema cannot establish the within-minute bid/ask event sequence. Existing conservative fill rules and MAE/MFE bounds do not cure uncertain provenance.

### Primary provenance, UTC and DST

Fresh bounded public-host canaries for FX January 2025 and September 2026 and Gold January 2018/2025 returned timeout/URL errors or HTTP 503; no successful raw quote capture was obtained. [Sanitized observations](EVIDENCE.json) distinguish failures from evidence of provider-wide absence. No endless retry or speculative alternate data replacement was performed.

A git-pinned mirror fixes bytes, not their production chain: the reviewed EURUSD fetch workflow references `fx31337/fx-data-download-action@master`; the Gold legacy build fetches an unpinned upstream Makefile. The exact producing decoder, metadata version and primary-to-mirror transformation therefore remain unproven. Do not label these files primary merely because they name Dukascopy.

UTC bar alignment is structurally checked. New York/London calculations use IANA timezones and include tests for winter, summer and US/UK transition mismatch weeks. These tests verify the research clock code; they cannot retrospectively prove the source timestamps' timezone. Require raw epoch timestamps, UTC bar-open semantics and primary samples around both DST transitions before certification.

Dukascopy's current [official bulk export guide](https://www.dukascopy.com/wiki/en/development/data-export/) documents AWS-authenticated requester-pays S3 access. No bucket request or AWS credential access was made. The [bounded acquisition plan](ACQUISITION_PLAN.md) specifies the smallest canaries, source metadata, cost/access gate, gap remediation and untouched future evaluation periods. An existing licensed primary export is also acceptable.

### Gold: what is resolved and what is not

The provider's [ITick documentation](https://www.dukascopy.com/client/javadoc3/com/dukascopy/api/ITick.html) defines bid/ask volumes as quantities available at quote levels. They are not exchange traded volume or a tick count. Phase 2's generic reference to zero “tick volumes” must not be used as a semantic conclusion. The mirror's exact volume conversion remains unverified; 55,833 of 55,850 bars have zero volume, which alone proves neither absent liquidity nor invalid prices.

Prices near 13 are not independently verified USD/oz prices. A 100× repair is a hypothesis and has **not** been applied. [Dukascopy's Gold product page](https://www.dukascopy.com/swiss/english/cfd/range-of-markets/gold/) describes its own product; it cannot certify Vantage's digits, lot size, tick value, symbol suffix or trading hours. The cached broker-symbol lead is unverified. Raw primary quotes plus versioned definitions and independent Vantage mapping remain required. Gold receives no performance inference.

## Frozen strategy evidence and reproducibility

Phase 3 revalidates the exact Phase 2 report, normalized inputs and trade-ledger hashes. The separate offline engine regression uses the same frozen registry, data and chronological periods and reproduced the exact report SHA256. This is **reproduction of old pilot evidence**, not a new independent OOS test. No new edge backtest is admitted while certification is empty; no parameters were optimized and no final holdout was reused for selection.

The frozen suite comprises 120 A/B/C variants, two baseline trials and 20 seeded random-control trials, producing 2,960 overlapping variant/control ledger rows. Those rows are not independent trades from one portfolio. A = London Asia sweep/reclaim reversal; B = NY opening-range breakout/acceptance/retest; C = external sweep/MSS first retracement, reversal/continuation, completed 15M/1H context. Both sides and 1M/3M/5M entries remain unchanged.

The table shows **per-variant OOS trade-count ranges and median variant expectancy**, never pooled expectancy. All rows are REJECT; the sample gate alone is sufficient before testing significance.

| Instrument | Family | TF | OOS trades per variant | Median variant OOS R |
|---|---|---:|---:|---:|
| EURUSD | A | 1M | 8–37 | −0.466 |
| EURUSD | A | 3M | 5–37 | −0.183 |
| EURUSD | A | 5M | 4–37 | −0.263 |
| EURUSD | B | 1M | 28–34 | −0.280 |
| EURUSD | B | 3M | 12–23 | −0.239 |
| EURUSD | B | 5M | 5–14 | −0.243 |
| EURUSD | C | 1M | 7–16 | −0.204 |
| EURUSD | C | 3M | 4–8 | −0.555 |
| EURUSD | C | 5M | 3–8 | +0.284 |
| GBPUSD | A | 1/3/5M | 0 | N/A |
| GBPUSD | B | 1M | 13–18 | −0.163 |
| GBPUSD | B | 3M | 6–14 | −0.170 |
| GBPUSD | B | 5M | 4–9 | −0.017 |
| GBPUSD | C | 1M | 1–10 | −0.259 |
| GBPUSD | C | 3M | 1–4 | −0.415 |
| GBPUSD | C | 5M | 1 | +0.098 |

[All 142 variant/control metric rows](results/pilot_variant_metrics.csv) include trade count, win rate, expectancy/average R, profit factor, costs, MAE/MFE, trade frequency, IS→OOS degradation, daily-block interval and full per-fold base/2× cost/target-sensitivity details. Drawdown is explicitly **maximum OOS fold drawdown**, not a stitched continuous multi-year equity curve. [Direction × NY entry-session subsets](results/pilot_direction_session_metrics.csv) show long/short behavior and non-overlapping clock buckets. Zero-trade subsets are absent, not winning or missing-data proof. Subset MAE/MFE inherit the minute-bar bounds; no new event-level precision is asserted.

The original positive 5M C medians rest on 1–8 trades and cannot establish an edge. FX variants fail the 100-trade/60-active-day gate; GBP also lacks the final pilot fold. Baselines and random controls remain included; no trial is promoted from unadjusted multiple comparisons. Positive-looking results do not override failed data, sampling, stability or stress-cost gates.

**Ranked qualifying candidates: NONE.** There is no statistically credible, cost-certified OOS result available to rank. Proposed future qualification is predeclared in the acquisition plan before acquiring untouched data; it adds family-wise correction rather than retroactively interpreting pilot confidence intervals as corrected evidence.

## Futures source assessment — no purchase

| Source | Coverage/schema evidence | Licensing and cost gate | Roll handling required |
|---|---|---|---|
| [Databento](https://databento.com/pricing/) | Vendor advertises CME/CBOT history and 16+ years generally; confirm actual per-contract/schema start dates, especially later-listed micros. Quotes/trades/definitions must be scoped. | Usage-priced historical data can be requested without a live subscription. Exact symbol/date/schema estimate not obtained. The displayed $199/month Standard live plan is optional, not a historical-data quote. Account/API access and applicable use/redistribution terms require review. No credits/signup/purchase. | Download raw contract IDs and definitions. Freeze roll logic; never infer fill prices from adjusted continuous series. |
| [CME DataMine](https://datamine.new.cmegroup.com/) | Exchange catalog offers historical datasets; exact intraday bid/ask coverage, delivery format and product dates must be confirmed. Settlement/continuous settlement series alone cannot test minute fills. | Dataset quote/order and applicable exchange information-license terms required; exact cost unknown. No order or authenticated query made. | Preserve expiration, contract calendar and actual contract prices; account for both roll legs. |

[CME's micro contract fact card](https://www.cmegroup.com/trading/equity-index/files/cme-micro-e-mini-futures-fact-card.pdf) supports MES $5/point and $1.25/tick, MNQ $2/point and $0.50/tick, MYM $0.50/point and $0.50/tick. Full-size E-minis are ten times those multipliers; see [CME FAQ](https://www.cmegroup.com/articles/faqs/frequently-asked-questions-micro-e-mini-equity-index-futures.html). Session/holiday calendars and historical fee schedules still need dataset-specific validation. NAS100/SP500 CFDs are not substitutes for NQ/ES futures. Proposed roll rule and cost treatment are in the acquisition plan; no futures backtest has been run.

## Read-only MT5/Vantage history audit

A file-only recheck of the known terminal journal matched the previously recorded BTCUSD entry, attached SL/TP, exit and exact-position close. No terminal process was observed. These are sanitized observations, not a republished original audit chain. Private paths, account identifiers and journal contents are excluded from this public repository.

This supports the two known historical mutation events; it does **not** establish present connectivity, account identity, reconciliation completeness or current account flatness. No SDK initialization, credential read, terminal startup or order-capable interface was used. The missing original DMEN source/authorization chain is not reconstructed from these descriptions, and is not needed to continue offline research.

## Next safe actions and remaining gates

1. Supply an existing licensed primary FX export or separately approve the bounded requester-pays acquisition identity and dollar ceiling. Exact costs remain unknown; no purchase is authorized by this report.
2. Certify primary correspondence, clock semantics, recent coverage, sessions and executable units/costs; complete gap remediation/exclusions. Keep Gold and futures quarantined independently until their own evidence passes.
3. Freeze the future chronology, multiple-testing protocol and registry, then rerun all families/controls unchanged. Publish every rejection; seal the final holdout until selection is complete.
4. Replay certified quotes through the existing read-only quote model and shadow file interface with hypothetical signals only. Data-feed qualification can start without claiming a selected trading edge. Any terminal startup/authenticated bridge needs separate access authorization. Every new DEMO order requires separate explicit approval; this work grants none.

## Reproduce this review

From `research/dat_mt5_edge` with the frozen Phase 2 normalized files and ledger already available:

```sh
python -m phase3.review
python -m unittest discover -s tests -q
python -m unittest discover -s tests_phase2 -q
python -m unittest discover -s tests_phase3 -q
# Optional offline engine regression, not a new OOS study:
python -m phase2.reproduce --root phase2/work/data --output phase3/work/regression --offline
```

Without those research data files, the review fails closed. No command above downloads data, starts MT5 or grants execution authority. [Certification output](results/certification.json) contains normalized hashes and the exact frozen report/ledger fingerprints. Validation: 47 tests pass (20 Phase 1, 17 Phase 2, 10 Phase 3). Frozen pilot report SHA256: `7e60b6d5456783f3d74abd593ea29c5330998cd88848b75d814387f91ec3c181`.
