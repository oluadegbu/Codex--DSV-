# DMB local shadow runbook

Use non-admin Linux and Python 3.11+. No credentials, new services, network,
package installation or paid API is needed. Read BUILD_STATE and unresolved
decisions first. Never point DMB at the ordinary BHB database or production paths.

## Existing observed labs

```sh
PYTHONPATH=src python -m dci.master --workspace "$PWD" --database /tmp/dmb-shadow.sqlite report
PYTHONPATH=src python -m dci.master --workspace "$PWD" --database /tmp/dmb-shadow.sqlite submit --task-id demo-bhb --correlation-id demo-correlation --project BHB
PYTHONPATH=src python -m dci.master --workspace "$PWD" --database /tmp/dmb-shadow.sqlite tick
```

The committed worker manifest records observed absolute paths. To reconstruct
reviewed labs elsewhere, use an empty **sibling** directory; existing labs are
never overwritten:

```sh
python tools/prepare_dmb_labs.py --destination /tmp/dmb-labs-new --manifest /tmp/dmb-workers-new.json
PYTHONPATH=src python -m dci.master --workspace "$PWD" --database /tmp/dmb-new.sqlite --workers /tmp/dmb-workers-new.json report
python tools/certify_dmb.py --workers /tmp/dmb-workers-new.json --output /tmp/dmb-new-evidence
```

Relocation checks bundle hashes, clones locally, updates and commits only the
workspace marker, and records the resulting HEAD in the new manifest. A fresh
DMB database is required for a changed registry or worker manifest. The current
prototype rejects silent configuration drift; migration/reconciliation is a
future task. Preserve old databases and audit evidence.

## Independent operation and Brain transport

```sh
PYTHONPATH=src python -m dci.master --workspace "$PWD" --database /tmp/dmb-shadow.sqlite foreground --ticks 10 --interval 1
PYTHONPATH=src python -m dci.master --workspace "$PWD" --database /tmp/dmb-shadow.sqlite mcp
```

`foreground` is bounded to 100 ticks, not a service installer. Exit/restart keeps
SQLite authority. `mcp` accepts newline JSON-RPC 2.0 on local stdin; initialize,
then `notifications/initialized`, then `tools/list`/`tools/call`. This transport is
a local prototype, not an authenticated remote ChatGPT connection. Avoid public
exposure. PAUSE/RESUME use `dmb_control`; no arbitrary commands are supported.
Reports are explicit requests; a conversation has no assumed background wake-up.

Synthetic infrastructure operations request simulated HEG approval and perform
only inert markers. Simulation approvals cannot approve deployments, credentials,
live trading, real provider delivery or uncertain execution retries.

## Certification and recovery

```sh
PYTHONPATH=src python -m unittest discover -s tests -v
python tools/certify_dmb.py --output /tmp/dmb-certification-evidence
python -m compileall -q src tools tests
```

The certification tool runs the regression suite, 100 actual trusted verifier
cycles, exact replay, periodic database reopen and an overlap barrier proving
three concurrent processes. It records Git/source hashes, resource limits,
reports and per-gate status. Evidence under `artifacts/` is local-only; reviewed
summary/log output is suitable for Git. Live gates remain blocked even when
local shadow checks pass.

A crash after claim can leave a worker running. On lease expiration DMB preserves
locks **and** budget reservations and records control-plane degradation. Do not
reset the lease, delete locks, or approve a blind rerun. Inspect exact worker/Git
artifacts and obtain a scoped reconciliation decision. Unrelated routes proceed
only within remaining budgets. Terminal predecessor failure remains visible;
dependent tasks do not silently disappear or execute.

GitHub publication currently fails with integration HTTP 403. Preserve local
commits/bundles. Once access is restored, inspect the latest remote tree and
publish a reviewed integration branch based on its remote parent. Local and
remote roots differ: do not force-push local main over existing remote history.
