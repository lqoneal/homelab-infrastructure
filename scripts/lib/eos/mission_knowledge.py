"""EMM-bound Operational Alpha mission knowledge and recommendation services."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any
import yaml

from scripts.lib.eos import capability_registry

PATH = "engineering/missions/operational-alpha-mission-knowledge.yaml"

class MissionKnowledgeError(ValueError): pass

def _digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()

def load(root: Path | str) -> dict[str, Any]:
    root = Path(root)
    try: value = yaml.safe_load((root / PATH).read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as error: raise MissionKnowledgeError(f"MISSION_KNOWLEDGE_UNAVAILABLE: {error}") from error
    if not isinstance(value, dict) or value.get("model_id") != "OPERATIONAL-ALPHA-MISSION-KNOWLEDGE" or not isinstance(value.get("missions"), list): raise MissionKnowledgeError("MISSION_KNOWLEDGE_INVALID")
    ids = [item.get("mission_id") for item in value["missions"] if isinstance(item, dict)]
    if ids != value.get("mission_sequence") or len(ids) != len(set(ids)): raise MissionKnowledgeError("MISSION_KNOWLEDGE_SEQUENCE_INVALID")
    from scripts.lib.eos.convergence_runtime import ConvergenceRuntime, ConvergenceRuntimeError
    try:
        entity = ConvergenceRuntime(root)._entity("MissionKnowledgeModel", value["model_id"], value["revision"])
        ConvergenceRuntime(root)._source(entity); capability_registry.load(root)
    except (ConvergenceRuntimeError, capability_registry.CapabilityRegistryError) as error: raise MissionKnowledgeError(str(error)) from error
    return value

def _missions(root: Path | str):
    value = load(root); by_id = {item["mission_id"]: item for item in value["missions"]}
    capabilities = {item["capability_id"] for item in capability_registry.load(root)["capabilities"] if item.get("lifecycle") == "Operational"}
    return value, by_id, capabilities

def readiness(root: Path | str, mission_id: str) -> dict[str, Any]:
    value, by_id, capabilities = _missions(root); mission = by_id.get(mission_id)
    if mission is None: raise MissionKnowledgeError("MISSION_NOT_FOUND")
    completed = {key for key, item in by_id.items() if item.get("lifecycle") == "COMPLETED"}
    missing_dependencies = sorted(set(mission["dependencies"]) - completed); missing_capabilities = sorted(set(mission["capability_prerequisites"]) - capabilities)
    blockers = list(mission.get("blocking_conditions", []))
    if missing_dependencies: blockers.append("DEPENDENCY_UNSATISFIED")
    if missing_capabilities: blockers.append("CAPABILITY_PREREQUISITE_MISSING")
    classification = "ELIGIBLE" if not blockers and mission["lifecycle"] == "CURRENT" else ("COMPLETED" if mission["lifecycle"] == "COMPLETED" else "BLOCKED")
    result = {"model_id": value["model_id"], "revision": str(value["revision"]), "mission_id": mission_id, "classification": classification, "objective_source": mission["objective_source"], "prerequisite_capabilities": mission["capability_prerequisites"], "missing_capabilities": missing_capabilities, "dependencies": mission["dependencies"], "missing_dependencies": missing_dependencies, "blocking_conditions": sorted(blockers), "completion_criteria": mission["completion_criteria"], "authoritative_evidence": [PATH, "engineering/capabilities/operational-alpha-capability-registry.yaml", mission["objective_source"]]}
    result["readiness_digest"] = _digest(result); return result

def recommend(root: Path | str) -> dict[str, Any]:
    value, _, _ = _missions(root); candidates = [readiness(root, item) for item in value["mission_sequence"]]; eligible = [item for item in candidates if item["classification"] == "ELIGIBLE"]; recommended = eligible[0] if eligible else None
    return {"model_id": value["model_id"], "result": "PASS" if recommended else "NO_ELIGIBLE_MISSION", "recommended_mission": recommended["mission_id"] if recommended else None, "rationale": "first mission in authoritative sequence with completed dependencies and operational prerequisites" if recommended else "no mission satisfies authoritative readiness criteria", "readiness": recommended, "blocked_missions": [item for item in candidates if item["classification"] == "BLOCKED"], "authoritative_evidence": [PATH, "engineering/capabilities/operational-alpha-capability-registry.yaml"]}

def explain(root: Path | str, mission_id: str) -> dict[str, Any]:
    result = readiness(root, mission_id); result["explanation"] = "mission is recommended" if result["classification"] == "ELIGIBLE" else "mission is not recommended because readiness conditions are unmet or it is complete"; return result

def prerequisites(root: Path | str, mission_id: str) -> dict[str, Any]:
    result = readiness(root, mission_id); return {key: result[key] for key in ("mission_id", "dependencies", "missing_dependencies", "prerequisite_capabilities", "missing_capabilities", "blocking_conditions", "authoritative_evidence")}

def dependency_graph(root: Path | str) -> dict[str, Any]:
    value, by_id, _ = _missions(root); return {"model_id": value["model_id"], "nodes": value["mission_sequence"], "edges": [{"from": dep, "to": mission_id} for mission_id, item in by_id.items() for dep in item["dependencies"]], "result": "PASS"}
