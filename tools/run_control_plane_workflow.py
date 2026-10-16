"""Execute intake-to-paper-result and actual controller restart in separate processes."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workers", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    out = Path(args.output).resolve()
    if out.exists() or root / "docs" in out.parents:
        raise PermissionError("fresh untracked evidence directory required")
    out.mkdir(parents=True)
    workers = Path(args.workers).resolve(strict=True)
    argv = [sys.executable, "-m", "dci.master.runtime_cli", "--workspace", str(root),
            "--database", str(out / "master.sqlite"), "--workers", str(workers)]
    env = {"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8", "PYTHONDONTWRITEBYTECODE": "1", "PYTHONPATH": str(root / "src")}
    def cli(command, payload=None):
        proc = subprocess.run(argv + [command], input=None if payload is None else json.dumps(payload),
                              env=env, capture_output=True, text=True, timeout=30, check=True)
        return json.loads(proc.stdout)
    for task, dependencies in (("research-001", []), ("research-002", ["research-001"])):
        cli("intake", {"task_id": task, "correlation_id": "corr-" + task, "project_id": "DCI", "dependencies": dependencies})
    first, second = cli("tick"), cli("tick")
    cli("intake", {"task_id": "research-001", "correlation_id": "corr-research-001", "project_id": "DCI", "dependencies": []})
    duplicate = cli("tick")
    cli("intake", {"task_id": "research-crash", "correlation_id": "corr-research-crash", "project_id": "DCI"})
    # Crash the actual controller after an actual child completes and atomically
    # seals its receipt, before planner.finish. No fake execution or fake receipt.
    fault = ("from pathlib import Path; import os,sys,time; sys.path.insert(0,sys.argv[1]+'/src'); "
             "from dci.bridge.store import BridgeStore; from dci.master.registry import PortfolioRegistry; "
             "from dci.master.planner import PortfolioPlanner; from dci.master.control_plane import ShadowControlPlane; "
             "root=Path(sys.argv[1]); store=BridgeStore(sys.argv[2]); "
             "planner=PortfolioPlanner(store,PortfolioRegistry(root/'portfolio/REGISTRY.v1.json'),sys.argv[3],root); "
             "runtime=ShadowControlPlane(planner); job=planner.claim(int(time.time()))[0]; "
             "evidence=runtime.dispatch(job); assert evidence['passed']; os._exit(73)")
    proc = subprocess.run([sys.executable, "-I", "-c", fault, str(root), str(out / "master.sqlite"), str(workers)],
                          env=env, capture_output=True, timeout=30)
    if proc.returncode != 73:
        raise RuntimeError("controller fault scenario failed: " + proc.stderr.decode())
    restarted = cli("tick")
    final = cli("report")
    if len(first["executed"]) != 1 or len(second["executed"]) != 1 or duplicate["executed"]:
        raise RuntimeError("lost, duplicate or dependency dispatch")
    if restarted["recovered_without_reexecution"] != ["research-crash"] or restarted["executed"]:
        raise RuntimeError("receipt recovery reexecuted a worker")
    if len(final["jobs"]) != 3 or any(job["state"] != "SUCCEEDED" for job in final["jobs"]) or final["held_resources"] or not final["audit_chain_valid"]:
        raise RuntimeError("durable final state or audit failed")
    results = []
    for dispatch in final["control_plane"]["dispatches"]:
        directory = Path(dispatch["directory"])
        receipt = json.loads((directory / "receipt.json").read_text())
        report = json.loads((directory / "report.json").read_text())
        result = json.loads((directory / "result.json").read_text())
        if [event["type"] for event in result["audit"]] != ["paper_entry", "paper_mark", "paper_exit"]:
            raise RuntimeError("paper workflow did not complete")
        results.append({"task_id": receipt["task_id"], "correlation_id": receipt["correlation_id"],
                        "pid": receipt["pid"], "uid": receipt["uid"], "worker_git_commit": receipt["git_before"],
                        "exit_code": receipt["exit_code"], "process_group_terminated": receipt["process_group_terminated"],
                        "fence": receipt["fence"], "files_sha256": receipt["files_sha256"],
                        "paper_events": report["paper_events"], "synthetic": result["synthetic"], "mode": result["mode"],
                        "score": result["score"], "receipt_sha256": hashlib.sha256((directory / "receipt.json").read_bytes()).hexdigest()})
    summary = {"schema_version": 1, "generated_at": datetime.now(timezone.utc).isoformat(),
               "workflow": "intake -> dependency planner -> actual child -> verified result/ledger -> durable completion -> restart -> report",
               "status": "PASS", "scope": "real trusted Linux process execution with synthetic paper data; no actual Codex or hostile OS isolation certification",
               "completed_jobs": 3, "duplicate_dispatches": 0, "controller_crash_exit_code": 73,
               "restart_recovered_without_worker_rerun": restarted["recovered_without_reexecution"],
               "audit_valid": True, "reservations_released": True, "results": results,
               "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root).decode().strip(),
               "workers_manifest_sha256": hashlib.sha256(workers.read_bytes()).hexdigest(),
               "new_sources_sha256": {p: hashlib.sha256((root / p).read_bytes()).hexdigest() for p in
                                      ("src/dci/master/control_plane.py", "src/dci/master/runtime_cli.py", "tools/shadow_research_entry.py",
                                       "tools/prepare_shadow_research_worker.py", "tools/run_control_plane_workflow.py")},
               "codex_dispatch_enabled": False, "remote_delivery_enabled": False, "services_installed": False,
               "production_changes": False, "live_trading": False}
    (out / "WORKFLOW.json").write_text(json.dumps(summary, indent=2) + "\n")
    (out / "PORTFOLIO_REPORT.json").write_text(json.dumps(final, indent=2) + "\n")
    print(json.dumps({k: summary[k] for k in ("status", "completed_jobs", "duplicate_dispatches", "controller_crash_exit_code", "restart_recovered_without_worker_rerun")}))


if __name__ == "__main__":
    main()
