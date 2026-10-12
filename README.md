# Directive Crypto Intelligence (DCI)

DCI is an isolated Solana wallet-intelligence and memecoin research system.
Phase 0 provides a deterministic **synthetic shadow-only** vertical slice.
There is no wallet signing, transaction submission, real fund movement, or live trading.

## Run locally

Python 3.11+; runtime and tests use only the standard library. No install or API key required.

```sh
PYTHONPATH=src python -m unittest discover -s tests -v
PYTHONPATH=src python -m dci tests/fixtures/synthetic.json
python -m compileall -q src tests
```

The fixture reconstructs synthetic early buyers, loads point-in-time wallet profiles,
deduplicates independent clusters, gates risk, scores an opportunity, and tracks
paper entry, marks and exit. Prices and identities are artificial. Outputs are
research evidence, never investment recommendations or profitability claims.

## Current capabilities and limits

- Public Solana finalized RPC read-only adapter with method allowlist, timeout,
  bounded response and injectable transport. Tests do not access the network.
- Discovery/risk adapter protocols; fixture discovery; versioned wallet registry
  and experimental bounded outcome recalibration.
- Cluster-aware convergence, missing/stale risk rejection, deterministic Decimal
  scoring with the initial 25/20/15/20/10/10 research hypothesis.
- Bounded synthetic USD shadow ledger with modeled combined fee/slippage cost,
  stop, take-profit and time exits. No on-chain execution code.
- Atomic SQLite paper journal with idempotent retry, conflict detection and restart recovery.
- Automated tests and GitHub Actions configuration.

Live transaction decoding, real token cohort selection, real wallet linkage,
market/rug data completeness and Temporal workflows are **not implemented**.
Do not classify raw token balance changes as verified buys. An explicit DEX-aware
parser and evidence provenance are required first. No daemon is deployed.

See [architecture](docs/DCI_ARCHITECTURE.md), [worker instructions](CODEX.md),
[supervisor policy](SUPERVISOR_POLICY.md), [build state](BUILD_STATE.json) and
[decisions](decisions/README.md). GitHub is the durable development record.

## Durable local shadow replay

```sh
PYTHONPATH=src python -m dci tests/fixtures/synthetic.json --journal /tmp/dci-paper.sqlite
```

Run the same command again to verify idempotency. The journal retains modeled
entries, marks, exits and input/config evidence across process restarts. Use a
dedicated DCI database; unrelated databases are rejected. Journal files stay out
of GitHub. This standalone CLI works without ChatGPT or an operator browser;
continuous ingestion and Temporal scheduling are still pending.

Publication status is recorded in BUILD_STATE.json. The current authenticated
GitHub connector has independently passed write/readback certification. The
implementation is published on a development branch in draft PR #1; historical
403 evidence remains unchanged. The main branch has not been updated.

## Brain–Hands Bridge and Human Escalation Gateway

An isolated local BHB/HEG shadow prototype adds a versioned SQLite mailbox,
non-admin one-shot Runner, fixed Hands verification templates, local MCP Brain
tools, durable NEEDS_HUMAN decisions and simulated notification fallback.
See [architecture](docs/BHB_HEG_ARCHITECTURE.md), [runbook](docs/BHB_RUNBOOK.md),
[baseline](docs/BHB_BASELINE.md), [certification evidence](docs/evidence/BHB_CERTIFICATION.json)
and [integration roadmap](docs/BHB_INTEGRATION_ROADMAP.md).

```sh
PYTHONPATH=src python tools/certify_bridge.py
```

Synthetic gates can pass independently of live gates. Windows DirectiveCodex,
live Codex execution, actual ChatGPT delivery and real notification
providers remain BLOCKED. The Windows remote currently runs as Administrator;
no implementation was performed there. No continuous service is installed.

## Directive Master Brain

DMB adds a versioned 13-project [portfolio registry](portfolio/REGISTRY.v1.json),
dependency/priority planner, three Git-pinned isolated trusted shadow labs,
central local MCP inbox/outbox, HEG simulation and Temporal-compatible contracts.
See [architecture](docs/DMB_ARCHITECTURE.md), [runbook](docs/DMB_RUNBOOK.md),
[portfolio report](docs/evidence/DMB_PORTFOLIO_REPORT.json),
[dependency graph](docs/evidence/DMB_DEPENDENCY_GRAPH.json) and
[certification](docs/evidence/DMB_CERTIFICATION.json).

```sh
python tools/certify_dmb.py --output /tmp/dmb-evidence
```

Local shadow verification passes 100 real verifier cycles with no lost/duplicate
execution and three overlapping processes. **Full DMB SHADOW CERTIFIED remains
BLOCKED** by live interfaces, authenticated delivery, stronger OS worker isolation,
actual external project access. GitHub publication now passes independently. DAT/DPM lab results
are synthetic research, not certification of their production repositories.

## DMB Phase 8

[External integration assessment](docs/DMB_PHASE8.md) preserves prior certification
and adds explicit authorization/isolation probes, project reconciliation and an
offline signed-event/receipt contract lab. The original 84 tests remain unchanged;
16 additive checks bring the passing regression suite to 100. Full external
certification remains BLOCKED. See the [matrix](docs/evidence/phase8/CERTIFICATION_MATRIX.json),
[hashes](docs/evidence/phase8/ARTIFACT_MANIFEST.json) and
[reconciliation ledger](portfolio/RECONCILIATION.phase8.v1.json).

```sh
python tools/verify_phase8.py
```

This runs local tests/fault fixtures and preserves the old certificate/bundle.
It does not connect remote providers, install services or certify live identity.

Phase 8 continuation on October 12 adds 17 separate offline authorization-policy
fixtures while preserving the existing 100-test suite and all prior certificate
hashes. See [continuation evidence](docs/DMB_PHASE8_RECHECK_20261012.md).

```sh
python tools/verify_phase8_authorization.py --output /tmp/dmb-auth-evidence
```

These fixtures provide no real OAuth authentication or human approval.

## GitHub publication

[Draft PR #1](https://github.com/oluadegbu/Codex--DSV-/pull/1) publishes the verified
implementation on a dedicated development branch. Main is unchanged.
[GitHub Actions](https://github.com/oluadegbu/Codex--DSV-/actions/runs/38305161935)
passes on the verified import commit.

[Publication certificate](docs/evidence/publication/CERTIFICATION.json),
[original commit provenance](docs/evidence/publication/PROVENANCE.json), and the
verified original Git-history bundle preserve the exact local implementation
commits. Publication uses the existing remote parent, with no force push.

This chat's authenticated GitHub connector passed the write check independently
of the operator's Codex Cloud authorization. Historical certificate failures
remain unchanged; BUILD_STATE.json records current publication status.
Full DMB external certification remains blocked by the other safety/runtime gates.
