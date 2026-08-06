"""Read-only repository/EOS synchronization verification."""
from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any, Mapping

from scripts.lib.eos.canonical_baseline import resolve as resolve_baseline
from scripts.lib.eos.state_sync import SynchronizationError, frontmatter, render, validate


def _git(root: Path, *args: str) -> tuple[str, str | None]:
    result = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, check=False)
    return result.stdout.strip(), None if result.returncode == 0 else (result.stderr.strip() or "git command failed")


def _checkpoint_status(root: Path, eos_workspace: Path, current: str) -> dict[str, Any]:
    pointer = eos_workspace / "eos/state/ACTIVE-CHECKPOINT"
    if not pointer.is_file():
        return {"result": "UNAVAILABLE", "reason": "ACTIVE-CHECKPOINT is missing"}
    lines = pointer.read_text(encoding="utf-8").splitlines()
    target = lines[0].strip() if lines else ""
    checkpoint = Path(target)
    if not checkpoint.is_absolute():
        checkpoint = eos_workspace / "eos/checkpoints" / target
    if not checkpoint.is_file():
        return {"result": "FAIL", "reason": f"active checkpoint does not resolve: {target}"}
    recorded = ""
    for line in checkpoint.read_text(encoding="utf-8").splitlines():
        if line.startswith("Commit: `") and line.endswith("`"):
            recorded = line[len("Commit: `"):-1]
            break
    if not recorded:
        return {"result": "FAIL", "path": str(checkpoint), "reason": "active checkpoint has no repository commit"}
    resolved, error = _git(root, "rev-parse", "--verify", f"{recorded}^{{commit}}")
    if error:
        return {"result": "FAIL", "path": str(checkpoint), "recorded_commit": recorded, "reason": error}
    return {"result": "PASS" if resolved == current else "HISTORICAL", "path": str(checkpoint), "recorded_commit": resolved, "reason": "aligned with current repository baseline" if resolved == current else "historical checkpoint predates current published baseline"}


def assess(observed: Mapping[str, Any]) -> dict[str, Any]:
    """Assess resolved facts; this also provides a deterministic test seam."""
    checks = {key: dict(value) for key, value in observed.items()}
    blockers = [f"{name}: {check.get('reason', 'verification failed')}" for name, check in checks.items() if check.get("result") in {"FAIL", "BLOCKED"}]
    synchronized = all(checks.get(name, {}).get("result") == "PASS" for name in ("repository_identity", "published_baseline", "eos", "baseline_parity", "manifest_consistency"))
    if not synchronized:
        blockers.append("repository–EOS synchronization prerequisites are unresolved")
    checks["synchronization"] = {"result": "PASS" if synchronized else "FAIL", "reason": "repository and EOS published baselines are current and consistent" if synchronized else "; ".join(blockers)}
    return {"result": "PASS" if synchronized and not blockers else "FAIL", "checks": checks, "defects": blockers, "read_only": True, "next_action": "Continue with the next authorized operation; do not repeat publication or EOS synchronization" if synchronized and not blockers else "Resolve the reported repository–EOS verification blocker"}


def verify(root: Path | str, eos_workspace: Path | str, project: str = "homelab") -> dict[str, Any]:
    """Resolve current repository/EOS state without synchronization side effects."""
    root, workspace = Path(root).resolve(), Path(eos_workspace).resolve()
    checks: dict[str, dict[str, Any]] = {}
    baseline = resolve_baseline(root, workspace, project)
    identity = baseline["identity"]
    head, origin = baseline["current_head"], baseline["published_head"]
    branch = _git(root, "branch", "--show-current")[0]
    dirty, dirty_error = _git(root, "status", "--porcelain")
    checks["repository_identity"] = {"result": baseline["checks"]["repository_identity"], "identity": identity}
    published = baseline["publication_parity"] == "PASS"
    checks["published_baseline"] = {"result": "PASS" if published else "FAIL", "branch": branch, "head": head, "origin_main": origin, "clean": not bool(dirty), "working_tree": "clean" if not dirty else "candidate changes present", "reason": "HEAD equals origin/main on main; local candidate changes are reported separately" if published and dirty else ("HEAD equals origin/main on clean main" if published else "repository is not at the published main baseline")}

    eos_id_path = workspace / "eos/state/EOS-ID.md"
    eos_state_path = workspace / "eos/state/EOS-STATE.md"
    manifest_path = workspace / "eos/state/EOS-MANIFEST.md"
    try:
        eos_id, eos_state, eos_manifest = frontmatter(eos_id_path), frontmatter(eos_state_path), frontmatter(manifest_path)
        identity_matches = baseline["checks"]["repository_identity"] == "PASS" and baseline["checks"]["eos_parity"] == "PASS"
        state_matches = baseline["checks"]["eos_parity"] == "PASS"
        checks["eos"] = {"result": "PASS" if identity_matches and state_matches else "FAIL", "state": str(eos_state_path), "manifest": str(manifest_path), "repository_commit": baseline["eos_baseline"], "repository_branch": eos_state.get("repository_branch"), "reason": "EOS identity and recorded repository baseline resolved" if identity_matches and state_matches else "EOS identity or recorded repository baseline mismatch"}
        parity = baseline["checks"]["eos_parity"] == "PASS" and baseline["checks"]["publication_parity"] == "PASS"
        checks["baseline_parity"] = {"result": "PASS" if parity else "FAIL", "repository_head": head, "origin_main": origin, "eos_repository_commit": baseline["eos_baseline"], "reason": "repository HEAD, origin/main, and EOS baseline are equal" if parity else "repository and EOS baselines disagree"}
        try:
            drift = validate(render(root, workspace, project))
            checks["manifest_consistency"] = {"result": "PASS" if not drift else "FAIL", "reason": "canonical EOS projection matches EOS-STATE and EOS-MANIFEST" if not drift else "canonical EOS projection drift: " + ", ".join(drift)}
        except SynchronizationError as error:
            checks["manifest_consistency"] = {"result": "FAIL", "reason": str(error)}
    except (OSError, SynchronizationError, UnicodeError) as error:
        checks["eos"] = {"result": "FAIL", "reason": f"canonical EOS state unresolved: {error}"}
        checks["baseline_parity"] = {"result": "FAIL", "reason": "EOS baseline unavailable"}
        checks["manifest_consistency"] = {"result": "FAIL", "reason": "EOS manifest/state unavailable"}
    checks["checkpoint"] = _checkpoint_status(root, workspace, head)
    return assess(checks)
