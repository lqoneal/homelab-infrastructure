"""Durable, deterministic, fail-closed authorization after execution start."""
from __future__ import annotations

import json
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from scripts.lib.emp.authority_resolution import digest


AUTHORIZATION_STATES = ("PENDING", "AUTHORIZED", "DENIED", "EXPIRED", "REVOKED")


class ExecutionAuthorizationError(ValueError):
    """Authorization input, state, binding, or transition is invalid."""


class ExecutionAuthorizationStore:
    def __init__(self, directory: Path | str):
        self.directory = Path(directory)

    def path(self, execution_id: str) -> Path:
        return self.directory / f"{execution_id}.json"

    def load(self, execution_id: str) -> dict[str, Any]:
        try:
            value = json.loads(self.path(execution_id).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise ExecutionAuthorizationError(f"invalid authorization state: {error}") from error
        supplied = value.pop("state_digest", None)
        if supplied != digest(value):
            raise ExecutionAuthorizationError("authorization state digest mismatch")
        value["state_digest"] = supplied
        return value

    def save(self, value: dict[str, Any]) -> Path:
        data = deepcopy(value)
        data.pop("state_digest", None)
        data["state_digest"] = digest(data)
        self.directory.mkdir(parents=True, exist_ok=True)
        temporary = self.path(data["execution_id"]).with_suffix(".tmp")
        temporary.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        temporary.replace(self.path(data["execution_id"]))
        return self.path(data["execution_id"])


def _utc(value: datetime | str) -> datetime:
    if isinstance(value, str):
        value = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if value.tzinfo is None:
        raise ExecutionAuthorizationError("authorization timestamp must include timezone")
    return value.astimezone(timezone.utc)


def _time(value: datetime | str) -> str:
    return _utc(value).isoformat().replace("+00:00", "Z")


def request(*, execution_id: str, mission_id: str, wop_id: str, repository: str,
            authority: str, operator: str, expires_at: datetime | str) -> dict[str, Any]:
    if not all((execution_id, mission_id, wop_id, repository, authority, operator)):
        raise ExecutionAuthorizationError("authorization request identity is incomplete")
    unsigned = {
        "schema_version": 1,
        "authorization_type": "ZEUS_EXECUTION_AUTHORIZATION_REQUEST",
        "execution_id": execution_id,
        "mission_id": mission_id,
        "wop_id": wop_id,
        "repository": repository,
        "authority": authority,
        "operator": operator,
        "requested_at": _time(datetime.now(timezone.utc)),
        "expires_at": _time(expires_at),
        "state": "PENDING",
    }
    return {**unsigned, "request_digest": digest(unsigned)}


def decide(request_record: dict[str, Any], *, decision: str, authority_lease: str,
           operator: str, at: datetime | str) -> dict[str, Any]:
    decision = decision.upper()
    if decision not in {"AUTHORIZED", "DENIED"}:
        raise ExecutionAuthorizationError("authorization decision is invalid")
    expected = digest({key: value for key, value in request_record.items() if key != "request_digest"})
    if request_record.get("request_digest") != expected:
        raise ExecutionAuthorizationError("authorization request replay diverged")
    if not operator or not authority_lease:
        raise ExecutionAuthorizationError("authorization decision identity or lease is absent")
    unsigned = {
        "schema_version": 1,
        "authorization_type": "ZEUS_EXECUTION_AUTHORIZATION_RECEIPT",
        "request_digest": expected,
        "execution_id": request_record["execution_id"],
        "mission_id": request_record["mission_id"],
        "wop_id": request_record["wop_id"],
        "repository": request_record["repository"],
        "authority": request_record["authority"],
        "authority_lease": authority_lease,
        "operator": operator,
        "decision": decision,
        "decided_at": _time(at),
        "expires_at": request_record["expires_at"],
        "state": decision,
    }
    return {**unsigned, "receipt_digest": digest(unsigned)}


def validate(request_record: dict[str, Any], receipt: dict[str, Any], *, at: datetime | str) -> dict[str, Any]:
    expected = digest({key: value for key, value in request_record.items() if key != "request_digest"})
    if request_record.get("request_digest") != expected:
        raise ExecutionAuthorizationError("authorization request is not replay-safe")
    if receipt.get("request_digest") != expected:
        raise ExecutionAuthorizationError("authorization receipt is not bound to request")
    unsigned = {key: value for key, value in receipt.items() if key != "receipt_digest"}
    if receipt.get("receipt_digest") != digest(unsigned):
        raise ExecutionAuthorizationError("authorization receipt digest mismatch")
    for field in ("execution_id", "mission_id", "wop_id", "repository", "authority"):
        if receipt.get(field) != request_record.get(field):
            raise ExecutionAuthorizationError(f"authorization {field} binding mismatch")
    if receipt.get("decision") != "AUTHORIZED" or receipt.get("state") != "AUTHORIZED":
        raise ExecutionAuthorizationError("execution authorization is not granted")
    if _utc(receipt["expires_at"]) <= _utc(at):
        raise ExecutionAuthorizationError("authorization lease is expired")
    return receipt


def transition(state: dict[str, Any], target: str, *, at: datetime | str, reason: str = "") -> dict[str, Any]:
    target = target.upper()
    if target not in AUTHORIZATION_STATES:
        raise ExecutionAuthorizationError("unknown authorization state")
    current = state.get("state")
    allowed = {"PENDING": {"AUTHORIZED", "DENIED", "EXPIRED"}, "AUTHORIZED": {"REVOKED", "EXPIRED"},
               "DENIED": set(), "EXPIRED": set(), "REVOKED": set()}
    if target not in allowed.get(current, set()):
        raise ExecutionAuthorizationError(f"invalid authorization transition {current} -> {target}")
    updated = deepcopy(state)
    updated["state"] = target
    updated["updated_at"] = _time(at)
    updated["transition_reason"] = reason or target
    return updated
