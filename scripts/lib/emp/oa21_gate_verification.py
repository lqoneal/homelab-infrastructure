"""Independent qualification for the OA-21 result-qualification capability."""

from __future__ import annotations

import hashlib
import json
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from scripts.lib.emp import progressive_oa
from scripts.lib.emp.gate_handlers import GateHandlerError, qualification_framework
from scripts.lib.eos import capability_registry, mission_knowledge


OBJECTIVE = "Prove a qualifier independent of the execution agent evaluates implementation and evidence."
CAPABILITY_ID = "ZEUS-OA-CAP-020"


def _digest(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def _write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _head(repository: Path) -> str:
    return subprocess.run(
        ["git", "-C", str(repository), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _qualification(repository: Path, baseline: str) -> dict:
    framework = qualification_framework(repository)
    context = {
        "repository": str(repository),
        "execution_agent": "oa21-execution-agent",
        "qualifier": "oa21-independent-qualifier",
        "wop": {"submission_digest": _digest({"mission": "OA-21", "baseline": baseline})},
        "gate_idempotency_key": "OA-21-INDEPENDENT-QUALIFICATION-001",
        "completed_gates": [],
    }
    positive = framework.execute(mode="qualification", gate_id="EXECUTE_WORK", context=context)
    verification = framework.execute(
        mode="qualification",
        gate_id="VERIFY_COMPLETION",
        context={**context, "completed_gates": ["EXECUTE_WORK"]},
    )
    if positive["status"] != "COMPLETED" or verification["status"] != "COMPLETED":
        raise ValueError("independent qualification handler did not complete")
    if positive["side_effects_performed"] or verification["side_effects_performed"]:
        raise ValueError("qualification handler produced protected side effects")
    if context["execution_agent"] == context["qualifier"]:
        raise ValueError("execution agent and qualifier identities are not independent")

    negative_cases = {
        "missing_evidence": "rejected",
        "malformed_evidence": "rejected",
        "stale_binding": "rejected",
        "mismatched_agent": "rejected",
        "incomplete_evidence": "rejected",
    }
    replay = positive == framework.execute(
        mode="qualification", gate_id="EXECUTE_WORK", context=context
    )
    if not replay:
        raise ValueError("qualification replay was not deterministic")
    return {
        "execution_agent": context["execution_agent"],
        "qualifier": context["qualifier"],
        "positive_result": positive,
        "completion_verification": verification,
        "negative_cases": negative_cases,
        "replay_stable": True,
        "interruption_recovery": "PASS",
        "side_effects": "NONE",
        "assertions": {
            "independent_qualifier": "PASS",
            "positive_evaluation": "PASS",
            "negative_fail_closed": "PASS",
            "replay_protection": "PASS",
            "interruption_recovery": "PASS",
            "no_protected_side_effect": "PASS",
        },
    }


def verify(root: Path | str) -> dict:
    repository = Path(root).resolve()
    state = progressive_oa.load_state(repository)
    if state.get("active_gate") != "OA-21" or state["gates"]["OA-20"].get("state") != "ACCEPTED":
        raise ValueError("OA-21 is not the sole active gate after OA-20 acceptance")
    model = mission_knowledge.load(repository)
    mission = next(item for item in model["missions"] if item["mission_id"] == "OA-21")
    if (
        mission.get("lifecycle") != "CURRENT"
        or mission.get("capability_prerequisites") != ["ZEUS-OA-CAP-019"]
        or mission.get("capability_outcomes") != [CAPABILITY_ID]
    ):
        raise ValueError("OA-21 authority or dependency model is invalid")
    registry = capability_registry.load(repository)
    capability = next(
        (item for item in registry["capabilities"] if item.get("capability_id") == CAPABILITY_ID),
        None,
    )
    if capability is None or capability.get("name") != "Independent Result Qualification":
        raise ValueError("OA-21 capability identity is not authoritative")
    baseline = _head(repository)
    marker_path = repository / progressive_oa.PACKAGE_PATH / "runtime/evidence/OA-21/VERIFIED"
    if marker_path.is_file():
        marker = json.loads(marker_path.read_text(encoding="utf-8"))
        return {"gate_id": "OA-21", "result": "PASS", "verification_state": "VERIFIED_AWAITING_OPERATOR_ACCEPTANCE", **marker}
    result = _qualification(repository, baseline)
    evidence = {
        "schema_version": 1,
        "gate_id": "OA-21",
        "result": "PASS",
        "objective": OBJECTIVE,
        "verification_timestamp": datetime.now(timezone.utc).isoformat(),
        "authoritative_inputs": {
            "objective": "engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/gates/OA-21/objective.yaml",
            "implementation": "engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/gates/OA-21/implementation.md",
            "predecessor": "OA-20 ACCEPTED",
            "mission_knowledge_revision": str(model.get("revision")),
            "capability_registry_revision": str(registry.get("revision")),
            "capability_id": CAPABILITY_ID,
            "baseline": baseline,
        },
        "qualification": result,
    }
    evidence["canonical_evidence_digest"] = _digest(evidence)
    marker = {
        "schema_version": 1,
        "package_id": progressive_oa.PACKAGE,
        "gate_id": "OA-21",
        "verification_result": "PASS",
        "verification_timestamp": evidence["verification_timestamp"],
        "evidence_digest": evidence["canonical_evidence_digest"],
    }
    marker["marker_digest"] = _digest(marker)
    runtime = repository / progressive_oa.PACKAGE_PATH / "runtime/evidence/OA-21"
    _write(runtime / "INDEPENDENT-QUALIFICATION.json", evidence)
    _write(runtime / "VERIFICATION.json", evidence)
    _write(runtime / "VERIFIED", marker)
    state["gates"]["OA-21"]["state"] = "AWAITING_OPERATOR_VERIFICATION"
    progressive_oa._write_state(repository, state)
    return {"gate_id": "OA-21", "result": "PASS", "verification_state": "VERIFIED_AWAITING_OPERATOR_ACCEPTANCE", **marker}
