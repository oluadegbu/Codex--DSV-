# Local shadow runbook

Python 3.11+, dedicated non-admin DCI workspace. Never run as Administrator.
Windows activation must use verified non-admin DirectiveCodex; current connection
fails that gate. The cloud test identity is agent, not DirectiveCodex.

From the repository root:

```sh
PYTHONPATH=src python -m unittest discover -s tests -v
PYTHONPATH=src python tools/certify_bridge.py
PYTHONPATH=src python -m dci.bridge.brain --database /tmp/dci-bhb.sqlite --workspace .
```

The third command starts a foreground local stdio prototype. Send JSON-RPC
initialize, then notifications/initialized, then tools/call. A task request:

```json
{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"dci_submit_task","arguments":{"action":"synthetic_check","task_id":"example-task-001","correlation_id":"example-correlation-001"}}}
```

Use stable task/correlation IDs on retries. Do not replace an uncertain request
with a new ID. Independently run one scheduler tick:

```sh
PYTHONPATH=src python -m dci.bridge --database /tmp/dci-bhb.sqlite --workspace .
```

Then call dci_get_status with the exact task_id from Brain. dci_control supports
PAUSE and RESUME. Default Runner has no Hands process adapter. --hands enables
only fixed local tests/fixture/Codex read-only templates, without privilege changes.
Live Codex certification currently fails initialization and remains blocked.
--now is a synthetic-clock option; it is not a production scheduling interface.

Dedicated databases must not be shared with the paper journal or DAT/DPM.
Runtime DBs and raw Hands logs are ignored by Git. Raw logs stay local; only
reviewed summaries/hashes and deterministic certification evidence are committed.
No notifications are sent externally by any command above. There is no CLI live
approval endpoint. SimulationSession approval tests cannot authorize production.

After crashes, wait for lease expiry and run a tick. NEEDS_HUMAN means reconcile
or seek the exact authorized decision; do not delete rows, reset state, modify
leases or requeue uncertain external operations. Failed delivery never grants
permission. Preserve DB/audit evidence before diagnosing.

To prepare Windows later, obtain a certified non-admin connection and accessible
isolated workspace, compare Git history and transplant only missing commits.
Do not use Administrator, force pushes, shared credentials, service installation
or protected-path workarounds to complete this runbook.

Windows PowerShell equivalents, only after the non-admin/access gate is certified:

```powershell
$env:PYTHONPATH = 'src'
python -m unittest discover -s tests -v
python tools/certify_bridge.py
python -m dci.bridge --database .\artifacts\dci-bhb.sqlite --workspace .
```

Create the dedicated artifacts directory through the authorized non-admin session
first. Runtime refuses an account other than DirectiveCodex or a token containing
the Administrators group, including a filtered administrative token.
