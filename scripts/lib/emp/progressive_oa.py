"""Repository-controlled Progressive Operational Alpha package interface."""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

import yaml


PACKAGE = "GH-ZEUS-OA-PROGRESSIVE-001"
PACKAGE_PATH = Path("engineering/work-orders") / PACKAGE


class ProgressiveOAError(ValueError):
    pass


def _root(root: Path) -> Path:
    return root.resolve()


def _package(root: Path) -> Path:
    return _root(root) / PACKAGE_PATH


def _load_yaml(path: Path) -> dict:
    value = yaml.safe_load(path.read_text())
    if not isinstance(value, dict):
        raise ProgressiveOAError(f"invalid mapping: {path}")
    return value


def gates(root: Path) -> list[dict]:
    value = _load_yaml(_package(root) / "gate-specification.yaml")
    result = value.get("gates")
    if not isinstance(result, list) or len(result) != 30:
        raise ProgressiveOAError("progressive gate specification must contain 30 gates")
    return result


def gate(root: Path, gate_id: str) -> dict:
    normalized = gate_id.upper()
    for item in gates(root):
        if item["gate_id"] == normalized:
            return item
    raise ProgressiveOAError(f"unknown Progressive OA gate: {gate_id}")


def state_path(root: Path) -> Path:
    override = os.environ.get("ZEUS_PROGRESSIVE_OA_STATE")
    return Path(override) if override else _package(root) / "runtime" / "state.json"


def load_state(root: Path) -> dict:
    path = state_path(root)
    if not path.exists():
        return {
            "schema_version": 1,
            "package_id": PACKAGE,
            "status": "READY",
            "active_gate": "OA-01",
            "gates": {
                f"OA-{number:02d}": {"state": "PENDING", "acceptance_receipt": None}
                for number in range(1, 31)
            },
        }
    value = json.loads(path.read_text())
    if value.get("package_id") != PACKAGE:
        raise ProgressiveOAError("state package identity mismatch")
    return value


def _write_state(root: Path, value: dict) -> None:
    path = state_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
    temporary.replace(path)


def objective(root: Path, gate_id: str) -> dict:
    item = gate(root, gate_id)
    return {
        "gate_id": item["gate_id"],
        "title": item["title"],
        "mission_objective": item["mission_objective"],
        "capability_being_established": item["capability_being_established"],
        "source_references": item["authoritative_source_references"],
    }


def evidence(root: Path, gate_id: str) -> dict:
    item = gate(root, gate_id)
    base = _package(root)
    return {
        "gate_id": item["gate_id"],
        "requirements": item["required_evidence"],
        "template": str(base / "gates" / gate_id.upper() / "evidence-template.yaml"),
        "runtime_directory": str(base / "runtime" / "evidence" / gate_id.upper()),
    }


def show(root: Path, gate_id: str) -> dict:
    item = dict(gate(root, gate_id))
    item["implementation_procedure"] = str(
        _package(root) / "gates" / gate_id.upper() / "implementation.md"
    )
    item["verification_guide"] = str(
        _package(root) / "gates" / gate_id.upper() / "verification.md"
    )
    return item


def status(root: Path) -> dict:
    value = load_state(root)
    return {
        "package_id": PACKAGE,
        "status": value["status"],
        "active_gate": value["active_gate"],
        "active_gate_state": value["gates"][value["active_gate"]]["state"]
        if value["active_gate"]
        else None,
        "accepted_gates": [
            key for key, item in value["gates"].items() if item["state"] == "ACCEPTED"
        ],
        "declaration_authorized": False,
    }


def next_action(root: Path) -> dict:
    value = status(root)
    state = value["active_gate_state"]
    if value["active_gate"] is None:
        action = "REQUEST_SEPARATE_OA_DECLARATION_AUTHORITY"
    elif state == "PENDING":
        action = f"EXECUTE_{value['active_gate']}"
    elif state == "AWAITING_OPERATOR_VERIFICATION":
        action = f"VERIFY_AND_DECIDE_{value['active_gate']}"
    elif state in ("FAILED", "REJECTED", "INTERRUPTED"):
        action = f"CORRECT_OR_RECOVER_{value['active_gate']}"
    else:
        action = f"RESUME_{value['active_gate']}"
    return {**value, "next_action": action}


def explain(root: Path, gate_id: str) -> dict:
    item = gate(root, gate_id)
    return {
        **objective(root, gate_id),
        "rationale": item["rationale"],
        "success_criteria": item["exact_success_criteria"],
        "manual_verification": str(
            _package(root) / "gates" / gate_id.upper() / "verification.md"
        ),
    }


def _receipt_digest(value: dict) -> str:
    unsigned = {key: item for key, item in value.items() if key != "receipt_digest"}
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def decide(
    root: Path, gate_id: str, decision: str, operator: str | None, at: str | None
) -> tuple[dict, bool]:
    normalized = gate_id.upper()
    value = load_state(root)
    receipt_dir = _package(root) / "runtime" / "decisions" / normalized
    receipt_path = receipt_dir / f"{decision.lower()}.json"
    if receipt_path.exists():
        receipt = json.loads(receipt_path.read_text())
        if receipt["decision"] != decision:
            raise ProgressiveOAError("conflicting decision receipt")
        return receipt, True
    if value["active_gate"] != normalized:
        raise ProgressiveOAError(
            f"{normalized} is not the sole active gate ({value['active_gate']})"
        )
    current = value["gates"][normalized]
    if current["state"] not in ("AWAITING_OPERATOR_VERIFICATION", decision):
        raise ProgressiveOAError(
            f"{normalized} is not awaiting operator verification; state={current['state']}"
        )
    if not operator:
        raise ProgressiveOAError("--operator is required")
    evidence_dir = _package(root) / "runtime" / "evidence" / normalized
    marker = evidence_dir / "VERIFIED"
    if not marker.exists():
        raise ProgressiveOAError(f"verified evidence marker missing: {marker}")
    timestamp = at or datetime.now(timezone.utc).isoformat()
    receipt = {
        "schema_version": 1,
        "package_id": PACKAGE,
        "gate_id": normalized,
        "decision": decision,
        "operator": operator,
        "decided_at": timestamp,
        "evidence_marker_sha256": hashlib.sha256(marker.read_bytes()).hexdigest(),
    }
    receipt["receipt_digest"] = _receipt_digest(receipt)
    receipt_dir.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    current["state"] = decision
    current["acceptance_receipt"] = str(receipt_path) if decision == "ACCEPTED" else None
    if decision == "ACCEPTED":
        number = int(normalized[-2:])
        if number == 30:
            value["active_gate"] = None
            value["status"] = "DECLARATION_PREPARATION_COMPLETE"
        else:
            following = f"OA-{number + 1:02d}"
            value["active_gate"] = following
            value["status"] = "READY"
    else:
        value["status"] = "STOPPED_FAIL_CLOSED"
    _write_state(root, value)
    return receipt, False


def verify_receipt(root: Path, gate_id: str) -> dict:
    normalized = gate_id.upper()
    path = _package(root) / "runtime" / "decisions" / normalized / "accepted.json"
    if not path.exists():
        raise ProgressiveOAError(f"acceptance receipt does not exist: {path}")
    receipt = json.loads(path.read_text())
    if receipt.get("receipt_digest") != _receipt_digest(receipt):
        raise ProgressiveOAError("acceptance receipt integrity failure")
    return {"gate_id": normalized, "receipt": str(path), "integrity": "PASS"}


def controller(root: Path) -> dict:
    """Advance state only across a verified receipt; never implements a gate itself."""
    value = load_state(root)
    active = value["active_gate"]
    if active is None:
        return next_action(root)
    current = value["gates"][active]
    if current["state"] == "PENDING":
        # Execution is intentionally delegated to the gate implementation procedure.
        # A runner records this state only when explicitly invoked under the admitted WOP.
        current["state"] = "IMPLEMENTATION_REQUIRED"
        value["status"] = "ACTIVE"
        _write_state(root, value)
    return next_action(root)
