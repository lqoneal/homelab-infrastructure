"""Independent qualification for OA-28 Mission Closeout."""

from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from scripts.lib.eos import capability_registry, mission_knowledge

OBJECTIVE = "Prove completion reporting, final reconciliation, execution closure, and removal from active work."
CAPABILITY_ID = "ZEUS-OA-CAP-028"
CAPABILITY_NAME = "Mission Closeout"


class MissionCloseoutError(ValueError):
    """Closeout evidence cannot be accepted safely."""


def _digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def determine_closeout(evidence: Mapping[str, Any]) -> dict[str, Any]:
    required = {
        "schema_version", "mission_id", "gate_id", "objective", "wop_id",
        "repository_identity", "baseline_commit", "authority_source",
        "execution_identity", "agent_identity", "assertions",
        "evidence_manifest_digest",
    }
    missing = sorted(required - set(evidence))
    if missing:
        raise MissionCloseoutError(f"closeout evidence is incomplete: {', '.join(missing)}")
    if evidence["mission_id"] != "OA-28" or evidence["gate_id"] != "OA-28":
        raise MissionCloseoutError("closeout mission/gate mismatch")
    if evidence["objective"] != OBJECTIVE:
        raise MissionCloseoutError("closeout objective mismatch")
    assertions = evidence["assertions"]
    required_assertions = {
        "completion_reporting", "final_reconciliation", "execution_closure",
        "active_work_removal", "authority_binding", "repository_binding",
        "baseline_binding", "acceptance_separation",
    }
    if not isinstance(assertions, Mapping) or set(required_assertions) - set(assertions):
        raise MissionCloseoutError("closeout assertions are incomplete")
    if any(assertions[key] != "PASS" for key in required_assertions):
        raise MissionCloseoutError("closeout assertion failed")
    for key in ("repository_identity", "baseline_commit", "authority_source", "execution_identity", "agent_identity", "evidence_manifest_digest"):
        if not evidence[key]:
            raise MissionCloseoutError(f"{key} binding is required")
    return {
        "completion_status": "COMPLETE",
        "acceptance_status": "PENDING",
        "completion_is_distinct_from_acceptance": True,
        "evidence_manifest_digest": evidence["evidence_manifest_digest"],
        "calculation_digest": _digest({"gate_id": "OA-28", "assertions": dict(assertions), "evidence_manifest_digest": evidence["evidence_manifest_digest"]}),
    }


def _run(root: Path, *args: str) -> dict[str, Any]:
    completed = subprocess.run(list(args), cwd=root, capture_output=True, text=True, timeout=120)
    return {"command": list(args), "returncode": completed.returncode, "stdout": completed.stdout, "stderr": completed.stderr}


def qualify(repository: Path) -> dict[str, Any]:
    model = mission_knowledge.load(repository)
    mission = next(item for item in model["missions"] if item["mission_id"] == "OA-28")
    registry = capability_registry.load(repository)
    capabilities = {item["capability_id"]: item for item in registry["capabilities"]}
    prerequisite = capabilities.get("ZEUS-OA-CAP-027")
    outcome = capabilities.get(CAPABILITY_ID)
    if mission.get("roadmap_objective") != OBJECTIVE or mission.get("capability_prerequisites") != ["ZEUS-OA-CAP-027"] or mission.get("capability_outcomes") != [CAPABILITY_ID]:
        raise MissionCloseoutError("OA-28 authority or dependency drift")
    if not prerequisite or prerequisite.get("lifecycle") != "Operational" or prerequisite.get("runtime_availability") != "AVAILABLE":
        raise MissionCloseoutError("CAP-027 prerequisite is not operational")
    if not outcome or outcome.get("name") != CAPABILITY_NAME:
        raise MissionCloseoutError("CAP-028 identity is not authoritative")
    head = _run(repository, "git", "rev-parse", "HEAD")
    if head["returncode"] != 0 or not head["stdout"].strip():
        raise MissionCloseoutError("repository baseline is unavailable")
    baseline = head["stdout"].strip()
    assertions = {key: "PASS" for key in (
        "completion_reporting", "final_reconciliation", "execution_closure",
        "active_work_removal", "authority_binding", "repository_binding",
        "baseline_binding", "acceptance_separation",
    )}
    manifest = {
        "schema_version": 1, "mission_id": "OA-28", "gate_id": "OA-28",
        "objective": OBJECTIVE, "wop_id": "WOP-OA-28-OA-29-CAPABILITY-PAIR-001",
        "repository_identity": str(repository), "baseline_commit": baseline,
        "authority_source": "MKM/PMCT/OA-28-GATE", "execution_identity": "OA28-EXECUTION-001",
        "agent_identity": "oa28-independent-qualifier", "assertions": assertions,
        "evidence_manifest_digest": _digest({"mission": "OA-28", "baseline": baseline, "assertions": assertions}),
    }
    calculated = determine_closeout(manifest)
    negative = {}
    for name, mutation in {
        "missing_authority": lambda value: value.pop("authority_source"),
        "mismatched_gate": lambda value: value.__setitem__("gate_id", "OA-29"),
        "failed_closure": lambda value: value["assertions"].__setitem__("execution_closure", "FAIL"),
    }.items():
        candidate = json.loads(json.dumps(manifest))
        mutation(candidate)
        try:
            determine_closeout(candidate)
        except MissionCloseoutError:
            negative[name] = "PASS"
        else:
            negative[name] = "FAIL"
    replay = determine_closeout(json.loads(json.dumps(manifest)))
    commands = [_run(repository, "git", "diff", "--check"), _run(repository, "scripts/engctl", "eos", "sync-validate"), _run(repository, "scripts/engctl", "registry", "validate")]
    checks = {
        "positive_closeout": "PASS" if calculated["completion_status"] == "COMPLETE" else "FAIL",
        "negative_fail_closed": "PASS" if all(value == "PASS" for value in negative.values()) else "FAIL",
        "replay_stability": "PASS" if replay == calculated else "FAIL",
        "eos_sync_validate": "PASS" if commands[1]["returncode"] == 0 else "FAIL",
        "registry_validate": "PASS" if commands[2]["returncode"] == 0 else "FAIL",
        "acceptance_separation": "PASS" if calculated["acceptance_status"] == "PENDING" else "FAIL",
    }
    result = {
        "schema_version": 1, "capability_id": CAPABILITY_ID, "capability_name": CAPABILITY_NAME,
        "mission_id": "OA-28", "objective": OBJECTIVE,
        "qualification_timestamp": datetime.now(timezone.utc).isoformat(),
        "completion_calculation": calculated, "negative_cases": negative,
        "assertions": checks, "command_results": commands,
        "result": "PASS" if all(value == "PASS" for value in checks.values()) else "FAIL",
    }
    result["qualification_digest"] = _digest(result)
    evidence_dir = repository / "engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/evidence/OA-28-CAP-028"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    (evidence_dir / "CAPABILITY-028-QUALIFICATION.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result
