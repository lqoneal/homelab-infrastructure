"""Canonical read-only EMP repository-state projection.

This module composes existing repository identity, canonical baseline,
and read-only Git facts. It owns no repository, EOS, lifecycle,
publication, execution, or synchronization authority.
"""

from __future__ import annotations

from pathlib import Path
import subprocess
from typing import Any

from scripts.lib.emp.repository_identity import (
    resolve as resolve_repository_identity,
)
from scripts.lib.eos.canonical_baseline import (
    resolve as resolve_canonical_baseline,
)


def _git(
    root: Path,
    *args: str,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )


def _text(
    result: subprocess.CompletedProcess[str],
) -> str:
    return result.stdout.strip()


def _paths(
    result: subprocess.CompletedProcess[str],
) -> list[str]:
    if result.returncode != 0:
        return []

    return [
        value
        for value in result.stdout.splitlines()
        if value
    ]


def project(
    repository_root: Path | str,
    eos_workspace: Path | str = "/data/engineering",
    project: str = "homelab",
) -> dict[str, Any]:
    """Return the shared read-only repository-state view."""

    root = Path(repository_root).expanduser().resolve()
    eos = Path(eos_workspace).expanduser().resolve()

    errors: list[Any] = []

    try:
        identity = resolve_repository_identity(root)
    except Exception as exc:
        identity = {}
        errors.append(
            {
                "code": "REPOSITORY_IDENTITY_RESOLUTION_FAILED",
                "message": str(exc),
            }
        )

    try:
        baseline = resolve_canonical_baseline(
            root,
            eos,
            project,
        )
    except Exception as exc:
        baseline = {
            "result": "FAIL",
            "errors": [
                {
                    "code": "CANONICAL_BASELINE_RESOLUTION_FAILED",
                    "message": str(exc),
                }
            ],
            "eos_baseline": None,
            "eos_parity": "FAIL",
        }

    baseline_errors = baseline.get("errors", [])

    if isinstance(baseline_errors, list):
        errors.extend(baseline_errors)
    elif baseline_errors:
        errors.append(baseline_errors)

    head_result = _git(
        root,
        "rev-parse",
        "--verify",
        "HEAD",
    )

    origin_result = _git(
        root,
        "rev-parse",
        "--verify",
        "refs/remotes/origin/main",
    )

    branch_result = _git(
        root,
        "branch",
        "--show-current",
    )

    staged_quiet = _git(
        root,
        "diff",
        "--cached",
        "--quiet",
    )

    worktree_quiet = _git(
        root,
        "diff",
        "--quiet",
    )

    staged_result = _git(
        root,
        "diff",
        "--cached",
        "--name-only",
    )

    unstaged_result = _git(
        root,
        "diff",
        "--name-only",
    )

    untracked_result = _git(
        root,
        "ls-files",
        "--others",
        "--exclude-standard",
    )

    head = (
        _text(head_result)
        if head_result.returncode == 0
        else None
    )

    origin_main = (
        _text(origin_result)
        if origin_result.returncode == 0
        else None
    )

    branch = (
        _text(branch_result)
        if branch_result.returncode == 0
        else None
    )

    git_failures = (
        ("HEAD_RESOLUTION_FAILED", head_result),
        ("ORIGIN_MAIN_RESOLUTION_FAILED", origin_result),
        ("BRANCH_RESOLUTION_FAILED", branch_result),
        ("STAGED_PATH_RESOLUTION_FAILED", staged_result),
        ("UNSTAGED_PATH_RESOLUTION_FAILED", unstaged_result),
        ("UNTRACKED_PATH_RESOLUTION_FAILED", untracked_result),
    )

    for code, result in git_failures:
        if result.returncode != 0:
            errors.append(
                {
                    "code": code,
                    "message": (
                        result.stderr.strip()
                        or code
                    ),
                }
            )

    return {
        "branch": branch,
        "eos_baseline": baseline.get("eos_baseline"),
        "eos_parity": baseline.get("eos_parity"),
        "errors": errors,
        "head": head,
        "head_origin_parity": (
            head is not None
            and origin_main is not None
            and head == origin_main
        ),
        "index_clean": staged_quiet.returncode == 0,
        "origin_main": origin_main,
        "repository_id": identity.get("repository_id"),
        "repository_root": str(root),
        "result": (
            "PASS"
            if (
                not errors
                and baseline.get("result") == "PASS"
            )
            else "FAIL"
        ),
        "staged_paths": _paths(staged_result),
        "unstaged_paths": _paths(unstaged_result),
        "untracked_paths": _paths(untracked_result),
        "worktree_clean": worktree_quiet.returncode == 0,
    }
