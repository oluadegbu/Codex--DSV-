# DPM isolated synthetic research worker

This is an independent DMB SHADOW workstream, not the production DPM repository.
No actual DPM state, strategy, source or certification was provided. The results
below certify this bounded synthetic module only.

`dpm_shadow.evaluate()` accepts version 1 SHADOW RESEARCH requests containing
explicit synthetic paths, consecutive period indices and fixed initial weights.
It calculates portfolio cumulative return and peak-to-trough drawdown from fixed
initial exposure indices. It produces no allocations, orders or execution intent.
All values use a deterministic 128-digit decimal context; returns and weights must
be decimal strings or integers. Each synthetic return lies within [-1, 1].

Inputs require exact fields and asset matching. Invalid modes, intents, malformed
paths, repeated scenarios and resource-limit violations fail closed. Limits are
32 scenarios, 16 assets, 512 periods, 65,536 total samples, 64 input characters
and absolute decimal exponent at most 40. The fixed local module has no network,
credentials, provider, trading, notification or persistent-service interfaces.

Run offline checks:

```sh
PYTHONPATH=src python -m unittest discover -s tests -v
```

Workspace: `/workspace/dmb-workers/dpm_simulation`. Worker identity: `agent`,
UID 1000. The directory is an isolated local Git repository with scope recorded
in `WORKER_SCOPE.json`. `WORKER_REPORT.json` records actual test and Git evidence.
Production DPM integration, live Codex authentication and remote Git publication
remain uncertified. Next safe action: review non-secret DPM interface artifacts,
then expand synthetic stress fixtures within this unchanged SHADOW boundary.
