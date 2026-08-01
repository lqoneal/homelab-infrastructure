"""Canonical OA-22 gate qualification for CAP-022."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from scripts.lib.emp import progressive_oa
from scripts.lib.emp.oa22_cap022_verification import qualify
from scripts.lib.eos import capability_registry, mission_knowledge


OBJECTIVE = "Prove fail-closed handling and bounded generation of separately authorized corrective work."


def _digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def verify(repository: Path) -> dict:
    state = progressive_oa.load_state(repository)
    if state["gates"]["OA-21"].get("state") != "ACCEPTED":
        raise ValueError("OA-21 is not accepted")
    if state.get("active_gate") not in {"OA-22", "OA-23"}:
        raise ValueError("OA-22 is not active or canonically accepted")
    if state["gates"]["OA-22"].get("state") == "ACCEPTED":
        marker_path = repository / progressive_oa.PACKAGE_PATH / "runtime/evidence/OA-22/VERIFIED"
        if not marker_path.is_file():
            raise ValueError("accepted OA-22 has no verification marker")
        marker = json.loads(marker_path.read_text(encoding="utf-8"))
        return {"gate_id": "OA-22", "result": "PASS", "verification_state": "ACCEPTED",
                "evidence_digest": marker["evidence_digest"], "marker_digest": marker["marker_digest"]}
    model = mission_knowledge.load(repository)
    mission = next(item for item in model["missions"] if item["mission_id"] == "OA-22")
    if mission.get("capability_prerequisites") != ["ZEUS-OA-CAP-021"] or mission.get("capability_outcomes") != ["ZEUS-OA-CAP-022"]:
        raise ValueError("OA-22 authority or dependency model is invalid")
    registry = capability_registry.load(repository)
    cap021 = next(item for item in registry["capabilities"] if item["capability_id"] == "ZEUS-OA-CAP-021")
    cap022 = next(item for item in registry["capabilities"] if item["capability_id"] == "ZEUS-OA-CAP-022")
    if cap021.get("lifecycle") != "Operational" or cap021.get("runtime_availability") != "AVAILABLE":
        raise ValueError("CAP-021 prerequisite is not operational")
    if cap022.get("name") != "Failure and Corrective-Work Generation":
        raise ValueError("CAP-022 identity is not authoritative")
    result = qualify(repository)
    evidence = {
        "schema_version": 1, "gate_id": "OA-22", "result": result["result"],
        "objective": OBJECTIVE, "verification_timestamp": datetime.now(timezone.utc).isoformat(),
        "authoritative_inputs": {
            "objective": "engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/gates/OA-22/objective.yaml",
            "predecessor": "OA-21 ACCEPTED", "mission_knowledge_revision": str(model.get("revision")),
            "capability_registry_revision": str(registry.get("revision")),
            "prerequisite": "ZEUS-OA-CAP-021", "outcome": "ZEUS-OA-CAP-022",
        }, "assertions": result["assertions"], "qualification": result,
    }
    evidence["canonical_evidence_digest"] = _digest(evidence)
    marker = {"schema_version": 1, "package_id": progressive_oa.PACKAGE, "gate_id": "OA-22",
              "verification_result": "PASS", "verification_timestamp": evidence["verification_timestamp"],
              "evidence_digest": evidence["canonical_evidence_digest"]}
    marker["marker_digest"] = _digest(marker)
    runtime = repository / progressive_oa.PACKAGE_PATH / "runtime/evidence/OA-22"
    _write(runtime / "VERIFICATION.json", evidence)
    _write(runtime / "VERIFIED", marker)
    state["gates"]["OA-22"]["state"] = "AWAITING_OPERATOR_VERIFICATION"
    progressive_oa._write_state(repository, state)
    return {"gate_id": "OA-22", "result": "PASS", "verification_state": "VERIFIED_AWAITING_OPERATOR_ACCEPTANCE",
            "evidence_digest": evidence["canonical_evidence_digest"], "marker_digest": marker["marker_digest"],
            "evidence_directory": str(runtime.relative_to(repository))}
