"""Foreground DMB paper-research workflow using the existing durable authority.

One trusted Linux worker initially. No services, remote authentication, Codex
activation or production access. A receipt can recover completion, never retry an
uncertain started process. Local SHA evidence is not hostile-user authentication.
"""
from dataclasses import dataclass, replace
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
from uuid import uuid4

from dci.bridge.protocol import ProtocolError, canonical
from dci.bridge.runner import Runner
from .brain import MasterBrainTools
from .planner import Job


@dataclass(frozen=True)
class ShadowResearchJob(Job):
    operation: str = "shadow_research"

    def validate(self):
        if self.operation != "shadow_research" or self.project_id != "DCI":
            raise ProtocolError("only fixed DCI shadow research is enabled")
        Job.validate(replace(self, operation="verify_lab"))


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def atomic_json(path, value):
    path = Path(path)
    temporary = path.with_name(path.name + "." + str(uuid4()) + ".tmp")
    with temporary.open("x", encoding="utf-8") as stream:
        stream.write(canonical(value))
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)
    if os.name == "posix":
        fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)


class ShadowControlPlane:
    def __init__(self, planner):
        self.planner, self.store = planner, planner.store
        if planner.config["max_parallel"] != 1 or len(planner.workers) != 1:
            raise ProtocolError("first runtime milestone permits one worker only")
        self.entry = planner.workspace / "tools/shadow_research_entry.py"
        self.entry_sha = digest(self.entry)
        with self.store.tx():
            marker = self.store.db.execute("SELECT value FROM meta WHERE key='dmb_runtime_v1'").fetchone()
            if marker is None:
                self.store.db.execute("CREATE TABLE runtime_dispatch(task TEXT, fence INTEGER, scope TEXT, directory TEXT, state TEXT, receipt_sha TEXT, PRIMARY KEY(task,fence))")
                self.store.db.execute("INSERT INTO meta VALUES ('dmb_runtime_v1',?)", (self.entry_sha,))
            elif marker[0] != self.entry_sha:
                raise ProtocolError("runtime entry drift; preserve database and reconcile migration")

    def submit(self, arguments, now):
        allowed = {"task_id", "correlation_id", "project_id", "operation", "priority", "dependencies", "ttl_seconds"}
        if type(arguments) is not dict or not {"task_id", "correlation_id", "project_id"} <= set(arguments) <= allowed:
            raise ProtocolError("fixed shadow intake fields required; no shell/prompt input")
        if "dependencies" in arguments and type(arguments["dependencies"]) is not list:
            raise ProtocolError("dependency array required")
        return self.planner.submit(ShadowResearchJob(**{**arguments, "dependencies": tuple(arguments.get("dependencies", []))}), now)

    def _job(self, task):
        row = self.store.db.execute("SELECT * FROM master_jobs WHERE task=?", (task,)).fetchone()
        if row is None:
            raise ProtocolError("unregistered task")
        return {**dict(row), **self.store.task(task), "scope_digest": row["scope"], "worker_spec": self.planner.workers[row["worker"]]}

    def _route(self, job):
        return {"task_id": job["id"], "correlation_id": job["correlation"], "scope_digest": job["scope_digest"],
                "worker_id": job["worker"], "workspace": job["workspace"], "fence": job["attempts"]}

    def _directory(self, row):
        path = Path(row["directory"])
        expected = self.planner.workspace / "artifacts/control-plane"
        if path.is_symlink() or path.parent != expected or path.resolve() != path:
            raise ProtocolError("dispatch directory boundary changed")
        return path

    def cancel(self, task, now):
        job = self._job(task)
        if job["state"] != "RUNNING":
            raise ProtocolError("cancellation requires a running owned dispatch")
        row = self.store.db.execute("SELECT * FROM runtime_dispatch WHERE task=? AND fence=?", (task, job["attempts"])).fetchone()
        if row is None or row["state"] != "INTENT":
            raise ProtocolError("no active dispatch to cancel")
        request = self._route(job)
        with self.store.tx():
            self.store.audit("runtime", "cancel_requested", request, now)
        atomic_json(self._directory(row) / "cancel.json", request)
        return {"task_id": task, "requested": True, "termination_certified": False}

    def _preflight(self, job):
        if os.name != "posix" or os.geteuid() == 0 or 0 in os.getgroups():
            raise PermissionError("trusted Linux process-group/resource runtime required")
        if job["operation"] != "shadow_research":
            raise PermissionError("uncertified execution operation disabled")
        root = Path(job["workspace"])
        if root.resolve() != root or any(p.is_symlink() for p in root.rglob("*") if ".git" not in p.parts):
            raise PermissionError("worker symlinks rejected")
        head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, timeout=5).decode().strip()
        status = subprocess.check_output(["git", "status", "--porcelain"], cwd=root, timeout=5)
        if head != job["worker_spec"]["expected_commit"] or status:
            raise PermissionError("unreviewed worker Git state")
        if digest(root / "tests/fixtures/synthetic.json") != job["worker_spec"]["fixture_sha256"]:
            raise PermissionError("fixture scope changed")
        inventory = {str(p.relative_to(root)): digest(p) for folder in ("src", "tests") for p in sorted((root / folder).rglob("*.py"))}
        if inventory != job["worker_spec"]["source_sha256"]:
            raise PermissionError("reviewed source inventory changed")

    def _execute(self, job, directory):
        route = self._route(job)
        self._preflight(job)
        request = {**route, "worker_spec": job["worker_spec"], "entry_sha256": self.entry_sha}
        atomic_json(directory / "request.json", request)
        env = {"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8", "PYTHONDONTWRITEBYTECODE": "1", "GIT_CONFIG_NOSYSTEM": "1"}
        cancelled, timed_out = False, False
        begin = time.monotonic()
        with (directory / "stdout.log").open("wb") as out, (directory / "stderr.log").open("wb") as err:
            process = subprocess.Popen([sys.executable, "-I", str(self.entry), str(directory / "request.json")],
                                       cwd=job["workspace"], env=env, stdout=out, stderr=err, shell=False, start_new_session=True)
            try:
                uid = Path(f"/proc/{process.pid}").stat().st_uid
                while process.poll() is None:
                    signal_path = directory / "cancel.json"
                    if signal_path.exists():
                        if json.loads(signal_path.read_text()) != route:
                            raise ProtocolError("cancellation route/fence mismatch")
                        cancelled = True
                        break
                    if time.monotonic() - begin >= job["worker_spec"]["max_seconds"]:
                        timed_out = True
                        break
                    time.sleep(.02)
            finally:
                # Clean only the new, owned process group, including surviving children.
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                process.wait(timeout=3)
        try:
            os.killpg(process.pid, 0)
        except ProcessLookupError:
            group_gone = True
        else:
            group_gone = False
        if not group_gone or timed_out:
            return {**route, "outcome": "AMBIGUOUS", "passed": False, "gate": "timeout or process-group termination uncertain"}
        head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=job["workspace"], timeout=5).decode().strip()
        unchanged = head == job["worker_spec"]["expected_commit"] and not subprocess.check_output(["git", "status", "--porcelain"], cwd=job["workspace"], timeout=5)
        if not unchanged:
            return {**route, "outcome": "AMBIGUOUS", "passed": False, "gate": "worker Git state changed"}
        if not cancelled and (process.returncode != 0 or not (directory / "report.json").is_file()):
            return {**route, "outcome": "AMBIGUOUS", "passed": False, "gate": "no verified worker completion"}
        evidence = {**route, "outcome": "COMPLETE", "passed": not cancelled, "cancelled": cancelled,
                    "pid": process.pid, "uid": uid, "exit_code": process.returncode, "process_group_terminated": group_gone,
                    "git_before": head, "git_after": head, "git_worktree_unchanged": True, "artifact": str(directory),
                    "entry_sha256": self.entry_sha, "runtime": "trusted Linux deterministic paper worker; not Codex/OS confinement"}
        files = [p for p in directory.iterdir() if p.name in {"stdout.log", "stderr.log", "report.json", "result.json", "paper.sqlite"}]
        evidence["files_sha256"] = {p.name: digest(p) for p in files}
        atomic_json(directory / "receipt.json", evidence)
        return self._verify(job, directory)

    def _verify(self, job, directory):
        receipt_path = directory / "receipt.json"
        limit = job["worker_spec"]["max_output_bytes"]
        if receipt_path.is_symlink() or receipt_path.stat().st_size > limit:
            raise ProtocolError("invalid receipt file")
        evidence = json.loads(receipt_path.read_text())
        if any(evidence.get(k) != v for k, v in self._route(job).items()) or evidence.get("entry_sha256") != self.entry_sha:
            raise ProtocolError("receipt route/fence/runtime mismatch")
        if evidence.get("outcome") != "COMPLETE" or type(evidence.get("passed")) is not bool or type(evidence.get("cancelled")) is not bool:
            raise ProtocolError("unsupported receipt outcome")
        if evidence["passed"] == evidence["cancelled"] or evidence.get("process_group_terminated") is not True or type(evidence.get("uid")) is not int or evidence["uid"] <= 0 or type(evidence.get("pid")) is not int or evidence["pid"] <= 0:
            raise ProtocolError("unverified process termination or identity")
        if evidence.get("artifact") != str(directory) or evidence.get("git_before") != job["worker_spec"]["expected_commit"] or evidence.get("git_after") != evidence["git_before"] or evidence.get("git_worktree_unchanged") is not True:
            raise ProtocolError("receipt Git/workspace scope mismatch")
        files = evidence.get("files_sha256")
        if type(files) is not dict or not {"stdout.log", "stderr.log"} <= set(files) <= {"stdout.log", "stderr.log", "report.json", "result.json", "paper.sqlite"}:
            raise ProtocolError("invalid evidence inventory")
        for name, expected in files.items():
            path = directory / name
            if path.is_symlink() or path.stat().st_size > limit or digest(path) != expected:
                raise ProtocolError("evidence file changed")
        if evidence["passed"]:
            if evidence.get("exit_code") != 0 or not {"report.json", "result.json", "paper.sqlite"} <= set(files):
                raise ProtocolError("missing successful execution evidence")
            report = json.loads((directory / "report.json").read_text())
            result = json.loads((directory / "result.json").read_text())
            if any(report.get(k) != v for k, v in self._route(job).items()) or report.get("uid") != evidence["uid"] or report.get("pid") != evidence["pid"]:
                raise ProtocolError("worker process/report mismatch")
            if report.get("result_sha256") != files["result.json"] or report.get("mode") != "SHADOW" or result.get("mode") != "SHADOW" or result.get("synthetic") is not True:
                raise ProtocolError("result is outside paper scope")
        self._preflight(job)
        return evidence

    def _complete(self, job, row, now):
        directory = self._directory(row)
        evidence = self._verify(job, directory)
        checksum = digest(directory / "receipt.json")
        if row["receipt_sha"] and row["receipt_sha"] != checksum:
            raise ProtocolError("sealed receipt changed")
        current = self.store.task(job["id"])
        if current["state"] in ("SUCCEEDED", "FAILED"):
            saved = self.store.db.execute("SELECT evidence FROM executions WHERE task=?", (job["id"],)).fetchone()
            if saved is None or saved[0] != canonical(evidence):
                raise ProtocolError("terminal execution differs from receipt")
        elif current["state"] == "RUNNING" and current["lease"] > now and current["expires"] > now:
            self.planner.finish(job, evidence, now)
        else:
            return False  # Never revive an expired lease or clear an uncertain quarantine.
        with self.store.tx():
            self.store.db.execute("UPDATE runtime_dispatch SET state='COMMITTED',receipt_sha=? WHERE task=? AND fence=?", (checksum, job["id"], job["attempts"]))
            self.store.audit("runtime", "completion_committed", {"task_id": job["id"], "fence": job["attempts"], "receipt_sha256": checksum}, now)
        return True

    def recover(self, now):
        recovered = []
        for row in list(self.store.db.execute("SELECT * FROM runtime_dispatch WHERE state!='COMMITTED'")):
            job = self._job(row["task"])
            if job["attempts"] != row["fence"] or job["scope_digest"] != row["scope"]:
                raise ProtocolError("dispatch fence/scope changed")
            directory = self._directory(row)
            if not (directory / "receipt.json").exists():
                continue
            try:
                if self._complete(job, row, now):
                    recovered.append(job["id"])
            except (ValueError, KeyError, OSError, ProtocolError):
                if self.store.task(job["id"])["state"] == "RUNNING":
                    with self.store.tx():
                        Runner(self.store, self.planner.workspace)._human(job["id"], now, "CONTROL_PLANE_DEGRADED", "Durable worker evidence invalid; retain reservation")
        self.planner.recover(now)
        return recovered

    def dispatch(self, job):
        directory = self.planner.workspace / "artifacts/control-plane" / str(uuid4())
        try:
            self._preflight(job)
            self._directory({"directory": str(directory)})
        except (OSError, PermissionError, ProtocolError):
            return {**self._route(job), "outcome": "BEFORE_START_UNAVAILABLE", "passed": False, "gate": "preflight failed; no process started"}
        directory.mkdir(parents=True)
        now = int(time.time())
        with self.store.tx():
            self.store.db.execute("INSERT INTO runtime_dispatch VALUES (?,?,?,?, 'INTENT',NULL)", (job["id"], job["attempts"], job["scope_digest"], str(directory)))
            self.store.audit("runtime", "dispatch_intent", {**self._route(job), "directory": str(directory), "entry_sha256": self.entry_sha}, now)
        try:
            return self._execute(job, directory)
        except Exception as exc:
            # After intent any exception is conservatively uncertain; no blind retry.
            return {**self._route(job), "outcome": "AMBIGUOUS", "passed": False, "gate": type(exc).__name__}

    def tick(self):
        recovered = self.recover(int(time.time()))
        completed = []
        for job in self.planner.claim(int(time.time())):
            evidence = self.dispatch(job)
            now = int(time.time())
            row = self.store.db.execute("SELECT * FROM runtime_dispatch WHERE task=? AND fence=?", (job["id"], job["attempts"])).fetchone()
            try:
                if evidence["outcome"] == "COMPLETE":
                    if not self._complete(job, row, now):
                        self.planner.recover(now)
                else:
                    self.planner.finish(job, evidence, now)
            except (ProtocolError, OSError, ValueError):
                if self.store.task(job["id"])["state"] == "RUNNING":
                    with self.store.tx():
                        Runner(self.store, self.planner.workspace)._human(job["id"], now, "CONTROL_PLANE_DEGRADED", "Completion cannot be verified; retain reservation")
            completed.append(evidence)
        return {"recovered_without_reexecution": recovered, "executed": completed}

    def report(self):
        return {**MasterBrainTools(self.planner).report(), "scope": "foreground trusted DCI paper-workflow control plane; external and Codex routes disabled", "control_plane": {
            "enabled_operation": "shadow_research", "codex_dispatch_enabled": False,
            "external_delivery_enabled": False, "services_installed": False,
            "dispatches": [dict(row) for row in self.store.db.execute("SELECT * FROM runtime_dispatch ORDER BY rowid DESC LIMIT 100")],
            "dispatch_total": self.store.db.execute("SELECT count(*) FROM runtime_dispatch").fetchone()[0],
            "scope": "actual trusted Linux paper-workflow processes; Windows/Codex containment and authenticated remote delivery remain uncertified"}}
