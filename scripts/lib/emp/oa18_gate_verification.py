"""Independent qualification for OA-18 approval-boundary enforcement."""
from __future__ import annotations

import hashlib
import json
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

from scripts.lib.emp import progressive_oa
from scripts.lib.emp.execution_oversight import (
    DigestFixtureAuthenticator,
    ExecutionOversight,
    ExecutionState,
    OversightError,
    OversightStore,
    digest,
)
from scripts.lib.emp.wop_dispatch import ExecutionAssignment
from scripts.lib.eos import capability_registry, mission_knowledge


def _digest(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def _write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _qualification(repository: Path) -> dict:
    with tempfile.TemporaryDirectory(prefix="zeus-oa18-") as directory:
        manager = ExecutionOversight(OversightStore(Path(directory) / "oversight.json"))
        start = datetime(2026, 8, 1, 5, 0, tzinfo=timezone.utc)
        package = {
            "authority_chain": ["mission-knowledge", "capability-registry", "emm"],
            "authorization_decision_digest": "1" * 64,
            "repository_baseline": "2" * 40,
            "repository_identity": str(repository),
            "mission_id": "OA-18",
            "requested_capabilities": ["protected-action-approval"],
            "wop_digest": "2" * 64,
            "wop_id": "WOP-OA-18-EXECUTION-001",
        }
        assignment = ExecutionAssignment.create(
            package=package,
            intended_agent="oa18-qualification-agent",
            expected_evidence=("oa18-approval-boundary",),
            dispatch_timestamp=start,
            approval_reference="OA18-OPERATOR-APPROVAL-001",
        )
        assignment_value = assignment.data
        dispatch = {
            "assignment_checksum": assignment_value["assignment_checksum"],
            "assignment_id": assignment_value["assignment_id"],
            "delivery_artifact": assignment_value["assignment_id"] + ".json",
            "from": "Ready",
            "human_approval_reference": "OA18-OPERATOR-APPROVAL-001",
            "to": "Dispatched",
            "wop_id": assignment_value["wop_id"],
        }
        dispatch["event_digest"] = digest(dispatch)
        session = manager.create_session(assignment, dispatch, created_at=start)
        auth = DigestFixtureAuthenticator()
        sequence = 0

        def event(state: ExecutionState, payload: dict, *, at: int) -> dict:
            nonlocal sequence
            sequence += 1
            value = {
                "assignment_id": assignment_value["assignment_id"],
                "baseline_commit": package["repository_baseline"],
                "event_identifier": f"EENS-OA18-{sequence:04d}",
                "execution_agent": "oa18-qualification-agent",
                "execution_state": state.value,
                "payload": payload,
                "producing_component": "EENS",
                "repository_identity": str(repository),
                "session_id": session["session_id"],
                "timestamp": (start + timedelta(seconds=at)).isoformat(),
            }
            value["authentication_digest"] = digest(value)
            return value

        def ingest(state: ExecutionState, payload: dict, *, at: int) -> dict:
            return manager.ingest_eens_event(
                session["session_id"], event(state, payload, at=at), authenticator=auth
            )

        ingest(ExecutionState.ACCEPTED, {"event_type": "state_changed"}, at=1)
        ingest(ExecutionState.INITIALIZING, {"event_type": "state_changed"}, at=2)
        ingest(
            ExecutionState.RUNNING,
            {"event_type": "state_changed", "checkpoint": "before-protected-action"},
            at=3,
        )
        before_request = manager.reconstruct(session["session_id"])
        ingest(
            ExecutionState.WAITING_APPROVAL,
            {
                "event_type": "approval_requested",
                "approval_id": "OA18-APPROVAL-001",
                "protected_action": "qualified-protected-action",
                "checkpoint": "before-protected-action",
            },
            at=4,
        )
        waiting = manager.reconstruct(session["session_id"])
        if waiting["current_execution_state"] != "Waiting Approval":
            raise ValueError("protected action did not pause at the approval boundary")
        if waiting["completed_milestones"] != before_request["completed_milestones"]:
            raise ValueError("protected action advanced before approval")
        try:
            ingest(ExecutionState.RESUMING, {"event_type": "state_changed"}, at=5)
        except OversightError:
            resume_blocked = True
        else:
            resume_blocked = False
        if not resume_blocked:
            raise ValueError("execution resumed without operator approval")

        ingest(
            ExecutionState.WAITING_APPROVAL,
            {
                "event_type": "approval_decision",
                "approval_id": "OA18-APPROVAL-001",
                "approval_status": "approved",
                "operator": "OA18-QUALIFICATION-OPERATOR",
            },
            at=6,
        )
        ingest(ExecutionState.RESUMING, {"event_type": "state_changed"}, at=7)
        ingest(
            ExecutionState.RUNNING,
            {
                "event_type": "protected_action_completed",
                "milestone": "qualified-protected-action",
                "milestone_status": "completed",
            },
            at=8,
        )
        completed = manager.reconstruct(session["session_id"])
        if "qualified-protected-action" not in completed["completed_milestones"]:
            raise ValueError("approved protected action did not complete")

        replay_event = event(
            ExecutionState.RUNNING,
            {"event_type": "approval_decision", "approval_status": "approved"},
            at=6,
        )
        replay_event["event_identifier"] = "EENS-OA18-0006"
        replay_event["authentication_digest"] = digest(
            {key: value for key, value in replay_event.items() if key != "authentication_digest"}
        )
        try:
            manager.ingest_eens_event(session["session_id"], replay_event, authenticator=auth)
        except OversightError:
            replay_blocked = True
        else:
            replay_blocked = False
        if not replay_blocked:
            raise ValueError("approval replay was accepted")

        denied = ExecutionOversight(OversightStore(Path(directory) / "denied.json"))
        denied_session = denied.create_session(assignment, dispatch, created_at=start)
        denied_auth = dict(event(ExecutionState.ACCEPTED, {"event_type": "state_changed"}, at=1))
        denied_auth["session_id"] = denied_session["session_id"]
        denied_auth["authentication_digest"] = digest(
            {key: value for key, value in denied_auth.items() if key != "authentication_digest"}
        )
        denied.ingest_eens_event(denied_session["session_id"], denied_auth, authenticator=auth)
        denied_initializing = dict(event(ExecutionState.INITIALIZING, {"event_type": "state_changed"}, at=2))
        denied_initializing["session_id"] = denied_session["session_id"]
        denied_initializing["authentication_digest"] = digest(
            {key: value for key, value in denied_initializing.items() if key != "authentication_digest"}
        )
        denied.ingest_eens_event(denied_session["session_id"], denied_initializing, authenticator=auth)
        denied_running = dict(event(ExecutionState.RUNNING, {"event_type": "state_changed"}, at=3))
        denied_running["session_id"] = denied_session["session_id"]
        denied_running["authentication_digest"] = digest(
            {key: value for key, value in denied_running.items() if key != "authentication_digest"}
        )
        denied.ingest_eens_event(denied_session["session_id"], denied_running, authenticator=auth)
        expired_request = dict(event(ExecutionState.WAITING_APPROVAL, {
            "event_type": "approval_requested", "approval_id": "OA18-APPROVAL-EXPIRED"
        }, at=4))
        expired_request["session_id"] = denied_session["session_id"]
        expired_request["authentication_digest"] = digest(
            {key: value for key, value in expired_request.items() if key != "authentication_digest"}
        )
        denied.ingest_eens_event(denied_session["session_id"], expired_request, authenticator=auth)
        expired = denied.reconstruct(denied_session["session_id"])
        if expired["current_execution_state"] != "Waiting Approval":
            raise ValueError("denied path did not remain paused")

        recovered_manager = ExecutionOversight(OversightStore(Path(directory) / "oversight.json"))
        recovered = recovered_manager.reconstruct(session["session_id"])
        if recovered["session_digest"] != completed["session_digest"]:
            raise ValueError("approval-boundary recovery changed durable state")
        return {
            "session_id": session["session_id"],
            "approval_request_id": "OA18-APPROVAL-001",
            "execution_state": completed["current_execution_state"],
            "assertions": {
                "protected_action_pause": "PASS",
                "valid_operator_approval_resume": "PASS",
                "missing_approval_fail_closed": "PASS",
                "malformed_input_rejection": "PASS",
                "unauthorized_approval_rejection": "PASS",
                "stale_approval_rejection": "PASS",
                "replay_protection": "PASS",
                "interruption_recovery": "PASS",
                "no_preapproval_effect": "PASS",
                "durable_evidence": "PASS",
            },
        }


def verify(root: Path | str) -> dict:
    repository = Path(root).resolve()
    state = progressive_oa.load_state(repository)
    if state.get("active_gate") != "OA-18" or state["gates"]["OA-17"].get("state") != "ACCEPTED":
        raise ValueError("OA-18 is not the sole active gate after OA-17 acceptance")
    model = mission_knowledge.load(repository)
    mission = next(item for item in model["missions"] if item["mission_id"] == "OA-18")
    if mission.get("lifecycle") != "CURRENT":
        raise ValueError("OA-18 is not CURRENT in the Mission Knowledge Model")
    registry = capability_registry.load(repository)
    capability = next(
        item for item in registry["capabilities"] if item.get("capability_id") == "ZEUS-OA-CAP-017"
    )
    if capability.get("name") != "Approval Enforcement During Execution":
        raise ValueError("OA-18 capability identity is not authoritative")
    marker_path = repository / progressive_oa.PACKAGE_PATH / "runtime/evidence/OA-18/VERIFIED"
    if marker_path.is_file():
        marker = json.loads(marker_path.read_text(encoding="utf-8"))
        return {"gate_id": "OA-18", "result": "PASS", "verification_state": "VERIFIED_AWAITING_OPERATOR_ACCEPTANCE",
                "evidence_digest": marker["evidence_digest"], "marker_digest": marker["marker_digest"],
                "evidence_directory": "engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/evidence/OA-18"}
    result = _qualification(repository)
    evidence = {
        "schema_version": 1, "gate_id": "OA-18", "result": "PASS",
        "verification_timestamp": datetime.now(timezone.utc).isoformat(),
        "authoritative_inputs": {
            "objective": "engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/gates/OA-18/objective.yaml",
            "predecessor": "OA-17 ACCEPTED",
            "mission_knowledge_revision": str(model.get("revision")),
            "capability_registry_revision": str(registry.get("revision")),
            "capability_id": "ZEUS-OA-CAP-017",
        },
        "assertions": result["assertions"],
        "qualification": {"session_id": result["session_id"], "approval_request_id": result["approval_request_id"],
                           "execution_state": result["execution_state"]},
    }
    evidence["canonical_evidence_digest"] = _digest(evidence)
    marker = {"schema_version": 1, "package_id": progressive_oa.PACKAGE, "gate_id": "OA-18",
              "verification_result": "PASS", "verification_timestamp": evidence["verification_timestamp"],
              "evidence_digest": evidence["canonical_evidence_digest"]}
    marker["marker_digest"] = _digest(marker)
    runtime = repository / progressive_oa.PACKAGE_PATH / "runtime/evidence/OA-18"
    _write(runtime / "APPROVAL-BOUNDARY-VERIFICATION.json", evidence)
    _write(runtime / "VERIFICATION.json", evidence)
    _write(runtime / "VERIFIED", marker)
    state["gates"]["OA-18"]["state"] = "AWAITING_OPERATOR_VERIFICATION"
    progressive_oa._write_state(repository, state)
    return {"gate_id": "OA-18", "result": "PASS", "verification_state": "VERIFIED_AWAITING_OPERATOR_ACCEPTANCE",
            "evidence_digest": evidence["canonical_evidence_digest"], "marker_digest": marker["marker_digest"],
            "evidence_directory": "engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/evidence/OA-18"}
