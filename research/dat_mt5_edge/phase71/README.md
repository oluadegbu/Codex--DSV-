# Reproduce offline preparation

From `research/dat_mt5_edge` using existing standard-library Python 3.10+:

```sh
python -m phase71.certify
```

This verifies 124 baseline public file identities and runs 39 new preflight tests
plus the existing 88 regressions. It creates only isolated temporary fixture DBs
and `phase71/results/offline_verification.json`. It does not compile MQL5, start a
terminal, read credentials, connect accounts or send orders. No native runtime
certification follows from these tests.

The [report](REPORT.md), [Gate A request](GATE_A_APPROVAL_DRAFT.md),
[conditional operator procedure](OPERATOR_PROCEDURE.md) and
[separate Gate B requirements](GATE_B_REQUIREMENTS.md) define the remaining gates.
Default targets and approvals are disabled. Do not run the native collector until
the exact private target/build/role/isolation evidence and separate approval exist.
