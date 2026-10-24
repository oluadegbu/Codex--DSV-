# Proposed bounded export authorization — NOT APPROVED / NOT EXECUTED

This is a reviewable future request, not a request to change current safeguards.
Rights confirmation and operator approval are distinct gates. Do not execute this
document merely because it is committed to PR #2.

## Stage 0: no-terminal alternative (preferred)

Ask the confirmed broker entity, only after separate approval to send the inquiry,
to supply EURUSD M1 and genuine historical paired bid/ask CSV for the half-open UTC
interval **[2024-01-10T00:00:00Z, 2024-01-11T00:00:00Z)**, plus source/timezone,
symbol and licensed-use documentation. No sign-in, paid retrieval, new registration
or credential sharing. Broker supply capability and price must be confirmed free;
stop if a charge is required. Operator approval for actual delivery/retention is
still required after terms are known.

## Stage 1: smallest MT5 export request, conditional alternative

Proposed approval wording:

> Approve one operator-supervised, non-administrator, data-only export session for
> exactly one broker entity/server identified in the approved rights record,
> exactly EURUSD, and UTC 2024-01-10 inclusive to 2024-01-11 exclusive. Export at most
> two files: M1 bars and genuine historical tick Bid/Ask/flags CSV. Permission is
> limited to a verified pre-existing isolated research terminal and broker-enforced
> read-only data entitlement; no orders, scripts, EAs, tester, APIs or production
> terminal/profile/cache access. Provider rights must explicitly permit DAT's use.

This wording deliberately leaves the broker unselected: the operator must select
**one** of Exness-MT5Real10 or VantageMarkets-Demo and attach the verified entity,
agreement/version and written grant before approval becomes actionable. Both
brokers together are not silently authorized. No account identifiers belong in
the public approval record.

Destination proposed, not created on the VPS:
`%USERPROFILE%\Documents\DATMT5Research\Phase6_4\Exports\<approved-broker>\EURUSD\2024-01-10\`.
It must resolve under the actual standard user's research-owned directory, outside
all DAT/production/terminal trees, without redirection into them. Do not use the
Administrator profile. Raw exports stay private and are excluded from PR #2;
publish only permitted aggregate validation metadata and evidence hashes.

Limits: one interactive session, **30 minutes**, no unattended retry, at most
**100 MiB/file and 200 MiB total output**, and no range expansion, disk-space
remediation, production setting change or new installation. Verify the supported
GUI can bound server requests before pressing Request; if not, stop. Request may
write only the isolated terminal's own cache/logs and approved export directory;
this is not a filesystem-read-only operation and therefore needs explicit approval.
No protected cache file is copied, hashed or decoded. Hashing is limited to the
new, expressly licensed CSV and its non-sensitive export manifest after approval.

Preconditions, all mandatory:

1. Provider confirms applicable entity, entitlement, historical quote ownership,
   2023/24 and current-use rights, internal retention/normalization/automated offline
   testing, authorized internal cloud processing, and aggregate-result publication.
   Resolve Exness's own-trading restriction in writing if applicable. No raw-data
   redistribution or transfer of license between brokers is assumed.
2. Operator confirms existing isolated terminal executable/data-folder pair has no
   production shared state, autoloaded EAs, scripts, copied credentials, live account
   session or service integration. A new chart profile is insufficient. If this
   cannot be established without prohibited access/change, stop and use Stage 0.
3. Officially supported standard-user interactive session and effective non-elevated
   process identity are verified by the operator. The current elevated tool runner
   is not an approved substitute. No runas, impersonation or policy/account changes.
4. Broker-enforced read-only entitlement is verified by the operator without
   revealing credentials to the research tools. Credential entry, if needed, is
   outside this request and requires separately scoped operator authorization.
   Existing production account access is not authorized.
5. Exact native export clock and UTC date mapping are documented before request.
   If offset/DST or request bounds are unknown, stop; do not guess or fetch all data.

Proposed manual sequence after those gates and separate startup/connectivity
authorization: confirm isolated session; open Market Watch symbol management;
choose EURUSD, Bars/M1 and approved date bounds; Request only if bounded;
Export CSV to the approved path. Repeat on Ticks for the same interval only.
Record build, server label, source clock, request bounds, schema, returned counts
and first/last timestamps, read-only entitlement attestation and contract specs
without account numbers or secrets. Empty/unavailable data is a result: do not
switch accounts, dates, symbol suffixes or methods. Close only this research
instance if opened under approval; leave production processes untouched.

The full MT5 application remains order-capable software even when the approved
operation is data-only. No claim is made that GUI isolation or an Algo Trading
toggle proves capability removal. If broker-enforced read-only access cannot be
confirmed, terminal-based export is **NO-GO**.

## Later candidate scope — separate approval, not included above

| Instrument | Exact mapping prerequisite | Proposed diagnostic interval, UTC | Data products |
|---|---|---|---|
| GBPUSD | Confirm broker's exact GBPUSD contract | 2024-01-10 to 2024-01-11, half-open | M1 + genuine ticks |
| BTCUSD | Confirm BTCUSD vs BTCUSDz, CFD/spot and unit economics | Same 2024 one-day interval | M1 + genuine ticks; stop if unavailable |
| XAUUSD | Confirm Gold mapping, including whether XAUUSD.crp is valid; units/scale | Same 2024 one-day interval | M1 + genuine ticks; stop if unavailable |
| EURUSD/GBPUSD DST canaries | Historical clock rules confirmed | 2024-07-10 to 2024-07-11, half-open | M1 + ticks |
| FX deep-coverage test | Canary passed and separate bulk bounds/cost approval | 2023-01-01 to 2025-01-01, half-open | M1; tick windows separately bounded |

These dates do not authorize access to the **2026-01-01 through 2026-09-30 sealed
holdout**, including the observed September 2026 BTC TKC. No 2026 fallback. A 2024
canary is an engineering diagnostic, not fresh strategy OOS. Existing evaluated
periods and frozen results retain their lineage. No strategy promotion, DEMO/live
authorization or forward-feed deployment is included.
