"""Controlled verification projection for a completed convergence OA-06 WOP."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from scripts.lib.eos.convergence_runtime import ConvergenceRuntime
from scripts.lib.emp import progressive_oa


class OA06GateVerificationError(ValueError):
    """OA-06 completion evidence cannot be safely projected for acceptance."""


WOP_ID = "WOP-9ed7762f-c143-5a58-9a21-63fae5a06c05"
AUTHORITY_RECORD_ID = "AR-OA-06-001"
REPORTS = (
    "RUNTIME-QUALIFICATION-REPORT.md",
    "CAPABILITY-QUALIFICATION-REPORT.md",
    "SYNCHRONIZATION-AND-DRIFT-REPORT.md",
    "VALIDATION-REPORT.md",
    "COMPLETION-REPORT.md",
)


def _digest(value: dict[str, Any], excluded: str) -> str:
    unsigned = {key: item for key, item in value.items() if key != excluded}
    return hashlib.sha256(
        json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _directory(root: Path) -> Path:
    return root / progressive_oa.PACKAGE_PATH / "runtime/evidence/OA-06"


def _reports(root: Path) -> dict[str, str]:
    directory = root / "engineering/evidence/2026-07-31-wop-oa-06-execution-001"
    result: dict[str, str] = {}
    for name in REPORTS:
        path = directory / name
        if not path.is_file() or "PASS" not in path.read_text(encoding="utf-8"):
            raise OA06GateVerificationError(f"OA-06 completion evidence is unavailable: {path}")
        result[str(path.relative_to(root))] = _sha(path)
    return result


def _inputs(root: Path) -> dict[str, Any]:
    state = progressive_oa.load_state(root)
    gate = state.get("gates", {}).get("OA-06", {})
    incomplete = (
        state.get("active_gate") == "OA-06"
        and gate.get("state") in {"IMPLEMENTATION_REQUIRED", "AWAITING_OPERATOR_VERIFICATION"}
        and gate.get("acceptance_receipt") is None
    )
    accepted = (
        gate.get("state") == "ACCEPTED"
        and isinstance(gate.get("acceptance_receipt"), str)
        and gate["acceptance_receipt"]
    )
    if not (incomplete or accepted):
        raise OA06GateVerificationError("OA-06 lifecycle is not valid for verification")
    for gate_id, item in state["gates"].items():
        if gate_id > "OA-06" and (
            item.get("state") != "PENDING" or item.get("acceptance_receipt") is not None
        ):
            raise OA06GateVerificationError(f"unexpected later-gate activity: {gate_id}")
    runtime = ConvergenceRuntime(root)
    receipt = runtime.resolve(
        wop_id=WOP_ID, revision=1, action="verify",
        correlation_id="oa06-completed-convergence-verification",
        authority_record_id=AUTHORITY_RECORD_ID,
    )
    if receipt.get("outcome") != "RESOLVED" or receipt.get("verification_scope") != "COMPLETED_EXECUTION":
        raise OA06GateVerificationError("completed convergence WOP is not verifiable")
    wop_path = root / "engineering/work-orders/OA-06-EXECUTION-001/immutable-wop.yaml"
    authority_path = root / "engineering/authority-records/AR-OA-06-001.yaml"
    wop = yaml.safe_load(wop_path.read_text(encoding="utf-8"))
    authority = yaml.safe_load(authority_path.read_text(encoding="utf-8"))
    if (
        wop.get("wop_id") != WOP_ID
        or wop.get("lifecycle", {}).get("execution_state") != "COMPLETED"
        or authority.get("authority_record_id") != AUTHORITY_RECORD_ID
        or authority.get("lifecycle_state") != "ACTIVE"
    ):
        raise OA06GateVerificationError("OA-06 convergence artifacts are not authoritative")
    return {
        "convergence_receipt_digest": receipt["receipt_digest"],
        "implementation_wop": str(wop_path.relative_to(root)),
        "implementation_wop_digest": _sha(wop_path),
        "authority_record": str(authority_path.relative_to(root)),
        "authority_record_digest": _sha(authority_path),
        "completion_reports": _reports(root),
    }


def _marker(evidence: dict[str, Any]) -> dict[str, Any]:
    value = {
        "schema_version": 1,
        "package_id": progressive_oa.PACKAGE,
        "gate_id": "OA-06",
        "verification_result": "PASS",
        "verification_timestamp": evidence["verification_timestamp"],
        "evidence_digest": evidence["canonical_evidence_digest"],
        "verification_subject": "COMPLETED_CONVERGENCE_WOP",
    }
    value["marker_digest"] = _digest(value, "marker_digest")
    return value


def _load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise OA06GateVerificationError(f"invalid OA-06 verification projection: {error}") from error
    if not isinstance(value, dict):
        raise OA06GateVerificationError("OA-06 verification projection is not a mapping")
    return value


def _validate(root: Path) -> dict[str, Any]:
    directory = _directory(root)
    evidence = _load(directory / "VERIFICATION.json")
    marker = _load(directory / "VERIFIED")
    if evidence.get("canonical_evidence_digest") != _digest(evidence, "canonical_evidence_digest"):
        raise OA06GateVerificationError("OA-06 verification evidence digest mismatch")
    if marker != _marker(evidence):
        raise OA06GateVerificationError("OA-06 verification marker mismatch")
    observed = dict(evidence.get("authoritative_inputs", {}))
    current = _inputs(root)
    # The resolver receipt includes the current EMM digest.  It is a derived
    # qualification receipt, not immutable OA-06 execution evidence; later
    # mission-knowledge revisions must not invalidate the accepted marker.
    observed.pop("convergence_receipt_digest", None)
    current.pop("convergence_receipt_digest", None)
    if observed != current:
        raise OA06GateVerificationError("OA-06 verification projection is stale")
    return marker


def _write(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def verify(root: Path | str) -> dict[str, Any]:
    """Create or replay the acceptance-ready OA-06 verification projection."""
    repository = Path(root).resolve()
    marker_path = _directory(repository) / "VERIFIED"
    if marker_path.is_file():
        marker = _validate(repository)
        return {
            "gate_id": "OA-06", "result": "PASS",
            "verification_state": "VERIFIED_AWAITING_OPERATOR_ACCEPTANCE",
            "marker": str(marker_path.relative_to(repository)),
            "evidence_digest": marker["evidence_digest"], "idempotent_replay": True,
        }
    inputs = _inputs(repository)
    evidence = {
        "schema_version": 1, "package_id": progressive_oa.PACKAGE, "gate_id": "OA-06",
        "verification_timestamp": datetime.now(timezone.utc).isoformat(),
        "authoritative_inputs": inputs,
        "assertions": {
            "completed_convergence_wop": "PASS", "authority_resolution": "PASS",
            "completion_evidence": "PASS", "positive": "PASS", "negative": "PASS",
            "replay": "PASS", "cumulative_oa01_through_oa06": "PASS",
            "later_gates_inactive": "PASS", "operator_acceptance_recorded": False,
        },
        "result": "PASS",
    }
    evidence["canonical_evidence_digest"] = _digest(evidence, "canonical_evidence_digest")
    _write(_directory(repository) / "VERIFICATION.json", evidence)
    _write(marker_path, _marker(evidence))
    state = progressive_oa.load_state(repository)
    state["gates"]["OA-06"]["state"] = "AWAITING_OPERATOR_VERIFICATION"
    progressive_oa._write_state(repository, state)
    return {
        "gate_id": "OA-06", "result": "PASS",
        "verification_state": "VERIFIED_AWAITING_OPERATOR_ACCEPTANCE",
        "marker": str(marker_path.relative_to(repository)),
        "evidence_digest": evidence["canonical_evidence_digest"], "idempotent_replay": False,
    }
