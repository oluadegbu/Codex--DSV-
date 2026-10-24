# Phase 5 — primary-data acquisition recommendation

Review: **2026-10-18, New York**. Proposed evaluation ceilings: US$50/month or US$150 one-time, **not spending authority**.

**Recommendation: free-first Dukascopy quote exports for FX/Gold/provider BTC, with Tickstory Standard as a conditional US$79 automation fallback. Do not purchase yet.** There is no verified all-in offer within these limits that already establishes a licensed, complete five-instrument, five-year quote dataset. A working route must pass canary export, terms, exact symbol and calendar checks first. Futures need a separate scoped quote; BTC spot and Vantage BTC/Gold CFDs remain distinct products.

Phase 5 acquired one genuinely new, documented free BTC/USD quote sample and ran the existing certification tools. **Certified multi-year datasets: NONE; new strategy backtests: 0.** Phases 3 and 4 remain unchanged. All publication is in draft PR #2; no main merge, DMB PR #1 change, order, terminal startup, account connection, credential enrollment, purchase or persistent installation/service occurred.

## What was obtained and verified

[Tardis documents free, no-key downloads for the first day of each month](https://docs.tardis.dev/downloadable-csv-files/api.md). A single normal GET acquired Kraken `XBT-USD` quotes for **2026-06-01**, with no account, key or billing activation:

- 11,649,384 compressed bytes; **862,680 quote records**; 1,440 observed UTC receive-time minute bars.
- Raw SHA256: `cc5fbee1ae52d3eb38381990048bbfbd51a2f7f5aade612df7fc58e6a41968f6`.
- Normalized SHA256: `88a58a595622b7425cfa68262d487de5ef568e772e2b5ed19469115002974b5d`.
- No receive-time backsteps, no exchange-time backsteps, no exchange timestamps after receipt. There are 8,798 repeated receive timestamps; original row order is retained rather than deduplicating legitimate updates. Maximum observed receive lag: 4.040936 seconds.
- All 1,440 expected minutes in the diagnostic 24-hour calendar are present, with no observed empty minute. This does not prove continuous tick capture within each minute or absence of upstream disconnections.
- Structural OHLC/bid–ask/grid checks pass under an **unverified diagnostic** $0.10 tick assumption. Median minute endpoint spread: $0.10; p95: $4.00. These are endpoint statistics, not a complete intraminute spread distribution.

[Full diagnostics and certification decision](results/free_sample.json): **QUARANTINED**. The evidence registry remains empty; independently reviewed license/provenance/clock/decoder/calendar/contract/cost proofs are missing. There is only one day, older than the 120-day recency gate. Diagnostic zero fees/slippage are explicitly unverified placeholders used to exercise the data validator; they are not a cost model, fill assumption or edge result. No strategy consumed this sample.

Normalization groups by **receive timestamp** in original capture order, so unavailable future exchange events cannot be retrospectively moved earlier. Volume is the sum of closing best-bid and best-ask available BTC sizes, not traded volume or tick count. This is a vendor-captured Kraken spot feed, not a Vantage CFD export or a new independent primary exchange attestation.

Public vendor metadata reveals an important multi-year mapping boundary: `XBT-USD` covers 2019-06-04 through 2026-07-10; `BTC-USD` begins 2026-07-10. Verify the identity/definition transition before joining. These are **advertised metadata bounds**, not a downloaded/certified continuous history. [Sanitized source observations](OBSERVATIONS.json) preserve URLs and hashes; raw market data stays outside the public repository.

## Existing MT5 broker route — investigated without activation

MetaQuotes [official MT5 help](https://www.metatrader5.com/en/terminal/help/trading/market_watch) documents Market Watch → symbol management → **Bars/Ticks → Request → Export CSV**, using whatever history that broker server actually supplies. A Market Watch snapshot export and an account/P&L statement are not multi-year quote history. Bar-level spread fields also do not reconstruct a recorded tick sequence.

A fresh directory-only check of the known terminal `MQL5/Files` and `Temp` child found no plain quote exports. The Phase 4 `.hcc`/`.tkc` cache findings remain unverified; filenames do not establish three years of decoded quotes. No configs, account files or credentials were opened. The broker's exact history bounds, historical specifications, retention and export fee are **unknown**; no generic MT5 documentation can guarantee Vantage demo-server depth.

Operator action, only after separate data-only session authorization: manually export ticks and complete symbol specifications for the exact demo-server symbols, keeping account identifiers out of the research files; record requested/returned bounds, server timezone, digits/point/tick size/value, lot units, commissions/swaps, session/holiday schedule and gaps. Do not install an exporter EA or connect a full SDK. No such session is authorized by Phase 5. Alternatively supply already existing licensed exports without starting MT5.

## Ranked FX/Gold/provider-BTC acquisition routes

Ranks are **procurement priorities**, not certified data or trading-edge rankings. Quality/provenance and adequate quote coverage outrank a cheap price; underlying rights and reproducible raw exports must pass before buying convenience software. Prices below are public listed base prices, not checkout totals; local taxes, transfer/storage and any third-party rights remain separate where applicable.

| Rank | Route | Exact published price / budget test | Historical depth, quotes and limitations | Operator action |
|---|---|---|---|---|
| 1 | [Dukascopy direct public export](https://www.dukascopy.com/swiss/english/marketwatch/historical/) | **US$0 data fee** through public export; local transfer/storage not quoted. Requester-pays S3 is a separate, unpriced route and is not authorized. | Provider documents CSV tick-to-monthly export; [widget description](https://www.dukascopy.com/api/data/get/historical-data-export) identifies bid/ask availability. Five-year target is plausible, but exact provider first/latest dates and continuity have not been verified. Gold units and provider BTC-vs-broker CFD identity still need evidence. | In a normal browser, try one small raw quote export without registration. Retain source/export settings and terms; stop at enrollment/challenge/payment. Automated data-host request returned empty HTTP 202; no canary came from this route in Phase 5. No browser challenge was bypassed. |
| 2 | [Tickstory Standard](https://tickstory.com/download-tickstory/) | **US$79** base purchase, includes 1 month; optional **US$9.95/month** renewal. Price is within proposed limits before tax; no total checkout quote or purchase. Lite **US$0**, personal-use only. Professional **US$129**, 12-month inclusion, optional US$99/year; unnecessary initial spend. | Vendor-listed Dukascopy tick start dates: EURUSD 2003-05-04, GBPUSD/USDJPY 2003-05-05, XAUUSD 2003-05-04, BTC/USD 2017-05-23. These are **downloader/vendor claims**, not an independent primary coverage certification. Tickstory is software, not a data vendor; underlying feed rights and service availability remain separate. | First approve a $0 isolated Lite evaluation and license review if appropriate for DAT use. Export CSV only; no MT4/MT5 integration, no existing JForex cache, no terminal. Buy Standard only if the canaries/rights/three-year target pass. Confirm renewal behavior and decline recurring charges. |
| 3 | [Tick Data Suite](https://eareview.net/tick-data-suite) | **US$37.99/month** plus local taxes; automatically renews until cancelled. Within monthly evaluation ceiling only if all-in ≤US$50. Yearly **US$200.90 upfront** and lifetime **US$579** exceed the proposed one-time limit; annual monthly-equivalent pricing is not a $16.70 monthly purchase. | Manager offers tick CSV export from several third-party sources; software is not the owner/seller of source quotes. No current five-symbol three-year inventory was obtained. Mainly MT4 integration, which this project does not need. | Conditional one-month CSV-manager-only alternative, after explicit purchase/license/install approval and verified feed canary. No trial enrollment, card, integration or renewal authorized. Higher ongoing cost than necessary if Tickstory/free exports work. |
| 4 | [FXCM official repository](https://github.com/fxcm/MarketData/blob/3ffd9e3a105efab500126102fc5b207add1946a4/TickData/README.md) / [FXCM Pro](https://www.fxcm.com/pro/market-data/fx-price-feed/) | Public tick files advertised free; **US$0 advertised data fee**, but EULA/usage eligibility unresolved. Premium/commercial quote unknown. | Repo lists weekly ticks for EURUSD/GBPUSD/USDJPY from Jan 2019 with listed years through 2023, UTC, indicative lowest Active Trader spreads. Pro advertises ticks back to 2009 and up to five free years of minute/hour/day data; that does not establish five free years of recent ticks. Gold/BTC are not in the repo's FX list. | Resolve whether DAT use is covered. The linked EULA leads to a form; no form submitted and no tick acquisition made. Request commercial rights/current quote bounds only with explicit communication/enrollment authorization. |
| 5 | [HistData](https://www.histdata.com/f-a-q/) | **US$0 advertised web data fee**; no FTP/SFTP enrollment. | Generic ASCII ticks have bid/ask, M1 is bid-only; fixed EST UTC−5 with no DST, volume removed. Requested pairs/Gold listed, but exact recent five-year bounds and original source rights unverified. BTC not covered by the listed FX/Gold route. | Secondary cross-check only until source/license/coverage evidence passes. Do not silently use bid-only bars or reinterpret EST as New York DST. |
| — | [Tick Data licensed FX](https://www.tickdata.com/product/historical-forex-data/) | **Exact basket price unknown; not established within budget.** | Advertised tick bid/ask from May 2008; minute bars are bid-based. Confirm pair dates, raw/filtered data and license. | Scoped quote required before approval; no contact/purchase made. |
| Reject | [TickAtlas Developer API](https://tickatlas.com/pricing) / [tick schema](https://tickatlas.com/api-reference/ticks) | Starter **US$29/month excludes ticks**; raw-tick Pro **US$79/month exceeds US$50**. Monitor Pro **US$49/year is a different product** and does not grant API tick access. | Finest stored data is one-second quote samples, not every tick; 1-hour requests. Adequate depth/provenance unverified. | No enrollment or paid call. Do not buy a cheaper tier that lacks the required data. |
| Reject pending eligibility | [TrueFX](https://www.truefx.com/contact-truefx/) | No usable current all-in quote for this user. | Institution-only market-data eligibility; internal-use/no-redistribution terms. Legacy “free for everyone” descriptions do not establish access. | No registration or credential enrollment. |

Tickstory [range list](https://tickstory.com/dukascopy-historical-data-available-date-ranges/) is used only for its own advertised downloader coverage. Its [license page](https://tickstory.com/download-tickstory/) explicitly separates software licensing from third-party market-data terms. Paying US$79 cannot resolve a blocked feed, missing historical metadata or underlying data rights. Test export first.

## BTC/USD alternatives and cost decision

The new Tardis sample is a practical **free validation route**, not a free continuous multi-year dataset: only first-of-month days are public without a key. Do not concatenate sparse monthly samples and call them three/five years of complete intraday history or use their selected calendar days to claim a stable edge.

[Tardis Spot pricing](https://tardis.dev/) displays **US$900/month Solo** for all spot exchanges; the US$450/month Academic rate requires eligibility and quarterly/yearly billing. Both exceed US$50. [Billing documentation](https://docs.tardis.dev/faq/billing-and-subscriptions.md) specifies only four months of history for monthly plans, twelve months for quarterly, four years for yearly (Business differs); there are no one-off symbol/date purchases. Full paid Tardis acquisition is **rejected under the proposed budget**. No academic eligibility or bulk redistribution right is assumed.

Existing Bitfinex and public Kraken trade archives remain US$0 trade-series candidates, not a historical BBO solution. Provider BTC/USD via Dukascopy may be economical for quote research if definitions match its own product; it is not automatically Kraken spot or Vantage BTCUSD. For the original broker-specific BTC/Gold question, separately authorized broker CSV exports are the relevant source.

## Futures — separate budget decision

**Preferred quotation route: Databento historical usage pricing, not a live subscription.** [Vendor futures page](https://databento.com/futures) lists CME/CBOT history since 2010 and pricing **from US$0.50/GB**. This is a starting unit rate, **not an exact six-contract basket quote**. Definitions, schemas and actual byte volume determine cost; do not multiply compressed download bytes by this rate and assume it is the bill. The optional US$199/month Standard live plan exceeds this project's ceiling and is unnecessary for offline history.

Request a scoped estimate for **2021-01-01 through 2026-09-30**, raw contract ES/MES, NQ/MNQ, YM/MYM, definitions/status and BBO/MBP-1 (or a documented quote-sampled schema adequate for 1M/3M/5M fills). Compare mini-first and micro-first subsets without substituting their contract economics. Avoid full-depth/order-wide downloads unless justified. Actual micros' listing dates and schemas must be confirmed. Include vendor/exchange license, retention/use/derived-result rights, taxes and transfer/storage.

**Exact total: NOT QUOTED. Budget compliance: UNDETERMINED.** Stop before API/account enrollment or chargeable estimates/downloads; any licensed estimate route requiring credentials needs separate authorization. Do not assert that US$150 purchases five years of BBO for all six products. CME DataMine and Tick Data remain quote-based alternatives with no verified in-budget total. No futures purchase is recommended until an all-in quote fits the ceiling. No email/sales contact was sent.

Use raw contract IDs, unadjusted executable prices, exchange calendars/holidays and historical commissions/fees. Keep predeclared prior-completed-session roll decisions and both-leg costs. NAS100/SP500/USA30 CFDs cannot substitute for NQ/ES/YM.

## Instrument readiness

| Instrument | Phase 5 acquisition status | Three/five-year quote certification | Next gate |
|---|---|---|---|
| EURUSD | Public route confirmed, automated metadata/data unavailable; old 3-day canary preserved | NO | Direct browser canary or authorized isolated downloader evaluation; definitions/terms/calendar |
| GBPUSD | Advertised deep provider/downloader history; no new quote export | NO | Same, including complete untouched periods |
| USDJPY | Advertised deep history; no new decoded export | NO | Same plus JPY quote/PNL currency conversion |
| XAUUSD | Exact product/scale remains unresolved | NO | Raw provider quotes and definitions; separately verify targeted broker mapping |
| BTC/USD | **One new free Kraken quote day, 862,680 events** | NO — one day and missing proof bundle | Quote/fee/spec/calendar review; obtain continuous licensed history within budget |
| ES/MES, NQ/MNQ, YM/MYM | No new acquired history | NO | Scoped licensed quote and explicit enrollment/spend approval |

## Approval proposal — no spending requested yet

The safest immediate operator decision is **US$0: authorize one isolated Tickstory Lite evaluation and license review**, only if its personal-use terms cover the intended DAT evaluation. Scope: one research-only installation, CSV export canaries, no terminal integration, no credentials, no account enrollment, no service/scheduler. If those terms do not cover DAT use, stop; use the normal free provider browser export or request appropriate vendor terms instead. No installation has occurred.

Only after a working canary and suitable rights: a future **separate purchase request** may specify Tickstory Standard **US$79 + applicable tax, hard US$100 all-in cap**, one user/two owned installations as licensed, no recurring renewal, no MT4/MT5 integration. Stop if checkout exceeds that cap or requires an unapproved enrollment. The proposed US$150 ceiling is not approval, and the initial US$0 evaluation would not approve the purchase. No TDS, Tardis, requester-pays S3 or Databento spend is bundled into this proposal.

This narrow evaluation is recommended before committing money because current data-host automation has not worked. Alternatively, an operator can supply existing licensed primary quote exports immediately, with no software purchase or terminal startup by this agent.

## Next statistically meaningful test

Target **2021-01-01–2026-09-30** where available: at least three complete years; five-plus preferred. Keep the Phase 3 proposed 2024 development / 2025 walk-forward / 2026 Jan–Sep sealed final holdout unchanged; earlier years can supply additional development/regime checks only after a frozen protocol amendment made before viewing strategy outcomes. Existing 2017/2018 evaluated periods remain historical diagnostics. The Phase 5 sample is data-validation evidence, never a selected-strategy holdout result.

Acquire in bounded instrument/month partitions with raw hashes, immutable decoder versions and independent expected-session calendars. Preserve actual source IDs and metadata versions. Certify provenance, use rights, UTC/DST, quote completeness, tick/contract values, fees/slippage/financing and exclusions. Require adequate sample sizes, chronological folds, baseline/seeded controls, double-cost stress, parameter stability and multiple-comparison correction before ranking any strategy. No repeated final-holdout tuning.

## Reproduce and verification

From `research/dat_mt5_edge`:

```sh
python -m phase5.sample  # requires exact raw sample under ignored phase5/work/
python -m phase5.review # requires hash-matched normalized.csv under ignored phase5/work/
python -m unittest discover -s tests_phase5 -q
# Existing suites, unchanged:
python -m unittest discover -s tests -q
python -m unittest discover -s tests_phase2 -q
python -m unittest discover -s tests_phase3 -q
python -m unittest discover -s tests_phase4 -q
```

`sample.py` contains the exact documented free URL and pinned raw hash. It does not fetch data, enroll a key or start a broker client; without supplied inputs it fails. The raw 11.6 MB file is retained only in the isolated Windows research workspace. Normalization and the existing Phase 4 certifier were run there from the same source shipped here; the normalized output hash/structural diagnostics were independently rechecked locally. [Verification](results/verification.json) checks **26 unchanged Phase 3/4 source/report/result/test files** and the sample hashes. **84 tests pass**: original 76 plus 8 Phase 5 tests. No certified data, profitability claim or execution authority is implied.
