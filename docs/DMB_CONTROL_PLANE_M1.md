# Functional DMB shadow control plane — milestone 1

Delivered: task intake → dependency planning → actual deterministic worker
dispatch → DCI paper research → artifact verification → durable completion →
restart recovery → consolidated reporting. This uses the existing portfolio
registry, PortfolioPlanner, BHB database, audit, resource locks and Brain tools.
It adds one fixed `shadow_research` operation; it does not replace the architecture.

The shortest executable path is one trusted, non-root Linux foreground controller
and one Git-pinned disposable DCI worker. Python 3.11+ and Git suffice. No account,
service, credential, network endpoint or package installation is needed. Actual
process execution is verified; input prices/wallets and paper outcomes remain
synthetic. Codex dispatch, external notifications and remote Brain authentication
remain disabled in this runtime.

## Run the complete workflow

Use new output paths. Preparation refuses to overwrite a workspace or manifest.

```sh
python tools/prepare_shadow_research_worker.py --destination /tmp/dmb-research-worker-m1 --manifest artifacts/research-workers-m1.json
python tools/run_control_plane_workflow.py --workers artifacts/research-workers-m1.json --output artifacts/research-workflow-m1
```

The driver executes separate CLI processes, submits two dependency-linked jobs,
dispatches actual Python worker processes, then submits a third job and exits the
actual controller with code 73 after a verified worker receipt is durable but
before scheduler completion. A new controller verifies and commits that receipt
without reexecuting the worker. Duplicate intake also produces no new dispatch.
`WORKFLOW.json` records child PIDs/UIDs, Git state, artifact digests, paper events
and restart outcomes. SQLite journals and raw logs remain private under artifacts.

For normal operation use `python -m dci.master.runtime_cli` with `PYTHONPATH=src`:

```sh
PYTHONPATH=src python -m dci.master.runtime_cli --workspace "$PWD" --database artifacts/research-state.sqlite --workers artifacts/research-workers-m1.json intake <<'JSON'
{"task_id":"research-1","correlation_id":"corr-research-1","project_id":"DCI"}
JSON
PYTHONPATH=src python -m dci.master.runtime_cli --workspace "$PWD" --database artifacts/research-state.sqlite --workers artifacts/research-workers-m1.json foreground --ticks 10
PYTHONPATH=src python -m dci.master.runtime_cli --workspace "$PWD" --database artifacts/research-state.sqlite --workers artifacts/research-workers-m1.json report
```

The `mcp` command exposes the existing central tools over local stdio, with intake
restricted to this operation. `status --task-id research-1` returns correlated
durable results. `cancel --task-id research-1` requests cancellation of a currently
running owned dispatch; its response explicitly does not certify termination.
The eventual verified receipt records termination and the task becomes FAILED.
No dependent job executes after cancellation or failure.

## Execution and recovery boundaries

- Mailbox input contains stable IDs, priority and dependency IDs. Commands,
  prompts, environment values, alternate fixtures and filesystem paths are not
  accepted. The only enabled project is DCI.
- A fresh worker clone pins clean Git, all Python sources and the fixed synthetic
  fixture. The actual entry enforces 256 MB address space, 10 CPU seconds, 1 MB
  per-file output and 64 descriptors; the controller enforces 20 wall seconds.
  The scheduler permits one worker and retains workspace/memory reservations.
- A durable dispatch intent precedes process launch. The child runs with fixed
  argv, no shell and a minimal environment without inherited provider credentials.
  Results and the paper ledger are written to a separate per-attempt directory.
- A receipt is atomically written only after the controller observes process
  termination. Verification checks route/fence/correlation, pinned Git/source
  scope, child identity, output hashes and the shadow-only result envelope.
- A restart can finish an intact receipt only while the original lease and task
  deadline are valid. It can also repair a journal/terminal-state commit gap
  without emitting another RESULT. It never resets a lease or reruns effects.
- Missing/tampered evidence, unknown started-process outcome or expiry retains
  the reservation and enters control-plane degradation. Ordinary simulated
  approvals cannot clear that quarantine. Local file hashes/audit assume trusted
  same-account code; they are not hostile-user authentication or OS confinement.
- Cancellation kills only the newly owned Linux process group. Cancellation and
  timeout are distinct: a timed-out/uncertain outcome stays quarantined. An actual
  owned-process cancellation integration test stops its newly created child long
  enough to deliver the normal cancel request, then proves group termination.

No Windows ACL, account, production permission, trading control, kill switch,
Administrator recovery access or service was changed. DAT Temporal Integration
remains a separate preserved milestone; Temporal contracts are unchanged.

## Current Windows access boundary

The operator reports DirectiveCodex non-admin identity, official CLI v0.162.1,
ChatGPT authentication and genuine Codex execution PASS. That baseline is retained
as operator-reported evidence. One guarded read-only check of the currently
connected Desktop Commander executor still returns Administrator/High; no worker
was launched through that token. Access to the verified non-admin connection,
not another routine authentication check, is the prerequisite for the next
Codex integration milestone. Isolation/cancellation/recovery of that genuine
Windows Codex worker cannot be inferred from the Linux deterministic workflow.

See [milestone evidence](evidence/control-plane-m1/WORKFLOW.json),
[focused checks](evidence/control-plane-m1/FOCUSED_TESTS.log),
[source binding](evidence/control-plane-m1/SOURCE_CERTIFICATION.json) and
[artifact hashes](evidence/control-plane-m1/ARTIFACT_MANIFEST.json).

The prior Phase9 manifest is a snapshot: its README/BUILD_STATE hashes refer to
local source commit `1a7319098dd5099858e9c1cbeb2739df37cb0458`. New live project
state advances without rewriting historical certificates. Continuity verification
checks those two historical files from Git and all old evidence bytes in place.
