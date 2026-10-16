"""Fixed, resource-bounded DCI paper pipeline entry; no mailbox commands."""
import hashlib
import json
import os
from pathlib import Path
import resource
import subprocess
import sys


def main():
    if os.name != "posix" or os.geteuid() == 0 or 0 in os.getgroups():
        raise PermissionError("non-root Linux resource runtime required")
    path = Path(sys.argv[1]).resolve(strict=True)
    request = json.loads(path.read_text())
    worker = request["worker_spec"]
    root = Path(request["workspace"]).resolve(strict=True)
    if root != Path(worker["workspace"]) or Path.cwd() != root:
        raise PermissionError("worker workspace mismatch")
    marker = json.loads((root / "WORKER_SCOPE.json").read_text())
    if marker != {"mode": "SHADOW", "worker_id": request["worker_id"], "workspace": str(root)}:
        raise PermissionError("worker marker mismatch")
    resource.setrlimit(resource.RLIMIT_AS, (worker["memory_mb"] * 1048576,) * 2)
    resource.setrlimit(resource.RLIMIT_CPU, (worker["cpu_seconds"],) * 2)
    resource.setrlimit(resource.RLIMIT_FSIZE, (worker["max_output_bytes"],) * 2)
    resource.setrlimit(resource.RLIMIT_NOFILE, (64,) * 2)
    git = lambda *argv: subprocess.check_output(["git", *argv], cwd=root, timeout=3).decode().strip()
    head = git("rev-parse", "HEAD")
    if head != worker["expected_commit"] or git("status", "--porcelain"):
        raise PermissionError("unreviewed Git state")
    fixture = root / "tests/fixtures/synthetic.json"
    if hashlib.sha256(fixture.read_bytes()).hexdigest() != worker["fixture_sha256"]:
        raise PermissionError("fixture drift")
    sys.path.insert(0, str(root / "src"))
    from dci.pipeline import run_fixture
    result = run_fixture(fixture, path.parent / "paper.sqlite")
    output = json.dumps(result, sort_keys=True).encode()
    (path.parent / "result.json").write_bytes(output)
    if head != git("rev-parse", "HEAD") or git("status", "--porcelain"):
        raise PermissionError("worker Git state changed")
    report = {k: request[k] for k in ("task_id", "correlation_id", "scope_digest", "worker_id", "workspace", "fence")}
    report.update(mode="SHADOW", pid=os.getpid(), uid=os.geteuid(), result_sha256=hashlib.sha256(output).hexdigest(),
                  paper_events=[event["type"] for event in result["audit"]], git_commit=head)
    with (path.parent / "report.json").open("x") as stream:
        json.dump(report, stream)
        stream.flush()
        os.fsync(stream.fileno())


if __name__ == "__main__":
    main()
