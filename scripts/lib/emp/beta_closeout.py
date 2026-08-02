"""Canonical independent qualification and explicit closeout for Beta missions."""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from scripts.lib.emp.authority_resolution import digest
from scripts.lib.emp.native_session import NativeSessionStore, session_identifier
from scripts.lib.emp.runtime_paths import runtime_path


class BetaCloseoutError(ValueError):
    pass


MISSION = "ZDCL-01"
EXECUTION = "MISSION-EXECUTION-e638cdc2-1e7b-5833-a03f-8ab224301fe1"
ADMISSION = "MISSION-ADMISSION-0a7c96eb-1483-5e03-a594-0896aac589cd"
SESSION = "ZEUS-SESSION-f4aadd8a-77b9-53b3-958d-15a32a7d9b04"
IMPLEMENTATION = "3ffd533bf45f876614cdb0ce49df380bc21d4de0"
HANDLER = "zeus.operational.zdcl01-native-session"
HANDLER_VERSION = "0.1.0"
RECORD = Path("engineering/mission-completions/ZDCL-01.yaml")


def _load_sealed(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    supplied = value.pop("state_digest", None)
    if supplied != digest(value):
        raise BetaCloseoutError(f"state digest mismatch: {path}")
    value["state_digest"] = supplied
    return value


def _chain(entries: list[dict[str, Any]]) -> bool:
    previous = None
    for sequence, entry in enumerate(entries, 1):
        material = deepcopy(entry); supplied = material.pop("evidence_digest", None)
        material.pop("publication", None)
        if material.get("sequence") != sequence or material.get("previous_evidence_digest") != previous or supplied != digest(material):
            return False
        previous = supplied
    return True


def qualify(root: Path | str) -> dict[str, Any]:
    root = Path(root).resolve()
    execution = _load_sealed(runtime_path(root, "mission-executions") / f"{EXECUTION}.json")
    admission = _load_sealed(runtime_path(root, "mission-admissions") / f"{ADMISSION}.json")
    session = NativeSessionStore(runtime_path(root, "native-sessions")).load(SESSION)
    execute_results = [item.get("payload", {}).get("result", {}) for item in execution["evidence"] if item.get("event") == "GATE_COMPLETED"]
    handler_results = [item for item in execute_results if item.get("handler_id")]
    checks = {
        "published_implementation": subprocess.run(["git", "-C", str(root), "cat-file", "-e", IMPLEMENTATION + "^{commit}"], capture_output=True).returncode == 0,
        "mission_contract": (root / "engineering/mission-contracts/contracts/ZDCL-01.yaml").is_file(),
        "admission_identity": admission.get("admission_id") == ADMISSION and admission.get("request", {}).get("mode") == "operational",
        "execution_identity": execution.get("execution_id") == EXECUTION and execution.get("admission_id") == ADMISSION,
        "session_identity": session.get("session_id") == SESSION == session_identifier(EXECUTION),
        "session_execution_binding": session.get("execution_id") == EXECUTION and execution.get("session_id") == SESSION,
        "completion": execution.get("state") == "Completed" and session.get("lifecycle_state") == "COMPLETED",
        "checkpoint_completeness": execution.get("completed_gates") == ["VALIDATE_WOP", "PREPARE_EXECUTION", "EXECUTE_WORK", "VERIFY_COMPLETION"] and len(session.get("checkpoints", [])) == 4,
        "execution_evidence_chain": _chain(execution.get("evidence", [])),
        "session_evidence_chain": _chain(session.get("evidence", [])),
        "suspension_resume": [item["event"] for item in session["evidence"] if item["event"] in {"SESSION_SUSPENDED", "SESSION_RESUMED"}] == ["SESSION_SUSPENDED", "SESSION_RESUMED"],
        "handler_identity": len(handler_results) == 2 and all(item.get("handler_id") == HANDLER and item.get("handler_version") == HANDLER_VERSION for item in handler_results),
        "effect_profile": all(item.get("declared_effects") == {"filesystem": [], "network": [], "publication": ["append-only-session-evidence"], "repository": [], "runtime": ["native-sessions", "mission-executions"]} for item in handler_results),
        "effects_bounded": all(item.get("effects_performed") == [{"domain": "runtime", "effect": "native-session-lifecycle"}, {"domain": "publication", "effect": "append-only-session-evidence"}] for item in handler_results),
        "authority_binding": session.get("mission_id") == MISSION and session.get("submission_id") and session.get("wop_id") == "WOP-ZDCL-01-FOUNDATION-001",
        "identity_normalized": all(session.get(field) for field in ("principal", "submitter", "execution_agent")),
        "production_isolation": subprocess.run(["git", "-C", str(root), "rev-list", "-1", "OA-v1.0.0"], text=True, capture_output=True).stdout.strip() == "8d5b9655252e471909b9d6b087aed49cabae8e45",
        "planning_isolation": subprocess.run(["git", "-C", str(root), "rev-list", "-1", "OB-PLAN-v1.0.0"], text=True, capture_output=True).stdout.strip() == "bc229167e06bca8db379d782944d8e3234aa1093",
    }
    result = "PASS" if all(checks.values()) else "FAIL"
    value = {"schema_version": 1, "mission_id": MISSION, "implementation_baseline": IMPLEMENTATION, "admission_id": ADMISSION, "execution_id": EXECUTION, "session_id": SESSION, "handler": {"id": HANDLER, "version": HANDLER_VERSION}, "checks": checks, "result": result}
    value["qualification_digest"] = digest(value)
    if result != "PASS":
        raise BetaCloseoutError("independent qualification failed: " + ", ".join(key for key, passed in checks.items() if not passed))
    return value


def record_path(root: Path | str) -> Path:
    return Path(root) / RECORD


def load(root: Path | str) -> dict[str, Any] | None:
    path = record_path(root)
    if not path.is_file(): return None
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict): raise BetaCloseoutError("invalid completion record")
    supplied = value.pop("record_digest", None)
    if supplied != digest(value): raise BetaCloseoutError("completion record digest mismatch")
    value["record_digest"] = supplied
    return value


def acceptance_summary(root: Path | str) -> dict[str, Any]:
    qualification = qualify(root)
    return {"mission": MISSION, "implementation_baseline": IMPLEMENTATION, "operational_admission": ADMISSION, "execution": EXECUTION, "native_session": SESSION, "handler": f"{HANDLER} v{HANDLER_VERSION}", "qualification_result": qualification["result"], "residual_risks": ["Human-first raw-output suppression and publication-controller automation remain deferred platform work."], "recommended_disposition": "ACCEPT"}


def accept(root: Path | str, *, operator: str, rationale: str, at: datetime) -> dict[str, Any]:
    if not operator: raise BetaCloseoutError("operator identity is required")
    qualification = qualify(root)
    existing = load(root)
    if existing:
        if existing.get("acceptance", {}).get("operator") != operator: raise BetaCloseoutError("acceptance already recorded by a different operator")
        return existing
    value = {"schema_version": 1, "record_type": "BetaMissionCompletion", "mission_id": MISSION, "implementation": "COMPLETE", "qualification": {"result": "PASS", "digest": qualification["qualification_digest"]}, "acceptance": {"status": "ACCEPTED", "operator": operator, "rationale": rationale, "recorded_at": at.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")}, "lifecycle": "COMPLETED", "capability": {"id": "ZDCL-01-NATIVE-SESSION", "status": "OPERATIONAL", "availability": "AVAILABLE", "qualification": "PASS"}, "bindings": {"implementation_baseline": IMPLEMENTATION, "admission_id": ADMISSION, "execution_id": EXECUTION, "session_id": SESSION, "handler_id": HANDLER, "handler_version": HANDLER_VERSION}, "authority": {"mission_contract": "engineering/mission-contracts/contracts/ZDCL-01.yaml", "derived_from_session": False}, "recommendations": {"handler": "QUALIFIED_FOR_BOUNDED_EFFECT_PROFILE", "qualification_handler": "PRESERVED", "deferred_platform_work": ["human-first raw-output suppression", "publication controller"]}}
    value["record_digest"] = digest(value)
    path = record_path(root); path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(value, sort_keys=False), encoding="utf-8")
    return load(root) or value
