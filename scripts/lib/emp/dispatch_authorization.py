"""Deterministic, fail-closed human dispatch-authorization receipts."""
from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from scripts.lib.emp.agent_qualification import registry as agent_registry
from scripts.lib.eos import mission_knowledge


def _digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def request(repository: Path | str, mission_id: str = "OA-14") -> dict[str, Any]:
    root = Path(repository).resolve()
    recommendation = mission_knowledge.recommend(root)
    if recommendation.get("result") != "PASS" or recommendation.get("recommended_mission") != mission_id:
        raise ValueError("dispatch authorization requires the requested mission to be eligible")
    agents = [item for item in agent_registry(root).get("agents", [])
              if item.get("active") is True and item.get("qualification_status") == "QUALIFIED"]
    if len(agents) != 1:
        raise ValueError("dispatch authorization requires exactly one qualified agent")
    model = mission_knowledge.load(root)
    mission = next(item for item in model["missions"] if item["mission_id"] == mission_id)
    head = subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip()
    unsigned = {
        "schema_version": 1,
        "authorization_type": "HUMAN_DISPATCH_AUTHORIZATION_REQUEST",
        "mission_id": mission_id,
        "selected_execution_agent": agents[0]["agent_id"],
        "required_capabilities": sorted(mission["capability_prerequisites"]),
        "repository_identity": str(root),
        "repository_head": head,
        "authority_source": mission_knowledge.PATH,
        "operator_authorization_required": True,
        "execution_started": False,
        "protected_effect_authorized": False,
        "expires_at": None,
    }
    return {**unsigned, "request_digest": _digest(unsigned)}


def authorize(request_record: dict[str, Any], operator: str, expires_at: str) -> dict[str, Any]:
    if not operator or not expires_at or request_record.get("execution_started") or request_record.get("protected_effect_authorized"):
        raise ValueError("authorization request is malformed or already has an effect")
    unsigned = {
        "schema_version": 1,
        "authorization_type": "HUMAN_DISPATCH_AUTHORIZATION_RECEIPT",
        "request_digest": request_record.get("request_digest"),
        "mission_id": request_record.get("mission_id"),
        "operator": operator,
        "expires_at": expires_at,
        "execution_started": False,
        "protected_effect_authorized": True,
    }
    if not unsigned["request_digest"] or request_record.get("request_digest") != _digest({key: value for key, value in request_record.items() if key != "request_digest"}):
        raise ValueError("authorization request digest is invalid")
    return {**unsigned, "receipt_digest": _digest(unsigned)}


def reject(request_record: dict[str, Any], reason: str) -> dict[str, Any]:
    if not reason or request_record.get("execution_started") or request_record.get("protected_effect_authorized"):
        raise ValueError("rejection request is malformed or already has an effect")
    unsigned = {"schema_version": 1, "authorization_type": "HUMAN_DISPATCH_REJECTION_RECEIPT", "request_digest": request_record.get("request_digest"), "mission_id": request_record.get("mission_id"), "reason": reason, "execution_started": False, "protected_effect_authorized": False}
    return {**unsigned, "receipt_digest": _digest(unsigned)}


def validate(repository: Path | str, request_record: dict[str, Any], receipt: dict[str, Any]) -> dict[str, Any]:
    root = Path(repository).resolve()
    expected_request_digest = _digest({key: value for key, value in request_record.items() if key != "request_digest"})
    if request_record.get("request_digest") != expected_request_digest:
        raise ValueError("authorization request replay diverged")
    if request_record.get("repository_identity") != str(root) or request_record.get("authority_source") != mission_knowledge.PATH:
        raise ValueError("authorization request repository or authority binding is invalid")
    if receipt.get("request_digest") != expected_request_digest or receipt.get("execution_started") or not receipt.get("protected_effect_authorized"):
        raise ValueError("authorization receipt is not bound or contains an invalid effect")
    unsigned = {key: value for key, value in receipt.items() if key != "receipt_digest"}
    if receipt.get("receipt_digest") != _digest(unsigned):
        raise ValueError("authorization receipt digest is invalid")
    if datetime.fromisoformat(receipt["expires_at"].replace("Z", "+00:00")) <= datetime.now(timezone.utc):
        raise ValueError("authorization receipt is expired")
    return receipt
