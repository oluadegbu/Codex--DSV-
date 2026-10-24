# Gate A — one read-only DEMO session, DRAFT / NOT APPROVED

Designated server confirmed by the user: **VantageMarkets-Demo**. This designation
is not permission to connect and does not prove an account is DEMO. No account
number, credential, company, terminal or exact contract mapping has been verified.

## Proposed exact approval wording

> Approve one supervised, read-only MT5 preflight to the one privately allowlisted
> dedicated DEMO account on VantageMarkets-Demo, using the independently reviewed
> native collector source and compiled binary recorded in the private manifest.
> Permit startup of only the exact isolated research terminal/build/data folder
> and operator-managed investor/read-only authentication for this session. The
> session may last at most ten minutes, in the precise UTC window in the manifest.
> Run the one-shot collector once with its approved nonce; inspect only account/
> terminal identity, permissions, flatness, availability of the four exact approved
> symbols, contract/volume/stop/margin properties, current bid/ask, health and ping.
> Permit ordinary isolated terminal cache/log writes and one private result file
> of at most 64 KiB, followed by offline validation and sanitized reporting.
> Do not place, modify, cancel or close orders; select/switch/fall back to another
> account; enable trading/DLLs; change passwords, permissions or production settings;
> download historical data; activate SHADOW, an unattended worker or any strategy.
> Stop on failed identity/DEMO/read-only/isolation evidence, timeout, stale data or
> unexpected exposure. Gate B and all DEMO/live order authority remain OFF.

This text becomes actionable only when the private manifest below is complete and
the human explicitly approves that exact scope. No approval is inferred from a
JSON Boolean, a fixture, server name, old journal or this document.

## Required private manifest, before approval

- Exact existing dedicated demo login/server, company string and currency;
  only one account in the allowlist. No public account identifiers or passwords.
- Existing investor/read-only access independently verified through the operator/
  broker's supported means; no mutation-based permission test. Master trading
  credentials are prohibited. No new password or account may be created under
  this approval; if needed, request that specific action separately.
- Exact terminal name/build, binary hash, executable and separate isolated data
  paths; independent evidence of no shared production state, accounts, profiles,
  EAs/services or unrelated exposure. Standard-user operation and private output
  permissions must already be in place; no automatic ACL/policy changes.
- Independently reviewed MQ5 source hash, offline native compilation log/build,
  compiled EX5 hash and reproducible source→binary provenance. No terminal startup
  or broker session is needed for that offline review. Current native compilation
  is **NOT VERIFIED**; do not substitute the Python tests for it.
- Existing terminal Algo Trading/DLL permissions and script trading/DLL permission
  OFF. Operator evidence of investor access plus the account trading flag FALSE.
  A FALSE flag alone does not prove which password role was used.
- Exact EURUSD/GBPUSD/XAUUSD/BTCUSD broker symbols, approved expected units/product
  identity, private output location and permitted private snapshot retention.
  No guessed suffix, fuzzy symbol selection or historical-data licensing grant.
- Approval/reviewer reference, unique session nonce and start/end UTC timestamps,
  at most ten minutes apart, outside closed/stale market periods. The collector
  checks a five-second cooperative capture budget. The operator independently
  supervises and stops a stalled script; no service/scheduler is created.

## Scope and abort rules

The collector cannot start/login/switch an account; authentication is a separate
operator action within the approved session. It checks broker-provided DEMO mode,
exact account/server/company/currency and terminal identity at entry, around each
symbol and before output. REAL/CONTEST/unknown/mismatch denies capture. It requires
zero positions and orders, never closes/cancels unexpected exposure and does not
select symbols into Market Watch. Unselected/unavailable/stale symbols fail closed.

The fixed module has no submission, modification or closing call. Investor access
is the independent broker boundary; the full MT5 application is not inherently
order-incapable if somebody logs in with a master password. Do not test read-only
permissions by attempting an order. Do not enable a forbidden setting to make
the collector run. There is no reconnect, retry, alternate account or fallback.

The five-second capture budget is cooperative between native getters; an API stall
cannot be represented as a hard OS deadline. The script honors stop requests and
rejects an overrun. No valid output means NO-GO, not silent success. Terminal ping
is the last reported value, not an active network benchmark. Quote age is a
server-relative estimate, not independently certified UTC execution freshness.

All raw snapshots and normal terminal logs stay private in the isolated research
terminal. They may contain account/path/contract identifiers but never passwords
from this collector. Only the validator's redacted status/codes are publishable.
Do not publish raw bid/ask, login, server paths, binary locations or approval records.

Completion: independently confirm same account/permissions, no order/position
change, one nonce-bound snapshot and acceptable offline validation. Account
switching ABA races and snapshot authenticity require isolation/supervision;
local matching of JSON fields is not proof of a genuine broker session.

**Status now: no Gate A approval, terminal startup, authentication or native run.**
