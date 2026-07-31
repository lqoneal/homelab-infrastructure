"""EMM-bound Operational Alpha mission knowledge and recommendation services."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any
import yaml

from scripts.lib.eos import capability_registry

PATH = "engineering/missions/operational-alpha-mission-knowledge.yaml"
ROADMAP_PATH = "engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/ROADMAP.md"

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
    roadmap = authoritative_roadmap(root)
    if value.get("roadmap_provenance", {}).get("controlled_id") != roadmap["controlled_id"]:
        raise MissionKnowledgeError("MISSION_KNOWLEDGE_ROADMAP_BINDING_INVALID")
    for item in value["missions"]:
        source = item.get("roadmap_source")
        if source and (source != ROADMAP_PATH or roadmap["objectives"].get(item.get("mission_id")) != item.get("roadmap_objective")):
            raise MissionKnowledgeError("MISSION_KNOWLEDGE_ROADMAP_DIVERGED")
    return value

def authoritative_roadmap(root: Path | str) -> dict[str, Any]:
    """Resolve the EMM-bound roadmap source; this is not projection state."""
    path = Path(root) / ROADMAP_PATH
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as error:
        raise MissionKnowledgeError(f"ROADMAP_UNAVAILABLE: {error}") from error
    objectives: dict[str, str] = {}
    revision = next((line.split(":", 1)[1].strip() for line in lines if line.startswith("Revision:")), None)
    for line in lines:
        if not line.startswith("| OA-"):
            continue
        fields = [field.strip() for field in line.split("|")[1:-1]]
        if len(fields) == 3 and fields[0].startswith("OA-"):
            objectives[fields[0]] = fields[1]
    if list(objectives) != [f"OA-{index:02d}" for index in range(1, 31)]:
        raise MissionKnowledgeError("ROADMAP_SEQUENCE_INVALID")
    if not revision:
        raise MissionKnowledgeError("ROADMAP_REVISION_MISSING")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return {"controlled_id": "ZEUS-OA-ROADMAP-002", "revision": revision,
            "source": ROADMAP_PATH, "digest": digest, "objectives": objectives}


def _emm_roadmap_binding(root: Path | str, roadmap: dict[str, Any]) -> dict[str, Any]:
    """Resolve the roadmap entity through EMM before evaluating drift."""
    from scripts.lib.eos.convergence_runtime import ConvergenceRuntime, ConvergenceRuntimeError

    try:
        entity = ConvergenceRuntime(Path(root))._entity(
            "MissionRoadmap", roadmap["controlled_id"], roadmap["revision"]
        )
        source, source_digest = ConvergenceRuntime(Path(root))._source(entity)
    except ConvergenceRuntimeError as error:
        raise MissionKnowledgeError(f"ROADMAP_EMM_BINDING_INVALID: {error}") from error
    if source.as_posix() != (Path(root).resolve() / ROADMAP_PATH).as_posix() or source_digest != roadmap["digest"]:
        raise MissionKnowledgeError("ROADMAP_EMM_SOURCE_DRIFT")
    return entity

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

def blockers(root: Path | str, mission_id: str) -> dict[str, Any]:
    """Resolve blockers for the requested mission, never an implicit OA-01."""
    result = readiness(root, mission_id)
    return {
        "mission_id": mission_id,
        "blocking_conditions": result["blocking_conditions"],
        "missing_capabilities": result["missing_capabilities"],
        "missing_dependencies": result["missing_dependencies"],
        "result": "PASS" if not result["blocking_conditions"] else "BLOCKED",
        "authoritative_evidence": result["authoritative_evidence"],
    }

def dependency_graph(root: Path | str) -> dict[str, Any]:
    value, by_id, _ = _missions(root); return {"model_id": value["model_id"], "nodes": value["mission_sequence"], "edges": [{"from": dep, "to": mission_id} for mission_id, item in by_id.items() for dep in item["dependencies"]], "result": "PASS"}

def _classification(item: dict[str, Any], readiness_result: dict[str, Any]) -> str:
    if item.get("lifecycle") == "COMPLETED":
        return "COMPLETED"
    if item.get("lifecycle") == "UNAUTHORIZED":
        return "UNAUTHORIZED"
    if readiness_result.get("classification") == "ELIGIBLE":
        return "ELIGIBLE"
    if item.get("lifecycle") == "STAGED":
        return "NOT_READY"
    if item.get("lifecycle") == "CURRENT":
        return "BLOCKED" if readiness_result.get("blocking_conditions") else "NOT_READY"
    return "NOT_READY"

def portfolio(root: Path | str) -> dict[str, Any]:
    value, by_id, _ = _missions(root)
    missions = []
    for mission_id in value["mission_sequence"]:
        item = by_id[mission_id]
        readiness_result = readiness(root, mission_id)
        missions.append({
            "mission_id": mission_id,
            "lifecycle": item.get("lifecycle"),
            "classification": _classification(item, readiness_result),
            "dependencies": list(item.get("dependencies", [])),
            "missing_dependencies": readiness_result["missing_dependencies"],
            "capability_prerequisites": list(item.get("capability_prerequisites", [])),
            "missing_capabilities": readiness_result["missing_capabilities"],
            "objective_source": item["objective_source"],
            "blocking_conditions": readiness_result["blocking_conditions"],
        })
    return {
        "model_id": value["model_id"], "revision": str(value["revision"]),
        "result": "PASS", "missions": missions,
        "authoritative_source": PATH,
        "owner": value.get("authoritative_owner"),
    }

def list_missions(root: Path | str) -> dict[str, Any]:
    result = portfolio(root)
    return {"result": result["result"], "model_id": result["model_id"],
            "revision": result["revision"], "missions": result["missions"],
            "authoritative_source": result["authoritative_source"]}

def roadmap(root: Path | str) -> dict[str, Any]:
    """Return a read-only roadmap projection derived exclusively from the Mission Knowledge Model."""
    value, by_id, _ = _missions(root)
    source = value["roadmap_provenance"]["source"]
    controlled = authoritative_roadmap(root)
    recommended_mission = recommend(root)["recommended_mission"]
    entries = []
    for mission_id in value["mission_sequence"]:
        mission = by_id[mission_id]
        readiness_result = readiness(root, mission_id)
        entries.append({
            "mission_id": mission_id,
            "lifecycle": mission["lifecycle"],
            "classification": _classification(mission, readiness_result),
            "recommendation": mission_id == recommended_mission,
            "objective": mission["roadmap_objective"],
            "source_entry": mission["roadmap_entry"],
            "objective_source": mission["objective_source"],
            "dependencies": mission["dependencies"],
            "provenance": value["roadmap_provenance"]["derivation_chain"],
        })
    verified = roadmap_verification(root)
    return {
        "result": "PASS",
        "roadmap_id": controlled["controlled_id"],
        "model_id": value["model_id"],
        "revision": str(value["revision"]),
        "source": source,
        "roadmap_revision": controlled["revision"],
        "roadmap_digest": controlled["digest"],
        "mission_knowledge_revision": str(value["revision"]),
        "provenance_verification": verified,
        "derivation": "Mission Knowledge Model read-only projection",
        "authority_chain": value["roadmap_provenance"]["derivation_chain"],
        "missions": entries,
    }

def roadmap_verification(root: Path | str) -> dict[str, Any]:
    """Run the single EMM reconciliation check for roadmap provenance and drift."""
    value = load(root)
    controlled = authoritative_roadmap(root)
    entity = _emm_roadmap_binding(root, controlled)
    mismatches = []
    if str(value["roadmap_provenance"].get("revision")) != str(controlled["revision"]):
        mismatches.append("ROADMAP_REVISION_MISMATCH")
    if value["roadmap_provenance"].get("digest") != controlled["digest"]:
        mismatches.append("ROADMAP_DIGEST_MISMATCH")
    if value["mission_sequence"] != list(controlled["objectives"]):
        mismatches.append("ROADMAP_SEQUENCE_MISMATCH")
    for mission in value["missions"]:
        mission_id = mission.get("mission_id")
        if mission.get("roadmap_source") != ROADMAP_PATH or mission.get("roadmap_entry") != mission_id:
            mismatches.append(f"{mission_id}:ROADMAP_PROVENANCE_MISMATCH")
        if mission.get("roadmap_objective") != controlled["objectives"].get(mission_id):
            mismatches.append(f"{mission_id}:ROADMAP_OBJECTIVE_MISMATCH")
    return {"result": "PASS" if not mismatches else "FAIL", "mismatches": mismatches,
            "roadmap_id": controlled["controlled_id"], "roadmap_revision": controlled["revision"],
            "roadmap_digest": controlled["digest"], "mission_knowledge_revision": str(value["revision"]),
            "emm_entity_revision": str(entity.get("revision")),
            "drift_owner": "EMM",
            "qualification_owner": "PROC-0006"}

def queue(root: Path | str) -> dict[str, Any]:
    result = portfolio(root)
    eligible = [item for item in result["missions"] if item["classification"] == "ELIGIBLE"]
    eligible.sort(key=lambda item: (item["mission_id"]))
    return {"result": "PASS" if eligible else "NO_ELIGIBLE_MISSION",
            "queue": [item["mission_id"] for item in eligible],
            "selection_rule": "controlled mission sequence, then mission identifier",
            "authoritative_source": PATH}

def health(root: Path | str) -> dict[str, Any]:
    result = portfolio(root)
    counts: dict[str, int] = {}
    for item in result["missions"]:
        counts[item["classification"]] = counts.get(item["classification"], 0) + 1
    graph = dependency_graph(root)
    return {"result": "PASS", "inventory_count": len(result["missions"]),
            "classification_counts": counts, "dependency_integrity": graph["result"],
            "recommended_mission": recommend(root)["recommended_mission"],
            "authoritative_source": PATH}

def synchronization(root: Path | str, mission_id: str) -> dict[str, Any]:
    """Project synchronization semantics from the authoritative mission model."""
    value, by_id, capabilities = _missions(root)
    mission = by_id.get(mission_id)
    if mission is None:
        raise MissionKnowledgeError("MISSION_NOT_FOUND")
    lifecycle = str(mission.get("lifecycle", "")).upper()
    sources = [str(mission["objective_source"])]
    sources.extend(str(item) for item in mission.get("evidence_relationships", []))
    missing_sources = [item for item in sources if not (Path(root) / item).exists()]
    missing_capabilities = sorted(
        set(mission.get("capability_prerequisites", [])) - capabilities
    )
    blockers = sorted(mission.get("blocking_conditions", []))
    terminal = lifecycle in {"COMPLETED", "ACCEPTED", "ARCHIVED"}
    result = "PASS" if not missing_sources and not missing_capabilities and not blockers else "FAIL"
    return {
        "schema_version": 1,
        "mission_id": mission_id,
        "lifecycle": lifecycle,
        "synchronization_mode": "TERMINAL_COMPLETION_PROJECTION" if terminal else "CURRENT_LIFECYCLE_PROJECTION",
        "result": result,
        "authoritative_source": PATH,
        "objective_source": mission["objective_source"],
        "evidence_relationships": mission.get("evidence_relationships", []),
        "missing_sources": missing_sources,
        "missing_capabilities": missing_capabilities,
        "blocking_conditions": blockers,
    }

def orchestration_verification(root: Path | str) -> dict[str, Any]:
    """Verify the canonical, read-only orchestration transaction.

    Mission Knowledge Model remains the sole owner: this is a deterministic
    projection and never creates authority, WOP, dispatch, or mission state.
    """
    decision = recommend(root)
    if decision["result"] != "PASS":
        return {"result": "NO_ELIGIBLE_MISSION", "decision": decision}
    from scripts.lib.emp.agent_qualification import registry as agent_registry
    registry = agent_registry(Path(root))
    agents = [item for item in registry.get("agents", [])
              if item.get("active") is True and item.get("qualification_status") == "QUALIFIED"]
    if len(agents) != 1:
        return {"result": "NO_QUALIFIED_EXECUTION_AGENT", "decision": decision,
                "qualified_agents": sorted(item.get("agent_id", "") for item in agents),
                "authoritative_source": PATH}
    mission = decision["readiness"]
    agent = agents[0]
    contract = {
        "mission_id": decision["recommended_mission"],
        "selected_execution_agent": agent["agent_id"],
        "required_capabilities": mission["prerequisite_capabilities"],
        "authority_source": PATH,
        "execution_constraints": agent.get("execution_constraints", []),
        "expected_evidence_outputs": ["dispatch-contract", "capability-qualification", "operator-capability-summary", "synchronization-report", "validation-report"],
    }
    return {"result": "PASS", "transaction": "DETERMINISTIC_ORCHESTRATION",
            "decision_trace": {"recommendation": decision, "agent_count": len(agents)},
            "dispatch_contract": contract, "authoritative_source": PATH}

def dispatch_verification(root: Path | str) -> dict[str, Any]:
    result = orchestration_verification(root)
    return {"result": result["result"], "dispatch": result.get("dispatch_contract"),
            "qualified_agents": result.get("qualified_agents", ([result["dispatch_contract"]["selected_execution_agent"]] if result.get("dispatch_contract") else [])),
            "authoritative_source": result.get("authoritative_source", PATH),
            "decision_trace": result.get("decision_trace")}
