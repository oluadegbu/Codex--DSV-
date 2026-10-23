# Offline mechanics reproduction

From `research/dat_mt5_edge`:

```sh
python -m phase7.certify
```

Existing Python 3.10+ standard library only. The command creates only temporary
synthetic test databases and `phase7/results/offline_certification.json` in this
isolated research checkout. It checks all 113 baseline public artifacts unchanged,
then runs the 56 new lifecycle tests and the existing 32 Phase 6.2 fixtures.
No historical market data, broker SDK, terminal, credentials or network is needed.

Inspect [REPORT.md](REPORT.md), [runtime design](RUNTIME.md), the disabled
[demo profile](demo_isolation.json) and [future canary approval draft](DEMO_CANARY_APPROVAL_DRAFT.md).

Fixtures are synthetic accounts/contracts and a synchronous single-owner model.
The results verify declared offline software behavior only; they do not certify
actual MT5 integration, real demo controls, complete CFD/broker semantics,
unattended operational readiness or profitability. No routing activation switch
exists in this package. Do not copy these fixture defaults into production.
