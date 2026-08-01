"""Mission-ID submission resolution over the existing Stage 1 authority.

This module is deliberately a resolver, not a second submission or queue
store.  A mission ID is resolved through the published Beta roadmap and then
to an existing authoritative WOP package.  The existing Stage1Runtime remains
the only component that validates and records a submission.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from scripts.lib.eos import operational_beta
from scripts.lib.emp.stage1_runtime import Stage1Error, Stage1Runtime


PACKAGE_ROOTS = (
    "engineering/work-orders",
    "engineering/wop-packages",
    "engineering/wops",
)


def _package_candidates(root: Path, mission_id: str) -> list[Path]:
    """Return deterministic package candidates without inventing authority."""
    card = operational_beta.mission_state(root, mission_id)
    expected_wop = f"WOP-{mission_id}-FOUNDATION-001"
    names = (expected_wop, mission_id)
    candidates: list[Path] = []
    for relative_root in PACKAGE_ROOTS:
        directory = root / relative_root
        for name in names:
            candidate = directory / name
            if candidate.is_dir() or candidate.is_file():
                candidates.append(candidate)
    # A package may be explicitly indexed by a future canonical package
    # manifest.  The index is optional and cannot itself authorize a package.
    index = root / "engineering/wop-packages/index.yaml"
    if index.is_file():
        import yaml

        data = yaml.safe_load(index.read_text(encoding="utf-8")) or {}
        for item in data.get("packages", []):
            if item.get("mission_id") == card["mission_id"] and item.get("path"):
                candidate = (root / item["path"]).resolve()
                if candidate.is_dir() or candidate.is_file():
                    candidates.append(candidate)
    unique = {path.resolve(): path.resolve() for path in candidates}
    return sorted(unique.values(), key=lambda path: path.as_posix())


def submit_by_mission(
    root: Path | str,
    mission_id: str,
    *,
    state_directory: Path | str,
    at: datetime | None = None,
    package: Path | str | None = None,
) -> dict[str, Any]:
    """Resolve and submit a mission without bypassing Stage 1 validation."""
    repository = Path(root).resolve()
    mission = mission_id.upper()
    card = operational_beta.mission_state(repository, mission)
    common = {
        "mission_id": mission,
        "operation": "BETA",
        "family": card["family"],
        "title": card["title"],
        "lifecycle": card["lifecycle"],
        "classification": card["classification"],
        "readiness": card["readiness"],
        "dependencies": card["dependencies"],
        "authority_source": "engineering/docs/architecture/OPERATION-BETA-ROADMAP.md",
        "repository": str(repository),
        "development_baseline": "OB-PLAN-v1.0.0",
        "production_baseline": "OA-v1.0.0",
        "selection_rationale": (
            "first eligible mission in the authoritative Beta sequence"
            if card["classification"] == "ELIGIBLE"
            else "mission is not selected because authoritative readiness is unmet"
        ),
        "authority": card.get("authoritative_sources", []),
        "missing_dependencies": card["missing_dependencies"],
    }
    if card["classification"] != "ELIGIBLE":
        return {**common, "result": "FAIL", "resolution": "MISSION_NOT_ELIGIBLE",
                "blockers": card["missing_dependencies"],
                "next_authorized_action": "Resolve the authoritative mission blockers."}

    candidates = [Path(package).resolve()] if package else _package_candidates(repository, mission)
    if len(candidates) > 1:
        return {**common,
            "result": "FAIL", "resolution": "AMBIGUOUS_WOP_PACKAGE",
            "packages": [str(path) for path in candidates],
            "next_authorized_action": "Retain exactly one authoritative qualified WOP package.",
        }
    if not candidates:
        return {**common,
            "result": "FAIL", "resolution": "WOP_PACKAGE_UNAVAILABLE",
            "wop_id": f"WOP-{mission}-FOUNDATION-001",
            "package_candidates": [
                str(repository / relative / name)
                for relative in PACKAGE_ROOTS
                for name in (f"WOP-{mission}-FOUNDATION-001", mission)
            ],
            "next_authorized_action": (
                "Publish and qualify the approved ZDCL WOP contract/package, "
                "then rerun this command."
            ),
        }

    package_path = str(candidates[0])
    try:
        record = Stage1Runtime(repository, state_directory).submit(candidates[0], at=at)
    except Stage1Error as error:
        evidence = dict(error.evidence)
        return {**common,
            "result": "FAIL", "resolution": "PACKAGE_VALIDATION_FAILED",
            "wop_id": f"WOP-{mission}-FOUNDATION-001", "package": package_path,
            "package_digest": evidence.get("package_digest"),
            "submission_id": evidence.get("instance_id") or evidence.get("existing_instance"),
            "submitter": evidence.get("operator"), "queue_state": "REJECTED",
            "admission_readiness": "NOT_READY", "blockers": [str(error)],
            "evidence": evidence,
            "next_authorized_action": (
                "Reconcile the reported package, authority, repository, or baseline defect, "
                "then resubmit the mission."
            ),
        }
    staging = record.get("staging_contract", {})
    submitter = record.get("operator", "")
    admission_command = (
        "zeus admit-mission start --mode qualification "
        f"--mission {mission} --wop {record['wop_id']} "
        f"--submitter {submitter} --principal {submitter}"
    )
    return {**common,
        "result": "PASS",
        "resolution": "AUTHORITATIVE_PACKAGE_REUSED",
        "wop_id": record["wop_id"],
        "package": package_path,
        "package_digest": record["package_digest"],
        "submission_id": record["instance_id"],
        "submitter": submitter, "priority": staging.get("priority", 0),
        "queue_state": record["state"],
        "readiness": card["readiness"],
        "admission_readiness": "READY",
        "blockers": [],
        "next_authorized_action": admission_command,
        "submission": record,
    }
