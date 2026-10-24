# Proposed data-only procedure — inactive

**Reviewable artifact:** `collector.py` is a passive MT5-export consumer, not an MT5 bridge. Its sole public method accepts bounded JSON bytes and a supplied clock, returning a validated quote tuple. It imports only `json` and `decimal`; no file, network, process, SDK, plugin/callback, credential, terminal or broker handle exists in this module. Source-level capability audit and runtime tests cover the exact pinned artifact. No exporter/terminal connection has been implemented or started.

The exact input keys are `schema`, `source_id`, `symbol`, `sequence`, `timestamp_ms`, `bid`, `ask`. Schema must be `MT5_QUOTES_V1`; prices are decimal strings. Reject extra/duplicate keys, unknown identity/symbol, invalid/nonfinite/off-grid/inverted prices, excessive spread, stale/future timestamps and replayed/out-of-order sequence/time. Rejected messages do not advance state. Source/symbol identity is an allowlist, **not authentication**. Fresh process state is not durable replay protection.

## What is demonstrated

`python -m phase4.capability_audit` checks the collector import/attribute boundary and rejects prohibited dynamic execution/I/O primitives. Tests also consume a valid message with file opening and imports disabled, reject order/modification/account/password/callback fields and exercise replay and malformed quotes. [Pinned audit output](results/collector_capability.json) binds the source hash. These checks demonstrate that the shipped consumer exposes no order-submission, modification or broker-mutation interface.

This is not an OS sandbox or a formal proof about arbitrary Python code in the host, nor proof about an external producer. Co-locating an MT5 Python SDK and merely wrapping a few quote functions would fail the intended capability separation; no such SDK adapter is supplied.

## Steps before a future broker-connected session

1. Review this file-only architecture first. Rehearse entirely offline using synthetic or certified historical exports; no account identifiers belong in the schema.
2. Separately authorize the exact terminal/account connectivity procedure, scope and duration before any startup or login. Current Phase 4 authorization does not cover it.
3. Prefer a broker-provided read-only credential/session if available; verify independently that the credential cannot mutate orders. Do not infer read-only access from disabled algo-trading toggles or an account label. Do not retrieve existing credentials to test this.
4. Produce a separately reviewed exporter artifact and demonstrate that it cannot access order-submission/modification functions. If MT5 cannot enforce the required data-only capability, use manual file export from a separately authorized session instead. Do not activate a full broker SDK under a nominal read-only wrapper.
5. Transfer quote-only exports into an isolated consumer environment with no broker package, credentials, terminal or broker network route. Validate signed/hashed producer identity, approved exact symbol, contract definition, UTC millisecond semantics, real spread and clock synchronization. Define an append-only durable replay/audit mechanism before unattended collection; none is deployed now.
6. Run hypothetical SHADOW decisions only after data and chronology gates pass. Never treat collection approval as DEMO authority. Every new DEMO order requires separate explicit authorization outside this interface.

There is no persistent service, scheduled task, EA, relay or deployment in Phase 4. Existing risk limits, account targeting, kill switches and all DAT/DMB controls remain untouched.
