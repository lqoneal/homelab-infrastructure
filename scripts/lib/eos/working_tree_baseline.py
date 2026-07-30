#!/usr/bin/env python3
"""Validate an authorized, path-scoped dirty working-tree baseline."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path


class BaselineError(RuntimeError):
    pass


def _git(root: Path, *args: str) -> bytes:
    return subprocess.check_output(["git", "-C", str(root), *args])


def _status_entries(root: Path) -> list[bytes]:
    raw = _git(root, "status", "--porcelain=v1", "-z", "--untracked-files=all")
    fields = raw.split(b"\0")
    return [field for field in fields if field]


def _path(entry: bytes) -> str:
    return entry[3:].decode("utf-8", "surrogateescape")


def _digest(root: Path, entries: list[bytes]) -> str:
    digest = hashlib.sha256()
    for entry in entries:
        path = root / _path(entry)
        digest.update(entry + b"\0")
        digest.update(
            hashlib.sha256(path.read_bytes()).digest()
            if path.is_file()
            else hashlib.sha256(b"<absent>").digest()
        )
    return digest.hexdigest()


def validate(root: Path, contract_path: Path) -> dict[str, object]:
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    handoff_paths = set(contract["handoff_paths"])
    entries = _status_entries(root)
    baseline_entries = [entry for entry in entries if _path(entry) not in handoff_paths]
    introduced = sorted(_path(entry) for entry in entries if _path(entry) in handoff_paths)

    staged = _git(root, "diff", "--cached", "--name-only", "-z")
    checks = {
        "head_matches": _git(root, "rev-parse", "HEAD").decode().strip()
        == contract["baseline_head"],
        "index_empty": staged == b"",
        "baseline_path_count_matches": len(baseline_entries)
        == contract["baseline_path_count"],
        "baseline_status_digest_matches": _digest(root, baseline_entries)
        == contract["baseline_status_sha256"],
        "handoff_paths_controlled": all(path in handoff_paths for path in introduced),
    }
    for artifact in contract.get("preserved_artifacts", []):
        path = root / artifact["path"]
        checks[f"preserved:{artifact['path']}"] = (
            path.is_file()
            and hashlib.sha256(path.read_bytes()).hexdigest() == artifact["sha256"]
        )
    if not all(checks.values()):
        failed = ", ".join(key for key, passed in checks.items() if not passed)
        raise BaselineError(f"controlled working-tree baseline rejected: {failed}")
    return {
        "decision": "AUTHORIZED_DIRTY_TREE",
        "baseline_path_count": len(baseline_entries),
        "handoff_paths_present": introduced,
        "checks": checks,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--contract", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = validate(args.repository.resolve(), args.contract.resolve())
    except (
        BaselineError,
        KeyError,
        OSError,
        subprocess.CalledProcessError,
        json.JSONDecodeError,
    ) as exc:
        print(f"FAIL: {exc}")
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
