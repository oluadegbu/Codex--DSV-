# DCI architecture — Phase 0

Status: synthetic offline vertical slice implemented; public RPC interface
implemented; production ingestion and orchestration pending.

## Target data flow

Historical high-performing tokens (plus matched failures)
→ finalized early-buy reconstruction → wallet profiling → smart-wallet registry
→ monitoring → independent cluster convergence → token/rug/liquidity risk
→ deterministic opportunity score → shadow entry/position/exit
→ measured outcomes → continuous wallet-quality recalibration.

## Modules and boundaries

| Module | Responsibility | Current evidence |
| --- | --- | --- |
| models | Validated immutable events, profiles and risk/opportunity contracts | Decimal feature validation |
| adapters | Finalized Solana RPC GET-equivalent reads and discovery/risk protocols | Mock transport; no network validation yet |
| research | Early buyer fixture reconstruction and time-indexed wallet registry | Synthetic only; beta(1,1) outcome prototype |
| confluence | Deduplicate event identities; one representative per independent cluster | Unknown clusters excluded |
| scoring | Versioned weights, stale/missing evidence and authority/liquidity gates | Deterministic pure function |
| shadow | Synthetic USD book, friction and bounded paper exposure | In-memory ledger with optional durable SQLite replay |
| journal | Atomic append-only command journal and deterministic restart recovery | Dedicated SQLite, retry and corruption tests |
| pipeline | Fixture end-to-end orchestration | No daemon or production orchestration |

Raw RPC transaction responses do not constitute verified buy events. A future
DEX-specific decoder must distinguish swaps, transfers, liquidity changes and
multi-hop routes, preserve instruction indices and source signatures, and handle
failed transactions, token extensions, reorgs and missing historical data.
Finalized events are the default correctness boundary; confirmed data requires
an explicit provisional model and rollback policy.

## Independence and profiling

Wallet linkage must be evidence based (funding, co-activity, shared custody and
other validated features); a unique address does not prove independence.
Fixtures provide synthetic cluster identities. Only profiles known by evaluation
time and with at least five samples are included; profile age is bounded.
Discovery considers finalized buys in the token launch/cutoff interval.
A real registry must retain feature provenance, cohort/version, costs, sample
sizes and out-of-sample outcomes. The current recalibration helper is an
experimental cohort replacement, not an automatic validated learning policy.

## Scoring hypothesis

All features are normalized to [0,1]; Decimal arithmetic avoids binary drift.
Wallet quality 25%, convergence 20%, timing 15%, safety 20%, liquidity 10%,
momentum 10%. Convergence saturates at three independent clusters. Two clusters
are required. Risk evidence must match token, be no older than 60 seconds and
not come from the future. Unknown or active mint/freeze authorities or unverified
liquidity reject entry regardless of score. These conservative checks are not a
complete rug detector. Actual SPL Token and Token-2022 extension checks, holder
concentration, LP control, executable liquidity, transfer restrictions and price
freshness are pending. Manual fixture safety scores are never live evidence.

A score of at least .70 is a provisional paper experiment threshold. Timing and
momentum are fixture features; live feature normalization needs explicit definitions
and calibration. Record versions and contributions for every opportunity.

## Shadow experiment defaults

Synthetic cash 1000 USD; position budget 100 USD; max three open positions.
Combined adverse fee/slippage model .003 on entry and exit. Stop at 20% modeled
loss, take-profit at 50% modeled gain, maximum hold 3600 seconds. Prices must be
positive finite; timestamps cannot regress. One entry per token per replay.
These are plumbing defaults for synthetic tests, not approved financial limits or
market-fill claims. No private keys, balances, signing or transaction submission.

## Intended standalone runtime

A dedicated Solana ingestion/scoring worker will operate outside ChatGPT and
DSV/OpenClaw. Temporal will schedule discovery, reconciliation, risk enrichment,
outcome evaluation and recalibration with bounded retries and idempotent activities.
SQLite is suitable for the next single-worker local shadow checkpoint milestone;
production multi-worker storage and Temporal hosting are unresolved. No Temporal
cluster, service account or VPS was provisioned in Phase 0. Deployment requires
its own operational plan and must retain the hard gates.

## Acceptance and validation

Tests cover fixture replay, point-in-time registry, duplicates and linked wallets,
future/unfinalized events, stale/unknown risk, input validation, read-only RPC
allowlisting, exposure caps, modeled PnL and exits. See BUILD_STATE.json for exact
executed checks. Fixture outcomes do not validate signal quality or profitability.

## Follow-on milestone: durable paper journal

The optional journal uses SQLite WAL, synchronous FULL and BEGIN IMMEDIATE to
serialize append/recovery. A command identity has exactly one canonical payload;
identical retries return recovered state without applying twice. Changed payloads
fail closed. Invalid commands roll back. Paper state is reconstructed from all
committed commands, including the scoring features, evidence identities and
configuration version stored on entry. Schema/policy mismatches and unrelated
databases are rejected. A process-exit test verifies recovery after committed writes.

Hash chaining detects accidental payload edits and sequence gaps. It is not
protection against a privileged attacker rewriting hashes or truncating the tail;
external audit anchoring and backup policy remain future work. Recovery is O(n)
and is intended for small local research runs. Policy v1 fixes the existing paper
limits; changing replay semantics requires a new journal policy version. This
journal does not provide distributed scheduling, high-volume ingestion, Temporal
workflows or a deployed daemon.

## BHB/HEG control-plane prototype

The new bridge package supplies local shadow task/status/results, a standalone
one-tick Runner, fixed Hands checks, Brain MCP stdio and HEG simulation. It is
separate from Solana ingestion and the paper journal. See
[BHB/HEG architecture](BHB_HEG_ARCHITECTURE.md) for identity, lifecycle and exact
limits. This addition does not activate live trading, replace the intended
Temporal layer or modify DAT/DPM/DSV/OpenClaw/Pulse production services.
