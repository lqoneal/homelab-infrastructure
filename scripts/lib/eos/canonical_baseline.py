"""Canonical read-only repository publication and mission-baseline resolution."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path
from typing import Any, Mapping

from scripts.lib.emp.repository_identity import resolve as resolve_repository_identity
from scripts.lib.eos.state_sync import SynchronizationError, frontmatter, render, validate


COMMIT = re.compile(r"^[0-9a-f]{40}$")


class BaselineResolutionError(ValueError):
    """A malformed or contradictory baseline source."""

    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(message)


def _git(root: Path, *args: str) -> tuple[str, str | None]:
    result = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, check=False)
    value = result.stdout.strip()
    return value, None if result.returncode == 0 else (result.stderr.strip() or "git command failed")


def _commit(value: Any, code: str, label: str) -> str:
    text = str(value or "").strip().lower()
    if not COMMIT.fullmatch(text):
        raise BaselineResolutionError(code, f"{label} is missing or malformed")
    return text


def resolve(
    root: Path | str,
    eos_workspace: Path | str,
    project: str = "homelab",
    *,
    mission_provenance_baseline: str | None = None,
    runtime_identity: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Resolve one read-only baseline contract for platform and mission views."""
    root, workspace = Path(root).resolve(), Path(eos_workspace).resolve()
    identity = resolve_repository_identity(root)
    head, head_error = _git(root, "rev-parse", "HEAD")
    published, published_error = _git(root, "rev-parse", "origin/main")
    branch, branch_error = _git(root, "branch", "--show-current")
    errors: list[dict[str, str]] = []
    if head_error or published_error or branch_error or branch != "main" or head != published:
        errors.append({"code": "PUBLICATION_PARITY_FAILURE", "message": "HEAD, origin/main, and published main are not equal"})

    eos_baseline = ""
    eos_identity_ok = False
    manifest_ok = False
    try:
        eos_id = frontmatter(workspace / "eos/state/EOS-ID.md")
        eos_state = frontmatter(workspace / "eos/state/EOS-STATE.md")
        eos_manifest = frontmatter(workspace / "eos/state/EOS-MANIFEST.md")
        eos_baseline = _commit(eos_state.get("repository_commit"), "EOS_BASELINE_MISMATCH", "EOS baseline")
        eos_identity_ok = (
            eos_id.get("repository_root") == identity["repository_path"]
            and eos_id.get("repository_remote") == identity["repository_identity"]
            and eos_state.get("project") == project
            and eos_manifest.get("project") == project
        )
        manifest_ok = not validate(render(root, workspace, project))
    except (OSError, UnicodeError, SynchronizationError, BaselineResolutionError) as error:
        errors.append({"code": getattr(error, "code", "EOS_BASELINE_MISMATCH"), "message": str(error)})

    if eos_baseline and eos_baseline != head:
        errors.append({"code": "EOS_BASELINE_MISMATCH", "message": "EOS baseline does not equal current repository HEAD"})
    if not eos_identity_ok:
        errors.append({"code": "REPOSITORY_IDENTITY_MISMATCH", "message": "EOS repository identity does not match canonical repository"})
    if not manifest_ok:
        errors.append({"code": "EOS_BASELINE_MISMATCH", "message": "EOS projection is not consistent with the repository"})

    runtime_ok = True
    if runtime_identity is not None:
        expected = {"repository": identity["repository_path"], "repository_fingerprint": identity["repository_fingerprint"],
                    "repository_id": identity["repository_id"], "repository_identity": identity["repository_identity"]}
        runtime_ok = all(runtime_identity.get(key) == value for key, value in expected.items())
        if not runtime_ok:
            errors.append({"code": "RUNTIME_REPOSITORY_BINDING_MISMATCH", "message": "runtime repository binding differs from canonical repository"})

    provenance = None
    relationship = "NOT_PROVIDED"
    if mission_provenance_baseline is not None:
        try:
            provenance = _commit(mission_provenance_baseline, "MISSION_PROVENANCE_BASELINE_MISSING", "mission provenance baseline")
            reachable = subprocess.run(["git", "-C", str(root), "cat-file", "-e", f"{provenance}^{{commit}}"], capture_output=True, check=False).returncode == 0
            if not reachable:
                errors.append({"code": "MISSION_PROVENANCE_BASELINE_MISSING", "message": "mission provenance commit is not reachable in repository history"})
                relationship = "UNREACHABLE"
            elif not head or subprocess.run(["git", "-C", str(root), "merge-base", "--is-ancestor", provenance, published], capture_output=True, check=False).returncode != 0:
                errors.append({"code": "MISSION_PROVENANCE_NOT_ANCESTOR", "message": "mission provenance baseline is not an ancestor of current publication"})
                relationship = "UNRELATED"
            else:
                relationship = "EQUAL" if provenance == published else "ANCESTOR"
        except BaselineResolutionError as error:
            errors.append({"code": error.code, "message": str(error)})

    checks = {
        "repository_identity": "PASS" if identity else "FAIL",
        "publication_parity": "PASS" if head and head == published and branch == "main" else "FAIL",
        "eos_parity": "PASS" if eos_baseline and eos_baseline == head else "FAIL",
        "runtime_binding": "PASS" if runtime_ok else "FAIL",
        "mission_provenance": "PASS" if mission_provenance_baseline is None or relationship in {"EQUAL", "ANCESTOR"} else "FAIL",
    }
    return {
        "result": "PASS" if not errors else "FAIL", "repository_identity": "PASS" if identity else "FAIL",
        "identity": identity,
        "current_head": head, "published_head": published, "eos_baseline": eos_baseline,
        "mission_provenance_baseline": provenance, "mission_baseline_relationship": relationship,
        "publication_parity": checks["publication_parity"], "eos_parity": checks["eos_parity"],
        "runtime_binding": checks["runtime_binding"], "checks": checks, "errors": errors,
    }
