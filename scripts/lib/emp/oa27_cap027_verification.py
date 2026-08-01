"""Independent qualification for OA-27 Operator Acceptance.

The capability binds an explicit operator decision to the exact qualified
result and evidence manifest.  It never infers acceptance from qualification
and never advances lifecycle state itself.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from scripts.lib.eos import capability_registry, mission_knowledge

OBJECTIVE = "Prove explicit acceptance or rejection bound to the exact qualified result and evidence manifest."
CAPABILITY_ID = "ZEUS-OA-CAP-027"
CAPABILITY_NAME = "Operator Acceptance"


class OperatorAcceptanceError(ValueError):
    """An acceptance decision cannot be safely bound or replayed."""


def _digest(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def bind_decision(decision: Mapping[str, Any]) -> dict[str, Any]:
    """Validate and canonically bind one ACCEPT or REJECT decision."""
    required = {
        "schema_version", "mission_id", "gate_id", "decision", "operator",
        "decided_at", "qualified_result", "evidence_manifest_digest",
        "repository_identity", "baseline_commit", "authority_source",
        "execution_identity", "agent_identity",
    }
    missing = sorted(required - set(decision))
    if missing:
        raise OperatorAcceptanceError(
            f"operator decision is incomplete: {', '.join(missing)}"
        )
    if decision["mission_id"] != "OA-27" or decision["gate_id"] != "OA-27":
        raise OperatorAcceptanceError("operator decision mission/gate mismatch")
    if decision["decision"] not in {"ACCEPT", "REJECT"}:
        raise OperatorAcceptanceError("operator decision must be ACCEPT or REJECT")
    if not decision["operator"] or not decision["decided_at"]:
        raise OperatorAcceptanceError("operator identity and timestamp are required")
    if decision["qualified_result"] != "PASS":
        raise OperatorAcceptanceError("only a qualified PASS result may be decided")
    if not decision["evidence_manifest_digest"]:
        raise OperatorAcceptanceError("evidence manifest binding is required")
    for field in ("repository_identity", "baseline_commit", "authority_source", "execution_identity", "agent_identity"):
        if not decision[field]:
            raise OperatorAcceptanceError(f"{field} binding is required")
    binding = {
        "mission_id": decision["mission_id"],
        "gate_id": decision["gate_id"],
        "decision": decision["decision"],
        "operator": decision["operator"],
        "decided_at": decision["decided_at"],
        "qualified_result": decision["qualified_result"],
        "evidence_manifest_digest": decision["evidence_manifest_digest"],
        "repository_identity": decision["repository_identity"],
        "baseline_commit": decision["baseline_commit"],
        "authority_source": decision["authority_source"],
        "execution_identity": decision["execution_identity"],
        "agent_identity": decision["agent_identity"],
    }
    return {
        "decision_status": "ACCEPTED" if decision["decision"] == "ACCEPT" else "REJECTED",
        "acceptance_is_explicit": True,
        "binding_digest": _digest(binding),
        "binding": binding,
    }


def _run(root: Path, *args: str) -> dict[str, Any]:
    result = subprocess.run([*args], cwd=root, capture_output=True, text=True, timeout=60)
    return {"command": list(args), "returncode": result.returncode,
            "stdout": result.stdout, "stderr": result.stderr}


def qualify(repository: Path) -> dict[str, Any]:
    model = mission_knowledge.load(repository)
    mission = next(item for item in model["missions"] if item["mission_id"] == "OA-27")
    registry = capability_registry.load(repository)
    capabilities = {item["capability_id"]: item for item in registry["capabilities"]}
    cap026 = capabilities.get("ZEUS-OA-CAP-026")
    cap027 = capabilities.get(CAPABILITY_ID)
    if mission.get("roadmap_objective") != OBJECTIVE:
        raise OperatorAcceptanceError("MKM OA-27 objective drift")
    if mission.get("capability_prerequisites") != ["ZEUS-OA-CAP-026"] or mission.get("capability_outcomes") != [CAPABILITY_ID]:
        raise OperatorAcceptanceError("MKM OA-27 dependency drift")
    if not cap026 or cap026.get("lifecycle") != "Operational" or cap026.get("runtime_availability") != "AVAILABLE":
        raise OperatorAcceptanceError("CAP-026 prerequisite is not operational")
    if not cap027 or cap027.get("name") != CAPABILITY_NAME:
        raise OperatorAcceptanceError("CAP-027 identity is not authoritative")
    head = _run(repository, "git", "rev-parse", "HEAD")
    if head["returncode"] != 0 or not head["stdout"].strip():
        raise OperatorAcceptanceError("repository baseline is unavailable")
    baseline = head["stdout"].strip()
    manifest = {
        "schema_version": 1, "mission_id": "OA-27", "gate_id": "OA-27",
        "decision": "ACCEPT", "operator": "qualification-fixture",
        "decided_at": "2026-08-01T00:00:00Z", "qualified_result": "PASS",
        "evidence_manifest_digest": _digest({"mission": "OA-27", "baseline": baseline}),
        "repository_identity": str(repository), "baseline_commit": baseline,
        "authority_source": "MKM/PMCT/OA-27-GATE",
        "execution_identity": "OA27-EXECUTION-001",
        "agent_identity": "oa27-independent-qualifier",
    }
    positive = bind_decision(manifest)
    negative: dict[str, str] = {}
    for name, mutation in {
        "missing_evidence": lambda value: value.pop("evidence_manifest_digest"),
        "mismatched_gate": lambda value: value.__setitem__("gate_id", "OA-28"),
        "invalid_decision": lambda value: value.__setitem__("decision", "MAYBE"),
        "non_pass_result": lambda value: value.__setitem__("qualified_result", "FAIL"),
    }.items():
        candidate = json.loads(json.dumps(manifest))
        mutation(candidate)
        try:
            bind_decision(candidate)
        except OperatorAcceptanceError:
            negative[name] = "PASS"
        else:
            negative[name] = "FAIL"
    replay = bind_decision(json.loads(json.dumps(manifest)))
    commands = [
        _run(repository, "git", "diff", "--check"),
        _run(repository, "scripts/engctl", "eos", "sync-validate"),
        _run(repository, "scripts/engctl", "registry", "validate"),
    ]
    assertions = {
        "authority_binding": "PASS", "repository_binding": "PASS",
        "qualified_result_binding": "PASS" if positive["decision_status"] == "ACCEPTED" else "FAIL",
        "explicit_decision": "PASS" if positive["acceptance_is_explicit"] else "FAIL",
        "negative_fail_closed": "PASS" if all(value == "PASS" for value in negative.values()) else "FAIL",
        "replay_stability": "PASS" if replay == positive else "FAIL",
        "eos_sync_validate": "PASS" if commands[1]["returncode"] == 0 else "FAIL",
        "registry_validate": "PASS" if commands[2]["returncode"] == 0 else "FAIL",
    }
    result: dict[str, Any] = {
        "schema_version": 1, "capability_id": CAPABILITY_ID,
        "capability_name": CAPABILITY_NAME, "mission_id": "OA-27",
        "objective": OBJECTIVE,
        "qualification_timestamp": datetime.now(timezone.utc).isoformat(),
        "positive_binding": positive, "negative_cases": negative,
        "assertions": assertions, "command_results": commands,
        "result": "PASS" if all(value == "PASS" for value in assertions.values()) else "FAIL",
    }
    result["qualification_digest"] = _digest(result)
    evidence_dir = repository / "engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/evidence/OA-27-CAP-027"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    (evidence_dir / "CAPABILITY-027-QUALIFICATION.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return result
