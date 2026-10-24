# DAT MT5 Phase 6.6S — restricted foreground execution handoff

2026-10-23. Research only / source read-only / non-trading / fail-closed.
**Route 2 selected; manual foreground launch pending. Dataset certification BLOCKED.**

This phase adds a launch/preflight wrapper and one complete copy-and-paste command
for the **unchanged Phase 6.6 audit engine**. It does not rebuild its parser,
certification framework or strategies. No remote audit, deployment, source read,
source change, strategy run or holdout access occurred.

## Route selection

| Priority route | Current evidence | Decision |
|---|---|---|
| 1 Existing non-admin session through supported execution interface | Current process-call schema has no user/session selector. No successful restricted-worker identity/ACL/resource proof exists. Previous pending directory result is now not found/expired, not a recovered success. | Not established; no elevated substitute |
| 2 Manual foreground in the existing approved non-admin session | User explicitly authorizes preparing one complete command. No service, task, new account, credentials or installation required by the proposed route. | **Selected**, actual session/preflight verification occurs only when operator launches |
| 3 Separate authorized non-admin machine and permitted data copy | No target, copy entitlement or verified transfer established | Reserve alternative; no copying performed |

There is no need to wait for persistent Desktop Commander connectivity to run
route 2. Human foreground launch is necessary because this agent has no supported
interface into the approved user's session. No impersonation, token substitution,
security-policy bypass, ACL edit or Administrator workload is used.

## Concrete handoff and verification

Open [RUN.md](RUN.md) and paste its one command into the approved account's normal
Windows PowerShell. Enter the already authorized source and local account from
the directive. The command contains no password fields or routine diagnostic
round trips. It obtains hash-pinned public code into a new user research folder,
honors existing execution policy and runs [Launch-ResearchAudit.ps1](Launch-ResearchAudit.ps1).

The launcher verifies identity/SID, non-admin token and integrity, conservative
read-only source/ancestor ACLs, output separation, existing dependencies, exact
audit hash and bounded process creation. Suspended creation permits Job Object
limits to be attached before Python executes. Native API or containment failure
stops the run. No Windows settings are changed.

Original audit SHA256:
`f25f7539b3b0f7940766167ff06c182cea576c8e59a33627e1e49c0592d79961`.
The original published/prepared bytes were already compared in Phase 6.6R; this
phase retrieved the same pinned script. Launcher hash is pinned in RUN.md.
No actual Windows dependency/token/ACL validation has yet occurred. Local
environment has no PowerShell/.NET compiler, so **Windows compilation and runtime
behavior remain untested**. Static review is not certification or a passed preflight.

Resource specification and limitations are explicit in RUN.md: 512 MiB committed
memory and one process in an ephemeral Job Object; monitored wall time; bounded
tree traversal; free-space preflight and 128 MiB sampled output stop threshold.
The disk monitor is not an instantaneous filesystem quota and may briefly overshoot.
No quota/policy/deployment is created. The source must remain stable while the
foreground audit runs. Conservative ACL screening can reject valid complex ACLs;
it does not rewrite them or silently accept ambiguity.

References checked for the native containment design:
[extended limits](https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-jobobject_extended_limit_information),
[job assignment](https://learn.microsoft.com/en-us/windows/win32/api/jobapi2/nf-jobapi2-assignprocesstojobobject),
[process creation flags](https://learn.microsoft.com/en-us/windows/win32/procthread/process-creation-flags).
Job limits apply after assignment; the helper creates suspended and resumes only
after successful attachment. Closing the job terminates its associated process.
These documented mechanisms do not prove the unexecuted wrapper works on this VPS.

## Dataset inventory, coverage and readiness

No dataset rows were inspected in this phase. Reported files remain unverified
until the foreground command returns actual output; no market dates or record
counts are inferred. Identity, permissions and execution readiness are **PENDING**.

| Instrument | Coverage/rows | Candle integrity/signal readiness | Bid/ask execution readiness | Rights | Classification |
|---|---|---|---|---|---|
| EURUSD M1 | UNKNOWN | NOT INSPECTED | NOT INSPECTED | UNKNOWN | **BLOCKED** |
| GBPUSD M1 | UNKNOWN | NOT INSPECTED | NOT INSPECTED | UNKNOWN | **BLOCKED** |
| XAUUSD | UNKNOWN | NOT INSPECTED; scale/units pending | NOT INSPECTED | UNKNOWN | **BLOCKED** |
| BTCUSDT | UNKNOWN | NOT INSPECTED; exchange/product pending | NOT INSPECTED; not MT5 CFD data | UNKNOWN | **BLOCKED** |
| Other FX/futures | UNKNOWN | NOT INSPECTED; calendar/roll/product pending | NOT INSPECTED | UNKNOWN | **BLOCKED** |

PASS 0; verified CONDITIONAL 0; demonstrated data FAIL 0. No best immediate
backtesting dataset qualifies. EURUSD M1 is the first certification target.

The engine's schema example is disabled. The default foreground command therefore
performs the existing metadata/checksum census and reports a quality-inspection
schema block. It must not invent a UTC convention, column mapping or provider
entitlement to force success. A genuinely reviewed schema can be supplied to the
same launcher for its bounded existing audit path; unsupported formats remain
blocked. No claims of actual first/last market timestamps are made from a census.

## Exact remaining actions and Phase 6.7 recommendation

1. **Manual action required:** launch the one command under the existing standard
   user. If preflight blocks, retain the exact local error; no elevation or automatic
   permissions change. Return private result files through an authorized channel.
2. Reconcile actual census, schemas and source timezone; use the existing bounded
   CSV/GZIP audit under the same verified worker. EURUSD first, then GBPUSD, Gold,
   crypto and other FX/futures. No synthetic test substitutes for this step.
3. Complete missing-session/DST, duplicate/OHLC, paired bid/ask versus candle,
   volume, provenance and intended organizational research-rights review. Establish
   costs and contracts: FX spread/commission/slippage/rollover; Gold scale/units;
   crypto venue/USDT basis/funding; futures dated contracts/roll/session/licensing.
4. Phase 6.7 begins only after a technically suitable, legally usable dataset
   qualifies. Retest unchanged London sweep reversal, NY breakout/retest and
   liquidity-sweep/MSS/retest definitions using chronological independent folds
   and executable costs. No optimization in this phase. Existing evaluated periods
   remain evaluated; the sealed 2026 final holdout remains inaccessible.

No new paid data is shown necessary yet. No vendor contact, purchase, credential
change, source/production change, scheduler, service, MT5, broker, trade or SHADOW
activation. Existing audit code/results/journals stay unchanged. Draft PR #2 only,
no merge/main or DMB PR #1 change. **Success criterion not yet met: manual launch
and real quality inspection still pending.**
