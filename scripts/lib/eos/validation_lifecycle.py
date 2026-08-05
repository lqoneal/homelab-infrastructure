#!/usr/bin/env python3
"""Classify repository/EOS validation according to the publication lifecycle."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path


def git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), *args],
        check=False,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip() if result.returncode == 0 else ""


def frontmatter_value(path: Path, key: str) -> str:
    if not path.is_file():
        return ""
    in_header = False
    for line in path.read_text(encoding="utf-8").splitlines():
        if line == "---":
            if in_header:
                break
            in_header = True
            continue
        if in_header and line.startswith(f"{key}:"):
            return line.split(":", 1)[1].strip()
    return ""


def checkpoint_commit(workspace: Path) -> str:
    pointer = workspace / "eos/state/ACTIVE-CHECKPOINT"
    checkpoint = pointer.read_text(encoding="utf-8").splitlines()[0].strip() if pointer.is_file() else ""
    if not checkpoint:
        candidates = sorted((workspace / "eos/checkpoints").glob("*.md"))
        checkpoint = str(candidates[-1]) if candidates else ""
    path = Path(checkpoint)
    if not path.is_file():
        return ""
    match = re.search(r"^Commit: `([^`]+)`", path.read_text(encoding="utf-8"), re.MULTILINE)
    return match.group(1).strip() if match else ""


def classify(root: Path, workspace: Path, project: str = "homelab") -> dict[str, object]:
    root = root.resolve()
    workspace = workspace.resolve()
    branch = git(root, "branch", "--show-current")
    head = git(root, "rev-parse", "HEAD")
    upstream = git(root, "rev-parse", "--abbrev-ref", "@{upstream}")
    origin_main = git(root, "rev-parse", "refs/remotes/origin/main")
    remote_head = git(root, "rev-parse", upstream) if upstream else ""
    dirty = bool(git(root, "status", "--porcelain"))
    eos_baseline = frontmatter_value(workspace / "eos/state/EOS-STATE.md", "repository_commit")
    checkpoint = checkpoint_commit(workspace)

    result: dict[str, object] = {
        "project": project,
        "branch": branch,
        "head": head,
        "upstream": upstream,
        "remote_head": remote_head,
        "published_baseline": origin_main,
        "eos_baseline": eos_baseline,
        "checkpoint_baseline": checkpoint,
        "working_tree": "dirty" if dirty else "clean",
        "classification": "UNCLASSIFIED",
        "valid": False,
        "reasons": [],
    }
    reasons: list[str] = result["reasons"]  # type: ignore[assignment]

    if not branch:
        result["classification"] = "DETACHED"
        reasons.append("active branch is unavailable")
    elif dirty:
        result["classification"] = "DIRTY"
        reasons.append("working tree is not clean")
    elif not origin_main:
        result["classification"] = "AMBIGUOUS"
        reasons.append("origin/main cannot be resolved")
    elif branch == "main":
        result["classification"] = "PUBLISHED"
        if head != origin_main:
            result["classification"] = "PUBLISHED_DRIFT"
            reasons.append("local main does not equal origin/main")
        if eos_baseline != head:
            result["classification"] = "PUBLISHED_DRIFT"
            reasons.append("EOS baseline does not equal published main")
        if checkpoint and checkpoint != head:
            result["classification"] = "PUBLISHED_DRIFT"
            reasons.append("checkpoint baseline does not equal published main")
        result["valid"] = not reasons
    else:
        if not upstream or not remote_head or head != remote_head:
            result["classification"] = "DIVERGENT_CANDIDATE"
            reasons.append("local and remote candidate heads differ or are unavailable")
        elif not branch.startswith("prepublication/"):
            result["classification"] = "UNRELATED_BRANCH"
            reasons.append("branch is not a governed prepublication candidate")
        elif not origin_main or subprocess.run(
            ["git", "-C", str(root), "merge-base", "--is-ancestor", origin_main, head],
            check=False,
        ).returncode != 0:
            result["classification"] = "OUTDATED_CANDIDATE"
            reasons.append("candidate is not descended from current published main")
        elif eos_baseline != origin_main:
            result["classification"] = "EOS_STALE"
            reasons.append("EOS does not represent current published main")
        elif checkpoint and checkpoint != origin_main:
            result["classification"] = "CHECKPOINT_STALE"
            reasons.append("checkpoint does not represent current published main")
        else:
            result["classification"] = "UNPUBLISHED_CANDIDATE"
            result["valid"] = True

    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("classify")
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--project", default="homelab")
    args = parser.parse_args()
    print(json.dumps(classify(args.root, args.workspace, args.project), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
