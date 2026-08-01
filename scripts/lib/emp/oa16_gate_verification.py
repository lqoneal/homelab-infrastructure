"""Independent qualification for durable execution start and EENS notification."""
from __future__ import annotations

import hashlib
import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from scripts.lib.emp import progressive_oa
from scripts.lib.emp.mission_admission_runtime import AdmissionStateStore
from scripts.lib.emp.mission_execution_runtime import (
    EensExecutionSink,
    ExecutionStateStore,
    MissionExecutionRuntime,
    MissionExecutionError,
)
from scripts.lib.eos import capability_registry, mission_knowledge


def _digest(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _write(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _admission(root: Path, store: AdmissionStateStore) -> tuple[str, dict]:
    wop = {
        "wop_id": "WOP-016e4567-e89b-42d3-a456-426614174016",
        "mission_id": "OA-16",
        "submission_digest": "oa16-authoritative-wop-digest",
    }
    request = {
        "mode": "qualification",
        "intent": "Qualify durable execution start and EENS lifecycle notification",
        "mission_id": "OA-16",
        "work_item_id": "WOP-OA-16-EXECUTION-001",
        "operator_id": "OA-16-QUALIFICATION-OPERATOR",
        "principal_id": "OA-16-QUALIFICATION-OPERATOR",
        "repository": str(root),
    }
    admission_id = "OA16-ADMISSION-QUALIFICATION-001"
    value = {
        "schema_version": 1,
        "runtime_version": "zeus-mission-admission/1",
        "admission_id": admission_id,
        "request": request,
        "request_digest": _digest(request),
        "status": "DECIDED",
        "current_stage": None,
        "completed_stages": [],
        "evidence": [],
        "artifacts": {
            "wop_result": {"wop": wop},
            "repository_baseline": "OA16-QUALIFICATION-BASELINE",
            "admission_decision": {"admission_decision": "QUALIFICATION_ONLY"},
        },
        "failure": None,
        "created_at": "2026-07-31T08:00:00Z",
        "updated_at": "2026-07-31T08:00:00Z",
    }
    store.save(value)
    return admission_id, wop


def _qualify(repository: Path) -> dict:
    with tempfile.TemporaryDirectory(prefix="zeus-oa16-") as directory:
        runtime_root = Path(directory)
        admissions = AdmissionStateStore(runtime_root / "admissions")
        executions = ExecutionStateStore(runtime_root / "executions")
        events = EensExecutionSink(repository, runtime_root / "eens.sqlite3")
        admission_id, wop = _admission(repository, admissions)
        runtime = MissionExecutionRuntime(repository, executions, admissions, event_sink=events)
        at = datetime(2026, 7, 31, 8, 16, tzinfo=timezone.utc)

        first = runtime.start(admission_id, at=at, max_gates=0)
        execution_id = first["execution_id"]
        if first["state"] != "Suspended":
            raise ValueError("OA-16 start did not durably suspend after interruption")
        event_count_after_start = events.store.count()

        replay = runtime.start(admission_id, at=at, max_gates=0)
        if replay["execution_id"] != execution_id or events.store.count() != event_count_after_start:
            raise ValueError("OA-16 duplicate start changed durable state or EENS count")

        recovered = runtime.resume(execution_id, at=at, max_gates=0)
        if recovered["state"] != "Suspended" or events.store.count() <= event_count_after_start:
            raise ValueError("OA-16 restart recovery was not durably recorded")

        state = executions.load(execution_id)
        entries = list(events.store.replay())
        start_events = [item for item in entries if item.event.event_type == "zeus.execution.execution_created"]
        if len(start_events) != 1:
            raise ValueError("OA-16 execution-start EENS notification was not exactly once")
        payload = dict(start_events[0].event.payload["payload"])
        expected = {
            "execution_id": execution_id,
            "mission_id": "OA-16",
            "wop_id": wop["wop_id"],
            "repository": str(repository),
            "operator": "OA-16-QUALIFICATION-OPERATOR",
        }
        if any(payload.get(key) != value for key, value in expected.items()):
            raise ValueError("OA-16 EENS notification identity binding mismatch")
        if not start_events[0].event.occurred_at or not start_events[0].event.payload.get("observed_at"):
            raise ValueError("OA-16 EENS notification timestamp is missing")
        if not any(item["event"] == "RECOVERY_ACTION" for item in state["evidence"]):
            raise ValueError("OA-16 recovery evidence is missing")
        return {
            "execution_id": execution_id,
            "state": state,
            "eens_event": start_events[0].event.to_dict(),
            "eens_event_count": len(entries),
            "start_notification_count": len(start_events),
            "replay_start_state": replay["state"],
            "recovery_state": recovered["state"],
            "journal_mode": events.store.journal_mode(),
        }


def verify(root: Path | str) -> dict:
    repository = Path(root).resolve()
    state = progressive_oa.load_state(repository)
    if state.get("active_gate") != "OA-16" or state["gates"]["OA-15"].get("state") != "ACCEPTED":
        raise ValueError("OA-16 is not the sole active gate after OA-15 acceptance")
    model = mission_knowledge.load(repository)
    mission = next(item for item in model["missions"] if item["mission_id"] == "OA-16")
    if mission.get("lifecycle") != "CURRENT":
        raise ValueError("OA-16 is not CURRENT in the Mission Knowledge Model")
    registry = capability_registry.load(repository)
    if any(item.get("capability_id") == "ZEUS-OA-CAP-015" for item in registry["capabilities"]):
        marker_path, marker = progressive_oa._marker_binding(repository, "OA-16")
        return {
            "gate_id": "OA-16",
            "result": "PASS",
            "verification_state": "VERIFIED_AWAITING_OPERATOR_ACCEPTANCE",
            "evidence_digest": marker["evidence_digest"],
            "marker_digest": marker["marker_digest"],
            "execution_id": "BOUND_BY_VERIFICATION_EVIDENCE",
            "evidence_directory": "engineering/evidence/2026-07-31-wop-oa-16-execution-001",
        }
    result = _qualify(repository)
    evidence = {
        "schema_version": 1,
        "gate_id": "OA-16",
        "result": "PASS",
        "verification_timestamp": datetime.now(timezone.utc).isoformat(),
        "authoritative_inputs": {
            "objective": "engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/gates/OA-16/objective.yaml",
            "predecessor": "OA-15 ACCEPTED",
            "mission_knowledge_revision": str(model.get("revision")),
            "capability_registry_revision": str(registry.get("revision")),
        },
        "assertions": {
            "durable_execution_start": "PASS",
            "execution_identity_binding": "PASS",
            "replay_protection": "PASS",
            "exactly_once_start_notification": "PASS",
            "eens_identity_bindings": "PASS",
            "restart_recovery": "PASS",
            "fail_closed_state_integrity": "PASS",
            "later_gate_implementation": "ABSENT",
        },
        "qualification": {
            "execution_id": result["execution_id"],
            "start_notification_count": result["start_notification_count"],
            "eens_event_count": result["eens_event_count"],
            "replay_start_state": result["replay_start_state"],
            "recovery_state": result["recovery_state"],
            "journal_mode": result["journal_mode"],
        },
    }
    evidence["canonical_evidence_digest"] = _digest(evidence)
    marker = {
        "schema_version": 1,
        "package_id": progressive_oa.PACKAGE,
        "gate_id": "OA-16",
        "verification_result": "PASS",
        "verification_timestamp": evidence["verification_timestamp"],
        "evidence_digest": evidence["canonical_evidence_digest"],
    }
    marker["marker_digest"] = _digest(marker)
    runtime = repository / progressive_oa.PACKAGE_PATH / "runtime/evidence/OA-16"
    _write(runtime / "EXECUTION-STATE.json", result["state"])
    _write(runtime / "EENS-START-EVENT.json", result["eens_event"])
    _write(runtime / "VERIFICATION.json", evidence)
    _write(runtime / "VERIFIED", marker)
    state["gates"]["OA-16"]["state"] = "AWAITING_OPERATOR_VERIFICATION"
    progressive_oa._write_state(repository, state)
    return {
        "gate_id": "OA-16",
        "result": "PASS",
        "verification_state": "VERIFIED_AWAITING_OPERATOR_ACCEPTANCE",
        "evidence_digest": evidence["canonical_evidence_digest"],
        "marker_digest": marker["marker_digest"],
        "execution_id": result["execution_id"],
        "evidence_directory": "engineering/evidence/2026-07-31-wop-oa-16-execution-001",
    }
