# DAT MT5 Phase 6.6 — transferred historical-data audit

Recorded 2026-10-22. **BLOCKED — source unavailable; no verified restricted VPS executor.**
Research only, read-only source, non-trading, fail-closed. Publication: existing
[draft PR #2](https://github.com/oluadegbu/Codex--DSV-/pull/2), unmerged.

The requested source is `C:\DirectiveAutoTrader\Researchdata\data\data` on
`WIN-HQAAFGGU1AM`. The directive reports existing transferred CSV/archive data;
this is a distinct acquisition route from protected MT5 caches. Those older
broker restrictions must not automatically be applied to unrelated exchange or
licensed vendor exports. Each transferred dataset needs its own provenance.

## Execution finding

The current Desktop Commander device listing reports the named VPS **Offline**,
last seen approximately **16 hours** before the observation. This is tool-relative
status, not an inferred exact outage timestamp. No alternate connected device was
listed. The process tool exposes command/device/shell/timeout controls, not a
supported user/session-token selector. Prior evidence identifies the runner as
Administrator; its current token cannot be freshly verified while offline.

The managed cloud shell is non-root (uid/gid 1000) and has enforced restricted
network policy, but has no configured VPS/data mount or authorized outbound identity
established by the runtime status. Cloud non-root status is not proof of access to
the Windows source. No unsupported connection, credential discovery, impersonation,
remote startup, new installation or security-policy change was attempted.

The user's Phase 6.6 instruction explicitly requires a verified restricted execution
environment and prohibits processing through the elevated remote executor. It also
instructs preparing the bounded package and reporting BLOCKED when unavailable.
Accordingly no remote process or source-file read/hash/decompression was attempted.
This is an access/execution block, **not** an inventory-only completion claim.

## Dataset inventory and coverage matrix

The searchable [manifest](DATASET_MANIFEST.csv) records **user-reported candidate
families**, not a recursive file inventory. Exact relative filenames, file counts,
sizes, checksums, source timestamps and duplicate findings are **NOT OBSERVED**.
No first/last market date or historical depth is inferred from filename/timeframe
descriptions. No source dataset is declared empty or corrupt based only on a warning.

| Priority / reported dataset | Reported resolution/type | Actual first/last, years, count | Quality / rights | Current disposition |
|---|---|---|---|---|
| 1 EURUSD | Compressed M1 CSV; possible histdata_raw archives | **UNKNOWN / NOT READ** | **UNKNOWN / UNKNOWN** | **NOT EVALUATED — BLOCKED** |
| 2 GBPUSD | Compressed M1 CSV; possible histdata_raw archives | **UNKNOWN / NOT READ** | **UNKNOWN / UNKNOWN** | **NOT EVALUATED — BLOCKED** |
| 3 XAUUSD | Gold files; duka_raw candidates | **UNKNOWN / NOT READ** | Scale, symbol, BBO, volume, rights **UNKNOWN** | **NOT EVALUATED — BLOCKED** |
| 4 BTCUSDT | M1/M3/M5/M15/H1; crypto/funding archives | **UNKNOWN / NOT READ** | Venue, spot/perpetual, fees/funding and rights **UNKNOWN** | **NOT EVALUATED — BLOCKED** |
| 5 ES/NQ/YM/GC | Futures archive; ES/NQ/YM duka_raw labels | **UNKNOWN / NOT READ** | Exchange futures vs index CFD, rolls, license **UNKNOWN** | **NOT EVALUATED — BLOCKED** |
| Other FX | AUDUSD/EURJPY/GBPJPY/NZDUSD compressed M1 | **UNKNOWN / NOT READ** | Source/timezone/rights **UNKNOWN** | **NOT EVALUATED — BLOCKED** |
| Other crypto/indices | Market/funding/index archives | **UNKNOWN / NOT READ** | Product mapping/rights **UNKNOWN** | **NOT EVALUATED — BLOCKED** |

No dataset receives PASS, CONDITIONAL or FAIL certification before inspection.
**PASS datasets: 0; technically verified CONDITIONAL datasets: 0; demonstrated
FAIL datasets: 0; pending datasets: all reported families.** This avoids calling an
unread file technically usable. The directive's warning that some duka_raw files
are empty remains a warning pending exact metadata; empty observed files will FAIL.

## Licensing and provenance assessment

No provider, license acceptance or original download receipt was inspected in this
phase. Folder labels `histdata_raw`, `duka_raw` and `futures` are provenance leads,
not proof of source, authenticity, licensed organizational use or exchange entitlement.
`ES`/`NQ`/`YM` labels must not be assumed to mean CME/CBOT contracts; index CFDs and
continuous synthetic prices are different products. BTCUSDT exchange data cannot
certify Vantage BTCUSD CFD execution or USD/USDT interchangeability.

For each actual file/member, link raw checksum → original URL/provider → acquisition
date/receipt → applicable terms/version → permitted internal organizational research,
retention/normalization and processing location → redistribution restrictions.
Document spot/perpetual, exchange, symbol, quote currency, timestamp clock, volume
units and historical contract/fee changes. Read only inert text evidence; do not
execute dataset scripts, macros, notebooks, binaries or links. Keep raw quotes and
private invoices/account details out of the public PR.

## Exact bounded inspection package

[INSPECTION_PACKAGE.md](INSPECTION_PACKAGE.md) defines the gates, commands, source
and output boundaries, explicit budgets and review sequence. [inspect_data.py](inspect_data.py)
is a standard-library, **not remotely executed** first-stage tool: bounded recursive
metadata/checksum census and explicit-schema CSV/GZIP quality audit. It refuses
non-Windows or administrator execution, requires operator attestation of restricted
source access, skips reparse points, does not extract archives and writes only to a
separate output directory. These checks do not provision ACLs or prove all host
capabilities are restricted. Runtime and filesystem restrictions must be verified
independently before invocation.

No reviewed schema can be supplied truthfully before source discovery. The example
schema is explicitly disabled. Format/timezone/calendar/contract-specific review
follows metadata inventory; unsupported ZIP/vendor formats stay pending a separately
reviewed bounded parser. Partial/capped scans never certify full coverage. The
package refuses data beyond 2025-12-31 for quality analysis and stops on encountering
2026-or-later timestamps before parsing price fields. Hashing opaque source bytes
does not analyze holdout prices; no 2026 strategy evaluation or optimization is allowed.

Prepared code receives only syntax/CLI inspection locally; no synthetic market tests
or source-data certification is substituted for the blocked audit. Tool observations
and publication verification are in [EVIDENCE.json](EVIDENCE.json).

## Ranked inspection shortlist — not usable-data ranking

1. **EURUSD compressed M1:** best first audit target under the directive. If sufficient,
   its M1 observations can support conservative M1/M3/M5 entries with M15/H1 context,
   subject to clock, licensing and executable-cost evidence. Nothing yet proves depth.
2. **GBPUSD compressed M1:** replicate certification independently; don't count duplicate
   archives as independent datasets or concatenate overlapping exports blindly.
3. **XAUUSD:** only after units/price scale, CFD versus spot contract and sessions resolve.
4. **BTCUSDT M1:** identify exchange/product first; derive higher bars deterministically
   and compare supplied M3/M5/M15/H1 for alignment, partial candles and duplicates.
5. **ES/NQ/YM/GC:** establish dated contracts, exchange entitlements, roll schedule and
   adjustment method; continuous back-adjusted bars alone are not executable fills.

No **usable dataset** can yet be ranked. Best immediate backtesting candidate is
**NONE QUALIFIED**; EURUSD is the first certification candidate, not approved input.

## Remaining acquisitions and Phase 6.7 plan

**No purchase is currently justified or proven necessary.** First determine whether
the transferred files already provide sufficient licensed 2023/24 development and
independent 2025 validation coverage. A separate bid/ask source, historical spread/
commission/slippage/funding/contract metadata or licensed futures contracts may still
be necessary; that cannot be decided from the unavailable inventory. Do not pay,
register, install or contact providers automatically.

Smallest safe operator action: restore the existing VPS connector to availability
and expose an officially supported **non-admin, restricted source-read-only session**
with a separate research output directory, using existing approved tooling. No
Administrator processing exception is requested. No terminal or broker connection
is needed for this transferred-data audit. If that route is unavailable, an
operator-controlled, expressly permitted copy of pre-2026 research CSVs plus license
evidence into an existing restricted offline workspace is an alternative; no transfer
or licensing permission is inferred or exercised here.

Then run the census and actual quality inspection, reconcile calendar/DST/contract
and rights evidence, and classify each dataset PASS/CONDITIONAL/FAIL. Only qualified
data may enter Phase 6.7. Preserve the frozen strategy definitions and evaluated-period
lineage; no repeated optimization against old OOS. Tentative, subject to adequate
coverage and existing lineage: 2023 training, 2024 validation/development and
chronological 2025 walk-forward. Do not call any previously tested interval fresh OOS.
The 2026-01-01 through 2026-09-30 final holdout stays sealed.

Retest the unchanged London sweep reversal, NY breakout/retest and liquidity-sweep/
MSS/retest families only where session clocks, resolution and costs support them.
Require side-correct bid/ask or explicitly conservative bar-price uncertainty,
baseline/random-entry controls, predeclared sample and robustness thresholds and
cost-adjusted OOS metrics. Phase 6.6 runs no strategies or optimization.

**Final status: BLOCKED. Actual historical coverage UNKNOWN. Source files read 0;
source changes 0; remote processing 0; certified datasets 0; strategy runs 0; sealed
holdout unopened; MT5/broker connections/orders 0; forward SHADOW OFF.**
