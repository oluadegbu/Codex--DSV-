# DAT MT5 Phase 7.1 — read-only DEMO preflight preparation

Recorded 2026-10-23. **OFFLINE PREPARATION / NON-TRADING / FAIL-CLOSED.**
**GO for offline package review. NO-GO for an actual connection now.**
Gate A and Gate B are separate and **neither is approved**.

Designated broker/server: **Vantage / VantageMarkets-Demo**, confirmed by the user
in this phase. This designation grants no connection, credential or order authority.
Private account, company/currency, terminal identity and exact symbol mappings have
not been supplied or verified. No broker account or terminal was accessed.

## Existing integration review

The available current implementation is Phase 7.0's fixture-only CFD lifecycle.
Its original **88 offline tests and all code/risk controls remain unchanged**.
The controller deliberately accepts only SimBroker and cannot route actual MT5
orders. The recovery inventory still does not establish the missing original
runnable execution adapter/authorization chain. No historic authority is restored.

Existing quote schema duplicate-key rejection and Decimal validation are reused
directly from Phase 4/6.2. The simulator, position sizing, risk limits, replay
journal and test strategy are not rebuilt or changed. This phase adds only a
separate read-only native collector design, offline admission/redaction validator,
tests, disabled configuration and separate approval procedures.

## Prepared package and checked surface

- [ReadOnlyDemoPreflight.mq5](ReadOnlyDemoPreflight.mq5): one-shot OnStart, four
  exact symbols, five-second cooperative capture budget, repeated identity fences,
  a unique bounded private output. No terminal startup, account login, switch,
  fallback, order submission/modification/cancel/close calls, history downloads,
  includes/imports, DLL calls, network API or symbol-selection call.
- [preflight.py](preflight.py): offline JSON verification and redaction only; no
  MT5/Python broker SDK or transport object. Default plan denies approval and the
  actual account allowlist is empty. Unknown/extra/duplicate fields fail closed.
- [OPERATOR_PROCEDURE.md](OPERATOR_PROCEDURE.md): conditional operator-managed
  investor session and private evidence handling, not an executable startup grant.
- [Gate A request](GATE_A_APPROVAL_DRAFT.md) and [Gate B requirements](GATE_B_REQUIREMENTS.md):
  separate operations, permissions and human decisions.

The native call list is checked against an explicit allowlist and reviewed source
hash. It has calculation-only `OrderCalcMargin`, **not** an order request/check/send.
No secret fields are defined, read or emitted. The fixed collector can only read
the current terminal/account and write its own local result; it cannot choose or
connect an account. There is no connected order adapter or routing-enable switch.

## Configuration and symbol mapping

[target.example.json](target.example.json) stays disabled with an empty allowlist.
[target_fields.example.json](target_fields.example.json) is an inert field guide;
login 0/blank paths/company/currency/symbols are invalid and are not active targets.
The operator must privately supply a complete single-account tuple after review.

| Alias | Designated server | Existing historical lead only | Actual Gate A mapping |
|---|---|---|---|
| EURUSD | VantageMarkets-Demo | EURUSD cache label | **UNSET / not verified** |
| GBPUSD | VantageMarkets-Demo | GBPUSD cache label | **UNSET / not verified** |
| XAUUSD | VantageMarkets-Demo | XAUUSD.crp cache label; contract meaning unverified | **UNSET / no suffix inference** |
| BTCUSD | VantageMarkets-Demo | BTCUSD/BTCUSDz labels with unresolved provenance | **UNSET / no alias fallback** |

Exact required private configuration: designated account/login, exact server and
company, currency, broker-reported DEMO mode, terminal name/build/binary hash and
isolated executable/data paths; four exact symbols; reviewed collector source/EX5
hashes and native compilation evidence; investor-access/isolation/reviewer evidence;
one approval reference/nonce and at-most-ten-minute UTC window. No credentials
belong in the configuration or public PR. Do not infer legal entity from server
or company display names; previous broker data-rights findings are not replaced.

## What a separately approved run would inspect

Terminal identity/build/connection, account login/server/company/currency/trade
mode, trading flags, leverage/margin mode and zero order/position counts; available
server symbol count plus the four requested mappings; selected/custom status,
calculation/trade/execution/filling modes, price digits/point, contract size, tick
size and asymmetric tick values, min/max/step/limit volume, stop/freeze distances,
margin properties and buy/sell margin estimates for minimum volume; current
bid/ask availability, server-relative quote age, last reported ping and capture time.

This is a bounded inspection of the four designated symbols, not an exhaustive
catalogue or historical-data export. Required missing/unselected/custom/stale
symbols deny the complete batch. No substitute symbol is selected automatically.
Margin estimates do not prove eventual order acceptance or account-wide margin.
Zero initial-margin/stop-level values can be legitimate dynamic settings, not a
promise of zero margin or unrestricted stops. Broker currency/contract semantics
remain subject to independent evidence before any later canary.

## Read-only isolation and minimum access

Minimum authentication is the operator's existing dedicated demo account login,
exact server and **investor/read-only password**, entered only through the official
terminal interface after Gate A approval. No master trading password, credential
file/token retrieval, password change or enrollment is permitted. If the broker
requires additional authentication/setup, stop for that separate gate.

MetaQuotes distinguishes [investor access without trading](https://www.metatrader5.com/en/terminal/help/startworking/authorization).
Vantage's [official investor-password explanation](https://global.vantagehelpcenter.com/hc/en-us/articles/10956738706447-What-is-an-investor-password-and-how-to-change-it)
describes view-only access without trade execution. These documents support the
proposed access type; they do not verify the actual unconnected session. This
phase does not create/change a password or contact support.

Account trade mode must be the actual DEMO enum, not an inferred server name;
REAL/CONTEST/unknown reject. Account trading must be FALSE and terminal/script
trading and DLL flags OFF. The account expert-permission flag is recorded, not
treated as authority when account trading is denied. References:
[account properties](https://www.mql5.com/en/docs/constants/environment_state/accountinformation),
[terminal properties](https://www.mql5.com/en/docs/constants/environment_state/terminalstatus).

The full MT5 application and MQL5 language are not generally incapable of trading.
The claim is limited to this fixed, hash-reviewed module's call surface plus the
independently verified broker read-only role. Merely wrapping an order-capable
SDK or setting a configuration Boolean would not establish that boundary. The
package deliberately does neither. Native compilation, EX5/source provenance,
actual investor mode, terminal isolation and runtime must still be verified.

## Offline results and limits

**127 tests pass: 39 new preflight tests plus all 88 preserved regressions.**
Two complete runs produced identical JSON (SHA256
`f2fa999d0b9e3fd7ee258f18af4a649729f663dd12a9a06cb043bb7477783df8`).
[Results](results/offline_verification.json) include test IDs, source hashes,
call-surface audit, prior-file preservation and explicit current NO-GO fields.
Run `python -m phase71.certify` from `research/dat_mt5_edge`.

Tests cover approval/window/nonce, exact allowlist and identity, REAL/CONTEST/
unknown account modes, terminal/path/build/permission changes, foreign exposure,
source/binary-manifest prerequisites, mappings, symbol/volume/stop/quote/margin
data, stale quotes, no fallback, unknown fields, secret redaction, prohibited API
surface mutations, SDK/import/network attempts and deterministic offline results.
Fixture evidence strings/hashes are explicitly synthetic, not actual attestations.

**Native compilation and MT5 runtime: NOT RUN.** No EX5 artifact is certified.
No actual account, quote, margin, credential role or connection latency is verified.
Snapshot matching does not authenticate a broker or validate the truth of an
operator evidence reference. Native fences do not eliminate account-switch ABA
races without independent isolation/supervision. Ping is last-reported telemetry;
quote age is a server-relative estimate, not a certified UTC execution feed.

The five-second native budget is cooperative; a blocking native getter may overrun.
The operator supervises the separately approved bounded session. A timeout/stopped/
partial/no-output capture is NO-GO, never a signal to enable trading or reconnect.
The collector's nonce-file check assumes one supervised invocation, not an
adversarial multi-process filesystem transaction. Raw account/path/quote data stay
private; only sanitized validator outcomes may be published.

## Gate A / Gate B and recommendation

The exact [Gate A approval request](GATE_A_APPROVAL_DRAFT.md) covers one supervised
investor session and metadata/current-quote inspection only, with bounded local
artifact/cache/log writes confined to an isolated research terminal. It does not
cover orders, account changes, historical downloads or SHADOW. Populate the private
target/build manifest and obtain independent native compilation/isolation/access
review **before requesting activation of that concrete session**.

[Gate B](GATE_B_REQUIREMENTS.md) needs its own fresh approval after independently
reviewed Gate A evidence, an implemented/reviewed actual order adapter, real
retcode/partial-fill/margin/stop semantics, account/risk/one-use grant controls,
watchdog and final-flat proof. Investor authentication does not become trading
authentication under Gate A. The preserved Phase 7.0 canary envelope is a proposal,
not a permission or an executable adapter.

**Recommendation: GO for offline review of this packet; operational Gate A NO-GO
until missing private target/build evidence and explicit approval; Gate B NO-GO.**
No broker/terminal/credential/order/production action, unattended execution, SHADOW
or sealed-holdout access occurred. All 124 prior public Git blobs, including Phase
7.0's exact result/risk files, are preserved. Draft PR #2 remains unmerged; main
and DMB PR #1 remain untouched.
