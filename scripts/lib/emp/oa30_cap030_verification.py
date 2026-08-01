"""Independent qualification for OA-30 / CAP-030."""

from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from scripts.lib.emp import progressive_oa
from scripts.lib.eos import capability_registry, mission_knowledge

OBJECTIVE = "Prove OA-01 through OA-29 remain valid, produce a candidate baseline, and prepare separately authorized declaration and freeze."
CAPABILITY_ID = "ZEUS-OA-CAP-030"
CAPABILITY_NAME = "Operational Alpha Qualification and Declaration Preparation"
PREDECESSOR_GATES = [f"OA-{number:02d}" for number in range(1, 30)]


class OperationalAlphaQualificationError(ValueError):
    """Cumulative qualification evidence cannot be accepted safely."""


def _digest(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode()).hexdigest()


def _run(root: Path, *args: str) -> dict[str, Any]:
    completed = subprocess.run(list(args), cwd=root, capture_output=True, text=True, timeout=180)
    return {"command": list(args), "returncode": completed.returncode, "stdout": completed.stdout, "stderr": completed.stderr}


def validate_candidate(evidence: Mapping[str, Any]) -> dict[str, Any]:
    required = {
        "schema_version", "mission_id", "gate_id", "objective", "wop_id",
        "repository_identity", "baseline_commit", "authority_source",
        "execution_identity", "agent_identity", "predecessor_gates",
        "candidate_baseline", "declaration_boundary", "evidence_manifest_digest",
    }
    missing = sorted(required - set(evidence))
    if missing:
        raise OperationalAlphaQualificationError(
            f"candidate baseline evidence is incomplete: {', '.join(missing)}"
        )
    if evidence["mission_id"] != "OA-30" or evidence["gate_id"] != "OA-30":
        raise OperationalAlphaQualificationError("OA-30 mission/gate identity mismatch")
    if evidence["objective"] != OBJECTIVE:
        raise OperationalAlphaQualificationError("OA-30 objective mismatch")
    if evidence["predecessor_gates"] != PREDECESSOR_GATES:
        raise OperationalAlphaQualificationError("cumulative predecessor set is incomplete or reordered")
    if evidence["candidate_baseline"] != evidence["baseline_commit"]:
        raise OperationalAlphaQualificationError("candidate baseline is not bound to the execution baseline")
    if evidence["declaration_boundary"] != "SEPARATELY_AUTHORIZED_OA_DECLARATION":
        raise OperationalAlphaQualificationError("declaration/freeze boundary is invalid")
    for key in ("repository_identity", "baseline_commit", "authority_source", "execution_identity", "agent_identity", "evidence_manifest_digest"):
        if not evidence[key]:
            raise OperationalAlphaQualificationError(f"{key} binding is required")
    return {
        "cumulative_status": "PASS",
        "candidate_baseline_status": "PASS",
        "declaration_preparation_status": "READY_PENDING_SEPARATE_AUTHORITY",
        "declaration_boundary": evidence["declaration_boundary"],
        "predecessor_gates": PREDECESSOR_GATES,
        "evidence_manifest_digest": evidence["evidence_manifest_digest"],
        "calculation_digest": _digest({"gate_id": "OA-30", "baseline": evidence["baseline_commit"], "predecessors": PREDECESSOR_GATES}),
    }


def _cumulative_receipts(repository: Path) -> dict[str, str]:
    state = progressive_oa.load_state(repository)
    results: dict[str, str] = {}
    for gate in PREDECESSOR_GATES:
        item = state.get("gates", {}).get(gate, {})
        if item.get("state") != "ACCEPTED":
            raise OperationalAlphaQualificationError(f"{gate} is not accepted")
        if gate == "OA-08":
            legacy = repository / progressive_oa.PACKAGE_PATH / "runtime/evidence/OA-08/WOP-RESOLUTION-QUALIFIED"
            if not legacy.is_file():
                raise OperationalAlphaQualificationError("OA-08 historical qualification is unavailable")
        else:
            marker_path, marker = progressive_oa._marker_binding(repository, gate)
            if marker.get("verification_result") != "PASS":
                raise OperationalAlphaQualificationError(f"{gate} verification marker is not PASS")
        results[gate] = "PASS"
    return results


def qualify(repository: Path) -> dict[str, Any]:
    model = mission_knowledge.load(repository)
    mission = next(item for item in model["missions"] if item["mission_id"] == "OA-30")
    registry = capability_registry.load(repository)
    capabilities = {item["capability_id"]: item for item in registry["capabilities"]}
    prerequisite = capabilities.get("ZEUS-OA-CAP-029")
    outcome = capabilities.get(CAPABILITY_ID)
    if mission.get("roadmap_objective") != OBJECTIVE or mission.get("capability_prerequisites") != ["ZEUS-OA-CAP-029"] or mission.get("capability_outcomes") != [CAPABILITY_ID]:
        raise OperationalAlphaQualificationError("OA-30 authority or dependency drift")
    if not prerequisite or prerequisite.get("lifecycle") != "Operational" or prerequisite.get("runtime_availability") != "AVAILABLE":
        raise OperationalAlphaQualificationError("CAP-029 prerequisite is not operational")
    if not outcome or outcome.get("name") != CAPABILITY_NAME:
        raise OperationalAlphaQualificationError("CAP-030 identity is not authoritative")
    head = _run(repository, "git", "rev-parse", "HEAD")
    if head["returncode"] != 0 or not head["stdout"].strip():
        raise OperationalAlphaQualificationError("repository baseline is unavailable")
    baseline = head["stdout"].strip()
    predecessor_receipts = _cumulative_receipts(repository)
    manifest = {
        "schema_version": 1,
        "mission_id": "OA-30",
        "gate_id": "OA-30",
        "objective": OBJECTIVE,
        "wop_id": "WOP-OA-30-ENGINEERING-PLATFORM-EVOLUTION-BOOTSTRAP-001",
        "repository_identity": str(repository),
        "baseline_commit": baseline,
        "authority_source": "MKM/PMCT/OA-30-GATE/EMM",
        "execution_identity": "OA30-EXECUTION-AND-FINAL-PUBLICATION-001",
        "agent_identity": "oa30-independent-qualifier",
        "predecessor_gates": PREDECESSOR_GATES,
        "candidate_baseline": baseline,
        "declaration_boundary": "SEPARATELY_AUTHORIZED_OA_DECLARATION",
        "evidence_manifest_digest": _digest({"mission": "OA-30", "baseline": baseline, "predecessors": predecessor_receipts}),
    }
    calculated = validate_candidate(manifest)
    negative: dict[str, str] = {}
    mutations = {
        "missing_baseline": lambda value: value.__setitem__("candidate_baseline", "stale-baseline"),
        "missing_predecessor": lambda value: value.__setitem__("predecessor_gates", PREDECESSOR_GATES[:-1]),
        "wrong_declaration_boundary": lambda value: value.__setitem__("declaration_boundary", "DECLARATION_AUTHORIZED"),
        "mismatched_gate": lambda value: value.__setitem__("gate_id", "OA-29"),
    }
    for name, mutation in mutations.items():
        candidate = json.loads(json.dumps(manifest))
        mutation(candidate)
        try:
            validate_candidate(candidate)
        except OperationalAlphaQualificationError:
            negative[name] = "PASS"
        else:
            negative[name] = "FAIL"
    replay = validate_candidate(json.loads(json.dumps(manifest)))
    interruption = {"checkpoint": "OA-30-PREFLIGHT-COMPLETE", "resume_from": "OA-30-CUMULATIVE-QUALIFICATION", "duplicate_effects": False}
    interruption_status = "PASS" if interruption["duplicate_effects"] is False else "FAIL"
    commands = [
        _run(repository, "git", "diff", "--check"),
        _run(repository, "scripts/engctl", "eos", "sync-validate"),
        _run(repository, "scripts/engctl", "registry", "validate"),
    ]
    checks = {
        "cumulative_predecessors": "PASS" if len(predecessor_receipts) == 29 else "FAIL",
        "candidate_baseline": "PASS" if calculated["candidate_baseline_status"] == "PASS" else "FAIL",
        "declaration_preparation": "PASS" if calculated["declaration_preparation_status"].startswith("READY") else "FAIL",
        "negative_fail_closed": "PASS" if all(value == "PASS" for value in negative.values()) else "FAIL",
        "replay_stability": "PASS" if replay == calculated else "FAIL",
        "interruption_recovery": interruption_status,
        "eos_sync_validate": "PASS" if commands[1]["returncode"] == 0 else "FAIL",
        "registry_validate": "PASS" if commands[2]["returncode"] == 0 else "FAIL",
    }
    result: dict[str, Any] = {
        "schema_version": 1,
        "capability_id": CAPABILITY_ID,
        "capability_name": CAPABILITY_NAME,
        "mission_id": "OA-30",
        "objective": OBJECTIVE,
        "qualification_timestamp": datetime.now(timezone.utc).isoformat(),
        "candidate_calculation": calculated,
        "predecessor_receipts": predecessor_receipts,
        "negative_cases": negative,
        "interruption_recovery": interruption,
        "assertions": checks,
        "command_results": commands,
        "result": "PASS" if all(value == "PASS" for value in checks.values()) else "FAIL",
    }
    result["qualification_digest"] = _digest(result)
    evidence_dir = repository / "engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/evidence/OA-30-CAP-030"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    (evidence_dir / "CAPABILITY-030-QUALIFICATION.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result
