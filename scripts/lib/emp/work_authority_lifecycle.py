#!/usr/bin/env python3
"""Controlled first-qualification work authority lifecycle."""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Mapping


class WorkAuthorityError(ValueError):
    """A work authority record or transition is invalid."""


STATES = (
    "PLANNED",
    "AUTHORIZED_FOR_IMPLEMENTATION",
    "IMPLEMENTED",
    "AUTHORIZED_FOR_QUALIFICATION",
    "QUALIFIED",
    "AUTHORIZED_FOR_COMMISSIONING",
    "COMMISSIONED",
    "OPERATIONALLY_ELIGIBLE",
)
TRANSITIONS = dict(zip(STATES, STATES[1:]))
PURPOSE_STATES = {
    "implementation": {"AUTHORIZED_FOR_IMPLEMENTATION"},
    "qualification": {"AUTHORIZED_FOR_QUALIFICATION"},
    "commissioning": {"AUTHORIZED_FOR_COMMISSIONING"},
    "operational": {"OPERATIONALLY_ELIGIBLE"},
}


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode()).hexdigest()


def validate_record(record: Mapping[str, Any]) -> dict[str, Any]:
    value = deepcopy(dict(record))
    required = {
        "schema_version", "work_id", "owner", "principal", "state",
        "authorization_reference", "scope", "history", "record_digest",
    }
    if set(value) != required or value.get("schema_version") != 1:
        raise WorkAuthorityError("work authority record shape is invalid")
    if value["owner"] != "Lawrence O'Neal" or value["principal"] != "loneal":
        raise WorkAuthorityError("production work authority owner is invalid")
    if value["state"] not in STATES or not value["authorization_reference"]:
        raise WorkAuthorityError("work authority state or authorization is invalid")
    if not isinstance(value["scope"], list) or not value["scope"]:
        raise WorkAuthorityError("work authority scope is empty")
    expected = digest({k: v for k, v in value.items() if k != "record_digest"})
    if value["record_digest"] != expected:
        raise WorkAuthorityError("work authority record digest mismatch")
    previous = None
    for event in value["history"]:
        if event.get("from") != previous or event.get("to") not in STATES:
            raise WorkAuthorityError("work authority history is invalid")
        if previous is not None and TRANSITIONS.get(previous) != event["to"]:
            raise WorkAuthorityError("work authority transition skipped a state")
        previous = event["to"]
    if previous != value["state"]:
        raise WorkAuthorityError("work authority history does not reach current state")
    return value


def authorize(record: Mapping[str, Any], purpose: str) -> dict[str, Any]:
    value = validate_record(record)
    if value["state"] not in PURPOSE_STATES.get(purpose, set()):
        raise WorkAuthorityError(f"work is not authorized for {purpose}")
    return value


def transition(
    record: Mapping[str, Any],
    target: str,
    *,
    authorization_reference: str,
    occurred_at: datetime,
    evidence_reference: str,
) -> dict[str, Any]:
    value = validate_record(record)
    if TRANSITIONS.get(value["state"]) != target:
        raise WorkAuthorityError("work authority transition is not permitted")
    if occurred_at.tzinfo is None or not authorization_reference or not evidence_reference:
        raise WorkAuthorityError("transition provenance is incomplete")
    prior = value["state"]
    value["state"] = target
    value["authorization_reference"] = authorization_reference
    value["history"].append({
        "from": prior,
        "to": target,
        "authorization_reference": authorization_reference,
        "evidence_reference": evidence_reference,
        "occurred_at": occurred_at.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
    })
    value["record_digest"] = digest(
        {key: item for key, item in value.items() if key != "record_digest"}
    )
    return validate_record(value)
