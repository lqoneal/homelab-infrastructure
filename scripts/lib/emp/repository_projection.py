"""Canonical, machine-readable projection of repository and EOS state.

This module is intentionally read-only.  It is the shared source for current
repository facts consumed by automation; lifecycle receipts may preserve the
observed facts as immutable provenance, but must not replace this projection.
"""

from __future__ import annotations

import os
import hashlib
import re
import subprocess
from pathlib import Path
from typing import Any, Mapping

from scripts.lib.emp.repository_identity import resolve as resolve_repository_identity
from scripts.lib.emp.publication_authority import resolve_repository_baseline
from scripts.lib.eos.state_sync import SynchronizationError, frontmatter, render, validate


class RepositoryProjectionError(ValueError):
    """Raised only when a projection cannot be constructed safely."""


def _run_git(root: Path, *args: str) -> subprocess.CompletedProcess[bytes]:
    environment = dict(os.environ)
    # This projection is intended for unattended automation.  It must never
    # wait for a credential or terminal prompt while resolving read-only facts.
    environment["GIT_TERMINAL_PROMPT"] = "0"
    return subprocess.run(
        ["git", "-C", str(root), *args],
        capture_output=True,
        check=False,
        env=environment,
    )


def _stdout(result: subprocess.CompletedProcess[bytes], label: str) -> str:
    if result.returncode != 0:
        detail = os.fsdecode(result.stderr).strip() or "git command failed"
        raise RepositoryProjectionError(f"{label}: {detail}")
    return os.fsdecode(result.stdout).strip()


def _nul_values(result: subprocess.CompletedProcess[bytes], label: str) -> list[str]:
    if result.returncode != 0:
        detail = os.fsdecode(result.stderr).strip() or "git command failed"
        raise RepositoryProjectionError(f"{label}: {detail}")
    return sorted(os.fsdecode(value) for value in result.stdout.split(b"\0") if value)


def _quiet(root: Path, *args: str) -> bool:
    result = _run_git(root, *args)
    if result.returncode not in (0, 1):
        detail = os.fsdecode(result.stderr).strip() or "git boolean command failed"
        raise RepositoryProjectionError(f"git {' '.join(args)}: {detail}")
    return result.returncode == 0


def _count_ahead_behind(root: Path) -> tuple[int | None, int | None]:
    result = _run_git(root, "rev-list", "--left-right", "--count", "HEAD...refs/remotes/origin/main")
    if result.returncode != 0:
        return None, None
    values = os.fsdecode(result.stdout).strip().split()
    if len(values) != 2 or not all(value.isdigit() for value in values):
        return None, None
    return int(values[0]), int(values[1])


def _eos_baseline_manifest_consistent(root: Path, paths: Mapping[str, Path], baseline: str) -> bool:
    """Verify EOS bytes against the repository tree recorded by EOS itself."""
    if not baseline:
        return False
    try:
        text = paths["manifest"].read_text(encoding="utf-8")
        canonical, projections = text.split("## Canonical sources", 1)[1].split("## Derived projections", 1)
    except (OSError, UnicodeError, ValueError):
        return False
    pattern = re.compile(r"^- path: ([^\n]+)\n  sha256: ([0-9a-f]{64})$", re.MULTILINE)
    canonical_entries = pattern.findall(canonical)
    projection_entries = pattern.findall(projections)
    if not canonical_entries or not projection_entries:
        return False
    for relative, expected in canonical_entries:
        blob = _run_git(root, "show", f"{baseline}:{relative}")
        if blob.returncode != 0 or hashlib.sha256(blob.stdout).hexdigest() != expected:
            return False
    state_dir = paths["manifest"].parent
    for relative, expected in projection_entries:
        path = state_dir / relative
        try:
            actual = hashlib.sha256(path.read_bytes()).hexdigest()
        except OSError:
            return False
        if actual != expected:
            return False
    return True


def _eos_projection(root: Path, workspace: Path, project: str, identity: dict[str, str], head: str) -> dict[str, Any]:
    state_dir = workspace / "eos" / "state"
    paths = {
        "identity": state_dir / "EOS-ID.md",
        "state": state_dir / "EOS-STATE.md",
        "manifest": state_dir / "EOS-MANIFEST.md",
    }
    if not all(path.is_file() for path in paths.values()):
        return {
            "available": False,
            "result": "UNAVAILABLE",
            "baseline": None,
            "parity": None,
            "identity_match": None,
            "manifest_consistent": None,
            "baseline_manifest_consistent": None,
            "workspace": str(workspace),
        }
    try:
        eos_id = frontmatter(paths["identity"])
        eos_state = frontmatter(paths["state"])
        frontmatter(paths["manifest"])
        baseline = str(eos_state.get("repository_commit") or "").strip().lower()
        identity_match = (
            eos_id.get("repository_root") == identity["repository_path"]
            and eos_id.get("repository_remote") == identity["repository_identity"]
            and eos_state.get("project") == project
        )
        drift = validate(render(root, workspace, project))
        manifest_consistent = not drift
        baseline_manifest_consistent = _eos_baseline_manifest_consistent(root, paths, baseline)
        parity = bool(baseline and baseline == head and identity_match and manifest_consistent)
        return {
            "available": True,
            "result": "PASS" if parity else "FAIL",
            "baseline": baseline or None,
            "parity": parity,
            "identity_match": identity_match,
            "manifest_consistent": manifest_consistent,
            "baseline_manifest_consistent": baseline_manifest_consistent,
            "workspace": str(workspace),
            "errors": drift,
        }
    except (OSError, UnicodeError, KeyError, SynchronizationError) as error:
        return {
            "available": True,
            "result": "FAIL",
            "baseline": None,
            "parity": False,
            "identity_match": False,
            "manifest_consistent": False,
            "baseline_manifest_consistent": False,
            "workspace": str(workspace),
            "errors": [str(error)],
        }


def project(
    repository: Path | str,
    eos_workspace: Path | str | None = None,
    project_name: str = "homelab",
    *,
    runtime_root: Path | str | None = None,
    mission_id: str | None = None,
    wop_id: str | None = None,
    publication_id: str | None = None,
) -> dict[str, Any]:
    """Return the live repository projection without mutating repository/EOS."""
    root = Path(repository).resolve()
    errors: list[str] = []
    try:
        top_level = Path(_stdout(_run_git(root, "rev-parse", "--show-toplevel"), "repository root")).resolve()
        if top_level != root:
            errors.append(f"repository root mismatch: expected {root}, observed {top_level}")
        identity = resolve_repository_identity(root)
        head = _stdout(_run_git(root, "rev-parse", "--verify", "HEAD^{commit}"), "HEAD")
        origin_main = _stdout(_run_git(root, "rev-parse", "--verify", "refs/remotes/origin/main^{commit}"), "origin/main")
        branch = _stdout(_run_git(root, "branch", "--show-current"), "branch")
        remote_result = _run_git(root, "remote", "get-url", "origin")
        remote_url = os.fsdecode(remote_result.stdout).strip() if remote_result.returncode == 0 else None

        # Invoke the stable porcelain-v2/NUL interface as the canonical status
        # probe.  Path collections below use independent NUL-safe primitives.
        status = _run_git(root, "status", "--porcelain=v2", "--branch", "-z")
        if status.returncode != 0:
            raise RepositoryProjectionError(os.fsdecode(status.stderr).strip() or "git status projection failed")
        status_records = [record for record in status.stdout.split(b"\0") if record and not record.startswith(b"#")]
        staged_paths = _nul_values(_run_git(root, "diff", "--cached", "--name-only", "-z"), "staged paths")
        unstaged_paths = _nul_values(_run_git(root, "diff", "--name-only", "-z"), "unstaged paths")
        untracked_paths = _nul_values(_run_git(root, "ls-files", "--others", "--exclude-standard", "-z"), "untracked paths")
        index_clean = _quiet(root, "diff", "--cached", "--quiet")
        tracked_worktree_clean = _quiet(root, "diff", "--quiet") and not staged_paths
        head_origin_parity = head == origin_main
        origin_main_ancestor_of_head = _quiet(root, "merge-base", "--is-ancestor", "refs/remotes/origin/main", "HEAD")
        head_ancestor_of_origin_main = _quiet(root, "merge-base", "--is-ancestor", "HEAD", "refs/remotes/origin/main")
        ahead_count, behind_count = _count_ahead_behind(root)
        eos = _eos_projection(
            root,
            Path(eos_workspace or os.environ.get("EOS_WORKSPACE", "/data/engineering")).resolve(),
            project_name,
            identity,
            head,
        )
        resolved_runtime = runtime_root
        if resolved_runtime is None:
            try:
                from scripts.lib.emp.runtime_paths import resolve_runtime

                resolved_runtime = resolve_runtime(root, require_writable=False)["root"]
            except Exception:
                resolved_runtime = None
        facts = {
            "repository_id": identity["repository_id"],
            "repository_identity": identity["repository_identity"],
            "repository_root": str(root),
            "branch": branch or None,
            "detached_head": not bool(branch),
            "head": head,
            "origin_main": origin_main,
            "origin_main_ancestor_of_head": origin_main_ancestor_of_head,
            "head_ancestor_of_origin_main": head_ancestor_of_origin_main,
            "ahead_count": ahead_count,
            "behind_count": behind_count,
            "index_clean": index_clean,
            "eos_available": eos["available"],
            "eos_baseline": eos["baseline"],
            "eos_identity_match": eos["identity_match"],
            "eos_manifest_consistent": eos["manifest_consistent"],
            "eos_baseline_manifest_consistent": eos["baseline_manifest_consistent"],
        }
        baseline = resolve_repository_baseline(
            facts,
            runtime_root=resolved_runtime,
            mission_id=mission_id,
            wop_id=wop_id,
            publication_id=publication_id,
        )
        errors.extend(baseline.get("errors", []))
        return {
            "result": "PASS" if not errors and baseline.get("result") == "PASS" else "FAIL",
            "repository_valid": not errors and baseline.get("repository_valid") is True,
            "repository_id": identity["repository_id"],
            "repository_identity": identity["repository_identity"],
            "repository_root": str(root),
            "repository_identity_source": identity["repository_identity_source"],
            "remote_url": remote_url,
            "branch": branch or None,
            "detached_head": not bool(branch),
            "head": head,
            "origin_main": origin_main,
            "head_origin_parity": head_origin_parity,
            "origin_main_ancestor_of_head": origin_main_ancestor_of_head,
            "head_ancestor_of_origin_main": head_ancestor_of_origin_main,
            "ahead_count": ahead_count,
            "behind_count": behind_count,
            "index_clean": index_clean,
            "tracked_worktree_clean": tracked_worktree_clean,
            "untracked_present": bool(untracked_paths),
            "worktree_clean": index_clean and tracked_worktree_clean and not untracked_paths,
            "staged_paths": staged_paths,
            "unstaged_paths": unstaged_paths,
            "untracked_paths": untracked_paths,
            "status_porcelain_v2_records": len(status_records),
            "eos_baseline": eos["baseline"],
            "eos_parity": eos["parity"],
            "eos": eos,
            "baseline_state_classification": baseline.get("classification"),
            "steady_state_converged": baseline.get("steady_state_converged"),
            "authorized_publication_transition": baseline.get("authorized_transition"),
            "publication_transition": baseline,
            "read_only": True,
            "projection_source": "live Git plumbing/porcelain-v2 and EOS projection",
            "errors": errors,
        }
    except (OSError, UnicodeError, RepositoryProjectionError) as error:
        return {
            "result": "FAIL",
            "repository_valid": False,
            "repository_root": str(root),
            "read_only": True,
            "projection_source": "live Git plumbing/porcelain-v2 and EOS projection",
            "errors": [str(error)],
        }
