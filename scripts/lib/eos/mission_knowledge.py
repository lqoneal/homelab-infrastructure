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


def current(root: Path | str) -> dict[str, Any]:
    """Return the single CURRENT mission from the authoritative model."""
    value, by_id, _ = _missions(root)
    current_ids = [mission_id for mission_id in value["mission_sequence"]
                   if by_id[mission_id].get("lifecycle") == "CURRENT"]
    if len(current_ids) != 1:
        raise MissionKnowledgeError("MISSION_CURRENT_CARDINALITY_INVALID")
    mission_id = current_ids[0]
    mission = by_id[mission_id]
    return {
        "mission_id": mission_id,
        "lifecycle": mission["lifecycle"],
        "objective": mission["roadmap_objective"],
        "objective_source": mission["objective_source"],
        "dependencies": list(mission.get("dependencies", [])),
        "capability_prerequisites": list(mission.get("capability_prerequisites", [])),
        "authoritative_source": PATH,
    }

def readiness(root: Path | str, mission_id: str) -> dict[str, Any]:
    value, by_id, capabilities = _missions(root); mission = by_id.get(mission_id)
    if mission is None: raise MissionKnowledgeError("MISSION_NOT_FOUND")
    completed = {key for key, item in by_id.items() if item.get("lifecycle") == "COMPLETED"}
    missing_dependencies = sorted(set(mission["dependencies"]) - completed); missing_capabilities = sorted(set(mission["capability_prerequisites"]) - capabilities)
    blockers = list(mission.get("blocking_conditions", []))
    if missing_dependencies: blockers.append("DEPENDENCY_UNSATISFIED")
    if missing_capabilities: blockers.append("CAPABILITY_PREREQUISITE_MISSING")
    classification = "ELIGIBLE" if not blockers and mission["lifecycle"] == "CURRENT" else ("COMPLETED" if mission["lifecycle"] == "COMPLETED" else "BLOCKED")
    missing_outcomes = sorted(set(mission.get("capability_outcomes", [])) - capabilities)
    result = {"model_id": value["model_id"], "revision": str(value["revision"]), "mission_id": mission_id, "lifecycle": mission["lifecycle"], "current_mission": current(root)["mission_id"], "classification": classification, "objective_source": mission["objective_source"], "prerequisite_capabilities": mission["capability_prerequisites"], "missing_capabilities": missing_capabilities, "outcome_capabilities": list(mission.get("capability_outcomes", [])), "missing_outcome_capabilities": missing_outcomes, "dependencies": mission["dependencies"], "missing_dependencies": missing_dependencies, "blocking_conditions": sorted(blockers), "completion_criteria": mission["completion_criteria"], "authoritative_evidence": [PATH, "engineering/capabilities/operational-alpha-capability-registry.yaml", mission["objective_source"]]}
    result["readiness_digest"] = _digest(result); return result

def recommend(root: Path | str) -> dict[str, Any]:
    value, by_id, capabilities = _missions(root)
    candidates = [readiness(root, item) for item in value["mission_sequence"]]
    current_id = current(root)["mission_id"]
    current_readiness = next(item for item in candidates if item["mission_id"] == current_id)
    mission = by_id[current_id]
    objective = mission["roadmap_objective"]
    successor = value["mission_sequence"][value["mission_sequence"].index(current_id) + 1] if current_id != value["mission_sequence"][-1] else None
    recommendation = None
    if current_readiness["classification"] == "BLOCKED" or current_readiness["missing_outcome_capabilities"]:
        missing = sorted(set(current_readiness["missing_capabilities"]) | set(current_readiness["missing_outcome_capabilities"]))
        recommendation = {
            "action": f"Execute WOP-{current_id}-EXECUTION-001",
            "wop": f"WOP-{current_id}-EXECUTION-001",
            "objective": objective,
            "missing_capabilities": missing,
            "authority": [PATH, "engineering/capabilities/operational-alpha-capability-registry.yaml", mission["objective_source"], ROADMAP_PATH],
            "expected_outcome": f"{current_id} COMPLETED; {successor} CURRENT" if successor else f"{current_id} COMPLETED",
            "successor_mission": successor,
        }
    eligible = [item for item in candidates if item["classification"] == "ELIGIBLE"]
    recommended = eligible[0] if eligible else None
    return {
        "model_id": value["model_id"],
        "result": "PASS" if recommendation or recommended else "NO_ELIGIBLE_MISSION",
        "recommended_mission": current_id if recommendation else (recommended["mission_id"] if recommended else None),
        "rationale": ("current mission is blocked; execute its authoritative WOP" if current_readiness["classification"] == "BLOCKED" else "current mission outcome is not yet operational; execute its authoritative WOP") if recommendation else ("first mission in authoritative sequence with completed dependencies and operational prerequisites" if recommended else "no mission satisfies authoritative readiness criteria"),
        "readiness": current_readiness if recommendation else recommended,
        "recommendation": recommendation,
        "blocked_missions": [item for item in candidates if item["classification"] == "BLOCKED"],
        "authoritative_evidence": [PATH, "engineering/capabilities/operational-alpha-capability-registry.yaml", ROADMAP_PATH],
    }


def state(root: Path | str, mission_id: str | None = None) -> dict[str, Any]:
    """Return current mission state without consulting runtime compatibility stores."""
    selected = mission_id.upper() if mission_id else current(root)["mission_id"]
    value, by_id, _ = _missions(root)
    mission = by_id.get(selected)
    if mission is None:
        raise MissionKnowledgeError("MISSION_NOT_FOUND")
    readiness_result = readiness(root, selected)
    return {
        "result": "PASS", "model_id": value["model_id"],
        "revision": str(value["revision"]), "mission_id": selected,
        "lifecycle": mission["lifecycle"],
        "current_mission": current(root)["mission_id"],
        "objective": mission["roadmap_objective"],
        "classification": readiness_result["classification"],
        "blocking_conditions": readiness_result["blocking_conditions"],
        "missing_capabilities": readiness_result["missing_capabilities"],
        "missing_dependencies": readiness_result["missing_dependencies"],
        "authoritative_source": PATH,
    }


def next_action(root: Path | str) -> dict[str, Any]:
    """Project the next controlled WOP action from the current mission only."""
    selected = current(root)
    readiness_result = readiness(root, selected["mission_id"])
    wop = f"WOP-{selected['mission_id']}-EXECUTION-001"
    blocked = readiness_result["classification"] == "BLOCKED"
    recommendation = recommend(root).get("recommendation")
    return {
        "result": "PASS", "resolver": "operational-alpha-mission-knowledge/1",
        "current_mission": selected["mission_id"],
        "current_lifecycle": selected["lifecycle"],
        "current_classification": readiness_result["classification"],
        "blocking_conditions": readiness_result["blocking_conditions"],
        "missing_capabilities": readiness_result["missing_capabilities"],
        "next_authorized_action": {
            "code": "EXECUTE_WOP" if recommendation else "WAIT_FOR_CAPABILITY",
            "wop": recommendation["wop"] if recommendation else None,
            "description": recommendation["action"] if recommendation else "Await the next qualified capability",
            "objective": recommendation["objective"] if recommendation else None,
            "expected_outcome": recommendation["expected_outcome"] if recommendation else None,
            "missing_capabilities": recommendation["missing_capabilities"] if recommendation else [],
            "authority": recommendation["authority"] if recommendation else [PATH],
            "requires_separate_transition_authority": True,
        },
        "authoritative_source": PATH,
    }


def snapshot(root: Path | str, mission_id: str | None = None) -> dict[str, Any]:
    """Combine the same model-derived state and readiness used by all views."""
    selected = mission_id.upper() if mission_id else current(root)["mission_id"]
    return {"result": "PASS", "state": state(root, selected),
            "readiness": readiness(root, selected),
            "next_action": next_action(root), "authoritative_source": PATH}

def explain(root: Path | str, mission_id: str) -> dict[str, Any]:
    result = readiness(root, mission_id)
    lifecycle = next(item["lifecycle"] for item in load(root)["missions"] if item["mission_id"] == mission_id)
    if lifecycle == "COMPLETED":
        rationale = "mission is complete; its successor is considered independently"
    elif result["classification"] == "ELIGIBLE":
        rationale = "mission is current and all authoritative prerequisites are satisfied"
    else:
        rationale = "mission is not eligible because authoritative prerequisites or lifecycle conditions are unmet"
    recommendation = recommend(root).get("recommendation") if mission_id == current(root)["mission_id"] else None
    return {
        "result": "PASS",
        "mission_id": mission_id,
        "lifecycle": lifecycle,
        "classification": result["classification"],
        "execution_eligibility": result["classification"] == "ELIGIBLE",
        "lifecycle_rationale": rationale,
        "blocking_conditions": result["blocking_conditions"],
        "missing_capabilities": result["missing_capabilities"],
        "missing_dependencies": result["missing_dependencies"],
        "successor_rule": "completed missions do not remain recommended; the next mission must independently satisfy readiness",
        "recommendation": recommendation,
        "authoritative_source": PATH,
    }

def brief(root: Path | str, mission_id: str) -> dict[str, Any]:
    """Return a deterministic, read-only engineering-intent projection."""
    value, by_id, _ = _missions(root)
    mission = by_id.get(mission_id)
    if mission is None:
        raise MissionKnowledgeError("MISSION_NOT_FOUND")
    objective = mission["roadmap_objective"]
    title = mission_id
    objective_path = Path(root) / mission["objective_source"]
    if objective_path.is_file():
        source = yaml.safe_load(objective_path.read_text(encoding="utf-8")) or {}
        title = source.get("title", title)
    sequence = value["mission_sequence"]
    capabilities = capability_registry.load(root)["capabilities"]
    introduced = [item["capability_id"] for item in capabilities
                  if item.get("mission_introduced") == mission_id
                  and item.get("lifecycle") == "Operational"]
    previous_id = sequence[sequence.index(mission_id) - 1] if sequence.index(mission_id) else None
    next_id = sequence[sequence.index(mission_id) + 1] if mission_id != sequence[-1] else None
    by_id = {item["mission_id"]: item for item in value["missions"]}
    recommendation = recommend(root).get("recommendation") if mission_id == current(root)["mission_id"] else None
    result = {
        "result": "PASS", "mission_id": mission_id, "mission_title": title,
        "engineering_objective": objective,
        "purpose": f"This mission exists to {objective[0].lower() + objective[1:]}",
        "operational_problem_solved": f"Lack of a qualified, controlled outcome for: {objective}",
        "capabilities_introduced": introduced or mission.get("capability_outcomes", []),
        "architectural_significance": "Advances the controlled Operational Alpha lifecycle through its authoritative gate contract.",
        "engineering_value": "Provides a deterministic, evidence-bound increment in the supervised execution lifecycle.",
        "operational_outcome_after_acceptance": f"{mission_id} is accepted and its immediate successor becomes eligible when prerequisites are satisfied.",
        "prerequisites": {"dependencies": mission.get("dependencies", []), "capabilities": mission.get("capability_prerequisites", []), "eligibility": mission.get("eligibility_criteria", [])},
        "completion_criteria": mission.get("completion_criteria", []),
        "expected_qualification_evidence": mission.get("evidence_relationships") or [f"{Path('engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/evidence') / mission_id}/VERIFIED"],
        "verification_commands": [f"zeus mission readiness {mission_id}", f"zeus mission blockers {mission_id}", f"zeus mission synchronization {mission_id}"],
        "successor_missions": [sequence[sequence.index(mission_id) + 1]] if mission_id != sequence[-1] else [],
        "risks_mitigated": ["unauthorized lifecycle advancement", "unbound or stale qualification evidence", "repository state drift"],
        "required_operator_authorization": "Explicit operator acceptance of the verified gate is required before successor eligibility.",
        "recommendation": recommendation,
        "previous_mission_summary": {"mission_id": previous_id, "lifecycle": by_id[previous_id]["lifecycle"] if previous_id else None, "objective": by_id[previous_id]["roadmap_objective"] if previous_id else None},
        "current_mission_summary": {"mission_id": mission_id, "lifecycle": mission["lifecycle"], "objective": objective},
        "next_mission_preview": {"mission_id": next_id, "lifecycle": by_id[next_id]["lifecycle"] if next_id else None, "objective": by_id[next_id]["roadmap_objective"] if next_id else None},
        "operational_alpha_progress": {"mission_number": sequence.index(mission_id) + 1, "total_missions": len(sequence), "completed": sum(1 for item in value["missions"] if item.get("lifecycle") == "COMPLETED"), "remaining": sum(1 for item in value["missions"] if item.get("lifecycle") != "COMPLETED"), "percent_complete": round(sum(1 for item in value["missions"] if item.get("lifecycle") == "COMPLETED") / len(sequence) * 100, 2)},
        "zeus_capability_delta": {"qualified_capabilities": introduced, "description": "Zeus can select only an integrity-qualified agent matching the authoritative execution profile."},
        "references": [mission["objective_source"], mission["roadmap_source"], *mission.get("controlled_document_relationships", [])],
        "authoritative_source": PATH, "roadmap_provenance": value["roadmap_provenance"],
    }
    result["brief_digest"] = _digest(result)
    return result

def prerequisites(root: Path | str, mission_id: str) -> dict[str, Any]:
    result = readiness(root, mission_id)
    value = {key: result[key] for key in ("mission_id", "lifecycle", "current_mission", "dependencies", "missing_dependencies", "prerequisite_capabilities", "missing_capabilities", "blocking_conditions", "authoritative_evidence")}
    value["recommendation"] = recommend(root).get("recommendation") if mission_id == current(root)["mission_id"] else None
    return value

def blockers(root: Path | str, mission_id: str) -> dict[str, Any]:
    """Resolve blockers for the requested mission, never an implicit OA-01."""
    result = readiness(root, mission_id)
    return {
        "mission_id": mission_id,
        "lifecycle": result["lifecycle"],
        "current_mission": result["current_mission"],
        "blocking_conditions": result["blocking_conditions"],
        "missing_capabilities": result["missing_capabilities"],
        "missing_dependencies": result["missing_dependencies"],
        "recommendation": recommend(root).get("recommendation") if mission_id == current(root)["mission_id"] else None,
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
    if decision["result"] != "PASS" or decision.get("readiness", {}).get("classification") != "ELIGIBLE":
        return {"result": "NO_ELIGIBLE_MISSION", "decision": decision}
    from scripts.lib.emp.dispatch_candidate import create
    candidate = create(Path(root))
    contract = {
        "mission_id": candidate["mission_id"],
        "selected_execution_agent": candidate["selected_execution_agent"],
        "required_capabilities": candidate["required_capabilities"],
        "authority_source": PATH,
        "execution_constraints": candidate["execution_constraints"],
        "expected_evidence_outputs": ["dispatch-contract", "capability-qualification", "operator-capability-summary", "synchronization-report", "validation-report"],
    }
    return {"result": "PASS", "transaction": "DETERMINISTIC_ORCHESTRATION",
            "decision_trace": {"recommendation": decision, "agent_count": 1},
            "dispatch_contract": contract, "authoritative_source": PATH}

def dispatch_verification(root: Path | str) -> dict[str, Any]:
    result = orchestration_verification(root)
    return {"result": result["result"], "dispatch": result.get("dispatch_contract"),
            "qualified_agents": result.get("qualified_agents", ([result["dispatch_contract"]["selected_execution_agent"]] if result.get("dispatch_contract") else [])),
            "authoritative_source": result.get("authoritative_source", PATH),
            "decision_trace": result.get("decision_trace")}
