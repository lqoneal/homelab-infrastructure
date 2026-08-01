"""Canonical OA-27 gate qualification for CAP-027."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from scripts.lib.emp import progressive_oa
from scripts.lib.emp.oa27_cap027_verification import CAPABILITY_ID, OBJECTIVE, qualify
from scripts.lib.eos import capability_registry, mission_knowledge


def _digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def verify(repository: Path) -> dict:
    state = progressive_oa.load_state(repository)
    if state.get("active_gate") not in {"OA-27", "OA-28"} or state["gates"]["OA-26"].get("state") != "ACCEPTED":
        raise ValueError("OA-27 requires accepted OA-26")
    marker_path = repository / progressive_oa.PACKAGE_PATH / "runtime/evidence/OA-27/VERIFIED"
    if state["gates"]["OA-27"].get("state") == "ACCEPTED":
        if not marker_path.is_file():
            raise ValueError("accepted OA-27 has no verification marker")
        return {"gate_id": "OA-27", "result": "PASS", "verification_state": "ACCEPTED", **json.loads(marker_path.read_text(encoding="utf-8"))}
    model = mission_knowledge.load(repository)
    mission = next(item for item in model["missions"] if item["mission_id"] == "OA-27")
    if mission.get("roadmap_objective") != OBJECTIVE or mission.get("capability_prerequisites") != ["ZEUS-OA-CAP-026"] or mission.get("capability_outcomes") != [CAPABILITY_ID]:
        raise ValueError("OA-27 authority or dependency model is invalid")
    registry = capability_registry.load(repository)
    capabilities = {item["capability_id"]: item for item in registry["capabilities"]}
    if capabilities["ZEUS-OA-CAP-026"].get("lifecycle") != "Operational" or capabilities["ZEUS-OA-CAP-026"].get("runtime_availability") != "AVAILABLE":
        raise ValueError("CAP-026 prerequisite is not operational")
    if capabilities[CAPABILITY_ID].get("name") != "Operator Acceptance":
        raise ValueError("CAP-027 identity is not authoritative")
    result = qualify(repository)
    if result["result"] != "PASS":
        raise ValueError("CAP-027 qualification failed")
    evidence = {
        "schema_version": 1, "gate_id": "OA-27", "result": "PASS",
        "objective": OBJECTIVE, "verification_timestamp": datetime.now(timezone.utc).isoformat(),
        "authoritative_inputs": {
            "objective": "engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/gates/OA-27/objective.yaml",
            "implementation": "engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/gates/OA-27/implementation.md",
            "predecessor": "OA-26 ACCEPTED", "mission_knowledge_revision": str(model.get("revision")),
            "capability_registry_revision": str(registry.get("revision")),
            "prerequisite": "ZEUS-OA-CAP-026", "outcome": CAPABILITY_ID,
        },
        "qualification": result,
        "acceptance_boundary": "explicit operator decision binds the exact qualified result and evidence manifest",
    }
    evidence["canonical_evidence_digest"] = _digest(evidence)
    marker = {
        "schema_version": 1, "package_id": progressive_oa.PACKAGE, "gate_id": "OA-27",
        "verification_result": "PASS", "verification_timestamp": evidence["verification_timestamp"],
        "evidence_digest": evidence["canonical_evidence_digest"],
    }
    marker["marker_digest"] = _digest(marker)
    runtime = repository / progressive_oa.PACKAGE_PATH / "runtime/evidence/OA-27"
    _write(runtime / "VERIFICATION.json", evidence)
    _write(runtime / "VERIFIED", marker)
    state["gates"]["OA-27"]["state"] = "AWAITING_OPERATOR_VERIFICATION"
    progressive_oa._write_state(repository, state)
    return {"gate_id": "OA-27", "result": "PASS", "verification_state": "VERIFIED_AWAITING_OPERATOR_ACCEPTANCE", **marker}
