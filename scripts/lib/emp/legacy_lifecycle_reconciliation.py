"""Bounded reconciliation for the one accepted pre-Mission-Contract run.

This is a derived execution projection, not a Mission Contract or a second
closeout authority.  It is deliberately identity-bound and fails closed when
the historical acceptance/publication facts are not independently present.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any, Mapping

from scripts.lib.emp.production_execution import atomic_write, load_json


MISSION = "MISSION-BETA-562F443E16C69401"
EXECUTION = "EXECUTION-START-5a6fec74-3c4b-5271-8c96-4cc89fe8855e"
WOP = "WOP-BETA-562F443E16C69401"
P5_PUBLICATION_BASELINE = "70f6671239f9d4c561960a87216765eef758a949"
REPORT = "engineering/evidence/operation-beta/p5-g6-controlled-active-execution-foundation-completion-report.md"
ACCEPTANCE = ".zeus/runtime/acceptance/P5-G6/P5-G6-RECONCILIATION-46fbd9c748e87d85.json"
RECEIPT_DIR = "legacy-lifecycle-reconciliations"


class LegacyReconciliationError(ValueError):
    pass


def _digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


def _valid_record(path: Path) -> dict[str, Any]:
    value = load_json(path)
    supplied = value.get("record_digest")
    if supplied != _digest({key: item for key, item in value.items() if key != "record_digest"}):
        raise LegacyReconciliationError("P5_G6_ACCEPTANCE_RECORD_DIGEST_MISMATCH")
    if value.get("record_type") != "ACCEPTANCE_RECONCILIATION":
        raise LegacyReconciliationError("P5_G6_ACCEPTANCE_RECORD_TYPE_INVALID")
    return value


def _git(root: Path, *args: str) -> str:
    result = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, check=False)
    if result.returncode:
        raise LegacyReconciliationError(result.stderr.strip() or "git verification failed")
    return result.stdout.strip()


def inspect(root: Path | str, runtime: Path | str, *, transaction: Mapping[str, Any] | None = None,
            monitoring: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Verify the exact historical facts and return a non-mutating disposition."""
    root, runtime = Path(root).resolve(), Path(runtime).resolve()
    report = root / REPORT
    acceptance = root / ACCEPTANCE
    if not report.is_file() or not acceptance.is_file():
        raise LegacyReconciliationError("HISTORICAL_ACCEPTANCE_EVIDENCE_MISSING")
    text = report.read_text(encoding="utf-8")
    required = {
        "P5_G6_OPERATOR_ACCEPTANCE": "ACCEPTED",
        "TRUE_ACTIVE_P5_G6_DEMONSTRATION": "PASS",
        "P5_G6_DISPOSITION": "ACCEPTED",
        "PUBLICATION_AUTHORIZED_BY_THIS_ACCEPTANCE": "NO",
        "P5_G7_AUTHORIZED_BY_THIS_ACCEPTANCE": "NO",
    }
    fields = {line.split("=", 1)[0]: line.split("=", 1)[1] for line in text.splitlines() if "=" in line}
    if any(fields.get(key) != expected for key, expected in required.items()):
        raise LegacyReconciliationError("HISTORICAL_ACCEPTANCE_EVIDENCE_CONFLICT")
    accepted = _valid_record(acceptance)
    if (accepted.get("mission_id"), accepted.get("execution_id"), accepted.get("wop_id"), accepted.get("gate_id")) != (MISSION, EXECUTION, WOP, "P5-G6"):
        raise LegacyReconciliationError("HISTORICAL_ACCEPTANCE_BINDING_MISMATCH")
    if accepted.get("new_operator_decision") is not False or accepted.get("publication_authorized") is not False:
        raise LegacyReconciliationError("HISTORICAL_ACCEPTANCE_AUTHORITY_ESCALATION")
    if _git(root, "cat-file", "-t", P5_PUBLICATION_BASELINE) != "commit" or _git(root, "merge-base", "--is-ancestor", P5_PUBLICATION_BASELINE, "HEAD") != "":
        raise LegacyReconciliationError("P5_G6_PUBLISHED_BASELINE_NOT_VERIFIED")
    from scripts.lib.emp.mission_contract_discovery import discover
    contracts = discover(root, MISSION)
    if contracts.get("applicable_candidate_count") != 0:
        raise LegacyReconciliationError("LEGACY_CONTRACT_CARDINALITY_NOT_ZERO")
    from scripts.lib.eos import operational_beta
    authority = operational_beta.authority(root)
    if authority.get("operation_id") != "OPERATION-BETA" or authority.get("current_platform_mission", {}).get("mission_id") != "BETA-04":
        raise LegacyReconciliationError("CURRENT_BETA_AUTHORITY_UNRESOLVED")
    if transaction and transaction.get("execution_id") != EXECUTION:
        raise LegacyReconciliationError("EXECUTION_IDENTITY_MISMATCH")
    if monitoring and (monitoring.get("mission_id"), monitoring.get("wop_id"), monitoring.get("execution_id")) != (MISSION, WOP, EXECUTION):
        raise LegacyReconciliationError("MONITORING_IDENTITY_MISMATCH")
    if monitoring and monitoring.get("repository_work_started") is True:
        raise LegacyReconciliationError("REPOSITORY_WORK_PENDING")
    return {
        "result": "PASS", "disposition": "RECONCILED_HISTORICAL", "mission_id": MISSION,
        "wop_id": WOP, "execution_id": EXECUTION, "gate_id": "P5-G6",
        "mission_contract_cardinality": 0, "mission_contract_created": False,
        "historical_acceptance": "ACCEPTED", "historical_publication": "VERIFIED",
        "native_beta_binding": "NONE", "repository_work_pending": False,
        "acceptance_record": str(acceptance), "publication_baseline": P5_PUBLICATION_BASELINE,
        "current_operation": "OPERATION-BETA", "current_platform_context": "BETA-04",
        "current_platform_next_action": authority.get("next_authorized_action"),
        "new_operator_decision": False, "read_only": True,
    }


def overlay(value: Mapping[str, Any], disposition: Mapping[str, Any]) -> dict[str, Any]:
    """Remove stale active-work instructions from a verified projection."""
    if disposition.get("disposition") != "RECONCILED_HISTORICAL":
        return dict(value)
    result = dict(value)
    result.update({
        "execution_state": "RECONCILED_HISTORICAL", "execution_liveness": "STOPPED",
        "provider_liveness": "STOPPED", "execution_monitoring_active": False,
        "progress_state": "RECONCILED", "current_work_position": "P5-G6:ACCEPTED_HISTORICAL",
        "mission_work_state": "STARTED", "repository_work_state": "NOT_STARTED",
        "active_work_units": [], "remaining_work_units": [],
        "completed_work_units": ["P5-G6:CONTROLLED_MISSION_WORK"],
        "next_authorized_action": "OPERATOR_REVIEW_LEGACY_LIFECYCLE_RECONCILIATION",
        "legacy_reconciliation": dict(disposition),
    })
    return result


def reconcile(root: Path | str, runtime: Path | str, *, transaction: Mapping[str, Any],
              monitoring: Mapping[str, Any] | None, approve: bool = False) -> dict[str, Any]:
    """Persist one idempotent receipt; host mutation remains approval-gated."""
    disposition = inspect(root, runtime, transaction=transaction, monitoring=monitoring)
    receipt_id = "LEGACY-RECON-" + _digest({"mission_id": MISSION, "execution_id": EXECUTION, "disposition": disposition["disposition"]})[:24]
    path = Path(runtime).resolve() / RECEIPT_DIR / f"{receipt_id}.json"
    if not approve:
        return {"result": "PASS", "replay": "NOT_PERSISTED", "receipt": None,
                "receipt_id": None, "receipt_path": None,
                "projection": overlay({}, disposition), "read_only": True,
                "approved_persistence_requested": False}
    if path.is_file():
        existing = load_json(path)
        if existing.get("receipt_digest") != _digest({key: item for key, item in existing.items() if key != "receipt_digest"}):
            raise LegacyReconciliationError("LEGACY_RECONCILIATION_RECEIPT_DIGEST_MISMATCH")
        return {"result": "PASS", "replay": "IDEMPOTENT", "receipt": existing,
                "receipt_id": existing.get("reconciliation_id"), "receipt_path": str(path),
                "projection": overlay({}, disposition), "read_only": False,
                "approved_persistence_requested": True}
    receipt = {"schema_version": 1, "record_type": "LEGACY_LIFECYCLE_RECONCILIATION", "reconciliation_id": receipt_id,
               "mission_id": MISSION, "wop_id": WOP, "execution_id": EXECUTION, "disposition": disposition["disposition"],
               "source_acceptance_record": disposition["acceptance_record"], "publication_baseline": P5_PUBLICATION_BASELINE,
               "mission_contract_created": False, "new_operator_decision": False, "runtime_mutation": "APPROVAL_REQUIRED",
               "replay": "IDEMPOTENT"}
    receipt["receipt_digest"] = _digest(receipt)
    path.parent.mkdir(parents=True, exist_ok=True)
    atomic_write(path, receipt)
    return {"result": "PASS", "replay": "NOT_REPLAYED", "receipt": receipt,
            "receipt_id": receipt_id, "receipt_path": str(path),
            "projection": overlay({}, disposition), "read_only": False,
            "approved_persistence_requested": True}
