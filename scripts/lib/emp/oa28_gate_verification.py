"""Canonical OA-28 gate qualification for CAP-028."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from scripts.lib.emp import progressive_oa
from scripts.lib.emp.oa28_cap028_verification import CAPABILITY_ID, OBJECTIVE, qualify
from scripts.lib.eos import capability_registry, mission_knowledge


def _digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def verify(repository: Path) -> dict:
    state = progressive_oa.load_state(repository)
    if state.get("active_gate") not in {"OA-28", "OA-29", "OA-30"} or state["gates"]["OA-27"].get("state") != "ACCEPTED":
        raise ValueError("OA-28 requires accepted OA-27")
    marker_path = repository / progressive_oa.PACKAGE_PATH / "runtime/evidence/OA-28/VERIFIED"
    if state["gates"]["OA-28"].get("state") == "ACCEPTED":
        if not marker_path.is_file():
            raise ValueError("accepted OA-28 has no verification marker")
        return {"gate_id": "OA-28", "result": "PASS", "verification_state": "ACCEPTED", **json.loads(marker_path.read_text(encoding="utf-8"))}
    model = mission_knowledge.load(repository)
    mission = next(item for item in model["missions"] if item["mission_id"] == "OA-28")
    if mission.get("roadmap_objective") != OBJECTIVE or mission.get("capability_prerequisites") != ["ZEUS-OA-CAP-027"] or mission.get("capability_outcomes") != [CAPABILITY_ID]:
        raise ValueError("OA-28 authority or dependency model is invalid")
    registry = capability_registry.load(repository)
    capabilities = {item["capability_id"]: item for item in registry["capabilities"]}
    if capabilities["ZEUS-OA-CAP-027"].get("lifecycle") != "Operational" or capabilities["ZEUS-OA-CAP-027"].get("runtime_availability") != "AVAILABLE":
        raise ValueError("CAP-027 prerequisite is not operational")
    if capabilities[CAPABILITY_ID].get("name") != "Mission Closeout":
        raise ValueError("CAP-028 identity is not authoritative")
    result = qualify(repository)
    if result["result"] != "PASS":
        raise ValueError("CAP-028 qualification failed")
    evidence = {
        "schema_version": 1, "gate_id": "OA-28", "result": "PASS", "objective": OBJECTIVE,
        "verification_timestamp": datetime.now(timezone.utc).isoformat(),
        "authoritative_inputs": {
            "objective": "engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/gates/OA-28/objective.yaml",
            "implementation": "engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/gates/OA-28/implementation.md",
            "predecessor": "OA-27 ACCEPTED", "mission_knowledge_revision": str(model.get("revision")),
            "capability_registry_revision": str(registry.get("revision")), "prerequisite": "ZEUS-OA-CAP-027", "outcome": CAPABILITY_ID,
        },
        "qualification": result, "acceptance_boundary": "operator acceptance remains distinct from evidence-calculated completion",
    }
    evidence["canonical_evidence_digest"] = _digest(evidence)
    marker = {"schema_version": 1, "package_id": progressive_oa.PACKAGE, "gate_id": "OA-28", "verification_result": "PASS", "verification_timestamp": evidence["verification_timestamp"], "evidence_digest": evidence["canonical_evidence_digest"]}
    marker["marker_digest"] = _digest(marker)
    runtime = repository / progressive_oa.PACKAGE_PATH / "runtime/evidence/OA-28"
    _write(runtime / "VERIFICATION.json", evidence)
    _write(runtime / "VERIFIED", marker)
    state["gates"]["OA-28"]["state"] = "AWAITING_OPERATOR_VERIFICATION"
    progressive_oa._write_state(repository, state)
    return {"gate_id": "OA-28", "result": "PASS", "verification_state": "VERIFIED_AWAITING_OPERATOR_ACCEPTANCE", **marker}
