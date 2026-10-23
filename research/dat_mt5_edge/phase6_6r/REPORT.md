# DAT MT5 Phase 6.6R — recovery verification

Recorded 2026-10-23. **BLOCKED: registry Online, device commands unresponsive;
restricted execution not verified.** This is an additive recovery result for
[draft PR #2](https://github.com/oluadegbu/Codex--DSV-/pull/2), not a repeated source
survey or a replacement inspection package.

## What changed since Phase 6.6

The authorized device registry now lists the authorized VPS **Online**, app 0.2.52.
Two observations showed last-seen age increasing from 8 to 10 minutes. However,
the actual source directory request failed with **Timeout — no response from
device**. Its asynchronous result was retrieved through get_tool_result rather
than retrying the original call. The bounded PowerShell identity/session/Python
diagnostic also returned **MCP request timed out**, without a PID or output.
Registry state does not demonstrate a functioning command channel.

Consequently current source existence/accessibility, standard-user session,
effective token, ACLs, Python installation and VPS package deployment remain
**NOT VERIFIED**. A timeout is not proof that the directory is absent, the account
is disabled, or the diagnostic process never ran. No command was resubmitted.
The diagnostic contained only identity/session/account-enabled/Python-path reads;
no audit, archive processing, source hashing or broker operation was requested.

The connected process schema exposes command/device/shell/time controls but no
supported user/session selector. Previous evidence identifies the runner as
Administrator; no fresh token result was obtained. It is not a certified research
worker. No impersonation, runas, permission bypass, installation, persistent service,
scheduler or security-policy change was attempted.

## Existing package integrity — verified without VPS execution

Located the original package on PR #2 at commit
`9eadc569f3084c1252460d17dd82e892f5799993`:
[inspect_data.py](../phase6_6/inspect_data.py) and
[inspection handoff](../phase6_6/INSPECTION_PACKAGE.md).
Fetched published script bytes match the existing prepared local copy exactly:

```text
SHA256 f25f7539b3b0f7940766167ff06c182cea576c8e59a33627e1e49c0592d79961
Git blob cf98f7097dbfed503eada1e2d530802cb447dbd4
Size 10828 bytes
```

Dependencies are Python standard library only; the handoff requires existing
Python 3.10+ on the restricted Windows worker. Remote Python presence/version
could not be checked. No script was copied onto or run on the VPS. No new synthetic
tests were substituted for actual inspection; old syntax/CLI results remain
historical package evidence, not dataset certification.

The package remains a first-stage bounded tool, not an autonomous rights/calendar/
contract certifier. It requires independent source-read-only containment and external
wall-time/memory limits. Its disabled schema cannot truthfully be enabled without
actual source-format and historical-clock review. No package code, schema, old
results or sealed holdout was changed in this recovery phase.

## Inspected inventory and historical coverage

**Data files inspected: 0. Complete inspected inventory: empty because access failed.**
This does not mean the source contains no files. The prior reported candidate
families remain leads; no filename, size, timestamp or price observations were returned.

| Priority instrument | Actual first/last and rows | Candle signal readiness | Bid/ask execution readiness | Classification |
|---|---|---|---|---|
| EURUSD M1 | UNKNOWN | BLOCKED | BLOCKED | **BLOCKED** |
| GBPUSD M1 | UNKNOWN | BLOCKED | BLOCKED | **BLOCKED** |
| XAUUSD | UNKNOWN | BLOCKED; scale/contract unresolved | BLOCKED | **BLOCKED** |
| BTCUSDT | UNKNOWN | BLOCKED; venue/spot/perpetual unresolved | BLOCKED; not an MT5 BTCUSD CFD proxy | **BLOCKED** |
| ES/NQ/YM/GC | UNKNOWN | BLOCKED; dated futures vs CFD unresolved | BLOCKED; rolls/contract/fees unresolved | **BLOCKED** |
| Other reported FX/archive families | UNKNOWN | BLOCKED | BLOCKED | **BLOCKED** |

Quality, missing periods, duplicate records, OHLC validity, timeframe, timezone/DST,
volume semantics, provenance and intended organizational-use rights remain
**NOT EVALUATED / UNKNOWN**. Neither candle research nor bid/ask execution-quality
readiness can be certified. PASS: 0; technically verified CONDITIONAL: 0; observed
FAIL: 0; all requested families BLOCKED. No data failure is inferred from the
infrastructure timeout. No paid-data requirement is yet established.

## Exact remaining blockers and smallest setup request

1. A responsive device command channel, not only an Online registry label. The
   completed directory error and diagnostic timeout are recorded in
   [EVIDENCE.json](EVIDENCE.json).
2. An officially supported non-admin worker with verified effective identity,
   source-read-only permissions, isolated existing output and required resource
   containment. None is currently evidenced by a successful diagnostic.
3. Actual bounded inventory/schema/price-quality inspection and provider-license,
   calendar/DST, contract and cost evidence review after access is restored.

[SETUP_REQUEST.md](SETUP_REQUEST.md) specifies the smallest operator-supported
recovery action. No Administrator audit exception is requested. Do not modify
production ACLs, accounts or policies automatically. Any required new installation,
security-sensitive change or persistent deployment needs separately scoped approval.

## Phase 6.7 recommendation

**Resume certification before backtesting.** Once the restricted route is proven,
execute the existing Phase 6.6 census and pre-2026 EURUSD quality inspection first;
then follow the established instrument order. Do not launch another provider
search or rebuild the framework. Best immediate backtesting candidate: **NONE
QUALIFIED**; EURUSD M1 remains the first certification candidate only.

For any subsequently qualified M1 dataset, the existing London sweep reversal,
NY breakout/retest and liquidity-sweep/MSS/retest families can be considered with
M1/M3/M5 entries and M15/H1 context. Require documented quote side, spread,
commission, slippage, rollover/funding and intrabar stop-order uncertainty. Futures
also require dated contracts/roll handling. OHLC alone cannot establish genuine
historical bid/ask execution. Do not invent numerical cost inputs before contracts
and source prices are verified.

Partitions remain provisional until actual coverage and evaluated-period lineage
are known: 2023 training, 2024 development/validation, chronological independent
2025 walk-forward where available. Previously evaluated data cannot become fresh
OOS. Preserve the 2026-01-01 through 2026-09-30 sealed holdout. No optimization,
strategy run or holdout analysis is authorized by this recovery step.

**MT5 starts, broker logins, trades, privileged data processing, source changes,
production changes and SHADOW activation: NONE REQUESTED OR PERFORMED.** No data
read is claimed from the timed-out diagnostics. Existing code, results, journals
and holdout remain unchanged; PR stays draft/unmerged, main and DMB PR #1 untouched.

Public evidence omits device/account identifiers, diagnostic call IDs and private
source paths. Automatic publication review rejected the earlier detailed payload;
this version retains only the operational conclusions needed for review.
