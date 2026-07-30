"""Foundational repository record mechanics for the Progressive runtime.

This module owns no Progressive authority.  It provides deterministic file,
serialization, digest, and state-transition mechanics consumed by the
canonical runtime and re-exported by the temporary compatibility adapter.
It must not import a Progressive runtime layer or compatibility module.
"""

from __future__ import annotations

import hashlib
import json
import os
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


def _marker_binding(root: Path, gate_id: str) -> tuple[Path, dict]:
    marker = _package(root) / "runtime" / "evidence" / gate_id / "VERIFIED"
    if not marker.is_file():
        raise ProgressiveOAError(f"verified evidence marker missing: {marker}")
    try:
        value = json.loads(marker.read_text())
    except (json.JSONDecodeError, OSError) as error:
        raise ProgressiveOAError(f"verified evidence marker invalid: {error}") from error
    if not isinstance(value, dict):
        raise ProgressiveOAError("verified evidence marker invalid: expected mapping")
    if value.get("package_id") != PACKAGE or value.get("gate_id") != gate_id:
        raise ProgressiveOAError("verified evidence marker package or gate mismatch")
    if value.get("verification_result") != "PASS":
        raise ProgressiveOAError("verified evidence marker result is not PASS")
    evidence_digest = value.get("evidence_digest")
    marker_digest = value.get("marker_digest")
    if not isinstance(evidence_digest, str) or not isinstance(marker_digest, str):
        raise ProgressiveOAError("verified evidence marker binding is incomplete")
    unsigned = {key: item for key, item in value.items() if key != "marker_digest"}
    calculated_marker_digest = hashlib.sha256(
        json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    if marker_digest != calculated_marker_digest:
        raise ProgressiveOAError("verified evidence marker digest mismatch")
    evidence_path = marker.parent / "VERIFICATION.json"
    if not evidence_path.is_file():
        raise ProgressiveOAError("verified evidence record missing")
    try:
        evidence = json.loads(evidence_path.read_text())
    except (json.JSONDecodeError, OSError) as error:
        raise ProgressiveOAError(f"verified evidence record invalid: {error}") from error
    digest_field = (
        "canonical_evidence_digest"
        if "canonical_evidence_digest" in evidence
        else "evidence_digest"
    )
    unsigned_evidence = {
        key: item for key, item in evidence.items() if key != digest_field
    }
    calculated_evidence_digest = hashlib.sha256(
        json.dumps(
            unsigned_evidence, sort_keys=True, separators=(",", ":")
        ).encode()
    ).hexdigest()
    if (
        evidence.get(digest_field) != calculated_evidence_digest
        or evidence_digest != calculated_evidence_digest
    ):
        raise ProgressiveOAError("verified evidence digest mismatch")
    return marker, value


def _resolve_receipt_path(
    root: Path, locator: str, gate_id: str | None = None
) -> Path:
    path = Path(locator)
    if not path.is_absolute() and path.name == locator and gate_id:
        path = (
            _package(root) / "runtime" / "decisions" / gate_id / path
        )
    elif not path.is_absolute():
        path = _root(root) / path
    path = path.resolve()
    decision_root = (_package(root) / "runtime" / "decisions").resolve()
    if decision_root not in path.parents:
        raise ProgressiveOAError("acceptance receipt path escapes decision history")
    return path


def _is_superseded(root: Path, gate_id: str, path: Path, receipt: dict) -> bool:
    directory = _package(root) / "runtime" / "decisions" / gate_id
    for candidate in sorted(directory.glob("*.json")):
        if candidate.resolve() == path.resolve():
            continue
        try:
            record = json.loads(candidate.read_text())
        except (json.JSONDecodeError, OSError):
            continue
        if record.get("decision") != "SUPERSEDED":
            continue
        historical = record.get("historical_receipt")
        digest = record.get("historical_receipt_digest")
        if (
            historical in (path.name, str(path), str(path.relative_to(directory)))
            or digest == receipt.get("receipt_digest")
        ):
            return True
    return False


def _validate_receipt_bindings(
    root: Path,
    gate_id: str,
    path: Path,
    receipt: dict,
    marker_path: Path,
    marker: dict,
    operator: str | None = None,
) -> None:
    if receipt.get("receipt_digest") != _receipt_digest(receipt):
        raise ProgressiveOAError("acceptance receipt integrity failure")
    if (
        receipt.get("decision") != "ACCEPTED"
        or receipt.get("package_id") != PACKAGE
        or receipt.get("gate_id") != gate_id
    ):
        raise ProgressiveOAError("acceptance receipt package, gate, or decision mismatch")
    if receipt.get("schema_version", 1) >= 2:
        manifest = _package(root) / "MANIFEST.sha256"
        if (
            not manifest.is_file()
            or receipt.get("package_manifest_sha256")
            != hashlib.sha256(manifest.read_bytes()).hexdigest()
        ):
            raise ProgressiveOAError("acceptance receipt package manifest mismatch")
    if _is_superseded(root, gate_id, path, receipt):
        raise ProgressiveOAError("acceptance receipt is superseded")
    if operator is not None and receipt.get("operator") != operator:
        raise ProgressiveOAError("acceptance receipt operator mismatch")
    if receipt.get("evidence_marker_sha256") != hashlib.sha256(
        marker_path.read_bytes()
    ).hexdigest():
        raise ProgressiveOAError("acceptance receipt marker file digest mismatch")
    if (
        "evidence_digest" in receipt
        and receipt.get("evidence_digest") != marker.get("evidence_digest")
    ):
        raise ProgressiveOAError("acceptance receipt evidence digest mismatch")
    if (
        "marker_digest" in receipt
        and receipt.get("marker_digest") != marker.get("marker_digest")
    ):
        raise ProgressiveOAError("acceptance receipt marker digest mismatch")


def _persist_receipt(path: Path, receipt: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = (json.dumps(receipt, indent=2, sort_keys=True) + "\n").encode()
    try:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    except FileExistsError:
        existing = path.read_bytes()
        if existing != encoded:
            raise ProgressiveOAError("acceptance receipt identity collision")
        return
    with os.fdopen(descriptor, "wb") as stream:
        stream.write(encoded)
        stream.flush()
        os.fsync(stream.fileno())


def _advance_after_acceptance(value: dict, normalized: str, receipt_path: Path) -> None:
    current = value["gates"][normalized]
    current["state"] = "ACCEPTED"
    current["acceptance_receipt"] = str(receipt_path)
    number = int(normalized[-2:])
    if number == 30:
        value["active_gate"] = None
        value["status"] = "DECLARATION_PREPARATION_COMPLETE"
    else:
        value["active_gate"] = f"OA-{number + 1:02d}"
        value["status"] = "READY"


def _validate_replay_lifecycle(value: dict, normalized: str) -> None:
    """Require a coherent current lifecycle before consulting receipt evidence."""
    try:
        number = int(normalized[-2:])
    except (TypeError, ValueError):
        raise ProgressiveOAError("runtime lifecycle binding is inconsistent")
    active = value.get("active_gate")
    if active is None:
        if number != 30 or value.get("status") != "DECLARATION_PREPARATION_COMPLETE":
            raise ProgressiveOAError("runtime lifecycle binding is inconsistent")
        return
    try:
        active_number = int(active[-2:])
    except (AttributeError, TypeError, ValueError):
        raise ProgressiveOAError("runtime lifecycle binding is inconsistent")
    if active not in value.get("gates", {}) or active_number <= number:
        raise ProgressiveOAError("runtime lifecycle binding is inconsistent")
    for intermediate in range(number + 1, active_number):
        item = value["gates"].get(f"OA-{intermediate:02d}", {})
        if (
            item.get("state") != "ACCEPTED"
            or not isinstance(item.get("acceptance_receipt"), str)
            or not item["acceptance_receipt"]
        ):
            raise ProgressiveOAError("runtime lifecycle binding is inconsistent")

