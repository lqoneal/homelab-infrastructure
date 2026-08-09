"""Canonical read-only repository publication and mission-baseline resolution."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path
from typing import Any, Mapping

from scripts.lib.emp.repository_identity import resolve as resolve_repository_identity
from scripts.lib.emp.repository_projection import project as project_repository
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


def resolve_commit_lineage(
    root: Path | str,
    provenance_baseline: str,
    current_published_baseline: str,
) -> dict[str, Any]:
    """Resolve immutable commit ancestry without substituting live authority.

    This helper is deliberately independent of HEAD/origin/EOS parity.  It is
    used to verify historical publication evidence at the baseline it records.
    The live ``resolve_provenance_lineage`` wrapper separately proves that the
    requested target is the currently synchronized publication projection.
    """
    repository = Path(root).resolve()
    errors: list[dict[str, str]] = []
    try:
        provenance = _commit(
            provenance_baseline,
            "MISSION_PROVENANCE_BASELINE_MISSING",
            "mission provenance baseline",
        )
        target = _commit(
            current_published_baseline,
            "CURRENT_PUBLISHED_BASELINE_MISSING",
            "current published baseline",
        )
    except BaselineResolutionError as error:
        return {
            "result": "FAIL",
            "provenance_baseline": None,
            "current_published_baseline": None,
            "baseline_relationship": "INVALID",
            "errors": [{"code": error.code, "message": str(error)}],
        }

    provenance_reachable = subprocess.run(
        ["git", "-C", str(repository), "cat-file", "-e", f"{provenance}^{{commit}}"],
        capture_output=True,
        check=False,
    ).returncode == 0
    target_reachable = subprocess.run(
        ["git", "-C", str(repository), "cat-file", "-e", f"{target}^{{commit}}"],
        capture_output=True,
        check=False,
    ).returncode == 0
    if not provenance_reachable:
        errors.append({
            "code": "MISSION_PROVENANCE_BASELINE_MISSING",
            "message": "receipt provenance baseline is not a reachable commit",
        })
    if not target_reachable:
        errors.append({
            "code": "CURRENT_PUBLISHED_BASELINE_MISSING",
            "message": "publication baseline is not a reachable commit",
        })

    if not errors and provenance == target:
        relationship = "IDENTICAL"
    elif not errors and subprocess.run(
        ["git", "-C", str(repository), "merge-base", "--is-ancestor", provenance, target],
        capture_output=True,
        check=False,
    ).returncode == 0:
        relationship = "ANCESTOR"
    else:
        relationship = "UNRELATED"
        if not errors:
            errors.append({
                "code": "MISSION_PROVENANCE_NOT_ANCESTOR",
                "message": "receipt provenance baseline is not an ancestor of the publication baseline",
            })

    return {
        "result": "PASS" if not errors else "FAIL",
        "provenance_baseline": provenance,
        "current_published_baseline": target,
        "baseline_relationship": relationship,
        "errors": errors,
    }


def resolve_provenance_lineage(
    root: Path | str,
    provenance_baseline: str,
    *,
    current_published_baseline: str | None = None,
    runtime_root: Path | str | None = None,
    mission_id: str | None = None,
    wop_id: str | None = None,
) -> dict[str, Any]:
    """Validate immutable receipt provenance against the current publication.

    A lifecycle receipt records the repository commit against which its
    transition was created.  That commit is immutable provenance, not a
    requirement that the repository remain frozen forever.  A later
    publication is valid when it is the synchronized ``origin/main`` head and
    is a commit descendant of the receipt baseline.  This helper deliberately
    does not rewrite receipts or consult timestamps, filesystem ordering, or
    legacy runtime projections.
    """
    repository = Path(root).resolve()
    errors: list[dict[str, str]] = []
    try:
        provenance = _commit(
            provenance_baseline,
            "MISSION_PROVENANCE_BASELINE_MISSING",
            "mission provenance baseline",
        )
    except BaselineResolutionError as error:
        return {
            "result": "FAIL",
            "provenance_baseline": None,
            "current_published_baseline": None,
            "baseline_relationship": "INVALID",
            "errors": [{"code": error.code, "message": str(error)}],
        }

    projection = project_repository(
        repository,
        runtime_root=runtime_root,
        mission_id=mission_id,
        wop_id=wop_id,
    )
    head = projection.get("head")
    published = projection.get("origin_main")
    target = current_published_baseline or head
    try:
        target = _commit(target, "CURRENT_PUBLISHED_BASELINE_MISSING", "current published baseline")
    except BaselineResolutionError as error:
        return {
            "result": "FAIL",
            "provenance_baseline": provenance,
            "current_published_baseline": None,
            "baseline_relationship": "INVALID",
            "errors": [{"code": error.code, "message": str(error)}],
        }

    if projection.get("result") != "PASS" or target != head:
        errors.append({
            "code": "PUBLICATION_PARITY_FAILURE",
            "message": "current repository baseline is neither converged nor an authorized publication transition",
        })

    commit_lineage = resolve_commit_lineage(repository, provenance, target)
    relationship = commit_lineage["baseline_relationship"]
    errors.extend(commit_lineage["errors"])

    return {
        "result": "PASS" if not errors else "FAIL",
        "provenance_baseline": provenance,
        "current_published_baseline": target,
        "published_head": published,
        "current_authorized_baseline": head,
        "baseline_state_classification": projection.get("baseline_state_classification"),
        "authorized_publication_transition": projection.get("authorized_publication_transition", False),
        "baseline_relationship": relationship,
        "errors": errors,
    }


def resolve(
    root: Path | str,
    eos_workspace: Path | str,
    project: str = "homelab",
    *,
    mission_provenance_baseline: str | None = None,
    runtime_identity: Mapping[str, Any] | None = None,
    runtime_root: Path | str | None = None,
    mission_id: str | None = None,
    wop_id: str | None = None,
) -> dict[str, Any]:
    """Resolve one read-only baseline contract for platform and mission views."""
    root, workspace = Path(root).resolve(), Path(eos_workspace).resolve()
    identity = resolve_repository_identity(root)
    projection = project_repository(
        root,
        workspace,
        project,
        runtime_root=runtime_root,
        mission_id=mission_id,
        wop_id=wop_id,
    )
    head = projection.get("head")
    published = projection.get("origin_main")
    branch = projection.get("branch")
    errors: list[dict[str, str]] = []
    if projection.get("result") != "PASS":
        errors.extend({"code": "PUBLICATION_PARITY_FAILURE", "message": message}
                      for message in projection.get("errors", ["repository baseline is invalid"]))
    eos_baseline = projection.get("eos_baseline") or ""

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
        lineage = resolve_commit_lineage(root, mission_provenance_baseline, str(head or ""))
        provenance = lineage.get("provenance_baseline")
        relationship = lineage.get("baseline_relationship", "INVALID")
        errors.extend(lineage.get("errors", []))

    checks = {
        "repository_identity": "PASS" if identity else "FAIL",
        "publication_parity": "PASS" if projection.get("result") == "PASS" else "FAIL",
        "eos_parity": "PASS" if projection.get("eos_parity") is True else "FAIL",
        "runtime_binding": "PASS" if runtime_ok else "FAIL",
        "mission_provenance": "PASS" if mission_provenance_baseline is None or relationship in {"IDENTICAL", "ANCESTOR"} else "FAIL",
    }
    return {
        "result": "PASS" if not errors else "FAIL", "repository_identity": "PASS" if identity else "FAIL",
        "identity": identity,
        "current_head": head, "published_head": published, "eos_baseline": eos_baseline,
        "current_authorized_baseline": head,
        "head_origin_parity": projection.get("head_origin_parity"),
        "baseline_state_classification": projection.get("baseline_state_classification"),
        "authorized_publication_transition": projection.get("authorized_publication_transition", False),
        "publication_transition": projection.get("publication_transition"),
        "mission_provenance_baseline": provenance,
        "provenance_baseline": provenance,
        "mission_baseline_relationship": "EQUAL" if relationship == "IDENTICAL" else relationship,
        "baseline_relationship": relationship,
        "provenance_valid": checks["mission_provenance"] == "PASS",
        "published_parity": checks["publication_parity"],
        "publication_parity": checks["publication_parity"], "eos_parity": checks["eos_parity"],
        "runtime_binding": checks["runtime_binding"], "checks": checks, "errors": errors,
    }


def resolve_execution_start_baseline(
    root: Path | str,
    eos_workspace: Path | str,
    provenance_baseline: str,
    *,
    runtime_identity: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Resolve immutable execution-start provenance against current publication."""
    value = resolve(
        root, eos_workspace,
        mission_provenance_baseline=provenance_baseline,
        runtime_identity=runtime_identity,
    )
    relationship = value.get("baseline_relationship")
    accepted = relationship in {"IDENTICAL", "ANCESTOR"}
    errors = list(value.get("errors", []))
    if not accepted and not any(item.get("code") == "EXECUTION_PROVENANCE_INVALID" for item in errors):
        errors.append({"code": "EXECUTION_PROVENANCE_INVALID", "message": "execution-start provenance is not identical to or an ancestor of current publication"})
    result = "PASS" if value.get("result") == "PASS" and accepted else "FAIL"
    return {
        **value,
        "result": result,
        "errors": errors,
        "execution_start_provenance_baseline": value.get("provenance_baseline"),
        "current_published_baseline": value.get("published_head"),
        "baseline_relationship": relationship,
        "provenance_valid": result == "PASS",
    }
