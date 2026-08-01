"""Fail-closed authorization boundary for separately authorized corrective work.

This module deliberately stops at authorization.  It never creates, queues, or
executes corrective work; those effects belong to the later CAP-022 outcome.
"""

from __future__ import annotations

import hashlib
import json
import os
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class CorrectiveAuthorizationError(ValueError):
    """The authorization request, receipt, or durable record is invalid."""


MAX_SCOPE_ITEMS = 32
MAX_SCOPE_BYTES = 4096


def digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _timestamp(value: datetime | str) -> str:
    if isinstance(value, str):
        value = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if value.tzinfo is None:
        raise CorrectiveAuthorizationError("timestamp must include timezone")
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _instant(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise CorrectiveAuthorizationError("timestamp is invalid") from error
    if parsed.tzinfo is None:
        raise CorrectiveAuthorizationError("timestamp must include timezone")
    return parsed.astimezone(timezone.utc)


def _scope(scope: list[str] | tuple[str, ...]) -> list[str]:
    if not isinstance(scope, (list, tuple)) or not scope:
        raise CorrectiveAuthorizationError("authorization scope is required")
    values = [str(item) for item in scope]
    if len(values) > MAX_SCOPE_ITEMS or any(not item or len(item) > 256 for item in values):
        raise CorrectiveAuthorizationError("authorization scope exceeds its bounded contract")
    if len(json.dumps(values, separators=(",", ":"))) > MAX_SCOPE_BYTES:
        raise CorrectiveAuthorizationError("authorization scope is too large")
    if len(set(values)) != len(values):
        raise CorrectiveAuthorizationError("authorization scope contains duplicates")
    return values


def request(*, authorization_id: str, mission_id: str, wop_id: str,
            repository: str, baseline: str, authority: str, operator: str,
            scope: list[str] | tuple[str, ...], requested_at: datetime | str,
            expires_at: datetime | str) -> dict[str, Any]:
    fields = (authorization_id, mission_id, wop_id, repository, baseline, authority, operator)
    if any(not isinstance(item, str) or not item for item in fields):
        raise CorrectiveAuthorizationError("authorization identity is incomplete")
    start = _instant(_timestamp(requested_at))
    expiry = _instant(_timestamp(expires_at))
    if expiry <= start:
        raise CorrectiveAuthorizationError("authorization expiry must follow request time")
    unsigned = {
        "schema_version": 1,
        "authorization_type": "ZEUS_CORRECTIVE_WORK_AUTHORIZATION_REQUEST",
        "authorization_id": authorization_id,
        "mission_id": mission_id,
        "wop_id": wop_id,
        "repository": repository,
        "baseline": baseline,
        "authority": authority,
        "operator": operator,
        "scope": _scope(scope),
        "requested_at": _timestamp(requested_at),
        "expires_at": _timestamp(expires_at),
        "state": "PENDING",
        "protected_effect_authorized": False,
        "corrective_work_generated": False,
    }
    return {**unsigned, "request_digest": digest(unsigned)}


def decide(request_record: dict[str, Any], *, decision: str, operator: str,
           authority_lease: str, decided_at: datetime | str) -> dict[str, Any]:
    decision = str(decision).upper()
    if decision not in {"AUTHORIZED", "DENIED"}:
        raise CorrectiveAuthorizationError("authorization decision is invalid")
    expected = digest({key: value for key, value in request_record.items() if key != "request_digest"})
    if request_record.get("request_digest") != expected:
        raise CorrectiveAuthorizationError("authorization request digest mismatch")
    if not operator or not authority_lease:
        raise CorrectiveAuthorizationError("operator or authority lease is absent")
    at = _timestamp(decided_at)
    if _instant(at) > _instant(request_record["expires_at"]):
        raise CorrectiveAuthorizationError("authorization decision is stale")
    unsigned = {
        "schema_version": 1,
        "authorization_type": "ZEUS_CORRECTIVE_WORK_AUTHORIZATION_RECEIPT",
        "authorization_id": request_record["authorization_id"],
        "request_digest": expected,
        "mission_id": request_record["mission_id"],
        "wop_id": request_record["wop_id"],
        "repository": request_record["repository"],
        "baseline": request_record["baseline"],
        "authority": request_record["authority"],
        "scope": list(request_record["scope"]),
        "operator": operator,
        "authority_lease": authority_lease,
        "decision": decision,
        "decided_at": at,
        "expires_at": request_record["expires_at"],
        "state": decision,
        "protected_effect_authorized": decision == "AUTHORIZED",
        "corrective_work_generated": False,
    }
    return {**unsigned, "receipt_digest": digest(unsigned)}


def validate(request_record: dict[str, Any], receipt: dict[str, Any], *, at: datetime | str) -> dict[str, Any]:
    expected = digest({key: value for key, value in request_record.items() if key != "request_digest"})
    if request_record.get("request_digest") != expected:
        raise CorrectiveAuthorizationError("request is not replay-safe")
    if receipt.get("request_digest") != expected:
        raise CorrectiveAuthorizationError("receipt is not bound to request")
    unsigned = {key: value for key, value in receipt.items() if key != "receipt_digest"}
    if receipt.get("receipt_digest") != digest(unsigned):
        raise CorrectiveAuthorizationError("receipt digest mismatch")
    for field in ("authorization_id", "mission_id", "wop_id", "repository", "baseline", "authority", "scope"):
        if receipt.get(field) != request_record.get(field):
            raise CorrectiveAuthorizationError(f"authorization {field} binding mismatch")
    if receipt.get("decision") != "AUTHORIZED" or receipt.get("state") != "AUTHORIZED":
        raise CorrectiveAuthorizationError("corrective work is not authorized")
    if receipt.get("corrective_work_generated") is not False:
        raise CorrectiveAuthorizationError("authorization boundary contains an effect")
    if _instant(receipt["expires_at"]) <= _instant(_timestamp(at)):
        raise CorrectiveAuthorizationError("authorization lease is expired")
    return receipt


class AuthorizationStore:
    """Small atomic durable store with idempotent identical replay."""

    def __init__(self, path: Path | str):
        self.path = Path(path)

    def load(self, authorization_id: str) -> dict[str, Any]:
        path = self.path / f"{authorization_id}.json"
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise CorrectiveAuthorizationError("authorization record is unavailable") from error
        supplied = value.pop("record_digest", None)
        if supplied != digest(value):
            raise CorrectiveAuthorizationError("authorization record digest mismatch")
        value["record_digest"] = supplied
        return value

    def save(self, record: dict[str, Any]) -> tuple[dict[str, Any], bool]:
        data = deepcopy(record)
        data.pop("record_digest", None)
        data["record_digest"] = digest(data)
        self.path.mkdir(parents=True, exist_ok=True)
        target = self.path / f"{data['authorization_id']}.json"
        if target.is_file():
            existing = self.load(data["authorization_id"])
            if existing != data:
                raise CorrectiveAuthorizationError("authorization replay diverged")
            return existing, False
        temporary = target.with_suffix(f".{os.getpid()}.tmp")
        temporary.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        temporary.replace(target)
        return data, True
