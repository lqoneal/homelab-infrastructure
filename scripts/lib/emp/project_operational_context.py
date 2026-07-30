"""Repository-only Project and Operational Context Reconstruction."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

import yaml

from scripts.lib.emp import progressive_oa
from scripts.lib.emp.controlled_mission_authority import ControlledMissionAuthority
from scripts.lib.emp.mission_resolution import resolve as resolve_mission


class ContextReconstructionError(ValueError):
    def __init__(self, result: dict[str, Any]):
        self.result = result
        super().__init__(f"{result['reconstruction']}: {result['reason']}")


def _digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(
        value, sort_keys=True, separators=(",", ":")
    ).encode()).hexdigest()


def _load(path: Path) -> Any:
    try:
        text = path.read_text(encoding="utf-8")
        return json.loads(text) if path.suffix == ".json" else yaml.safe_load(text)
    except (OSError, json.JSONDecodeError, yaml.YAMLError) as error:
        raise ValueError(f"{path}: {error}") from error


def _source(root: Path, path: Path) -> dict[str, str]:
    return {"locator": str(path.relative_to(root)),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def _denied(reason: str, checks: list[dict[str, str]]) -> dict[str, Any]:
    value = {
        "schema_version": 1,
        "capability": "Project and Operational Context Reconstruction",
        "reconstruction": "STOPPED_FAIL_CLOSED", "reconstructed": False,
        "reason": reason, "checks": checks, "repository_only": True,
        "protected_effects_allowed": False, "execution_agent_dispatched": False,
        "mission_executed": False, "next_authorized_action": "STOP_FAIL_CLOSED",
    }
    value["context_digest"] = _digest(value)
    return value


def reconstruct(root: Path | str, *,
                sources: Mapping[str, Path | str | None] | None = None,
                observed: Mapping[str, str] | None = None) -> dict[str, Any]:
    repository = Path(root).resolve()
    package = repository / progressive_oa.PACKAGE_PATH
    paths: dict[str, Path | None] = {
        "registry": repository / "engineering/registry/work-registry.yaml",
        "project_state": repository / "docs/project/PROJ-0001-PROJECT_STATE.md",
        "runtime_state": package / "runtime/state.json",
        "mission_contract": repository / "engineering/mission-contracts/contracts/MC-MISSION-CONTRACT-PUBLICATION-001.yaml",
        "wop": package / "immutable-wop.yaml",
        "execution_interface": repository / "engineering/execution/execution-interface.yaml",
        "admission_runtime": repository / "engineering/operations/zeus-mission-admission-runtime.md",
        "execution_runtime": repository / "engineering/operations/zeus-mission-execution-runtime.md",
        "agent_registry": repository / "engineering/dispatch/execution-agent-registry.json",
        "eens_policy": repository / "engineering/eens/production-eens-policy.yaml",
        "eos_authority": repository / "engineering/eos/repository-eos-authority.yaml",
        "gate_specification": package / "gate-specification.yaml",
        "pmct_contract": repository / "engineering/tests/zeus-operational-alpha/PMCT-CONTRACT.md",
        "pmct_matrix": repository / "engineering/tests/zeus-operational-alpha/PMCT-CAPABILITY-MATRIX.yaml",
    }
    for name, path in (sources or {}).items():
        paths[name] = None if path is None else Path(path)
    checks: list[dict[str, str]] = []

    def fail(reason: str) -> dict[str, Any]:
        checks.append({"check": "context_reconstruction", "result": "FAIL", "detail": reason})
        return _denied(reason, checks)

    try:
        for name, path in paths.items():
            if path is None or not path.is_file():
                return fail(f"authoritative source missing: {name}")
        authority = ControlledMissionAuthority(
            repository, expected_gate="OA-04", observed=observed,
            sources={"registry": paths["registry"], "project_state": paths["project_state"],
                     "state": paths["runtime_state"]},
        ).require(boundary="oa04_context_reconstruction")
        resolution = resolve_mission(
            repository, observed=observed,
            sources={"registry": paths["registry"], "wop": paths["wop"],
                     "execution_interface": paths["execution_interface"]},
        )
        if not resolution["resolved"]:
            return fail(resolution["reason"])
        registry = _load(paths["registry"])
        state = _load(paths["runtime_state"])
        agent_registry = _load(paths["agent_registry"])
    except ValueError as error:
        return fail(str(error))

    entities = registry.get("entities", {})

    def one(collection: str, identity: str) -> dict[str, Any]:
        matches = [item for item in entities.get(collection, [])
                   if item.get("registry_id") == identity]
        if len(matches) != 1:
            raise ValueError(f"{collection} identity missing or ambiguous: {identity}")
        return matches[0]

    try:
        work = one("work_items", authority["work_item_id"])
        mission = one("missions", work["mission_id"])
        phase = one("phases", work["phase_id"])
        project = one("projects", work["project_id"])
    except ValueError as error:
        return fail(str(error))
    if any(str(item.get("management_state", "")).lower() != "active"
           for item in (work, mission, phase, project)):
        return fail("project, mission, phase, and work must all be active")
    if phase.get("mission_id") != mission["registry_id"] or mission.get("project_id") != project["registry_id"]:
        return fail("project/mission/phase/work hierarchy is inconsistent")
    checks.append({"check": "project_operational_hierarchy", "result": "PASS",
                   "detail": project["registry_id"]})

    active_gate = state.get("active_gate")
    gate_state = state.get("gates", {}).get("OA-04", {}).get("state")
    later = {gate: item for gate, item in state.get("gates", {}).items() if gate > "OA-04"}
    if active_gate != "OA-04" or gate_state != "AWAITING_OPERATOR_VERIFICATION":
        return fail("OA-04 lifecycle state is not current")
    if any(item.get("state") != "PENDING" or item.get("acceptance_receipt") is not None
           for item in later.values()):
        return fail("later gate activity detected")
    checks.append({"check": "gate_lifecycle", "result": "PASS",
                   "detail": "OA-04 AWAITING_OPERATOR_VERIFICATION"})

    agents = agent_registry.get("agents", [])
    qualified = [item for item in agents if
                 str(item.get("qualification_status", item.get("status", ""))).upper() == "QUALIFIED"]
    admission_records = sorted((repository / ".zeus/runtime/mission-admissions").glob("*.json"))
    admission_states: dict[str, int] = {}
    for path in admission_records:
        record = _load(path)
        status = str(record.get("state", record.get("status", "UNKNOWN")))
        admission_states[status] = admission_states.get(status, 0) + 1
    source_records = {name: _source(repository, path) for name, path in sorted(paths.items())
                      if path is not None}
    blockers = [
        "OA-04 explicit operator acceptance is required before OA-05 eligibility",
        "OA-05 and later are pending and ineligible",
    ]
    if not qualified:
        blockers.append("no production execution agent is qualified")
    value = {
        "schema_version": 1, "capability": "Project and Operational Context Reconstruction",
        "reconstruction": "RECONSTRUCTED", "reconstructed": True, "repository_only": True,
        "repository": {
            "identity": authority["repository_identity"], "root": authority["repository_root"],
            "branch": authority["branch"], "head": authority["head"],
            "upstream": authority["upstream"], "qualified_baseline": authority["qualified_baseline"],
            "contract_baseline": authority["contract_baseline"],
        },
        "project": {"id": project["registry_id"], "title": project["title"], "state": project["management_state"]},
        "phase": {"id": phase["registry_id"], "title": phase["title"], "state": phase["management_state"]},
        "mission": {"id": mission["registry_id"], "title": mission["title"], "state": mission["management_state"]},
        "work_item": {"id": work["registry_id"], "title": work["title"], "state": work["management_state"]},
        "governing_authority": {"status": authority["contract_authorization_status"],
                                "source": authority["authority_source"],
                                "digest": authority["authority_digest"]},
        "mission_contract": {"id": authority["contract_id"], "lifecycle": authority["contract_lifecycle"],
                             **source_records["mission_contract"]},
        "admitted_wop": {"id": authority["wop_id"], "admission_state": authority["wop_admission_state"],
                         **source_records["wop"]},
        "gate_lifecycle": {
            "active_gate": active_gate, "state": gate_state,
            "accepted_gates": sorted(g for g, item in state["gates"].items()
                                     if item.get("state") == "ACCEPTED"),
            "later_gates": {g: item["state"] for g, item in later.items()},
        },
        "execution_runtime": {"state": state["status"], "dispatcher": "NOT_AUTHORIZED_FOR_OA-04",
                              "execution_agent_dispatched": False, "mission_executed": False},
        "mission_admission_runtime": {"package_admission": authority["wop_admission_state"],
                                      "operational_records": len(admission_records),
                                      "states": admission_states},
        "agent_qualification": {"state": "QUALIFIED_NOT_DISPATCHED" if qualified else "UNQUALIFIED",
                                "registered_agents": len(agents), "qualified_agents": len(qualified)},
        "eens_integration": {"state": "CONFIGURED_NOT_EXERCISED_BY_OA-04",
                             **source_records["eens_policy"]},
        "approval_requirements": authority["required_approvals"], "blockers": blockers,
        "next_authorized_action": "OPERATOR_VERIFY_AND_DECIDE_OA-04",
        "reconciliation": {"repository_eos": "SYNCHRONIZED",
                           "project_registry_runtime": "CONSISTENT"},
        "mission_resolution": resolution, "authoritative_sources": source_records,
        "checks": checks, "protected_effects_allowed": False,
        "execution_agent_dispatched": False, "mission_executed": False,
    }
    value["context_digest"] = _digest(value)
    return value


def require(root: Path | str, **kwargs: Any) -> dict[str, Any]:
    result = reconstruct(root, **kwargs)
    if not result["reconstructed"]:
        raise ContextReconstructionError(result)
    return result
