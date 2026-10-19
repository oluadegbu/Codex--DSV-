# Phase 6 — Tickstory Lite feasibility and license gate

**Decision: STOP before download, installation or license acceptance.** Review: 2026-10-18, New York. The conditional US$0 evaluation is recorded; its license and non-admin prerequisites are not yet established. No new permission to install or spend is inferred from earlier budget discussions.

The official Lite page says **“Personal use only”**; the full linked EULA could not be fetched (HTTP 403). Intended DAT organizational/commercial versus personal use is not established. Separately, the connected Windows runner is already elevated under the built-in Administrator identity. No usable non-admin Windows context has been verified. These are two independent blockers, not a conclusion that Tickstory necessarily requires elevation or prohibits every form of research.

No installer was downloaded/executed, no terms accepted, no elevation or security-policy/account change attempted, no purchase/subscription/renewal initiated and no MT4/MT5 integration, terminal startup, broker account/credential access or order occurred. Previous research artifacts and controls remain unchanged. This report is published only to existing draft PR #2, unmerged.

## Source, version and license verification

| Check | Evidence | Result |
|---|---|---|
| Official source | [Tickstory download page](https://tickstory.com/download-tickstory/) on the vendor domain | Official product page verified; US$0 Lite advertised |
| Current advertised release | [Vendor changelog](https://tickstory.com/changelog/) lists v1.9.8.16 dated 2026-10-04 | Product-family release verified; exact current Lite installer/build not verified |
| Edition restriction | Download comparison distinguishes personal-only Lite from personal/commercial paid editions | DAT evaluation permission unresolved; do not assume that non-trading research is necessarily personal use |
| Full agreement | Vendor page links [current EULA](https://tickstory.com/EULA); fetched URL returns HTTP 403 | Incomplete terms review; no acceptance and no alternate-host/mirror workaround |
| Executable authenticity | No executable obtained | Artifact URL, file hash, Authenticode publisher/status, PE requested-execution level and package terms not verified |
| Underlying data rights | Download page separates software from third-party feeds | A software license would not independently certify Dukascopy data rights, permitted exports or redistribution |

Search indexing exposes an older EULA snippet, not a complete current agreement suitable for acceptance. It does not resolve organizational evaluation/export permission. No form, registration, support message or vendor communication was sent. User approval cannot by itself replace the vendor's terms.

The [FAQ](https://tickstory.com/faq/) describes Windows support, per-user writable data/export locations and substantial disk needs. The changelog records a move to .NET 4.8 in 2024. These are documented requirements, not checks proving this host/package will work. No framework, dependency, compatibility layer or VM was installed.

## Installation feasibility and security assessment

A read-only OS identity/token check established that the currently connected Windows process is elevated and the identity is the built-in Administrator. It was used only for observation, not for an administrator-required installation, token manipulation or system mutation. One other enabled local identity was counted; its permissions, usable login/session and research isolation were not verified. Its existence does not establish a usable standard-user execution path. No username, credential or account identifier is published.

The local isolated research checkout runs as UID 1000 on Linux. Neither Wine nor Wine64 is available; it is not an existing Windows runtime for this evaluation. Installing Wine, .NET, a VM or an alternate runner has not been attempted. No account was created and no password, token, UAC setting, policy, firewall rule, scheduled task or service was changed.

**Important distinction:** the installer has not been inspected or run, so its elevation requirement is **UNKNOWN**, not “requires Administrator.” The present automation context fails the non-admin requirement regardless of whether the installer might support per-user installation. Installing into a research-named folder while the process is elevated would not meet the directive.

To resume within the existing restrictions, provide an already available standard-user Windows research session, isolated from DAT production, broker terminals, broker credentials and shared terminal caches. Verify the actual process token before execution. Then, only after terms are clear, retrieve the exact official artifact, record hash/publisher/version and inspect its execution manifest. A hash is an identity check, not a safety guarantee. If the official installer requests elevation, stop without attempting token tricks, `Run as Administrator`, policy changes, or a third-party repack. A newly created environment/account would require separate authorization; none is proposed as an automatic fix.

## Export capability and coverage

CSV export is a documented product capability: vendor [support guidance](https://tickstory.com/forum/viewtopic.php?t=442) distinguishes **Export to file** from downloading raw `.bi5` files. This older guidance is not a runtime test of the present Lite package. The current comparison page's download/server limits should not be interpreted as a verified lifetime two-file cap; actual permissible retrieval/export behavior remains untested.

[Vendor-advertised Dukascopy date ranges](https://tickstory.com/dukascopy-historical-data-available-date-ranges/) remain the Phase 5 leads: EURUSD from 2003-05-04, GBPUSD from 2003-05-05 and BTC/USD from 2017-05-23. They do not prove the Lite edition currently exposes each symbol, downloads recent history, preserves every quote, supplies five continuous years or permits DAT's intended use. No new coverage/quality metrics are attributed to Tickstory.

| Instrument, in required order | Phase 6 export | Runtime coverage, timestamps, bid/ask, gaps/duplicates/spreads | Certification |
|---|---|---|---|
| EURUSD | Not attempted: license/isolation gate | Not measured | NOT EVALUATED; no new certified data |
| GBPUSD | Not attempted: same upstream gate | Not measured | NOT EVALUATED; no new certified data |
| BTCUSD / provider BTC/USD | Not attempted, follows FX and symbol verification | Support and exact product identity unverified | NOT EVALUATED; do not substitute spot, CFD or stablecoin pair |

**Tickstory exports acquired: 0. New datasets certified: 0. Strategy backtests/promotions: 0.** No mock data, prior mirror or Phase 5 Kraken quote sample is relabeled as a Tickstory export.

## Prepared evaluation procedure after both gates clear

The following is a concrete plan for the already conditionally approved US$0 scope, not execution that has occurred:

1. Confirm readable current terms permit the actual operator/entity's DAT research and CSV export, including limits on retention/use/publication and the upstream data terms. Record the terms URL/version/date and permission basis. Stop if prohibited or still ambiguous.
2. Use the verified standard-user research environment. Verify exact official Lite artifact, signature/version and non-elevating setup path; retain logs under a user-owned isolated directory. Stop on elevation, paid feature/activation, subscription, framework/security modification or unapproved enrollment. Do not configure a terminal location, install an integration component, use an EA or share production caches.
3. EURUSD first, then GBPUSD: export raw ticks containing timestamps, both sides and volume fields if present, using **Export to file** only. Preserve the native export and settings before normalization. Choose small 2024 winter/summer and US/UK DST-mismatch canaries, plus rollover and a known holiday/session boundary. Use complete day boundaries so export end-date truncation cannot silently remove the last day; this is an explicit risk documented in the vendor changelog. Do not sort or deduplicate away legitimate equal-time updates.
4. Establish timestamp units and UTC/offset/DST semantics independently, source/provenance correspondence, actual price units/precision/tick size, spread distribution and volume meaning. Do not infer USDJPY or Gold economics from an FX default or treat available quote quantities as traded volume. Compare retained primary-format canaries only when dates/source genuinely overlap.
5. Run the existing Phase 4 package certifier with independent calendar, source/decoder/license/contract/cost proofs and the frozen holdout lineage. Classify missing hours, duplicate records, nonmonotonic times, crossed/zero quotes, gaps and stale periods. Quarantine failures; do not invent missing quotes or a calendar from observed rows. A custom CSV adapter may be needed after inspecting the actual schema; none has been assumed or implemented prematurely.
6. Only if FX canaries and rights pass, assess whether at least three complete years, preferably 2021 through 2026-09-30, can be retrieved legally at US$0 in bounded partitions. Preserve the Phase 3 chronology and seal the 2026 final holdout. Measure actual limits, runtime, bytes, date bounds and missing-session exclusions before claiming acquisition feasibility.
7. Then assess provider BTC/USD availability and exact identity, with its own sessions/specifications. Failure of a free tier does not authorize a paid upgrade. Do not promote a strategy from canary exports.

The requirements remain unchanged: the Phase 4 proof registry cannot be self-approved by dataset flags; even a certified small dataset is not statistically adequate edge evidence. Historical data alone does not verify Vantage account targeting or grant forward-connected collection/trading authority.

## Certification and preservation evidence

No new export exists to submit to the certifier. Therefore this phase reports **NOT EVALUATED**, rather than a fabricated certification pass/fail run. Existing Phase 3–5 reports/results, code and tests are locked by SHA256 in [baseline_lock.json](baseline_lock.json). [Verification output](results/verification.json) records their equality and zero new exports/authority actions. Verification is offline and reproducible:

```sh
# from research/dat_mt5_edge
python -m phase6.verify
```

This is a source/feasibility report; no strategy/collector code changed. The earlier 84-test evidence is preserved, not described as a new Phase 6 run. No redundant strategy regression or holdout evaluation was performed.

## Required clarification and next recommendation

1. **License:** obtain readable current Lite terms and establish whether this DAT evaluation is within permitted personal use, or obtain vendor confirmation covering the actual intended research/export use. This is a request for evidence/clarification, not permission to ignore a restriction. No vendor message will be sent without explicit instruction.
2. **Environment:** supply an existing usable, non-admin Windows research context. Do not send passwords or broker credentials in chat. No authorization to use Administrator, change policies or create accounts is requested.

After those two prerequisites are resolved, continue the EURUSD → GBPUSD → BTCUSD CSV-only evaluation under the existing conditional US$0 authorization; no need to re-approve routine allowed canary validation. Until then, continue only with supplied legally usable exports and the existing offline certification pipeline. Do not buy a paid edition as a substitute for unresolved licensing, source quality or isolation.
