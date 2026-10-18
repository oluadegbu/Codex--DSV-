# Phase 4 — verified-data readiness

**Certified research datasets: NONE. Qualifying strategy candidates: NONE.** Review: 2026-10-17, New York. Phase 4 adds a working, deterministic certification pipeline, recovers primary-format canaries and prepares a passive data interface. It does not resolve the remaining access/licensing/metadata gates by assumption.

No orders, broker connection, credential access/enrollment, terminal startup, purchase, persistent deployment or production-control changes occurred. Existing Phase 3 files, strategy definitions, frozen metrics, trial registry and tests remain unchanged. Draft PR #2 remains the sole publication target; DMB PR #1 and main are untouched.

## Deliverables and outcome

- [Source/cost comparison](SOURCES.md): ten primary/vendor/broker routes covering EURUSD, GBPUSD, USDJPY, Gold, BTCUSD and ES/MES/NQ/MNQ/YM/MYM. Exact historical/schema coverage and all-in costs are explicitly unknown where no scoped quote exists; no signup or purchase was made.
- [Recovery evidence](recovery_observations.json), [reconstructed-data diagnostics](results/recovery.json) and [readiness decisions](results/readiness.json).
- [Certification implementation](certify.py), [offline package CLI](certify_package.py) and [29 Phase 4 tests](../tests_phase4/test_phase4.py).
- [Inactive collector procedure and capability limits](COLLECTOR_PROCEDURE.md), [consumer](collector.py) and [source-hash audit](results/collector_capability.json).
- [Immutable baseline lock](baseline_lock.json): 19 original report/strategy/registry/source-lock/specification/test files verified before review. No previous holdout is called fresh OOS. Phase 3 remains historical baseline evidence, not a dataset license or an execution grant.

## Existing-data recovery

The scoped, read-only scan covered the previously authorized Windows Phase 1/2 research folders, the known terminal's `bases` cache and `MQL5/Files`, plus the isolated local repository artifacts. It was not an exhaustive disk/backup search; no newly verified licensed export or complete source/audit-chain backup was established. Private terminal paths and account identifiers are excluded from public artifacts. Configuration/credential files were not inspected.

### EURUSD July 2022 fragments

Eleven existing daily `.bi5` files match the successful source entries in the retained acquisition manifest. All decode to 1,440 records/day with valid record alignment, UTC-relative minute offsets, nonnegative finite volume, OHLC ordering and no duplicate minute offsets. The record format and 100,000 FX scale are explicit decoder assumptions inherited from the original collector, not newly certified by matching hashes.

Three dates have both sides: **2022-07-07, 2022-07-13 and 2022-07-20**. They produce **4,320 paired minutes**, no unpaired minutes within those days, and no crossed opens/closes. Full paired extrema/grid checks also pass. Median endpoint spread is 0.00004; p95 is 0.00009. Nineteen normalized bars have zero combined quote-volume values; these are not imputed or interpreted as no trades/liquidity. Other files are one-sided and excluded from paired research.

A new Decimal-based normalization is written only under ignored `phase4/work/`. It preserves original bytes and does not overwrite the older float-rendered normalized file. New normalized SHA256: `4a8a0433a5671302f57cbd0f69248da5e5ecf4acedb1cd48d63ea9b7d4f739ff`. The old 4,320-row normalized file hash is independently retained in the recovery manifest. Different rendering/volume arithmetic produces a different normalized hash; it is not a claim of a new primary capture.

This is a useful **structural canary**, not a certified research dataset: three noncontiguous days cannot establish recent multi-regime coverage, DST consistency, complete provider calendars, executable costs or statistical adequacy. Manifest/hash correspondence proves retained object identity, not an independent TLS/source attestation. Metadata/license/decoder review remains open. No strategy was backtested on these fragments.

### Frozen mirrors, BTC and terminal caches

The 2018 EURUSD (91,656 rows) and GBPUSD (58,245 rows) mirrors pass the new Decimal/grid structural diagnostics under the explicitly unverified FX pilot precision assumptions. Their primary chain, recent coverage, calendar completeness and executable costs remain blocked. Gold (55,850 rows) fails the assumed 0.001 price grid as well as its existing unresolved scale/contract/volume-conversion gates. This mismatch **does not identify a correct replacement tick or scaling factor**.

The Phase 1 BTC 2017/2018 original minute-file hashes still match their retained source manifest; the local 27,978-row complete-bucket 30M derivative is hash-verified. Source files are headerless trade candles, not BBO. They retain the documented missing-minute exclusions and already evaluated holdouts. Adding modeled spreads would not certify historical executable bid/ask.

Terminal metadata shows EURUSD/GBPUSD/USDJPY `.hcc` files with year-like names 2023/2024/2026 and BTC `.hcc`/September 2026 `.tkc` files. Filenames and bytes do not establish decoded dates, completeness, broker identity, spread history or contract metadata. No plain market-data export was found in the scoped `MQL5/Files` directory. No proprietary cache was decoded through MT5 or promoted into research, and no terminal/account connection was attempted.

## Instrument readiness matrix

| Instrument | Recovered evidence | Certification / edge testing | Next required evidence |
|---|---|---|---|
| EURUSD | Frozen 2018 mirror; 3 paired July 2022 canary days; opaque terminal cache | QUARANTINED; first choice for data-only validation | Primary quote/decoder/clock/license chain, recent complete sessions, reviewed costs/units |
| GBPUSD | Frozen 2018 Jan/Apr mirror; July fold absent; opaque cache | QUARANTINED; no new OOS | Same, including complete untouched forward periods |
| USDJPY | Opaque cache names only; no qualified decoded export | BLOCKED | Primary quotes, JPY quote/PNL conversion, definitions and cost schedule |
| XAUUSD / exact Vantage Gold symbol | Unverified mirror scale/grid; no qualified broker export | QUARANTINED | Raw scale/precision, exact product/suffix/lot/tick value, session and volume semantics |
| BTCUSD | 2017/2018 spot trade-candle proxy, opaque broker cache | QUARANTINED for quote-certified testing | Recent historical BBO, spot-vs-CFD identity, venue contract/fees and untouched periods |
| ES/MES | No licensed contract-aware history | BLOCKED | Contract-level quotes/definitions/calendar, roll and fee evidence |
| NQ/MNQ | Same | BLOCKED | Same; never substitute NAS100 CFD |
| YM/MYM | Same | BLOCKED | Same; micro listing dates verified independently |

Vantage's [own product comparison](https://www.vantagemarkets.com/commodities-trading/gold-trading/xauusd24-7/) distinguishes traditional XAUUSD (100 oz) from XAUUSD247 (1 oz), with different sessions and account/region qualifications. This resolves a **generic product distinction**, not the targeted demo-server symbol or its historical tick value. No automatic 100× Gold correction or product substitution is permitted.

## Certification protocol

The package consists of `manifest.json`, paired UTC-open 1M `quotes.csv`, independently sourced `calendar.json` expected-minute epochs and `proofs/{role}.txt` for provenance, license, clock, calendar, contract, costs and normalization. The reviewed bundle SHA binds the complete manifest, each proof hash, the data hash and the calendar hash. The separate repository-owned reviewed-bundle registry is currently empty; a dataset cannot approve itself by supplying `verified=true` or its own registry.

Hashes establish identity, not truth. Before a bundle enters that registry, review must substantiate primary acquisition and permitted use, immutable decoder and raw-to-normalized correspondence, DST/UTC semantics, actual calendar and exclusions, exact units/contracts and dated costs. No credential or trading permission follows from such a data review. Synthetic test fixtures exercise the positive path but are never entered in the market registry or reported as market evidence.

The deterministic checks reject empty/ragged/duplicate/out-of-order bars, invalid/nonfinite/crossed quotes, off-grid precision, inconsistent tick size/value/point value, unknown volume semantics, incompatible cost currency without conversion, missing/changed proofs and calendar mismatches. Floating conversion dust is tolerated only within 1e-8 of one tick; it cannot repair a material scale mismatch. A futures bundle requires one raw contract identity and explicitly unadjusted prices; roll portfolios remain a separate predeclared evaluation concern.

The calendar must independently enumerate the admitted research sessions. Missing minutes and quotes outside it quarantine the package. There is no interpolation or calendar inferred from observed data. The Phase 4 gate is deliberately stricter than a raw 99% availability statistic: unresolved gaps must be remediated or documented whole-session exclusions must be included in a separately reviewed calendar. No existing calendar was fabricated to make the pilot pass.

A package overlapping declared previously evaluated intervals is denied fresh-OOS use. Bundle review must check that lineage against the frozen registry; an empty list alone is not proof of novelty. Data-level certification is distinct from research readiness: readiness additionally requires at least 60 observed UTC days and last data within 120 days of an explicit as-of timestamp. Neither flag proves sufficient trade sample, edge significance or broker execution readiness. Strategy promotion still requires the Phase 3 predeclared economic/sample/stability/multiple-testing gates.

## Results and forward-SHADOW status

**New certified edge backtests: 0. Ranked qualifying candidates: NONE.** Repeating the frozen pilot on unchanged, uncertified data would not create fresh evidence. Phase 3's full matrix, positive-but-tiny subsets and 142 rejected variant/control trials are preserved unchanged. No new holdout was consumed, tuned against or relabeled.

The passive consumer is ready for **offline quote-validation rehearsal only**. Its bounded bytes-in/tuple-out interface has no SDK, file I/O, sockets, callbacks or broker handles. The pinned capability audit passes, including tests that process valid data with file opening/imports disabled and reject order/modification/account/password payload fields. These are scoped checks of the consumer, not proof about an arbitrary host, an external exporter or an MT5 session. No connected collector exists or is activated. See the [separately gated procedure](COLLECTOR_PROCEDURE.md).

## Automated next actions versus human gates

Safe automatic work: validate supplied exports in the isolated package format, check source/data/proof hashes, reconstruct existing raw canaries offline, classify gaps against a documented calendar, audit the passive consumer and rerun deterministic tests. Once a genuine evidence bundle is verified, freeze untouched chronology and protocol before any strategy evaluation. Do not tune repeatedly on final holdouts.

Human/access gates: provider eligibility or account/license enrollment; credential use; scoped requester-pays or licensed-data acquisition with an all-in estimate and dollar ceiling; broker/terminal startup/connectivity; persistent deployment. The [Phase 3 acquisition plan](../phase3/ACQUISITION_PLAN.md) remains unexecuted. A supplied existing licensed primary export is the shortest path that avoids new enrollment or spending. The source comparison lists alternatives; none has an approved purchase total.

Before any broker-connected SHADOW collection, review and separately authorize the exact data-only exporter/session and prove its capability restriction. If that cannot be enforced, use manual file exports from a separately authorized session. Any DEMO/live order requires a separate authorization; Phase 4 grants none.

## Reproducibility and validation

From `research/dat_mt5_edge`, using the existing frozen local normalized inputs plus the eleven recovered raw canaries under ignored `phase4/work/raw/`:

```sh
python -m phase4.run
python -m phase4.capability_audit
python -m unittest discover -s tests -q
python -m unittest discover -s tests_phase2 -q
python -m unittest discover -s tests_phase3 -q
python -m unittest discover -s tests_phase4 -q
# Independently supplied isolated package; exit 2 if quarantined:
python -m phase4.certify_package --package /path/to/isolated/export --asof 1792281600
```

The public repository contains code, hashes and sanitized diagnostics, not licensed/raw quote files or private host records. Missing local input files cause failure rather than automatic download. `phase4.run` verifies all 19 baseline hashes and regenerates recovery/readiness outputs deterministically; repeat-output byte hashes are tested. **76 tests pass: 20 Phase 1 + 17 Phase 2 + 10 Phase 3 + 29 Phase 4.** Existing baseline files are unchanged. No profitability claim is supported.
