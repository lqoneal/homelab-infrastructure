"""Canonical verification for the integrity-bound agent-selection gate."""
from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from scripts.lib.emp import progressive_oa
from scripts.lib.emp.agent_qualification import AgentQualificationError, select
from scripts.lib.eos import capability_registry, mission_knowledge

EVIDENCE_DIR = "engineering/evidence/2026-07-31-wop-oa-12-execution-001"


def _digest(value: dict[str, Any], field: str) -> str:
    unsigned = {key: item for key, item in value.items() if key != field}
    return hashlib.sha256(json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def verify(root: Path | str) -> dict[str, Any]:
    repository = Path(root).resolve()
    state = progressive_oa.load_state(repository)
    gate = state.get("gates", {}).get("OA-12", {})
    if state.get("active_gate") != "OA-12" or gate.get("state") not in {"PENDING", "IMPLEMENTATION_REQUIRED", "AWAITING_OPERATOR_VERIFICATION"}:
        raise ValueError("OA-12 is not the sole active verifiable gate")
    if state.get("gates", {}).get("OA-11", {}).get("state") != "ACCEPTED":
        raise ValueError("OA-11 acceptance is not current")

    capability = capability_registry.load(repository)
    cap = next((item for item in capability["capabilities"] if item.get("capability_id") == "ZEUS-OA-CAP-011"), None)
    if not cap or cap.get("runtime_availability") != "AVAILABLE" or cap.get("lifecycle") != "Operational":
        raise ValueError("ZEUS-OA-CAP-011 is not operational in the Capability Registry")
    model = mission_knowledge.load(repository)
    mission = next(item for item in model["missions"] if item["mission_id"] == "OA-12")
    if mission.get("lifecycle") != "CURRENT":
        raise ValueError("OA-12 qualification requires its current pre-acceptance lifecycle")

    criteria = {
        "mission_class": "engineering",
        "required_tools": ["zeus-cli", "bounded-artifact-handler"],
        "execution_profile": ["controlled-wop-only", "exact-repository-baseline", "no-unreviewed-external-effects"],
    }
    selected = select(repository, **criteria)
    replay = select(repository, **criteria)
    if selected != replay:
        raise ValueError("agent selection replay is not deterministic")
    negative = {}
    for name, values in {
        "wrong_mission_class": {**criteria, "mission_class": "untrusted"},
        "unsupported_tool": {**criteria, "required_tools": criteria["required_tools"] + ["unavailable-tool"]},
        "unsupported_profile": {**criteria, "execution_profile": criteria["execution_profile"] + ["unapproved-effect"]},
    }.items():
        try:
            select(repository, **values)
        except AgentQualificationError:
            negative[name] = "PASS"
        else:
            negative[name] = "FAIL"
    if set(negative.values()) != {"PASS"}:
        raise ValueError("agent selection negative cases did not fail closed")

    head = subprocess.check_output(["git", "-C", str(repository), "rev-parse", "HEAD"], text=True).strip()
    evidence = {
        "schema_version": 1,
        "gate_id": "OA-12",
        "result": "PASS",
        "verification_timestamp": datetime.now(timezone.utc).isoformat(),
        "authoritative_inputs": {
            "objective": "engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/gates/OA-12/objective.yaml",
            "repository_head": head,
            "predecessor": "OA-11 ACCEPTED",
            "capability_registry_revision": str(capability.get("revision")),
            "mission_knowledge_revision": str(model.get("revision")),
            "selected_agent": selected["selected_agent"],
            "selection_digest": selected["selection_digest"],
        },
        "assertions": {
            "repository_binding": "PASS",
            "mission_class_match": "PASS",
            "tool_profile_match": "PASS",
            "execution_profile_match": "PASS",
            "single_agent_selection": "PASS",
            "negative_fail_closed": negative,
            "idempotent_replay": "PASS",
            "later_gate_artifacts_absent": not (repository / progressive_oa.PACKAGE_PATH / "runtime/evidence/OA-13").exists(),
        },
    }
    if not evidence["assertions"]["later_gate_artifacts_absent"]:
        raise ValueError("OA-13 runtime artifacts exist")
    evidence["canonical_evidence_digest"] = _digest(evidence, "canonical_evidence_digest")
    marker = {"schema_version": 1, "package_id": progressive_oa.PACKAGE, "gate_id": "OA-12", "verification_result": "PASS", "verification_timestamp": evidence["verification_timestamp"], "evidence_digest": evidence["canonical_evidence_digest"]}
    marker["marker_digest"] = _digest(marker, "marker_digest")
    runtime_dir = repository / progressive_oa.PACKAGE_PATH / "runtime/evidence/OA-12"
    _write(runtime_dir / "VERIFICATION.json", evidence)
    _write(runtime_dir / "VERIFIED", marker)
    state["gates"]["OA-12"]["state"] = "AWAITING_OPERATOR_VERIFICATION"
    progressive_oa._write_state(repository, state)
    return {"gate_id": "OA-12", "result": "PASS", "verification_state": "VERIFIED_AWAITING_OPERATOR_ACCEPTANCE", "evidence_digest": evidence["canonical_evidence_digest"], "marker_digest": marker["marker_digest"], "evidence_directory": EVIDENCE_DIR}
