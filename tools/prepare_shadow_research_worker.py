"""Create a fresh local DCI worker clone/manifest; never touch production or old labs."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destination", required=True)
    parser.add_argument("--manifest", required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    if os.name != "posix" or os.geteuid() == 0 or 0 in os.getgroups():
        raise PermissionError("non-root Linux preparation required")
    destination = Path(args.destination).resolve()
    manifest = Path(args.manifest).resolve()
    if destination == root or root in destination.parents or destination in root.parents or destination.exists() or manifest.exists():
        raise PermissionError("use new sibling worker directory and new manifest")
    subprocess.run(["git", "clone", "--quiet", "--no-hardlinks", "--no-local", str(root), str(destination)], check=True, timeout=20)
    marker = {"mode": "SHADOW", "worker_id": "dci_shadow_research", "workspace": str(destination)}
    (destination / "WORKER_SCOPE.json").write_text(json.dumps(marker, indent=2) + "\n")
    git = lambda *argv: subprocess.check_output(["git", *argv], cwd=destination, timeout=5).decode().strip()
    git("add", "WORKER_SCOPE.json")
    git("-c", "user.name=DCI Shadow Worker", "-c", "user.email=shadow@example.invalid", "commit", "--quiet", "-m", "Bind fixed DCI shadow research worker workspace")
    source = {str(p.relative_to(destination)): hashlib.sha256(p.read_bytes()).hexdigest()
              for folder in ("src", "tests") for p in sorted((destination / folder).rglob("*.py"))}
    config = {"schema_version": 1, "mode": "SHADOW", "max_parallel": 1, "max_memory_mb": 256,
              "workers": [{"worker_id": marker["worker_id"], "workspace": str(destination), "project_ids": ["DCI"],
                           "expected_commit": git("rev-parse", "HEAD"), "source_sha256": source,
                           "fixture_sha256": hashlib.sha256((destination / "tests/fixtures/synthetic.json").read_bytes()).hexdigest(),
                           "max_seconds": 20, "memory_mb": 256, "cpu_seconds": 10, "max_output_bytes": 1048576,
                           "source_origin": "local pinned DCI synthetic paper pipeline; not production"}]}
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(json.dumps(config, indent=2) + "\n")
    print(json.dumps({"worker_workspace": str(destination), "manifest": str(manifest), "commit": config["workers"][0]["expected_commit"]}))


if __name__ == "__main__":
    main()
