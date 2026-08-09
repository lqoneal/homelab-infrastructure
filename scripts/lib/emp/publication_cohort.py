"""Durable source-level authority for one Zeus publication convergence.

Publication cohorts group qualified work sources, not Git paths.  Candidate
paths continue to come from the source manifests; this record only answers
which qualified sources are authorized to converge in the same transaction.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from scripts.lib.emp.canonical_lifecycle_resolver import resolve as resolve_lifecycle
from scripts.lib.emp.production_execution import atomic_write, digest, identifier, load_json
from scripts.lib.emp.repository_projection import project as project_repository
from scripts.lib.emp.runtime_paths import initialize_runtime, resolve_runtime


COHORT_SCHEMA = 1
COHORT_DIR = "publication-cohorts"


def _now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _runtime(root: Path, runtime_root: Path | str | None, *, writable: bool) -> Path:
    if writable:
        return initialize_runtime(root, explicit=runtime_root)["root"]
    return resolve_runtime(root, explicit=runtime_root, require_writable=False)["root"]


def _path(runtime: Path, cohort_id: str) -> Path:
    if not cohort_id.startswith("COHORT-"):
        raise ValueError("publication cohort identity is not canonical")
    return runtime / COHORT_DIR / f"{cohort_id}.json"


def _load(path: Path) -> dict[str, Any]:
    try:
        value = load_json(path)
    except Exception:
        return {}
    return value if isinstance(value, dict) else {}


def _active(values: list[dict[str, Any]]) -> list[dict[str, Any]]:
    superseded = {value.get("supersedes_cohort_id") for value in values if value.get("supersedes_cohort_id")}
    return [value for value in values if value.get("status") not in {"SUPERSEDED", "ABORTED"} and value.get("cohort_id") not in superseded]


def _records(root: Path, mission_id: str, wop_id: str, manifest: Path | str | None = None) -> list[dict[str, Any]]:
    # The candidate resolver owns manifest parsing and qualification semantics.
    # Import lazily to avoid a module cycle while allowing both surfaces to
    # share precisely the same source identity calculation.
    from scripts.lib.emp.publication_candidate_authority import _source_records

    return _source_records(root, mission_id, wop_id, manifest)


def _projection(root: Path, mission_id: str, runtime_root: Path | str | None,
                lifecycle_projection: Mapping[str, Any] | None) -> tuple[dict[str, Any], dict[str, Any]]:
    live = dict(lifecycle_projection or resolve_lifecycle(root, mission_id, runtime_root=runtime_root))
    repository = project_repository(
        root,
        runtime_root=runtime_root,
        mission_id=mission_id,
        wop_id=live.get("wop_id"),
    )
    return live, repository


def _derive(root: Path, mission_id: str, *, runtime_root: Path | str | None = None,
            supersedes_publication_id: str | None = None,
            lifecycle_projection: Mapping[str, Any] | None = None) -> dict[str, Any]:
    mission = str(mission_id).strip().upper()
    live, repository = _projection(root, mission, runtime_root, lifecycle_projection)
    if live.get("result") != "PASS":
        return {"result": "FAIL", "mission_id": mission, "blockers": [{"code": "MISSION_PROJECTION_INVALID", "reason": live.get("blockers")}], "next_authorized_action": "RESOLVE_MISSION_PROJECTION", "read_only": True}
    if repository.get("result") != "PASS":
        return {"result": "FAIL", "mission_id": mission, "blockers": [{"code": "REPOSITORY_PROJECTION_INVALID", "reason": repository.get("errors")}], "next_authorized_action": "RESOLVE_REPOSITORY_PROJECTION", "read_only": True}
    wop = str(live.get("wop_id") or "").upper()
    if not wop:
        return {"result": "FAIL", "mission_id": mission, "blockers": [{"code": "WOP_PROJECTION_MISSING", "reason": "live mission projection has no WOP identity"}], "next_authorized_action": "RESOLVE_PUBLICATION_COHORT_AUTHORITY", "read_only": True}
    records = _records(root, mission, wop)
    qualified = [value for value in records if value.get("publication_state") == "QUALIFIED_UNPUBLISHED"]
    excluded = [value for value in records if value not in qualified]
    if not qualified:
        return {"result": "FAIL", "mission_id": mission, "wop_id": wop, "repository": repository, "records": records, "blockers": [{"code": "NO_QUALIFIED_COHORT_SOURCE", "reason": "no qualified unpublished source can establish a publication cohort"}], "next_authorized_action": "RESOLVE_PUBLICATION_COHORT_AUTHORITY", "read_only": True}
    members = [
        {
            "source_id": value["source_id"],
            "source_path": value["source_path"],
            "source_type": value.get("source_type"),
            "mission_id": value.get("mission_id"),
            "wop_id": value.get("wop_id"),
            "qualification_state": value.get("qualification_state"),
            "publication_state": value.get("publication_state"),
            "context_digest": value.get("context_digest"),
            "dependency_relationship": value.get("dependency_relationship"),
        }
        for value in sorted(qualified, key=lambda item: item["source_id"])
    ]
    source_digest = digest(members)
    seed = {
        "mission_id": mission,
        "wop_id": wop,
        "repository_id": repository.get("repository_id"),
        "source_digest": source_digest,
        "supersedes_publication_id": supersedes_publication_id,
        "boundary": "CURRENT_QUALIFIED_UNPUBLISHED_CONVERGENCE",
    }
    cohort_id = identifier("COHORT", seed)
    return {
        "schema_version": COHORT_SCHEMA,
        "result": "PASS",
        "cohort_id": cohort_id,
        "mission_id": mission,
        "wop_id": wop,
        "repository_id": repository.get("repository_id"),
        "cohort_intent": "CURRENT_QUALIFIED_UNPUBLISHED_CONVERGENCE",
        "cohort_scope": "CURRENT_LIFECYCLE_BASELINE_BEFORE_DIVERGENCE_RECONCILIATION",
        "source_ids": [value["source_id"] for value in members],
        "dependency_source_ids": [value["source_id"] for value in members if value.get("dependency_relationship") not in {None, "DIRECT"}],
        "excluded_source_ids": [value.get("source_id") for value in excluded if value.get("source_id")],
        "members": members,
        "excluded_sources": [
            {"source_id": value.get("source_id"), "source_path": value.get("source_path"), "classification": value.get("publication_state"), "reason": value.get("publication_reason") or value.get("qualification_reason")}
            for value in excluded
        ],
        "authority_source": {"type": "LIVE_MISSION_WOP_QUALIFIED_SOURCE_PROJECTION", "mission_id": mission, "wop_id": wop, "source_digest": source_digest},
        "created_from": {"supersedes_publication_id": supersedes_publication_id, "lifecycle_projection": {key: live.get(key) for key in ("mission_id", "wop_id", "submission_id", "admission_id", "bootstrap_id", "lifecycle_state", "next_authorized_action")}, "repository_projection": {key: repository.get(key) for key in ("repository_id", "head", "origin_main", "eos_baseline")}},
        "baseline": {"head": repository.get("head"), "origin_main": repository.get("origin_main"), "eos_baseline": repository.get("eos_baseline")},
        "status": "ACTIVE",
        "blockers": [],
        "candidate_authority_state": "RESOLUTION_PENDING",
        "source_digest": source_digest,
        "created_at": None,
        "updated_at": None,
        "next_authorized_action": "RESOLVE_PUBLICATION_CANDIDATE_AUTHORITY",
        "read_only": True,
    }


def inspect(root: Path | str, mission_id: str, *, runtime_root: Path | str | None = None,
            lifecycle_projection: Mapping[str, Any] | None = None) -> dict[str, Any]:
    repository = Path(root).resolve()
    runtime = _runtime(repository, runtime_root, writable=False)
    values = [_load(path) for path in sorted((runtime / COHORT_DIR).glob("COHORT-*.json"))]
    matching = _active([value for value in values if value.get("mission_id") == str(mission_id).strip().upper()])
    if len(matching) > 1:
        return {"result": "FAIL", "mission_id": str(mission_id).strip().upper(), "blockers": [{"code": "PUBLICATION_COHORT_CARDINALITY_CONFLICT", "reason": "more than one active publication cohort resolves the mission"}], "next_authorized_action": "RECONCILE_PUBLICATION_COHORT_CARDINALITY", "read_only": True}
    if matching:
        current = matching[0]
        derived = _derive(repository, str(mission_id), runtime_root=runtime, lifecycle_projection=lifecycle_projection)
        if derived.get("result") != "PASS":
            return {**current, "result": "FAIL", "blockers": derived.get("blockers", []), "next_authorized_action": derived.get("next_authorized_action", "RESOLVE_PUBLICATION_COHORT_AUTHORITY"), "read_only": True}
        if current.get("source_digest") != derived.get("source_digest") or current.get("repository_id") != derived.get("repository_id") or current.get("wop_id") != derived.get("wop_id"):
            return {**current, "result": "FAIL", "blockers": [{"code": "PUBLICATION_COHORT_STALE", "reason": "live mission, repository, or qualified source projection changed after cohort establishment"}], "next_authorized_action": "RECONCILE_PUBLICATION_COHORT_AUTHORITY", "read_only": True}
        return {**current, "result": "PASS", "cohort_authority_result": "PASS", "source_count": len(current.get("source_ids", [])), "dependency_source_count": len(current.get("dependency_source_ids", [])), "shared_path_count": None, "ambiguous_path_count": 0, "blocked_path_count": 0, "next_authorized_action": "RESOLVE_PUBLICATION_CANDIDATE_AUTHORITY", "read_only": True}
    preview = _derive(repository, str(mission_id), runtime_root=runtime, lifecycle_projection=lifecycle_projection)
    return {"result": "FAIL", "mission_id": str(mission_id).strip().upper(), "cohort_authority_result": "NOT_ESTABLISHED", "preview": preview, "blockers": [{"code": "PUBLICATION_COHORT_NOT_ESTABLISHED", "reason": "no durable source-level publication cohort resolves the mission"}], "next_authorized_action": "ESTABLISH_PUBLICATION_COHORT_AUTHORITY", "read_only": True}


def establish(root: Path | str, mission_id: str, *, runtime_root: Path | str | None = None,
              supersedes_publication_id: str | None = None,
              lifecycle_projection: Mapping[str, Any] | None = None) -> dict[str, Any]:
    repository = Path(root).resolve()
    runtime = _runtime(repository, runtime_root, writable=True)
    derived = _derive(repository, mission_id, runtime_root=runtime, supersedes_publication_id=supersedes_publication_id, lifecycle_projection=lifecycle_projection)
    if derived.get("result") != "PASS":
        return derived
    existing_values = [_load(value) for value in sorted((runtime / COHORT_DIR).glob("COHORT-*.json"))]
    existing_active = _active([value for value in existing_values if value.get("mission_id") == derived.get("mission_id")])
    path = _path(runtime, str(derived["cohort_id"]))
    current_existing = _load(path) if path.is_file() else {}
    existing_prior = [value for value in existing_active if value.get("cohort_id") != derived.get("cohort_id")]
    if len(existing_prior) > 1:
        return {**derived, "result": "FAIL", "blockers": [{"code": "PUBLICATION_COHORT_CARDINALITY_CONFLICT", "reason": "more than one current cohort exists before establishing a successor"}], "next_authorized_action": "RECONCILE_PUBLICATION_COHORT_CARDINALITY", "read_only": True}
    if path.is_file():
        existing = current_existing
        immutable = ("mission_id", "wop_id", "repository_id", "source_digest", "source_ids")
        if any(existing.get(key) != derived.get(key) for key in immutable):
            return {**existing, "result": "FAIL", "blockers": [{"code": "PUBLICATION_COHORT_IDENTITY_CONFLICT", "reason": "existing cohort identity conflicts with live source projection"}], "next_authorized_action": "RECONCILE_PUBLICATION_COHORT_AUTHORITY", "read_only": True}
        if existing_prior and existing_prior[0].get("cohort_id") != existing.get("cohort_id") and not existing.get("supersedes_cohort_id"):
            existing["supersedes_cohort_id"] = existing_prior[0].get("cohort_id")
            existing["created_from"] = {**(existing.get("created_from") or {}), "supersedes_cohort_id": existing_prior[0].get("cohort_id")}
            existing["updated_at"] = _now()
            atomic_write(path, existing)
        return {**existing, "result": "PASS", "replayed": True, "cohort_authority_result": "PASS", "source_count": len(existing.get("source_ids", [])), "dependency_source_count": len(existing.get("dependency_source_ids", [])), "ambiguous_path_count": 0, "blocked_path_count": 0, "next_authorized_action": "RESOLVE_PUBLICATION_CANDIDATE_AUTHORITY", "read_only": False}
    now = _now()
    derived["created_at"] = now
    derived["updated_at"] = now
    if existing_prior:
        derived["supersedes_cohort_id"] = existing_prior[0].get("cohort_id")
        derived["created_from"]["supersedes_cohort_id"] = existing_prior[0].get("cohort_id")
    derived["cohort_authority_result"] = "PASS"
    atomic_write(path, derived)
    return {**derived, "replayed": False, "source_count": len(derived["source_ids"]), "dependency_source_count": len(derived["dependency_source_ids"]), "ambiguous_path_count": 0, "blocked_path_count": 0, "read_only": False}


def resolve_for_candidate(root: Path | str, mission_id: str, *, runtime_root: Path | str | None = None,
                          lifecycle_projection: Mapping[str, Any] | None = None) -> dict[str, Any] | None:
    value = inspect(root, mission_id, runtime_root=runtime_root, lifecycle_projection=lifecycle_projection)
    if value.get("cohort_authority_result") == "PASS":
        return value
    if value.get("next_authorized_action") == "ESTABLISH_PUBLICATION_COHORT_AUTHORITY":
        return None
    return value


def load_bound(root: Path | str, cohort_id: str, *, runtime_root: Path | str | None = None) -> dict[str, Any] | None:
    """Load exactly one persisted cohort without resolving the mission cohort.

    Transaction revalidation must not call :func:`inspect`, because inspect is
    intentionally a mission-level current-cohort projection and may discover a
    later qualified source.  This read-only loader is the durable boundary for
    a transaction's persisted ``publication_cohort_id``.
    """
    repository = Path(root).resolve()
    runtime = _runtime(repository, runtime_root, writable=False)
    if not isinstance(cohort_id, str) or not cohort_id.startswith("COHORT-"):
        return None
    path = _path(runtime, cohort_id)
    if not path.is_file():
        return None
    value = _load(path)
    return value if value.get("cohort_id") == cohort_id else None
