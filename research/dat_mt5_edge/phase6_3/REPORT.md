# DAT MT5 — Phase 6.3 VPS Historical Data Recovery (metadata-only)

**Recorded:** 2026-10-19. **Mode:** RESEARCH ONLY / READ-ONLY CACHE INSPECTION / SHADOW / NON-TRADING / FAIL-CLOSED.  
**Disposition:** The named MT5 cache files and additional relevant EURUSD/GBPUSD M1 files **exist**; software-documented cache classes are established. **Actual bar/tick coverage and records are NOT VERIFIED. No broker-data use rights are certified. No market dataset is promoted.**

This phase is an additive data-inventory report for [draft PR #2](https://github.com/oluadegbu/Codex--DSV-/pull/2). Prior strategy implementations, historical OOS/final-holdout results, Phase 3–6.2 artifact contents, production DAT/DSV/DMB and all MT5 caches remain untouched.

## Inspection boundary and exact nature of evidence

Authorized host was online when queried. Inspected **directory names and file metadata only** using Desktop Commander `list_directory` and `get_file_info`, limited to the specified MT5 `bases` subtree and the exact relevant broker/symbol `history` and `ticks` subfolders. Avoided account databases, credentials, configuration secrets, trading journals, mail, `trades`, logs and all file contents.

- **No shell/process, MT5, MetaEditor, strategy tester, API, authentication or broker connection was started.**
- **No file was opened/read as binary, hashed, decoded, copied, renamed, exported or changed.** No independent checksum evidence exists.
- No credential, administrator elevation, additional permission, installation, expenditure, download or network-policy change was requested.
- Metadata times below are **UTC** exactly as returned by the filesystem `Z` fields, **not** market timestamps. Files may retain old modification times after copies/synchronization. A filename's year/month is an **index-label inference**, not proof of date-span or row count.
- To avoid publishing the host's full account-folder path, relative paths start beneath `bases/`. The verified server directories were `Exness-MT5Real10` and `VantageMarkets-Demo`.

## Official platform semantics — supported classification, not contents proof

MetaQuotes [Files and Folders](https://www.metatrader5.com/en/terminal/help/start_advanced/structure) documents `yyyy.hcc` as a symbol's **one-minute price-history** files, by year, and `ticks.dat` as associated **symbol tick history**; derived timeframe `*.hc` files reside in a separate calculated `cache` directory. MetaQuotes [Real and Generated Ticks](https://www.metatrader5.com/en/terminal/help/algotrading/tick_generation) documents monthly `YYYYMM.tkc` files as **downloaded real tick-history cache files**. Consequently these filenames are not *merely generic configuration names*, but **their individual record counts, integrity, origin and execution suitability remain unverified** because content inspection and terminal access were prohibited.

The `*.hcc` class supports an **M1 OHLC candidate**, not independently a paired bid/ask tick sequence. The `*.tkc` class supports a **tick-history candidate** (potentially bid/ask), but the single named file is labeled September 2026 only. `ticks.dat` is documented as a tick store, but identically sized short `ticks.dat` files cannot prove deep tick coverage; they may hold little/no useful range, cache bookkeeping or recent slices. We explicitly do **not** assert which is true without a supported export. No custom `*.hcc`/`*.tkc` binary decoder or reverse-engineering was used.

## File inventory — all values directly verified as filesystem metadata

Column `modified UTC` is **filesystem last-modified**, not verified market coverage. Bytes are exact. A dash in "verified quote range" applies to **every** row: **NONE**. These are *not* quoted dates within the files.

| Server / exact symbol | Relative path under that server | Size (bytes) | Last modified (UTC) | Supported file-type interpretation |
|---|---|---:|---|---|
| Exness-MT5Real10 / EURUSD | `history/EURUSD/2024.hcc` | 14,518,323 | 2026-08-29 21:04:25.911 | M1 history cache labeled 2024 |
| Exness-MT5Real10 / EURUSD | `history/EURUSD/2026.hcc` | 15,144 | 2026-08-29 21:09:09.196 | M1 history cache labeled 2026; low size unexplained |
| Exness-MT5Real10 / GBPUSD | `history/GBPUSD/2024.hcc` | 16,253,196 | 2026-08-29 21:04:25.950 | M1 history cache labeled 2024 |
| Exness-MT5Real10 / GBPUSD | `history/GBPUSD/2026.hcc` | 15,144 | 2026-08-29 21:09:09.222 | M1 history cache labeled 2026; low size unexplained |
| Exness-MT5Real10 / BTCUSDz | `history/BTCUSDz/2026.hcc` | 24,479,811 | 2026-09-19 17:26:08.998 | M1 history cache labeled 2026 |
| Exness-MT5Real10 / BTCUSDz | `ticks/BTCUSDz/ticks.dat` | 123,312 | 2026-09-19 17:26:09.010 | Tick-associated file; actual paired ticks unknown |
| VantageMarkets-Demo / EURUSD | `history/EURUSD/2023.hcc` | 9,827,739 | 2026-08-29 21:04:24.510 | **Additional find:** M1 history cache labeled 2023 |
| VantageMarkets-Demo / EURUSD | `history/EURUSD/2024.hcc` | 14,518,323 | 2026-08-29 21:04:25.911 | **Additional find:** M1 history cache labeled 2024 |
| VantageMarkets-Demo / EURUSD | `history/EURUSD/2026.hcc` | 15,333 | 2026-08-29 21:09:09.169 | **Additional find:** M1 history cache labeled 2026; low size |
| VantageMarkets-Demo / EURUSD | `ticks/EURUSD/ticks.dat` | 123,312 | 2026-09-26 11:01:42.107 | Tick-associated file; actual paired ticks unknown |
| VantageMarkets-Demo / GBPUSD | `history/GBPUSD/2023.hcc` | 9,913,566 | 2026-08-29 21:04:24.539 | **Additional find:** M1 history cache labeled 2023 |
| VantageMarkets-Demo / GBPUSD | `history/GBPUSD/2024.hcc` | 16,253,196 | 2026-08-29 21:04:25.950 | **Additional find:** M1 history cache labeled 2024 |
| VantageMarkets-Demo / GBPUSD | `history/GBPUSD/2026.hcc` | 15,333 | 2026-08-29 21:09:09.197 | **Additional find:** M1 history cache labeled 2026; low size |
| VantageMarkets-Demo / GBPUSD | `ticks/GBPUSD/ticks.dat` | 123,312 | 2026-09-26 11:01:42.109 | Tick-associated file; actual paired ticks unknown |
| VantageMarkets-Demo / BTCUSD | `history/BTCUSD/2026.hcc` | 28,638,366 | 2026-10-02 21:00:00.384 | **Additional find:** M1 history cache labeled 2026 |
| VantageMarkets-Demo / BTCUSD | `ticks/BTCUSD/202609.tkc` | 796,555 | 2026-09-19 17:32:19.324 | **Named finding:** monthly tick cache labeled Sep 2026 |
| VantageMarkets-Demo / BTCUSD | `ticks/BTCUSD/ticks.dat` | 123,312 | 2026-09-26 11:01:42.097 | Tick-associated file; actual paired ticks unknown |
| VantageMarkets-Demo / BTCUSDz | `history/BTCUSDz/2026.hcc` | 15,144 | 2026-09-19 17:26:08.999 | **Additional find:** distinct symbol, M1 cache labeled 2026 |
| VantageMarkets-Demo / XAUUSD.crp | `ticks/XAUUSD.crp/ticks.dat` | 123,312 | 2026-09-26 11:01:42.220 | Tick-associated file; actual paired ticks unknown |

**Key warning: cross-server provenance.** Exness and Vantage EURUSD `2024.hcc` have **exactly the same 14,518,323-byte size and last-modified timestamp (down to milliseconds)**; GBPUSD `2024.hcc` likewise match at 16,253,196 bytes and identical timestamp. This is consistent with copies/shared cache origin, but **not proof of byte-identical contents**, independent broker price histories, or any license transfer. Avoid treating the files as independently sourced broker datasets. Do not hash/copy them without a subsequent permitted evidence-handling scope.

**Other coverage warnings:** No `2025.hcc` was visible in the exact listed EURUSD/GBPUSD history directories; `2023.hcc` was visible only under Vantage. Absence in local folders does **not** prove the broker servers lack history. The small 2026 EURUSD/GBPUSD files cannot establish 2026 coverage; neither file last-modified date nor naming proves row counts. The repeated 123,312-byte `ticks.dat` size across instruments suggests caution about interpreting them as large historical tick archives, but we **did not establish** whether they contain quotes, indexing, headers or another cache representation.

## Per-instrument data recovery assessment

| Broker and exact symbol | Observed types | Coverage: verified vs inferred | Bid/ask history | License/export status | Main quality issue | Minimum next action |
|---|---|---|---|---|---|---|
| Exness-MT5Real10 / **EURUSD** | 2024/2026 HCC | **Verified records: none**; filename labels 2024, 2026 only | **Unverified**; HCC is M1, not paired BBO; no tick files observed in symbol's named ticks subtree | Applicable data reuse/export terms **unresolved** | Missing 2025 locally; 2026 HCC tiny; cross-server possible copy | Obtain Exness written applicable data-use terms; later separately authorize broker-native M1 + tick CSV export with date bounds |
| Exness-MT5Real10 / **GBPUSD** | 2024/2026 HCC | **Verified records: none**; 2024/2026 inferred label | **Unverified** | Unresolved | Same as EURUSD | Same |
| Exness-MT5Real10 / **BTCUSDz** | 2026 HCC, ticks.dat | **Verified records: none**; 2026 filename only | **Unverified**, despite documented tick class | Unresolved | No earlier years; broker suffix / contract identity unverified | Clarify proprietary symbol, specs, fees, funding and permitted bounded tick export |
| VantageMarkets-Demo / **EURUSD** | 2023/2024/2026 HCC, ticks.dat | **Verified records: none**; 2023/2024/2026 inferred labels | **Unverified** | Applicable Vantage entity and third-party market-data rights **unresolved** | Missing 2025 locally; cross-server 2024 provenance; identical-size ticks.dat | Verify rights and, if separately approved, use supported export to inspect UTC/calendar/paired history and row counts |
| VantageMarkets-Demo / **GBPUSD** | 2023/2024/2026 HCC, ticks.dat | **Verified records: none** | **Unverified** | Unresolved | Same issues as EURUSD | Same |
| VantageMarkets-Demo / **BTCUSD** | 2026 HCC, 202609 TKC, ticks.dat | **Verified records: none**; tick-cache *month* Sep 2026 inferred by filename only | **Potential** in TKC file class; **not verified in this file** | Unresolved | One monthly TKC is not multi-year continuous BBO; price scale/sessions/commission/funding unknown | Obtain export rights; later manually export bounded tick month and compare to M1 series |
| VantageMarkets-Demo / **BTCUSDz** | 2026 HCC | **Verified records: none** | **Unverified** | Unresolved | Distinct symbol; mapping to BTCUSD uncertain | Verify if valid tradable instrument versus placeholder; do not silently merge with BTCUSD |
| VantageMarkets-Demo / **XAUUSD.crp** | ticks.dat | **Verified records: none**; no HCC identified for this symbol in approved inventory | **Unverified** | Unresolved | Suffix, contract multiplier, gold units, swap/financing, tick quality unknown | Clarify symbol identity/contract and provider rights before any native tick CSV export |

**Overall conclusion:** Cache file types are **identifiable** by official MT5 documentation. The actual price **records**, timestamps, paired quotes, completeness, trade-executable contract model and permitted DAT research rights are **not** identifiable from directory/size/date metadata alone. Do not label a symbol `CERTIFIED_RESEARCH_DATA`.

## Supported/documented extraction route — NOT USED IN PHASE 6.3

The official [MetaTrader 5 Market Watch Help](https://www.metatrader5.com/en/terminal/help/trading/market_watch) documents `Market Watch → Symbols → Bars or Ticks → select instrument/timeframe → Request → Export CSV`. The `Request` operation can fetch currently available broker-server data; merely having an old cache does not guarantee local-only extraction or a particular history depth. CSV export is an explicitly documented method, **not** a guarantee that license terms permit DAT retaining/analyzing the result.

The official [MQL5 CopyRates](https://www.mql5.com/en/docs/series/copyrates) and [CopyTicksRange](https://www.mql5.com/en/docs/series/copyticksrange) interfaces are another documented way to obtain M1 bars and bounded tick sequences, respectively, but using these requires **separate authorization to run a terminal/script/API**; such activity was expressly excluded here. **No custom parser of proprietary cache binaries** should be written. M1/OHLC bars do not reconstruct a true time-varying ask series; exported tick flags/Bid/Ask must be inspected if seeking bid/ask-based execution modelling.

Official MetaQuotes [Python integration documentation](https://www.mql5.com/en/docs/python_metatrader5/mt5copyratesfrom_py) describes UTC timestamps in its API, while chart/server-time displays and native export time interpretations require independent verification against the actual broker's clock/DST and a source control sample. Do not assume the Windows filesystem `modified` timestamps, file labels, exported CSV clock, or broker chart timezone are interchangeable. Record terminal build, broker server identity (without account IDs), exporter semantics and trusted UTC transformations **after** any authorized export.

A future approved read-only market-data session should first use native GUI export, recording: request start/end, exact returned earliest/latest timestamps, count of M1 bars/ticks and nontrading days, bid/ask/last flags, source server/timezone/DST, export-version fields, symbol digits/point/tick value, contract size, minimum/step lots, PnL currency, realistic spread/commission/slippage/swap/holiday calendars, license wording, and output hash. Export only into an **approved isolated research path**, never directly into production or source history-cache directories. **Authorization to inspect metadata here is not authorization for this next step.**

## Licensing and legal scope — open gate, no determination of permitted use

- **Exness:** See [official Exness legal documents](https://www.exness.com/legal-documents/). Exness offers different legal entities and agreements; `Exness-MT5Real10` is a **server label**, not verified proof of which legal entity, account contract, quote-provider rights or DAT organizational retention terms apply. No applicable signed grant was accessed and no permission to export/reuse/redistribute was inferred.
- **Vantage:** Its [official regulatory/legal-document index](https://www.vantagemarkets.com/regulations/) expressly states entity-dependent agreements. Its [demo trading description](https://www.vantagemarkets.com/trading-platform/demo-trading/) supports practising/test strategies within the platform but does **not** itself grant independent organizational archival, data redistribution, published-derived-data or automated extraction rights.
- **Tickstory Lite:** Remains disallowed for this DAT use without a new applicable vendor permission per Phase 6.1. No Tickstory downloads or decompilation.
- **Dukascopy:** Unresolved DAT organizational use/storage/automation rights remain blocked per Phase 6.1. Existing local broker caches do not resolve Dukascopy terms.

A broker/native GUI export being technically possible must **not** be conflated with an appropriate right to build a research data repository. Minimum authorization is a documented provider/entity grant or independently evidenced applicable agreement covering internal historical export, retention, normalization, automated/strategy testing and aggregate publications. No vendor was contacted in this phase.

## Comparison against Phase 6.2 readiness gates

| Phase 6.2 criterion | Phase 6.3 observation | Disposition |
|---|---|---|
| Licensed source and reviewed proof bundle | No signed/applied research export license reviewed | **FAIL / NOT VERIFIED** |
| Paired historical bid/ask, tick grid and symbol economics | Cache types documented, no actual rows/export/specs inspected | **FAIL / NOT VERIFIED** |
| Calendar-based coverage ≥99% per fold and overall | Actual quote timestamps/expected calendar absent; 2025 HCC file not visible in checked EUR/GBP directories | **FAIL / NOT VERIFIED** |
| Minimum trades ≥100 total, ≥20 per fold, ≥60 active UTC days | No market/strategy trade events generated or reviewed | **NOT EVALUATED** |
| Sessions ASIA/LONDON/NEW_YORK and TREND/RANGE/VOLATILE robustness | No admissible data or certified chronology | **NOT EVALUATED** |
| Six side-specific spread/slippage/commission/financing stress scenarios | No verified broker pricing, swap/financing and commission schedule | **NOT EVALUATED** |
| 2024 development and 2025 walk-forward | No 2025 HCC in enumerated EUR/GBP directories; no confirmed independent dataset | **BLOCKED** |
| 2026-01-01 to 2026-09-30 sealed final holdout | Files not decoded; no strategy read of 2026 history; earlier holdout lineage unchanged | **PRESERVED / NOT ACCESSED** |
| Quote-only forward shadow | No quote feed, account or terminal started | **INACTIVE** |
| No live/DEMO order authority | No trading APIs, orders or production changes | **PRESERVED: NONE** |

**No P&L, new edge, trade backtest, certified OOS evaluation or forward-shadow result is claimed.** Phase 6.2's earlier 32 synthetic software fixture results are historical and not rerun/reinterpreted as Phase 6.3 market evidence.

## Minimum next operator decision

**Priority 1, rights first:** Identify which Exness and Vantage contractual entity/market-data terms apply **without exposing account credentials**, and obtain written clarification that DAT may export *already entitled* historical paired quotes, retain them in an isolated internal research store and perform automated/offline research and aggregate-only reporting. No message is sent without explicit approval.

**Priority 2, separately approved data-only action:** Once rights and operational approval are confirmed, use **broker-supported MT5 GUI export** on a small EURUSD/GBPUSD M1 and tick-date canary, plus BTCUSD/XAUUSD where permitted. Do not use or reverse-engineer raw `*.hcc`, `*.tkc` or `ticks.dat` binaries; a non-privileged operator-controlled session and isolated export location must be authorized separately. No export creation or copied protected file is approved by Phase 6.3.

**Priority 3, certification:** Run the existing Phase 4 evidence-bundle certification followed by Phase 6.2 coverage, cost and chronological walk-forward gates **only after receiving appropriately licensed CSV/tick data**. Keep 2026 sealed OOS untouched until new independent validation is authorized.

**FINAL STATUS: METADATA SURVEY COMPLETE / 19 OBSERVED CACHE FILES / RECORD-LEVEL COVERAGE UNKNOWN / BID-ASK UNKNOWN / LICENSE UNRESOLVED / CERTIFIED DATASETS 0 / STRATEGY AND HOLDOUT RESULTS UNCHANGED / FORWARD SHADOW OFF / MT5 AND ORDERS OFF / DRAFT PR #2 UNMERGED.**
