"""Verify public Git preservation and sanitized metadata; never access broker data."""
import json
import subprocess
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
PREFIX = "research/dat_mt5_edge/phase6_4/"


def verify():
    lock = json.loads((HERE / "baseline_git_lock.json").read_text())
    # Read committed Git object names only, not quotes or private cache contents.
    raw = subprocess.check_output(
        ["git", "ls-tree", "--full-tree", "-r", "-z", "HEAD"], cwd=HERE
    ).decode()
    current = {}
    for row in raw.split("\0"):
        if row:
            meta, path = row.split("\t", 1)
            mode, kind, sha = meta.split()
            if kind == "blob":
                current[path] = sha
    for path, sha in lock["blobs"].items():
        if current.get(path) != sha:
            raise ValueError("baseline Git blob differs or absent: " + path)
        # These are previously public repository files, never protected caches.
        actual = subprocess.check_output(
            ["git", "hash-object", "--", path], cwd=HERE.parents[2], text=True
        ).strip()
        if actual != sha:
            raise ValueError("baseline working file differs: " + path)
    unexpected = set(current) - set(lock["blobs"])
    if any(not p.startswith(PREFIX) for p in unexpected):
        raise ValueError("unexpected changes outside isolated phase")
    metadata = json.loads((HERE / "CACHE_METADATA.json").read_text())
    groups = defaultdict(list)
    count = 0
    for server in metadata["servers"]:
        if not server["metadata_only"] or server["file_contents_opened"]:
            raise ValueError("invalid inspection boundary")
        for row in server["rows"]:
            count += 1
            key = tuple(row[k] for k in
                        ("broker_symbol", "area", "name", "bytes", "modified_utc"))
            groups[key].append(server["server_label"])
    pairs = [dict(symbol=k[0], area=k[1], filename=k[2], bytes=k[3],
                  filesystem_modified_utc=k[4], servers=sorted(v))
             for k, v in sorted(groups.items()) if len(set(v)) > 1]
    return dict(phase="6.4", baseline_commit=lock["baseline_commit"],
                baseline_blobs_preserved=len(lock["blobs"]),
                observed_cache_files=count, cross_server_metadata_match_groups=pairs,
                quote_content_duplicate_status="UNKNOWN",
                actual_market_coverage="UNKNOWN", data_use_permission="UNKNOWN",
                certified_datasets=0, new_strategy_backtests=0,
                protected_cache_contents_read=False, protected_cache_hashes_read=False,
                mt5_starts=0, broker_connections_started=0, orders=0,
                provider_inquiries_sent=0, forward_shadow="OFF",
                sealed_holdout_accessed=False)


if __name__ == "__main__":
    print(json.dumps(verify(), indent=2, sort_keys=True))
