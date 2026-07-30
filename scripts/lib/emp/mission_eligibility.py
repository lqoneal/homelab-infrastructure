"""Deterministic OA-06 mission eligibility classification."""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from pathlib import Path
from typing import Any, Iterable, Mapping


class MissionEligibilityError(ValueError):
    """Eligibility input is malformed or internally inconsistent."""


REQUIRED_FIELDS = {
    "mission_id", "candidate_state", "dependencies", "deferred",
    "admission_status", "authority_status", "repository_match",
    "baseline_match", "resources_available", "blocking_conditions",
}


def _digest(value: Any) -> str:
    payload = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode()
    return hashlib.sha256(payload).hexdigest()


def _validate(candidate: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(candidate, Mapping) or set(candidate) != REQUIRED_FIELDS:
        supplied = set(candidate) if isinstance(candidate, Mapping) else set()
        raise MissionEligibilityError(
            "candidate fields mismatch; "
            f"missing={sorted(REQUIRED_FIELDS - supplied)}; "
            f"unknown={sorted(supplied - REQUIRED_FIELDS)}"
        )
    value = deepcopy(dict(candidate))
    if not isinstance(value["mission_id"], str) or not value["mission_id"]:
        raise MissionEligibilityError("mission_id must be a non-empty string")
    if value["candidate_state"] not in {"CANDIDATE", "STAGED"}:
        raise MissionEligibilityError("candidate_state must be CANDIDATE or STAGED")
    for field in ("dependencies", "blocking_conditions"):
        if (
            not isinstance(value[field], list)
            or any(not isinstance(item, str) or not item for item in value[field])
        ):
            raise MissionEligibilityError(f"{field} must contain non-empty strings")
        value[field] = sorted(set(value[field]))
    for field in (
        "deferred", "repository_match", "baseline_match", "resources_available"
    ):
        if not isinstance(value[field], bool):
            raise MissionEligibilityError(f"{field} must be boolean")
    if value["admission_status"] not in {"ACCEPTED", "REJECTED", "MISSING"}:
        raise MissionEligibilityError("admission_status is invalid")
    if value["authority_status"] not in {
        "AUTHORIZED", "UNAUTHORIZED", "STALE", "MISSING"
    }:
        raise MissionEligibilityError("authority_status is invalid")
    return value


def classify(
    candidate: Mapping[str, Any], *, completed_missions: Iterable[str]
) -> dict[str, Any]:
    """Return one stable, mutually exclusive OA-06 classification."""
    value = _validate(candidate)
    completed = set(completed_missions)
    if any(not isinstance(item, str) or not item for item in completed):
        raise MissionEligibilityError("completed_missions must contain strings")

    ineligible = []
    if value["admission_status"] != "ACCEPTED":
        ineligible.append("ADMISSION_NOT_ACCEPTED")
    if value["authority_status"] != "AUTHORIZED":
        ineligible.append(f"AUTHORITY_{value['authority_status']}")
    if not value["repository_match"]:
        ineligible.append("REPOSITORY_MISMATCH")
    if not value["baseline_match"]:
        ineligible.append("BASELINE_MISMATCH")
    if value["candidate_state"] != "STAGED":
        ineligible.append("MISSION_NOT_STAGED")

    missing_dependencies = sorted(set(value["dependencies"]) - completed)
    blocked = []
    if missing_dependencies:
        blocked.append("DEPENDENCY_UNSATISFIED")
    if not value["resources_available"]:
        blocked.append("EXECUTION_RESOURCES_UNAVAILABLE")
    if value["blocking_conditions"]:
        blocked.append("BLOCKING_CONDITION")

    if ineligible:
        classification, reasons = "INELIGIBLE", sorted(ineligible)
    elif value["deferred"]:
        classification, reasons = "DEFERRED", ["MISSION_DEFERRED"]
    elif blocked:
        classification, reasons = "BLOCKED", sorted(blocked)
    else:
        classification, reasons = "ELIGIBLE", []

    result = {
        "schema_version": 1,
        "mission_id": value["mission_id"],
        "classification": classification,
        "reason_codes": reasons,
        "missing_dependencies": missing_dependencies,
        "protected_effect": "NONE",
    }
    result["classification_digest"] = _digest(result)
    return result


def evaluate_file(path: Path | str) -> dict[str, Any]:
    try:
        request = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise MissionEligibilityError(f"eligibility request invalid: {error}") from error
    if not isinstance(request, dict) or set(request) != {
        "candidate", "completed_missions"
    }:
        raise MissionEligibilityError("eligibility request shape is invalid")
    if not isinstance(request["completed_missions"], list):
        raise MissionEligibilityError("completed_missions must be a list")
    return classify(
        request["candidate"], completed_missions=request["completed_missions"]
    )
