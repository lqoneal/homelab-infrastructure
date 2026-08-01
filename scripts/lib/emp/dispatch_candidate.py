"""Authoritative, read-only deterministic dispatch-candidate projection."""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from scripts.lib.eos import mission_knowledge
from scripts.lib.emp.agent_qualification import registry as agent_registry


def _digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def create(repository: Path | str) -> dict[str, Any]:
    root = Path(repository).resolve()
    decision = mission_knowledge.recommend(root)
    if decision.get("result") != "PASS" or decision.get("recommended_mission") != "OA-13":
        raise ValueError("dispatch candidate requires an eligible OA-13 and one qualified agent")
    agents = [item for item in agent_registry(root).get("agents", [])
              if item.get("active") is True and item.get("qualification_status") == "QUALIFIED"]
    if len(agents) != 1:
        raise ValueError("dispatch candidate requires exactly one qualified agent")
    agent = agents[0]
    contract = {
        "mission_id": decision["recommended_mission"],
        "selected_execution_agent": agent["agent_id"],
        "required_capabilities": decision["readiness"]["prerequisite_capabilities"],
        "authority_source": mission_knowledge.PATH,
        "execution_constraints": agent.get("execution_constraints", []),
        "expected_evidence_outputs": ["dispatch-contract", "capability-qualification", "operator-capability-summary", "synchronization-report", "validation-report"],
    }
    head = subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip()
    candidate = {
        "schema_version": 1,
        "candidate_type": "DISPATCH_CANDIDATE",
        "mission_id": contract["mission_id"],
        "selected_execution_agent": contract["selected_execution_agent"],
        "required_capabilities": sorted(contract["required_capabilities"]),
        "execution_constraints": sorted(contract["execution_constraints"]),
        "repository_identity": str(root),
        "repository_head": head,
        "authority_source": contract["authority_source"],
        "expected_evidence_outputs": sorted(contract["expected_evidence_outputs"]),
        "execution_started": False,
        "protected_effect_authorized": False,
    }
    return {**candidate, "candidate_digest": _digest(candidate)}


def validate(repository: Path | str, candidate: dict[str, Any]) -> dict[str, Any]:
    expected = create(repository)
    if candidate != expected:
        raise ValueError("dispatch candidate replay diverged")
    if candidate.get("execution_started") or candidate.get("protected_effect_authorized"):
        raise ValueError("dispatch candidate contains an execution side effect")
    return expected
