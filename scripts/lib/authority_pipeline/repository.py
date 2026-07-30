"""Canonical repository identity and noncanonical-state preflight."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


CANONICAL_ROOT = Path("/data/engineering/repositories/homelab")
CANONICAL_REMOTE = "git@github.com:lqoneal/homelab-infrastructure.git"
EXTERNAL_ROOTS = (
    Path("/data/engineering/eos"),
    Path("/data/engineering/state"),
    Path("/data/engineering/shared"),
    Path("/data/engineering/staging"),
    Path("/data/engineering/recovery"),
    Path("/data/engineering/wops"),
)


class RepositoryPolicyError(ValueError):
    """Repository topology is unsuitable for a protected operation."""


def _git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), *args],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode:
        raise RepositoryPolicyError(result.stderr.strip() or "git command failed")
    return result.stdout.strip()


def _tree_digest(path: Path) -> str:
    value = hashlib.sha256()
    if not path.exists():
        return ""
    for item in sorted(path.rglob("*")):
        if not item.is_file() or item.is_symlink():
            continue
        relative = item.relative_to(path).as_posix().encode()
        value.update(len(relative).to_bytes(8, "big"))
        value.update(relative)
        value.update(hashlib.sha256(item.read_bytes()).digest())
    return value.hexdigest()


def _worktrees(root: Path) -> list[dict[str, str]]:
    records: list[dict[str, str]] = []
    current: dict[str, str] = {}
    for line in _git(root, "worktree", "list", "--porcelain").splitlines() + [""]:
        if not line:
            if current:
                records.append(current)
                current = {}
            continue
        key, _, value = line.partition(" ")
        current[key] = value
    return records


def _git_roots(paths: Iterable[Path]) -> list[str]:
    roots: set[str] = set()
    for base in paths:
        if not base.exists():
            continue
        for directory, names, _ in os.walk(base):
            if ".git" in names:
                roots.add(str(Path(directory).resolve()))
                names.remove(".git")
    return sorted(roots)


@dataclass(frozen=True)
class RepositoryObservation:
    data: dict

    @property
    def allowed(self) -> bool:
        return not self.data["failures"]


def observe(
    root: Path | str,
    *,
    expected_root: Path = CANONICAL_ROOT,
    expected_remote: str = CANONICAL_REMOTE,
    repository_search_roots: tuple[Path, ...] = (
        Path("/data/engineering/repositories"),
    ),
) -> RepositoryObservation:
    requested = Path(root).resolve()
    actual = Path(_git(requested, "rev-parse", "--show-toplevel")).resolve()
    common = Path(_git(requested, "rev-parse", "--git-common-dir"))
    if not common.is_absolute():
        common = (actual / common).resolve()
    worktrees = _worktrees(actual)
    stat = actual.stat()
    failures: list[dict[str, str]] = []

    def require(condition: bool, check: str, detail: str) -> None:
        if not condition:
            failures.append({"check": check, "detail": detail})

    require(actual == expected_root, "canonical_root", f"observed {actual}")
    remote = _git(actual, "remote", "get-url", "origin")
    require(remote == expected_remote, "remote_identity", f"observed {remote}")
    require(
        len(worktrees) == 1 and Path(worktrees[0]["worktree"]).resolve() == actual,
        "protected_worktree_count",
        f"observed {len(worktrees)} registered worktrees",
    )
    external_git = _git_roots(repository_search_roots)
    homelab_like = [
        item for item in external_git
        if Path(item).name.lower() == "homelab" and Path(item) != actual
    ]
    require(not homelab_like, "duplicate_git_tree", ", ".join(homelab_like))
    external = []
    for path in EXTERNAL_ROOTS:
        if path.exists():
            external.append(
                {
                    "path": str(path),
                    "writable": os.access(path, os.W_OK),
                    "tree_digest": _tree_digest(path),
                }
            )
    data = {
        "schema_version": 1,
        "canonical_root": str(actual),
        "filesystem": {"device": stat.st_dev, "inode": stat.st_ino},
        "git_common_directory": str(common),
        "branch": _git(actual, "branch", "--show-current"),
        "remote": remote,
        "head": _git(actual, "rev-parse", "HEAD"),
        "upstream": _git(actual, "rev-parse", "@{upstream}"),
        "merge_base": _git(actual, "merge-base", "HEAD", "@{upstream}"),
        "worktrees": worktrees,
        "external_git_roots": external_git,
        "external_state": external,
        "failures": failures,
    }
    data["observation_digest"] = hashlib.sha256(
        json.dumps(data, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return RepositoryObservation(data)


def require_canonical_write(root: Path | str) -> dict:
    observation = observe(root)
    if not observation.allowed:
        raise RepositoryPolicyError(json.dumps(observation.data["failures"]))
    return observation.data
