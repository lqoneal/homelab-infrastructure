"""Canonical verification for deterministic dispatch-candidate preparation."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from scripts.lib.emp import progressive_oa
from scripts.lib.emp.dispatch_candidate import create, validate
from scripts.lib.eos import capability_registry, mission_knowledge

EVIDENCE_DIR = "engineering/evidence/2026-07-31-wop-oa-13-execution-001"


def _digest(value: dict[str, Any], field: str) -> str:
    unsigned = {key: item for key, item in value.items() if key != field}
    return hashlib.sha256(json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def verify(root: Path | str) -> dict[str, Any]:
    repository = Path(root).resolve()
    state = progressive_oa.load_state(repository)
    gate = state.get("gates", {}).get("OA-13", {})
    if state.get("active_gate") != "OA-13" or gate.get("state") not in {"PENDING", "IMPLEMENTATION_REQUIRED", "AWAITING_OPERATOR_VERIFICATION"}:
        raise ValueError("OA-13 is not the sole active verifiable gate")
    if state.get("gates", {}).get("OA-12", {}).get("state") != "ACCEPTED":
        raise ValueError("OA-12 acceptance is not current")
    capability = capability_registry.load(repository)
    cap = next((item for item in capability["capabilities"] if item.get("capability_id") == "ZEUS-OA-CAP-012"), None)
    if not cap or cap.get("runtime_availability") != "AVAILABLE" or cap.get("lifecycle") != "Operational":
        raise ValueError("ZEUS-OA-CAP-012 is not operational in the Capability Registry")
    model = mission_knowledge.load(repository)
    mission = next(item for item in model["missions"] if item["mission_id"] == "OA-13")
    if mission.get("lifecycle") != "CURRENT":
        raise ValueError("OA-13 qualification requires its current pre-acceptance lifecycle")
    candidate = create(repository)
    replay = create(repository)
    if candidate != replay:
        raise ValueError("dispatch candidate replay is not deterministic")
    validate(repository, candidate)
    negative = {}
    for name, field in (("execution_started", "execution_started"), ("protected_effect_authorized", "protected_effect_authorized")):
        malformed = dict(candidate)
        malformed[field] = True
        try:
            validate(repository, malformed)
        except ValueError:
            negative[name] = "PASS"
        else:
            negative[name] = "FAIL"
    if set(negative.values()) != {"PASS"}:
        raise ValueError("dispatch candidate negative cases did not fail closed")
    evidence = {
        "schema_version": 1,
        "gate_id": "OA-13",
        "result": "PASS",
        "verification_timestamp": datetime.now(timezone.utc).isoformat(),
        "authoritative_inputs": {
            "objective": "engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/gates/OA-13/objective.yaml",
            "predecessor": "OA-12 ACCEPTED",
            "mission_knowledge_revision": str(model.get("revision")),
            "capability_registry_revision": str(capability.get("revision")),
            "candidate_digest": candidate["candidate_digest"],
            "selected_execution_agent": candidate["selected_execution_agent"],
        },
        "assertions": {
            "deterministic_candidate": "PASS",
            "qualified_agent_selection": "PASS",
            "repository_binding": "PASS",
            "negative_fail_closed": negative,
            "idempotent_replay": "PASS",
            "execution_started": "PASS_FALSE",
            "protected_effect_authorized": "PASS_FALSE",
            "later_gate_artifacts_absent": not (repository / progressive_oa.PACKAGE_PATH / "runtime/evidence/OA-14").exists(),
        },
    }
    if not evidence["assertions"]["later_gate_artifacts_absent"]:
        raise ValueError("OA-14 runtime artifacts exist")
    evidence["canonical_evidence_digest"] = _digest(evidence, "canonical_evidence_digest")
    marker = {"schema_version": 1, "package_id": progressive_oa.PACKAGE, "gate_id": "OA-13", "verification_result": "PASS", "verification_timestamp": evidence["verification_timestamp"], "evidence_digest": evidence["canonical_evidence_digest"]}
    marker["marker_digest"] = _digest(marker, "marker_digest")
    runtime_dir = repository / progressive_oa.PACKAGE_PATH / "runtime/evidence/OA-13"
    _write(runtime_dir / "CANDIDATE.json", candidate)
    _write(runtime_dir / "VERIFICATION.json", evidence)
    _write(runtime_dir / "VERIFIED", marker)
    state["gates"]["OA-13"]["state"] = "AWAITING_OPERATOR_VERIFICATION"
    progressive_oa._write_state(repository, state)
    return {"gate_id": "OA-13", "result": "PASS", "verification_state": "VERIFIED_AWAITING_OPERATOR_ACCEPTANCE", "evidence_digest": evidence["canonical_evidence_digest"], "marker_digest": marker["marker_digest"], "candidate_digest": candidate["candidate_digest"], "evidence_directory": EVIDENCE_DIR}
