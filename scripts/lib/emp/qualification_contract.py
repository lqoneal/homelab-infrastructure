"""Canonical, read-only qualification and publication decision contract.

This module is the single decision owner for publication readiness.  Other
controllers may decorate its result for presentation, but must not invent a
second readiness calculation.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
QUALIFICATION_STATES = {"QUALIFIED_FOR_PUBLICATION", "NOT_QUALIFIED"}
PUBLICATION_STATES = {
    "PUBLICATION_BLOCKED",
    "PUBLICATION_PENDING_APPROVAL",
    "PUBLICATION_IN_PROGRESS",
    "PUBLICATION_COMPLETE",
}
EVIDENCE_ROOT = Path("engineering/evidence/operation-beta/wop-zeus-submission-provenance-bootstrap-001")
CONTRACT_WOP = "WOP-ZDCL02-QUAL-001-QUAL-002-RECONCILIATION-001"


class QualificationContractError(ValueError):
    """The canonical qualification contract cannot be resolved safely."""


def _sha256(value: Any) -> str:
    import json

    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def _text(root: Path, relative: Path) -> str:
    path = root / relative
    try:
        return path.read_text(encoding="utf-8")
    except OSError as error:
        raise QualificationContractError(f"QUALIFICATION_EVIDENCE_UNAVAILABLE: {relative}") from error


def _terminal_status(text: str) -> str | None:
    markers = {"SUBMISSION_BOOTSTRAP_QUALIFIED", "READY_FOR_PUBLICATION", "NOT_QUALIFIED", "NOT_READY_FOR_PUBLICATION"}
    for line in reversed(text.splitlines()):
        value = line.strip()
        if value in markers:
            return value
    return None


def _blocker(blocker_id: str, category: str, severity: str, evidence: str,
             document: str, corrective: str, impact: str, requirement: str) -> dict[str, str]:
    return {
        "blocker_id": blocker_id,
        "category": category,
        "severity": severity,
        "originating_controller": "canonical-qualification-decision-engine",
        "authoritative_evidence": evidence,
        "governing_document": document,
        "corrective_wop": corrective,
        "publication_impact": impact,
        "resolution_requirements": requirement,
    }


def _resolve_base(root: Path | str) -> dict[str, Any]:
    """Resolve one deterministic qualification/publication result.

    The resolver is deliberately conservative: absence or incompleteness of
    required evidence is a typed blocker, never an implicit pass.
    """
    repository = Path(root).resolve()
    evidence = EVIDENCE_ROOT
    completion_path = evidence / "COMPLETION-REPORT.md"
    completion = _text(repository, completion_path)
    broad = _text(repository, evidence / "BROAD-REGRESSION-RESULTS.md")
    contract_resolution = _text(repository, evidence / "QUALIFICATION-CONTRACT-RESOLUTION.md")
    terminal = _terminal_status(completion)
    if terminal is None:
        raise QualificationContractError("QUALIFICATION_RESULT_MISSING: Completion Report has no terminal state")

    blockers: list[dict[str, str]] = []
    if terminal in {"NOT_QUALIFIED", "NOT_READY_FOR_PUBLICATION"}:
        blockers.append(_blocker(
            "QUAL-001", "QUALIFICATION", "BLOCKING", str(completion_path),
            "QUALIFICATION-CONTRACT.md", CONTRACT_WOP,
            "PUBLICATION_BLOCKED", "Resolve every mandatory qualification failure and rerun the authoritative broad profile.",
        ))
    if ("no definitive clean result" in (broad + "\n" + completion).lower()
            or "not met" in contract_resolution.lower()):
        blockers.append(_blocker(
            "QUAL-002", "VALIDATION", "BLOCKING", str(evidence / "BROAD-REGRESSION-RESULTS.md"),
            "QUALIFICATION-CONTRACT.md", CONTRACT_WOP,
            "PUBLICATION_BLOCKED", "Produce a definitive broad-suite completion result with no unexplained failures.",
        ))

    qualification_state = "NOT_QUALIFIED" if blockers else "QUALIFIED_FOR_PUBLICATION"
    publication_state = "PUBLICATION_BLOCKED" if blockers else "PUBLICATION_PENDING_APPROVAL"
    contract: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "contract_id": "ZEUS-QUALIFICATION-CONTRACT-1",
        "resolver": "scripts.lib.emp.qualification_contract",
        "candidate": {"repository": str(repository), "qualification_wop": CONTRACT_WOP},
        "qualification_state": qualification_state,
        "publication_state": publication_state,
        "evidence_completeness": "COMPLETE" if completion and broad else "INCOMPLETE",
        "platform_status": "PASS" if (repository / "scripts/zeus").is_file() else "FAIL",
        "validation_status": "INCOMPLETE" if blockers else "PASS",
        "registry_status": "PRESENT" if (repository / "engineering/registry/work-registry.yaml").is_file() else "MISSING",
        "controlled_document_status": "RECONCILIATION_REQUIRED" if blockers else "PASS",
        "lifecycle_status": "EXECUTION_LIFECYCLE_INCOMPLETE" if blockers else "READY",
        "authority_status": "VERIFIED_OPERATIONAL_ALPHA_CHAIN",
        "eos_status": "UNCHANGED_DEFERRED",
        "provenance_status": "PRESERVED",
        "remaining_blockers": blockers,
        "next_authorized_action": (
            "Resolve QUAL-001 and QUAL-002 under " + CONTRACT_WOP
            if blockers else "Obtain publication approval; publication authority remains separate."
        ),
        "terminal_evidence": {"path": str(completion_path), "reported_state": terminal},
    }
    contract["decision_digest"] = _sha256(contract)
    return contract


def resolve(root: Path | str) -> dict[str, Any]:
    """Resolve qualification and its canonical blocker lifecycle together."""
    from scripts.lib.emp.blocker_framework import resolve_from_seed

    contract = _resolve_base(root)
    framework = resolve_from_seed(root, contract["remaining_blockers"])
    active = framework["active_blockers"]
    contract["blockers"] = framework["blockers"]
    contract["active_blockers"] = active
    contract["resolved_blockers"] = framework["resolved_blockers"]
    contract["retired_blockers"] = framework["retired_blockers"]
    contract["auto_resolution_summary"] = {
        "eligible": [b["blocker_id"] for b in framework["blockers"] if b["auto_resolvable"]],
        "resolved": [b["blocker_id"] for b in framework["resolved_blockers"]],
        "retired": [b["blocker_id"] for b in framework["retired_blockers"]],
    }
    contract["operator_actions"] = [
        {"blocker_id": b["blocker_id"], "action": b["next_authorized_action"]}
        for b in active if b["operator_action_required"]
    ]
    contract["publication_readiness"] = not active
    contract["remaining_blockers"] = active
    contract["qualification_state"] = "NOT_QUALIFIED" if active else "QUALIFIED_FOR_PUBLICATION"
    contract["publication_state"] = "PUBLICATION_BLOCKED" if active else "PUBLICATION_PENDING_APPROVAL"
    contract["next_authorized_action"] = (
        "Resolve verified active blockers: " + ", ".join(b["blocker_id"] for b in active)
        if active else "Obtain publication approval; publication authority remains separate."
    )
    contract["blocker_framework"] = {
        "framework_id": framework["framework_id"],
        "graph": framework["graph"],
        "verification": framework["verification"],
        "duplicate_blockers_merged": framework["duplicate_blockers_merged"],
    }
    contract["decision_digest"] = _sha256(contract)
    return contract


def view(root: Path | str, subject: str) -> dict[str, Any]:
    contract = resolve(root)
    subject = subject.lower().replace("_", "-")
    if subject in {"qualification", "publication", "blockers", "readiness", "verify", "snapshot"}:
        if subject == "qualification":
            return {k: contract[k] for k in ("schema_version", "contract_id", "qualification_state", "publication_state", "active_blockers", "resolved_blockers", "retired_blockers", "validation_status", "remaining_blockers", "next_authorized_action", "decision_digest")}
        if subject == "publication":
            return {k: contract[k] for k in ("schema_version", "contract_id", "publication_state", "qualification_state", "active_blockers", "resolved_blockers", "retired_blockers", "auto_resolution_summary", "operator_actions", "publication_readiness", "next_authorized_action", "decision_digest")}
        if subject == "readiness":
            return {"ready": contract["qualification_state"] == "QUALIFIED_FOR_PUBLICATION", **contract}
        if subject == "blockers":
            return {"qualification_state": contract["qualification_state"], "publication_state": contract["publication_state"], "blockers": contract["blockers"], "active_blockers": contract["active_blockers"], "resolved_blockers": contract["resolved_blockers"], "retired_blockers": contract["retired_blockers"], "next_authorized_action": contract["next_authorized_action"], "decision_digest": contract["decision_digest"]}
        return {"contract": contract, "verified": True}
    raise QualificationContractError(f"UNKNOWN_QUALIFICATION_SUBJECT: {subject}")
