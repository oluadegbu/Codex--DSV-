# DAT MT5 Phase 6.4 — Broker data rights and export feasibility

Recorded 2026-10-20 UTC. Research only; fail-closed; no execution authority.
Publication target: [existing draft PR #2](https://github.com/oluadegbu/Codex--DSV-/pull/2).

**Decision: neither broker is cleared for DAT historical-data acquisition.**
Applicable account entities and accepted agreements are **UNKNOWN**. Native MT5 CSV
export is documented **YES** as a platform capability; permission for the proposed
external organizational research is **UNKNOWN** for these accounts. Current Exness
SC/B.V./VG terms contain an explicit adverse restriction, so reliance on those
standard terms alone for research beyond own trading with Exness is **NO**.
No export method is currently authorized to run. Certified datasets remain **0**.

This phase adds documentation, sanitized filesystem metadata and an offline
metadata/preservation verifier. Earlier Phase 3–6.3 results, strategy definitions,
2026 sealed holdout, production controls and DMB PR #1 are unchanged. No new
backtest or performance claim is made.

## Applicable entities and rights

Existing non-sensitive evidence establishes only the server-folder labels
`Exness-MT5Real10` and `VantageMarkets-Demo`. Neither identifies a contracting legal
entity, accepted agreement, account owner entitlement or upstream data license.
No account/configuration database, credential, journal or personal-area record was
opened. The required evidence is a redacted agreement cover/entity/version and
applicability confirmation supplied by the operator, or written broker confirmation.
Do not publish account numbers, addresses or credentials.

| Broker | Official candidate entities reviewed | Applicable existing account entity | DAT external research permission |
|---|---|---|---|
| Exness | SC Ltd (Seychelles, SD025); B.V. (Curaçao, 0003LSI); VG Ltd (BVI, SIBA/L/20/1133). The official index also lists Forexite Ltd (Belize); this is not an exhaustive regional list. | **UNKNOWN** | **UNKNOWN** for this account; **NO** to relying on the three reviewed standard agreements alone for use beyond own genuine trading with Exness |
| Vantage | Global Limited (Vanuatu, 700271); Markets (Pty) Ltd (South Africa, FSP 51268); VIG Group (Mauritius, GB24203446); UK has separate documentation | **UNKNOWN** | **UNKNOWN**; receipt of market information and demo strategy practice do not establish external database/automated research rights |

Official [Exness legal index](https://www.exness.com/legal-documents/) and
[Vantage entity-specific legal index](https://www.vantagemarkets.com/regulations/)
were reviewed on the report date. Current documents do not establish which terms
governed 2023/24 acquisition, whether a later amendment applies now, or a license
transfer between server folders.

Exness [SC agreement](https://www.exness.com/cdn/media/exnesssc/exness_sc_client_agreement.pdf),
24 July 2026 v039, Part C §2.5, restricts collecting/using platform data beyond the
client's genuine trading with Exness, including external systems. Part C §4.3
allows specified storage/analysis but requires written consent for third-party
reproduction. These provisions must be read together; §4.3 is not a sufficient
standalone grant for DAT's wider external research. Conditional decision **NO**
under standard terms for that wider purpose, pending a written applicable grant.
This is an operational permission assessment, not an account-specific legal ruling.

The [B.V. v026](https://www.exness.com/cdn/media/exnessbv/exness_bv_client_agreement.pdf)
and [VG v028](https://www.exness.com/cdn/media/exnessvg/exness_vg_client_agreement.pdf)
agreements, also dated 24 July 2026, contain equivalent own-trading/external-data
restrictions in Part C §2.5 and storage/third-party provisions in §4.3. Their
indicator provisions add restrictions but are not treated here as a universal ban
on every raw-price research use. Clarification must expressly cover non-trading
DAT research, internal cloud processing and aggregate-only public reporting.

Vantage [Global Limited agreement](https://www.vantagemarkets.com/company-profile/legal-documentation/vantageglobal-clientagreement)
§3.6 permits receiving market data through online services and recognizes third-party
services; §9.1(b) reserves intellectual-property use absent applicable permission.
No express DAT organizational archival/export/backtesting grant was established.
The [South African agreement](https://www.vantagemarkets.com/company-profile/legal-documentation/vantagemarkets-clientagreement)
(August 2025) describes an intermediary rather than transaction principal; the
[Mauritius agreement](https://www.vantagemarkets.com/company-profile/legal-documentation/vantageglobal-vig-clientagreement)
identifies a different entity. Brand-wide assumptions are unsafe. Absence of a
located research grant is **UNKNOWN**, not proof of a universal broker prohibition.

## Decisions by proposed method

YES = evidenced for the stated narrow question; NO = disallowed/unsuitable in the
stated scope; UNKNOWN = not established. Technical support never substitutes for
data-use rights or operator authorization.

| Method | Broker | Documented technical support | DAT data-use permission for existing account | Authorized now |
|---|---|---|---|---|
| MT5 Symbols → Bars → M1 → Export CSV | Exness | **YES**, generic platform; actual server/build/range **UNKNOWN** | **UNKNOWN**; standard reviewed Exness terms alone: **NO** for broader external use | **NO** |
| Same native M1 method | Vantage | **YES**, generic platform; actual server/build/range **UNKNOWN** | **UNKNOWN** | **NO** |
| MT5 Symbols → Ticks → Export CSV | Exness | **YES**, generic platform; actual paired tick availability **UNKNOWN** | **UNKNOWN**, with same Exness restriction | **NO** |
| Same native tick method | Vantage | **YES**, generic platform; actual paired tick availability **UNKNOWN** | **UNKNOWN** | **NO** |
| Broker supplies expressly licensed CSV without terminal use | Both, separately | **UNKNOWN** whether support will supply it | **UNKNOWN** until written scope is confirmed | **NO** acquisition yet; inquiry drafts only |
| Exness public tick-history archive | Exness | **YES**, official archive advertised; requested dates not downloaded/verified | **UNKNOWN** for DAT; publication/download availability is not a use grant | **NO** |
| File → Save current chart CSV as genuine bid/ask ticks | Both | **NO**, wrong data product; chart bars only | **UNKNOWN** for bar reuse | **NO** |
| Raw HCC/TKC/ticks.dat copying, hashing or custom decoding | Both | **NO**, excluded from proposed supported route; no decoder assessed | **UNKNOWN** | **NO**, explicitly prohibited |
| Python/MQL historical-data calls | Both | **YES**, documented interfaces; account/build availability **UNKNOWN** | **UNKNOWN** | **NO**, terminal/API execution not authorized |
| Strategy Tester generated ticks as genuine broker tick export | Both | **NO**, generated sequence is not observed bid/ask history | **UNKNOWN** | **NO** |

Official [MT5 Market Watch help](https://www.metatrader5.com/en/terminal/help/trading/market_watch)
documents Bars/Ticks requests and CSV export, including external application
analysis. This is platform functionality, not a license from either broker.
Request may fetch server history and write terminal caches. The documentation
describes all available history; a bounded request cannot be assumed without
verifying the installed GUI's controls. If request bounds cannot be guaranteed,
stop and use broker-supplied bounded CSV rather than silently widening the action.

Exness's [public archive](https://www.exness.com/tick-history/) is a separate possible
product. Its [support article](https://get.exness.help/hc/en-us/articles/360021547851-Tick-history)
names MT4Real1/3/9 feeds; those do not establish provenance for MT5Real10. Neither
archive prices nor account order-history exports prove this VPS cache's coverage.
No archive, account or historical quote file was acquired here.

## M1 bars versus genuine historical ticks

| Product | What it can support after certification | What it cannot establish |
|---|---|---|
| M1 OHLC, tick volume, recorded spread, real volume where supplied | Minute structure, indicative signals, conservative bar tests with separately evidenced costs | Intraminute path, simultaneous bid/ask evolution, exact stop/retest order or real tick fills |
| Native historical tick CSV with valid timestamps, Bid/Ask and change flags | Observed broker quotes, side-correct hypothetical fills, spread/path analysis | Executed fills, queue depth, guaranteed liquidity, historical fee/contract terms, independent exchange trades |
| Chart-save CSV / synthetic tester ticks | Limited chart history / simulation fixture | Independent full history / genuine recorded ticks |

The official [MqlRates structure](https://www.mql5.com/en/docs/constants/structures/mqlrates)
separates tick count from traded volume. A bar spread cannot reconstruct ask OHLC
or the time-varying spread path. Do not treat OTC tick volume as exchange volume.
The [MqlTick structure](https://www.mql5.com/en/docs/constants/structures/mqltick)
includes quote sides, time and change flags; unchanged values may carry forward.
Same timestamp alone is not sufficient reason to discard an otherwise distinct
tick. An absent/zero Ask or Last must not be invented from a bar spread.

Native CSV timestamp convention must be confirmed for this exporter/server,
including historical DST transitions. Python API UTC documentation does not prove
native GUI CSV is UTC. Preserve source clock and a reviewed UTC conversion; reject
ambiguous times. Confirm actual digits, point, tick size/value, lot size/step,
currency, fees, swaps, sessions and symbol identity before executable modelling.
`BTCUSDz`, `BTCUSD` and `XAUUSD.crp` must not be silently renamed or merged.

## 2023/2024 cache assessment — metadata only

[CACHE_METADATA.json](CACHE_METADATA.json) records 19 files re-observed on
2026-10-20 using directory traversal and filesystem stat only, scoped to the two
named servers and requested instrument families. No protected contents, checksums,
prices or market timestamps were inspected. User/host/private absolute paths are
omitted. This confirms the prior [Phase 6.3 inventory](../phase6_3/REPORT.md), not a
new dataset. The metadata-check process ran via the existing Windows runner;
it did not start MT5. The runner is not a certified standard-user export route.

| Server | Instrument | Filename labels found | Actual market coverage | Duplicate risk |
|---|---|---|---|---|
| Exness-MT5Real10 | EURUSD / GBPUSD | 2024, 2026 HCC | **UNKNOWN**; no 2023/2025 HCC observed in scoped folders | 2024 size and modification time match corresponding Vantage files |
| VantageMarkets-Demo | EURUSD / GBPUSD | 2023, 2024, 2026 HCC; ticks.dat | **UNKNOWN**; 2025 HCC not observed | Same 2024 cross-server warning; repeated ticks.dat sizes prove nothing about quotes |
| Exness-MT5Real10 | BTCUSDz | 2026 HCC, ticks.dat | **UNKNOWN** | Contract/source identity unresolved |
| VantageMarkets-Demo | BTCUSD | 2026 HCC, 202609 TKC, ticks.dat | **UNKNOWN** | September tick label intersects sealed holdout: do not export it |
| VantageMarkets-Demo | BTCUSDz / XAUUSD.crp | 2026 HCC / ticks.dat respectively | **UNKNOWN** | Distinct symbols; no inferred Gold scale or deep tick archive |

EURUSD 2024 is **14,518,323 bytes**, modified
`2026-08-29T21:04:25.911159Z` in both server folders; GBPUSD 2024 is
**16,253,196 bytes**, modified `2026-08-29T21:04:25.950164Z` in both.
Treat these as two possible shared-origin/copy pairs, not independent feeds or
proven byte duplicates. Vantage's EURUSD/GBPUSD 2023 files are **9,827,739** /
**9,913,566 bytes**. Their smaller sizes do not establish partial-year fractions.

[MetaQuotes file documentation](https://www.metatrader5.com/en/terminal/help/start_advanced/structure)
classifies HCC as minute history and calculated HC as derived timeframe cache.
[Tick-generation documentation](https://www.metatrader5.com/en/terminal/help/algotrading/tick_generation)
describes monthly real-tick TKC storage and distinguishes generated ticks.
Year/month labels suggest candidate periods only. Neither modification time nor
byte count establishes earliest/latest quote, completeness, row count or source
rights. No inferred bars-per-byte calculation or binary reverse engineering is used.

Subsequent permitted CSV checks must measure earliest/latest UTC, expected-session
missing bars, duplicate/conflicting records, repeated cross-source sequences,
bid/ask validity and tick-grid precision. If histories match, keep one provenance
lineage rather than counting twice or treating copies as independent validation.
Current disposition for every instrument: **QUARANTINED / NOT CERTIFIED**.

## Safest route and next actions

Prefer an expressly licensed, broker-supplied bounded CSV: it requires no MT5
startup on this VPS. If the broker instead supports native export, the proposed
[bounded operator procedure](EXPORT_AUTHORIZATION_REQUEST.md) requires separate
approval and proof of a pre-existing isolated standard-user terminal/session.
Phase 6.1 observed DirectiveCodex active and not a direct local Administrators
member; its effective export-process token was not tested. The connected runner
was elevated and no supported standard-user execution binding was established.
That historical observation is not a fresh certification of current availability.

A chart profile alone is not isolation. Do not copy production caches/configuration
or launch an existing production terminal to create the research instance. If no
already isolated, safe instance exists, terminal-dependent export stays blocked.
No new install, impersonation, token workaround, policy change or service is proposed.
Algo-trading toggles alone do not make a full trading terminal incapable of mutation.

The smallest next action is **operator review/approval to send the unsent
[broker clarification drafts](PROVIDER_INQUIRIES_DRAFT.md)** through a verified
official channel, and supply a redacted applicable entity/agreement identifier.
Permission must come from the entitled provider; user approval alone cannot grant it.
Only after rights and operational gates pass should a one-day EURUSD canary be
exported. Do not request bulk history first or touch the 2026-01-01 through
2026-09-30 sealed final holdout. No fallback to 2026 cache dates is permitted.

After approved receipt, automatic offline actions are export-only checksums,
schema/time/calendar/gap/duplicate validation, existing Phase 4 evidence-bundle
certification and Phase 6.2 readiness checks. A one-day canary verifies format and
feasibility, never sufficient sample size or an edge. Full 2023/24 development and
independent 2025 walk-forward coverage remain future separately scoped acquisition;
previously evaluated intervals cannot become fresh OOS evidence.

Reproduce this phase's metadata/preservation checks with [README.md](README.md).
The recorded [verification](VERIFICATION.json) checks all **91 prior public Git
blobs** unchanged and computes two cross-server metadata-match groups from 19
observations. This is preservation/metadata evidence, not dataset certification.
No purchases, vendor messages, broker connections, terminal starts, orders,
production settings or earlier research files were changed. Forward SHADOW remains
**OFF**. DEMO/live execution authority remains **NONE**.
