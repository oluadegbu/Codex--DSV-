# Phase 6.1 — free-data fallback and execution feasibility

Review: **2026-10-19, New York**. **No new FX dataset acquired or certified. Tickstory Lite is unsuitable for this phase; the existing Windows session is observable but not bound to a supported non-elevated execution interface.** Research continues offline; no trading, terminal startup, production mutation, installation, paid/cloud-chargeable request or credential enrollment occurred.

The progress in this phase is resolution of two uncertainties: the authoritative Tickstory EULA is now readable, and DirectiveCodex has an active session. Neither finding grants DAT data-use rights or changes the connected runner's privileges. All earlier Phase 3–6 evidence is preserved as historical observation; the earlier HTTP 403 report is not rewritten.

## A. Tickstory licensing determination

The [official current EULA](https://tickstory.com/EULA/) was retrieved through a normal public-page read. Its page revision shows 2026-02-28. Section 1(a) restricts the free version to personal use and defines organizational use for the software's intended purpose as commercial, including nonprofit and educational entities. No general research/evaluation exception for organizational use was established. Sections 4 and 7 also separate third-party content rights from the software license.

**Disposition: UNSUITABLE FOR THIS DAT PHASE absent a separate applicable vendor grant.** This is a fail-closed procurement determination for the stated DAT project, not a claim that all individual personal research is prohibited. No installer was downloaded, installed, run or accepted. A user approval cannot replace vendor permission. No vendor communication was sent. The prior paid fallback from Phase 5 remains a historical conditional proposal, not an authorized purchase or an automatic alternative.

## B. Primary free FX route: Dukascopy

The [official historical export page](https://www.dukascopy.com/swiss/english/marketwatch/historical/) advertises free CSV history and backtesting applications. However, the [current official site terms](https://www.dukascopy.com/swiss/english/legal-pages/terms-of-use/) have additional restrictions: General 3/4 limit ordinary download/use to personal non-commercial scope, restrict construction of databases and require express written consent for automated acquisition; General 5 establishes that ordinary site access is free. No export-specific agreement or grant resolving DAT's proposed organizational retention/automated-research scope was found.

**Acquisition disposition: LICENSE SCOPE UNRESOLVED — no new EURUSD/GBPUSD quotes fetched.** Free access does not by itself establish the requested internal dataset/automation rights. The marketing backtesting invitation and general terms need a provider-specific scope resolution; this report does not assume either overrides the other. Existing direct-format canaries remain quarantined and no mirror is promoted to primary status.

There is a separate technical limitation: the managed cloud HTTP policy is enforced and does not currently list Dukascopy hosts. One bounded public-description request through inherited networking failed with `URLError` and no HTTP status. This is not proof of a provider outage or an observed HTTP policy denial. No proxy bypass, alternate IP, header spoofing, challenge workaround or network-policy change was attempted. Web research tools can retrieve public documentation; that does not prove a permitted bulk binary-download path from the executor.

The earlier requester-pays S3 route remains off: no AWS identity/credentials, bucket listing, storage or chargeable request was used. The elevated Windows runner was used only for the expressly authorized read-only session check, not for market-data acquisition or research execution.

### Remaining primary-data evidence requirements

| Requirement | EURUSD | GBPUSD |
|---|---|---|
| Primary provider identification | Dukascopy public export route identified | Same |
| DAT retention/normalization/automation permission | Not established | Not established |
| New primary bid/ask capture in this phase | None | None |
| UTC/DST and source decoder correspondence | Prior evidence remains incomplete | Prior evidence remains incomplete |
| Recent complete three/five-year coverage | Not established | Not established |
| Independently reviewed units/specs and executable costs | Not established | Not established |
| Dataset/strategy promotion | BLOCKED | BLOCKED |

No tick scale, fee schedule, server calendar or paired-quote sequence was inferred from a website description. Prior 2018 mirrors and the three paired 2022 EURUSD days remain the previously documented evidence, not newly certified history.

## Free secondary alternative: HistData

[HistData's own description](https://www.histdata.com/about-us/) expressly shares data to support testing users' own or purchased strategies. Its [FAQ](https://www.histdata.com/f-a-q/) documents Generic ASCII tick bid/ask, bid-only M1 bars, fixed EST UTC−5 without DST and intentionally removed volume. This is a stronger explicit strategy-testing invitation than an unlicensed mirror label, but original contributing quote provenance and DAT organizational/retention/derived-publication rights are not independently established.

**Disposition: secondary canary candidate, not a certified primary substitute.** No newly registered FTP/SFTP access or credentials, raw download or corporate-rights assumption occurred. A public click on the tick-data selector returned the initial format chooser rather than a verified year/month inventory, so historical completeness/date bounds remain unverified. No alternate endpoints, hidden download tokens or external downloader installation were used.

The local workspace library/shared/scratch market-file scan found no new candidate exports in those scopes; it was not an exhaustive disk search. FXCM/TrueFX personal-use/eligibility issues documented earlier are not resolved by changing provider names. Public BTC trade archives and first-of-month quote samples do not supply continuous FX data.

## C. DirectiveCodex and supported execution route

Read-only checks found:

- The named local account exists and is enabled; its interactive session is **active**, not disconnected.
- It is **not a direct member** of the local Administrators group. This does not inspect its effective process token or rule out all indirect membership/privilege paths; no process was launched as that user to test.
- The presently connected process remains **elevated**. The device listing exposes one online device, not a separately verified DirectiveCodex-bound runner.
- The exposed `start_process` schema accepts command, device ID, shell, timeout and timing options. It exposes **no user/session identity selector**. A device selector is not a user-token selector.

**Conclusion:** DirectiveCodex's session is available as a read-only observation; a supported authorized non-elevated execution binding has **not** been established on this connection. This is narrower than saying the product could never support another user-scoped connection. No undocumented API, impersonation, token duplication, `runas`, interactive input injection into another session, task/service creation or security-policy change was attempted. No credentials were retrieved and no identity was switched.

Keep Windows-dependent execution blocked. If the already installed client supports an official user-scoped connection workflow, an operator can expose a standard-user runner through that workflow and have its process token verified before future work. Do not modify/restart the present elevated agent or set up another account/service automatically. The Linux workspace remains usable for offline evidence review and certification of supplied files.

## D. Certification results and chronology

**Newly acquired datasets: 0. New dataset certifications: NOT EVALUATED (no admissible new data). New strategy tests/promotions: 0.** No synthetic data or unverified mirror was relabeled primary. No historical date boundary, final holdout or strategy definition changed.

Existing Phase 5 normalized BTC sample diagnostics and Phase 6 preservation verification were rerun offline and still match. The sample stays quarantined. Those checks are not new quote captures or performance evidence. Phase 3–6 source/result/test artifacts are independently locked in [baseline_lock.json](baseline_lock.json); [verification output](results/verification.json) records their equality. The previous 84-test result remains historical test evidence, not a new Phase 6.1 suite claim. No strategy implementation changed, so no redundant strategy regression or holdout reuse was performed.

## Recommended next action

The shortest unblock is a **documented data-use grant or an existing licensed export**, not Tickstory or elevated execution. An operator-supplied EURUSD/GBPUSD primary export with source, permission, immutable definitions/decoder, calendar and cost evidence can enter the existing cloud/offline certifier immediately without any new terminal session.

A [concrete provider clarification draft](PERMISSION_REQUEST_DRAFT.md) is prepared for Dukascopy and HistData. It asks for free internal retention, normalization, bounded automation, aggregate-result publication and the allowed interface. **It has not been sent.** Explicit instruction and a verified official recipient/channel are required before contacting a vendor; no credential, payment or account enrollment is included. Provider permission, if obtained, must explicitly address the identified restrictions; another user approval alone is insufficient.

After permission is established, resolve only the required supported cloud download access through the managed configuration review workflow, or supply files downloaded through an already authorized export route. Do not bypass current networking or re-enable requester-pays access. Validate one winter/summer/DST canary per instrument first, then bounded month partitions toward 2021-01-01–2026-09-30. Preserve 2024 development, 2025 chronological walk-forward and the sealed 2026 final holdout. Run no strategy on those data until provenance, legal scope, source clock, gaps, paired quotes, contract economics and realistic costs pass their existing gates.

Windows connector binding is independent of the cloud data-license path. Resolve it only through a supported operator-managed user-scoped connection; no new installation, privileges or policy change is proposed. All DEMO/live execution authority remains off.

## Reproduce preservation check

From `research/dat_mt5_edge`:

```sh
python -m phase6_1.verify
```

This command reads local evidence and rewrites only the isolated Phase 6.1 verification output. It performs no downloads, installation, acceptance, broker connection or order. The research branch remains draft/unmerged; DMB PR #1, main and production DAT safeguards remain untouched.
