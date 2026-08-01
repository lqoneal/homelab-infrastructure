"""Canonical OA-24 gate qualification for CAP-024."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from scripts.lib.eos import capability_registry, mission_knowledge
from scripts.lib.emp import progressive_oa
from scripts.lib.emp.oa24_cap024_verification import CAPABILITY_ID, OBJECTIVE, qualify


def _digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def verify(repository: Path) -> dict:
    state = progressive_oa.load_state(repository)
    if state.get("active_gate") not in {"OA-24", "OA-25"} or state["gates"]["OA-23"].get("state") != "ACCEPTED":
        raise ValueError("OA-24 requires accepted OA-23")
    marker_path = repository / progressive_oa.PACKAGE_PATH / "runtime/evidence/OA-24/VERIFIED"
    if state["gates"]["OA-24"].get("state") == "ACCEPTED":
        if not marker_path.is_file():
            raise ValueError("accepted OA-24 has no verification marker")
        marker = json.loads(marker_path.read_text(encoding="utf-8"))
        return {"gate_id": "OA-24", "result": "PASS", "verification_state": "ACCEPTED", **marker}
    model = mission_knowledge.load(repository)
    mission = next(item for item in model["missions"] if item["mission_id"] == "OA-24")
    if mission.get("capability_prerequisites") != ["ZEUS-OA-CAP-023"] or mission.get("capability_outcomes") != [CAPABILITY_ID]:
        raise ValueError("OA-24 authority or dependency model is invalid")
    registry = capability_registry.load(repository)
    cap023 = next(item for item in registry["capabilities"] if item["capability_id"] == "ZEUS-OA-CAP-023")
    cap024 = next(item for item in registry["capabilities"] if item["capability_id"] == CAPABILITY_ID)
    if cap023.get("lifecycle") != "Operational" or cap023.get("runtime_availability") != "AVAILABLE":
        raise ValueError("CAP-023 prerequisite is not operational")
    if cap024.get("name") != "Resume and Idempotent Continuation":
        raise ValueError("CAP-024 identity is not authoritative")
    result = qualify(repository)
    evidence = {"schema_version": 1, "gate_id": "OA-24", "result": result["result"], "objective": OBJECTIVE,
                "verification_timestamp": datetime.now(timezone.utc).isoformat(),
                "authoritative_inputs": {"objective": "engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/gates/OA-24/objective.yaml",
                    "implementation": "engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/gates/OA-24/implementation.md",
                    "predecessor": "OA-23 ACCEPTED", "mission_knowledge_revision": str(model.get("revision")),
                    "capability_registry_revision": str(registry.get("revision")), "prerequisite": "ZEUS-OA-CAP-023", "outcome": CAPABILITY_ID},
                "qualification": result}
    evidence["canonical_evidence_digest"] = _digest(evidence)
    marker = {"schema_version": 1, "package_id": progressive_oa.PACKAGE, "gate_id": "OA-24", "verification_result": "PASS",
              "verification_timestamp": evidence["verification_timestamp"], "evidence_digest": evidence["canonical_evidence_digest"]}
    marker["marker_digest"] = _digest(marker)
    runtime = repository / progressive_oa.PACKAGE_PATH / "runtime/evidence/OA-24"
    _write(runtime / "VERIFICATION.json", evidence)
    _write(runtime / "VERIFIED", marker)
    state["gates"]["OA-24"]["state"] = "AWAITING_OPERATOR_VERIFICATION"
    progressive_oa._write_state(repository, state)
    return {"gate_id": "OA-24", "result": "PASS", "verification_state": "VERIFIED_AWAITING_OPERATOR_ACCEPTANCE", **marker}
