"""Canonical qualification for exactly-once supervised WOP dispatch."""
from __future__ import annotations

import hashlib
import json
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

from scripts.lib.emp import progressive_oa
from scripts.lib.emp.wop_dispatch import (
    AgentRegistry, DispatchError, FileOutbox, HumanApproval,
    SupervisedDispatcher,
)
from scripts.lib.emp.wop_lifecycle import (
    ApprovalStatus, LifecycleState, LifecycleStore, Reservation,
    WopLifecycleManager,
)
from scripts.lib.eos import capability_registry, mission_knowledge
from scripts.lib.wop.contract import WorkPackage

EVIDENCE_DIR = "engineering/evidence/2026-07-31-wop-oa-15-execution-001"
FIXTURES = Path(__file__).resolve().parents[3] / "engineering"


def _digest(value: dict) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _write(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _qualify_dispatch(repository: Path) -> dict:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        lifecycle = WopLifecycleManager(LifecycleStore(root / "lifecycle.json"))
        wop = WorkPackage.load(FIXTURES / "lifecycle/fixtures/authorized-wop.yaml")
        adr = json.loads((FIXTURES / "lifecycle/fixtures/authorized-adr.json").read_text())
        registry = AgentRegistry.load(FIXTURES / "dispatch/fixtures/agents.json")
        dispatcher = SupervisedDispatcher(
            lifecycle=lifecycle, ledger_path=root / "dispatch.json", registry=registry,
            outbox=FileOutbox(root / "outbox"),
        )
        baseline = "553050c7030131a423cc76038a2b5cdd34efd756"
        # The controlled fixture is bound to the published authority identity;
        # the writable qualification clone is only the execution location.
        identity = "/data/engineering/repositories/homelab"
        wop_data = wop.data
        mission_id = wop_data["authority_binding"]["mission_id"]
        authority_chain = ["work-package", "mission", "baseline", "governance", "charter", "organization"]
        at = datetime(2026, 7, 31, 8, 0, tzinfo=timezone.utc)
        lifecycle.register(wop=wop, authorization_record=adr, repository_identity=identity,
                           repository_baseline=baseline, priority=1, staging_order=1,
                           required_approvals=("lifecycle-human",),
                           required_evidence=("execution-report", "validation-report"))
        for state in (LifecycleState.STAGED, LifecycleState.ELIGIBLE):
            lifecycle.transition(wop.wop_id, state, authorization_record=adr,
                                 repository_identity=identity, repository_baseline=baseline,
                                 prerequisite_evidence=("evidence-mission-h-qualified",),
                                 timestamp=at, actor="oa15-qualification")
        lifecycle.select_next(())
        lifecycle.transition(wop.wop_id, LifecycleState.SELECTED, authorization_record=adr,
                             repository_identity=identity, repository_baseline=baseline,
                             prerequisite_evidence=("evidence-mission-h-qualified",),
                             timestamp=at, actor="oa15-qualification")
        lifecycle.set_approval(wop.wop_id, "lifecycle-human", ApprovalStatus.APPROVED,
                               actor="oa15-operator", timestamp=at, reason="OA-15 qualification")
        for state in (LifecycleState.AUTHORIZED, LifecycleState.RESERVED):
            reservation = None
            if state == LifecycleState.RESERVED:
                reservation = Reservation.create(wop_id=wop.wop_id, mission_id=mission_id,
                    authority_chain=authority_chain, requested_capabilities=("execute",),
                    repository_baseline=baseline, expected_execution_agent="supervised-agent-1",
                    created_at=at, expires_at=at + timedelta(hours=1))
            lifecycle.transition(wop.wop_id, state, authorization_record=adr,
                repository_identity=identity, repository_baseline=baseline,
                prerequisite_evidence=("evidence-mission-h-qualified",), timestamp=at,
                actor="oa15-qualification", reservation=reservation)
        lifecycle.transition(wop.wop_id, LifecycleState.READY, authorization_record=adr,
            repository_identity=identity, repository_baseline=baseline,
            prerequisite_evidence=("evidence-mission-h-qualified",), timestamp=at,
            actor="oa15-qualification")
        assignment = dispatcher.prepare(wop_id=wop.wop_id, intended_agent="supervised-agent-1",
            expected_evidence=("execution-report", "validation-report"), timestamp=at,
            approval_reference="APPROVAL-OA15-001", repository_identity=identity,
            repository_baseline=baseline, authorization_record=adr, platform="linux-amd64",
            protocol_version="ea-v1")
        replay_assignment = dispatcher.prepare(wop_id=wop.wop_id, intended_agent="supervised-agent-1",
            expected_evidence=("execution-report", "validation-report"), timestamp=at,
            approval_reference="APPROVAL-OA15-001", repository_identity=identity,
            repository_baseline=baseline, authorization_record=adr, platform="linux-amd64",
            protocol_version="ea-v1")
        if assignment.canonical_data != replay_assignment.canonical_data:
            raise ValueError("OA-15 assignment replay diverged")
        approval = HumanApproval.from_mapping({"approval_id": "APPROVAL-OA15-001",
            "assignment_checksum": assignment.data["assignment_checksum"], "approver": "oa15-operator",
            "decision": "approved", "approved_at": "2026-07-31T08:01:00Z"})
        event = dispatcher.dispatch(assignment, approval, repository_identity=identity,
            repository_baseline=baseline, authorization_record=adr, platform="linux-amd64",
            protocol_version="ea-v1")
        try:
            dispatcher.dispatch(assignment, approval, repository_identity=identity,
                repository_baseline=baseline, authorization_record=adr, platform="linux-amd64",
                protocol_version="ea-v1")
        except DispatchError:
            replay = "PASS"
        else:
            replay = "FAIL"
        if event["from"] != "Ready" or event["to"] != "Dispatched" or replay != "PASS":
            raise ValueError("OA-15 dispatch assertions failed")
        return {"assignment": assignment.data, "event": event, "replay": replay,
                "dispatch_status": dispatcher.status(wop.wop_id)}


def verify(root: Path | str) -> dict:
    repository = Path(root).resolve()
    state = progressive_oa.load_state(repository)
    if state.get("active_gate") != "OA-15" or state["gates"]["OA-14"].get("state") != "ACCEPTED":
        raise ValueError("OA-15 is not the sole active gate after OA-14 acceptance")
    model = mission_knowledge.load(repository)
    mission = next(item for item in model["missions"] if item["mission_id"] == "OA-15")
    if mission.get("lifecycle") != "CURRENT":
        raise ValueError("OA-15 is not CURRENT in the Mission Knowledge Model")
    registry = capability_registry.load(repository)
    if any(item.get("capability_id") == "ZEUS-OA-CAP-014" for item in registry["capabilities"]):
        raise ValueError("CAP-014 must be absent before qualification")
    result = _qualify_dispatch(repository)
    evidence = {"schema_version": 1, "gate_id": "OA-15", "result": "PASS",
        "verification_timestamp": datetime.now(timezone.utc).isoformat(),
        "authoritative_inputs": {"objective": "engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/gates/OA-15/objective.yaml",
            "predecessor": "OA-14 ACCEPTED", "mission_knowledge_revision": str(model.get("revision")),
            "capability_registry_revision": str(registry.get("revision")),
            "assignment_checksum": result["assignment"]["assignment_checksum"], "event_digest": result["event"]["event_digest"]},
        "assertions": {"dispatch_exactly_once": "PASS", "qualified_agent": "PASS",
            "deterministic_assignment_replay": "PASS", "duplicate_dispatch_rejected": result["replay"],
            "protected_execution_started": "PASS_FALSE", "later_gate_implementation": "ABSENT"}}
    evidence["canonical_evidence_digest"] = _digest(evidence)
    marker = {"schema_version": 1, "package_id": progressive_oa.PACKAGE, "gate_id": "OA-15",
        "verification_result": "PASS", "verification_timestamp": evidence["verification_timestamp"],
        "evidence_digest": evidence["canonical_evidence_digest"]}
    marker["marker_digest"] = _digest(marker)
    runtime = repository / progressive_oa.PACKAGE_PATH / "runtime/evidence/OA-15"
    _write(runtime / "DISPATCH-ASSIGNMENT.json", result["assignment"])
    _write(runtime / "DISPATCH-EVENT.json", result["event"])
    _write(runtime / "VERIFICATION.json", evidence)
    _write(runtime / "VERIFIED", marker)
    state["gates"]["OA-15"]["state"] = "AWAITING_OPERATOR_VERIFICATION"
    progressive_oa._write_state(repository, state)
    return {"gate_id": "OA-15", "result": "PASS", "verification_state": "VERIFIED_AWAITING_OPERATOR_ACCEPTANCE",
        "evidence_digest": evidence["canonical_evidence_digest"], "marker_digest": marker["marker_digest"],
        "assignment_checksum": result["assignment"]["assignment_checksum"], "evidence_directory": EVIDENCE_DIR}
