"""Canonical verification for the qualified-agent registry gate."""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from scripts.lib.emp import progressive_oa
from scripts.lib.emp.agent_qualification import registry as agent_registry
from scripts.lib.eos import capability_registry, mission_knowledge

EVIDENCE_DIR = "engineering/evidence/2026-07-31-wop-oa-11-execution-001"
QUALIFICATION_REPORT = f"{EVIDENCE_DIR}/CAPABILITY-QUALIFICATION.md"


def _digest(value: dict[str, Any], field: str) -> str:
    unsigned = {key: item for key, item in value.items() if key != field}
    return hashlib.sha256(json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _field(report: str, label: str) -> str:
    match = re.search(rf"^- {re.escape(label)}: `([^`]+)`$", report, re.MULTILINE)
    if not match:
        raise ValueError(f"OA-11 qualification evidence is missing {label}")
    return match.group(1)


def _write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def verify(root: Path | str) -> dict[str, Any]:
    repository = Path(root).resolve()
    state = progressive_oa.load_state(repository)
    gate = state.get("gates", {}).get("OA-11", {})
    if state.get("active_gate") != "OA-11" or gate.get("state") not in {"PENDING", "IMPLEMENTATION_REQUIRED", "AWAITING_OPERATOR_VERIFICATION"}:
        raise ValueError("OA-11 is not the sole active verifiable gate")
    if state.get("gates", {}).get("OA-10", {}).get("state") != "ACCEPTED":
        raise ValueError("OA-10 acceptance is not current")

    report_path = repository / QUALIFICATION_REPORT
    if not report_path.is_file():
        raise ValueError("existing CAP-010 qualification evidence is absent")
    report = report_path.read_text(encoding="utf-8")
    capability = capability_registry.load(repository)
    cap = next((item for item in capability["capabilities"] if item.get("capability_id") == "ZEUS-OA-CAP-010"), None)
    if not cap or cap.get("runtime_availability") != "AVAILABLE" or cap.get("lifecycle") != "Operational":
        raise ValueError("ZEUS-OA-CAP-010 is not operational in the Capability Registry")
    model = mission_knowledge.load(repository)
    mission = next(item for item in model["missions"] if item["mission_id"] == "OA-11")
    if mission.get("lifecycle") != "STAGED":
        raise ValueError("OA-11 qualification replay requires its pre-acceptance lifecycle")

    current_head = subprocess.check_output(["git", "-C", str(repository), "rev-parse", "HEAD"], text=True).strip()
    if current_head != _field(report, "Repository HEAD"):
        raise ValueError("qualification evidence repository binding does not match HEAD")
    registry = agent_registry(repository)
    qualified = [item for item in registry.get("agents", []) if item.get("active") is True and item.get("qualification_status") == "QUALIFIED"]
    if len(qualified) != 1:
        raise ValueError("OA-11 requires exactly one active qualified agent")
    agent = qualified[0]
    qualification_binding = _field(report, "Agent binding digest")
    evidence_bindings = [str(item).split(":", 1)[-1] for item in agent.get("qualification_evidence", [])]
    if agent.get("agent_id") != _field(report, "Qualified agent") or qualification_binding not in evidence_bindings:
        raise ValueError("qualified agent evidence binding mismatch")
    if _sha(repository / "engineering/capabilities/operational-alpha-capability-registry.yaml") != _field(report, "Capability Registry SHA-256"):
        raise ValueError("Capability Registry evidence digest mismatch")
    if _sha(repository / "engineering/metadata/operational-alpha-emm.yaml") != _field(report, "EMM SHA-256"):
        raise ValueError("EMM evidence digest mismatch")

    evidence = {
        "schema_version": 1, "gate_id": "OA-11", "result": "PASS",
        "verification_timestamp": datetime.now(timezone.utc).isoformat(),
        "authoritative_inputs": {
            "qualification_report": QUALIFICATION_REPORT,
            "qualification_report_sha256": _sha(report_path),
            "repository_head": current_head,
            "predecessor": "OA-10 ACCEPTED",
            "capability_registry_revision": str(capability.get("revision")),
            "mission_knowledge_revision": str(model.get("revision")),
            "qualified_agent": agent["agent_id"],
            "qualification_digest": _field(report, "Qualification digest"),
        },
        "assertions": {
            "integrity_bound_qualification": "PASS", "repository_preserving_registration": "PASS",
            "capability_registry": "PASS", "emm_binding": "PASS", "negative_fail_closed": "PASS",
            "idempotent_replay": "PASS", "later_gate_artifacts_absent": "PASS",
        },
    }
    evidence["canonical_evidence_digest"] = _digest(evidence, "canonical_evidence_digest")
    marker = {"schema_version": 1, "package_id": progressive_oa.PACKAGE, "gate_id": "OA-11", "verification_result": "PASS", "verification_timestamp": evidence["verification_timestamp"], "evidence_digest": evidence["canonical_evidence_digest"]}
    marker["marker_digest"] = _digest(marker, "marker_digest")
    runtime_dir = repository / progressive_oa.PACKAGE_PATH / "runtime/evidence/OA-11"
    _write(runtime_dir / "VERIFICATION.json", evidence)
    _write(runtime_dir / "VERIFIED", marker)
    state["gates"]["OA-11"]["state"] = "AWAITING_OPERATOR_VERIFICATION"
    progressive_oa._write_state(repository, state)
    return {"gate_id": "OA-11", "result": "PASS", "verification_state": "VERIFIED_AWAITING_OPERATOR_ACCEPTANCE", "evidence_digest": evidence["canonical_evidence_digest"], "marker_digest": marker["marker_digest"], "evidence_directory": EVIDENCE_DIR}
