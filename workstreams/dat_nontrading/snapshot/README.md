# DAT non-trading isolated DMB workstream

This independent SHADOW research sandbox validates synthetic historical OHLCV
bars and computes deterministic hypothetical first-close/last-close PnL with
entry and exit fees and slippage. The arithmetic can support research on futures
or MT5-style bars. It is not a DAT Futures/MT5 production integration, platform
certification, strategy implementation, account configuration, or broker adapter.
No real DAT source, system state, or credentials were supplied or accessed.

All identifiers must start with `SYNTH-`. Only `SHADOW` mode is accepted, and any
order intent is rejected. There is no execution API, network, broker dependency,
or account/symbol targeting. The workstream does not modify trading controls.
Timestamp validation rejects future, duplicated, and out-of-order samples;
OHLCV and parameters must be finite and within bounded numeric representation,
magnitude, and precision. Streams consume at most 1001 bars before rejecting
inputs over the 1000-bar resource limit. Quantity is bounded at 100 hypothetical
units; these research-only bounds do not replace any production risk controls.

Run the fixed local tests:

```sh
PYTHONPATH=src python -m unittest discover -s tests -v
```

`WORKER_REPORT.json` records identity, scope, actual test evidence, source hashes,
and Git provenance. Work proceeds under the unprivileged `agent` identity
(uid 1000) in `/workspace/dmb-workers/dat_nontrading`. Tests use synthetic data
only. There are no services, scheduled tasks, external providers, trading
operations, or production changes. Integration with actual DAT code requires
non-secret source artifacts and a separate compatibility review; live operation
remains explicitly outside this worker's authorization.
