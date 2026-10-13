"""One foreground Linux Codex diagnostic; never relocate credentials or retry a task.

This is a startup probe, not a Windows or isolation certification tool. It uses
the existing authentication/configuration and an ephemeral read-only turn in a
fresh clone. Output must be a new, untracked directory outside old certificates.
"""
import argparse
from datetime import datetime, timezone
import getpass
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import signal
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]
PROMPT = (
    "Bounded DMB SHADOW certification task. In this development clone only, "
    "report process identity, platform and working directory; run git rev-parse "
    "HEAD and git status --porcelain; run PYTHONPATH=src python -m unittest "
    "discover -s certification_tests -v. Report observed results. Do not modify "
    "files, perform external requests, inspect authentication files or environment "
    "variables, access other project workspaces, install anything, or trade."
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    if platform.system() != "Linux" or os.geteuid() == 0:
        raise PermissionError("This diagnostic requires a non-root Linux context")
    out = Path(args.output).resolve()
    if out == ROOT or ROOT / "docs" in out.parents or out.exists():
        raise PermissionError("Use a fresh output directory outside certificate paths")
    codex = shutil.which("codex")
    if not codex:
        raise RuntimeError("Supported Codex CLI is not present")
    out.mkdir(parents=True)
    clone = out / "development-clone"
    subprocess.run(["git", "clone", "--no-hardlinks", "--no-local", str(ROOT), str(clone)],
                   check=True, capture_output=True, timeout=15)
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=clone).decode().strip()
    command = [codex, "exec", "--sandbox", "read-only", "--json", "--ephemeral", "-C", str(clone), "-"]
    started = datetime.now(timezone.utc).isoformat()
    begin = time.monotonic()
    process = subprocess.Popen(command, cwd=clone, stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               start_new_session=True)
    # Observe the actual CLI owner while it exists. A fast early exit can prevent this.
    try:
        process_uid = Path(f"/proc/{process.pid}").stat().st_uid
    except FileNotFoundError:
        process_uid = None
    timed_out = False
    try:
        stdout, stderr = process.communicate(PROMPT.encode(), timeout=45)
    except subprocess.TimeoutExpired:
        timed_out = True
        # Terminate only the new process group created for this invocation.
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        try:
            stdout, stderr = process.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            stdout, stderr = process.communicate(timeout=5)
    (out / "CODEX.stdout.log").write_bytes(stdout)
    (out / "CODEX.stderr.log").write_bytes(stderr)
    events = []
    invalid_lines = 0
    for line in stdout.splitlines():
        try:
            events.append(json.loads(line))
        except (ValueError, TypeError):
            invalid_lines += 1
    completed = any(isinstance(e, dict) and e.get("type") == "turn.completed" for e in events)
    result = {
        "schema_version": 1, "captured_at": started,
        "host": platform.node(), "system": platform.system(), "kernel": platform.release(),
        "launcher_user": getpass.getuser(), "launcher_uid": os.geteuid(),
        "actual_cli_process_uid": process_uid, "process_id": process.pid,
        "workspace": str(clone), "source_commit": head, "command": command,
        "prompt_sha256": hashlib.sha256(PROMPT.encode()).hexdigest(),
        "exit_code": process.returncode, "duration_seconds": round(time.monotonic() - begin, 3),
        "timeout_seconds": 45, "timed_out": timed_out,
        "event_types": [e.get("type") for e in events if isinstance(e, dict)],
        "invalid_json_lines": invalid_lines, "completed_turn_observed": completed,
        "gate": "NOT TESTED" if completed else "BLOCKED",
        "classification": "Observed foreground CLI attempt; completion requires separate task-evidence review",
        "windows_identity_certified": False, "os_isolation_certified": False,
        "cancellation_certified": False, "restart_certified": False,
        "task_retried": False, "credentials_read_copied_or_relocated": False,
        "configuration_or_safety_overrides": False,
        "uncertain_outcome_quarantined": timed_out,
        "logs_sha256": {"stdout": hashlib.sha256(stdout).hexdigest(), "stderr": hashlib.sha256(stderr).hexdigest()},
        "clone_clean_after": not subprocess.check_output(["git", "status", "--porcelain"], cwd=clone).strip(),
    }
    (out / "CODEX_INVOCATION.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
