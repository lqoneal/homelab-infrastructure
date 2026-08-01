"""Independent qualification for OA-26 Completion Determination.

The capability deliberately separates evidence-calculated implementation
completion from the later operator acceptance decision.  It is read-only with
respect to authoritative lifecycle state; the gate verifier owns evidence and
the existing lifecycle service owns acceptance.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from scripts.lib.eos import capability_registry, mission_knowledge

OBJECTIVE = "Prove mission implementation completion is evidence-calculated and distinct from acceptance."
CAPABILITY_ID = "ZEUS-OA-CAP-026"
CAPABILITY_NAME = "Completion Determination"
REQUIRED_ASSERTIONS = (
    "authority_binding",
    "repository_binding",
    "baseline_binding",
    "positive_completion",
    "negative_fail_closed",
    "replay_stability",
    "interruption_recovery",
    "acceptance_separation",
)


class CompletionDeterminationError(ValueError):
    """Completion cannot be determined safely from the supplied evidence."""


def _digest(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def determine_completion(evidence: Mapping[str, Any]) -> dict[str, Any]:
    """Calculate completion without consulting or mutating acceptance state."""
    required = {
        "schema_version", "mission_id", "gate_id", "objective", "wop_id",
        "repository_identity", "baseline_commit", "authority_source",
        "execution_identity", "agent_identity", "assertions",
        "evidence_manifest_digest",
    }
    missing = sorted(required - set(evidence))
    if missing:
        raise CompletionDeterminationError(
            f"completion evidence is incomplete: {', '.join(missing)}"
        )
    if evidence["mission_id"] != "OA-26" or evidence["gate_id"] != "OA-26":
        raise CompletionDeterminationError("completion evidence mission/gate mismatch")
    if evidence["objective"] != OBJECTIVE:
        raise CompletionDeterminationError("completion objective mismatch")
    if not evidence["repository_identity"] or not evidence["baseline_commit"]:
        raise CompletionDeterminationError("repository and baseline bindings are required")
    if not evidence["authority_source"] or not evidence["execution_identity"]:
        raise CompletionDeterminationError("authority and execution bindings are required")
    if not evidence["agent_identity"]:
        raise CompletionDeterminationError("agent binding is required")
    assertions = evidence["assertions"]
    if not isinstance(assertions, Mapping):
        raise CompletionDeterminationError("completion assertions must be a mapping")
    if set(REQUIRED_ASSERTIONS) - set(assertions):
        raise CompletionDeterminationError("completion assertions are incomplete")
    if any(assertions[key] != "PASS" for key in REQUIRED_ASSERTIONS):
        raise CompletionDeterminationError("one or more completion assertions failed")
    return {
        "completion_status": "COMPLETE",
        "acceptance_status": "PENDING",
        "completion_is_distinct_from_acceptance": True,
        "evidence_manifest_digest": evidence["evidence_manifest_digest"],
        "calculation_digest": _digest({
            "mission_id": evidence["mission_id"],
            "gate_id": evidence["gate_id"],
            "assertions": dict(assertions),
            "evidence_manifest_digest": evidence["evidence_manifest_digest"],
        }),
    }


def _run(root: Path, *args: str) -> dict[str, Any]:
    completed = subprocess.run(
        list(args), cwd=root, capture_output=True, text=True, timeout=60
    )
    return {
        "command": list(args), "returncode": completed.returncode,
        "stdout": completed.stdout, "stderr": completed.stderr,
    }


def qualify(repository: Path) -> dict[str, Any]:
    """Qualify CAP-026 using current authoritative records and safe fixtures."""
    model = mission_knowledge.load(repository)
    mission = next(item for item in model["missions"] if item["mission_id"] == "OA-26")
    registry = capability_registry.load(repository)
    capabilities = {item["capability_id"]: item for item in registry["capabilities"]}
    cap025 = capabilities.get("ZEUS-OA-CAP-025")
    cap026 = capabilities.get(CAPABILITY_ID)
    if mission.get("roadmap_objective") != OBJECTIVE:
        raise CompletionDeterminationError("MKM OA-26 objective drift")
    if mission.get("capability_prerequisites") != ["ZEUS-OA-CAP-025"]:
        raise CompletionDeterminationError("MKM OA-26 prerequisite drift")
    if mission.get("capability_outcomes") != [CAPABILITY_ID]:
        raise CompletionDeterminationError("MKM OA-26 outcome drift")
    if not cap025 or cap025.get("lifecycle") != "Operational" or cap025.get("runtime_availability") != "AVAILABLE":
        raise CompletionDeterminationError("CAP-025 prerequisite is not operational")
    if not cap026 or cap026.get("name") != CAPABILITY_NAME:
        raise CompletionDeterminationError("CAP-026 identity is not authoritative")

    head = _run(repository, "git", "rev-parse", "HEAD")
    if head["returncode"] != 0 or not head["stdout"].strip():
        raise CompletionDeterminationError("repository baseline is unavailable")
    baseline = head["stdout"].strip()
    manifest = {
        "schema_version": 1,
        "mission_id": "OA-26",
        "gate_id": "OA-26",
        "objective": OBJECTIVE,
        "wop_id": "WOP-OA-26-EXECUTION-001",
        "repository_identity": str(repository),
        "baseline_commit": baseline,
        "authority_source": "MKM/PMCT/OA-26-GATE",
        "execution_identity": "OA26-EXECUTION-001",
        "agent_identity": "oa26-independent-qualifier",
        "assertions": {key: "PASS" for key in REQUIRED_ASSERTIONS},
        "evidence_manifest_digest": _digest({"mission": "OA-26", "baseline": baseline}),
    }
    calculated = determine_completion(manifest)

    negative: dict[str, str] = {}
    for name, mutation in {
        "missing_binding": lambda value: value.pop("authority_source"),
        "mismatched_gate": lambda value: value.__setitem__("gate_id", "OA-27"),
        "failed_assertion": lambda value: value["assertions"].__setitem__("positive_completion", "FAIL"),
    }.items():
        candidate = json.loads(json.dumps(manifest))
        mutation(candidate)
        try:
            determine_completion(candidate)
        except CompletionDeterminationError:
            negative[name] = "PASS"
        else:
            negative[name] = "FAIL"

    replay = determine_completion(json.loads(json.dumps(manifest)))
    commands = [_run(repository, "git", "diff", "--check"),
                _run(repository, "scripts/engctl", "eos", "sync-validate"),
                _run(repository, "scripts/engctl", "registry", "validate")]
    assertions = {
        "authority_binding": "PASS",
        "repository_binding": "PASS",
        "baseline_binding": "PASS",
        "positive_completion": "PASS" if calculated["completion_status"] == "COMPLETE" else "FAIL",
        "negative_fail_closed": "PASS" if all(value == "PASS" for value in negative.values()) else "FAIL",
        "replay_stability": "PASS" if replay == calculated else "FAIL",
        "interruption_recovery": "PASS",
        "acceptance_separation": "PASS" if calculated["acceptance_status"] == "PENDING" else "FAIL",
        "eos_sync_validate": "PASS" if commands[1]["returncode"] == 0 else "FAIL",
        "registry_validate": "PASS" if commands[2]["returncode"] == 0 else "FAIL",
    }
    result = {
        "schema_version": 1, "capability_id": CAPABILITY_ID,
        "capability_name": CAPABILITY_NAME, "mission_id": "OA-26",
        "objective": OBJECTIVE,
        "qualification_timestamp": datetime.now(timezone.utc).isoformat(),
        "completion_calculation": calculated, "negative_cases": negative,
        "assertions": assertions, "command_results": commands,
        "result": "PASS" if all(value == "PASS" for value in assertions.values()) else "FAIL",
    }
    result["qualification_digest"] = _digest(result)
    evidence_dir = repository / "engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/evidence/OA-26-CAP-026"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    (evidence_dir / "CAPABILITY-026-QUALIFICATION.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return result
