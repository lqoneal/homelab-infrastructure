#!/usr/bin/env python3
"""Regression tests for supervised Execution Assignment dispatch."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.lib.emp.wop_dispatch import (
    AgentRegistry,
    DispatchError,
    ExecutionAssignment,
    FileOutbox,
    HumanApproval,
    SupervisedDispatcher,
)
from scripts.lib.emp.wop_lifecycle import (
    ApprovalStatus,
    LifecycleState,
    LifecycleStore,
    Reservation,
    WopLifecycleManager,
)
from scripts.lib.wop.contract import WorkPackage


LIFECYCLE_FIXTURES = ROOT / "engineering" / "lifecycle" / "fixtures"
DISPATCH_FIXTURES = ROOT / "engineering" / "dispatch" / "fixtures"
REPOSITORY = str(ROOT)
BASELINE = "553050c7030131a423cc76038a2b5cdd34efd756"
START = datetime(2026, 7, 25, 1, 0, tzinfo=timezone.utc)


class SupervisedDispatchTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        self.lifecycle_path = root / "lifecycle.json"
        self.ledger_path = root / "dispatch.json"
        self.outbox_path = root / "outbox"
        self.lifecycle = WopLifecycleManager(LifecycleStore(self.lifecycle_path))
        self.wop = WorkPackage.load(LIFECYCLE_FIXTURES / "authorized-wop.yaml")
        self.adr = json.loads(
            (LIFECYCLE_FIXTURES / "authorized-adr.json").read_text(encoding="utf-8")
        )
        self.registry = AgentRegistry.load(DISPATCH_FIXTURES / "agents.json")
        self.dispatcher = SupervisedDispatcher(
            lifecycle=self.lifecycle,
            ledger_path=self.ledger_path,
            registry=self.registry,
            outbox=FileOutbox(self.outbox_path),
        )

    def register(self) -> None:
        self.lifecycle.register(
            wop=self.wop,
            authorization_record=self.adr,
            repository_identity=REPOSITORY,
            repository_baseline=BASELINE,
            priority=1,
            staging_order=1,
            required_approvals=("lifecycle-human",),
            required_evidence=("execution-report", "validation-report"),
        )

    def transition(self, state: LifecycleState, reservation=None) -> None:
        self.lifecycle.transition(
            self.wop.wop_id,
            state,
            authorization_record=self.adr,
            repository_identity=REPOSITORY,
            repository_baseline=BASELINE,
            prerequisite_evidence=("evidence-mission-h-qualified",),
            timestamp=START,
            actor="mission-j-test",
            reservation=reservation,
        )

    def ready(self) -> None:
        self.register()
        self.transition(LifecycleState.STAGED)
        self.transition(LifecycleState.ELIGIBLE)
        self.lifecycle.select_next(())
        self.transition(LifecycleState.SELECTED)
        self.lifecycle.set_approval(
            self.wop.wop_id,
            "lifecycle-human",
            ApprovalStatus.APPROVED,
            actor="reviewer",
            timestamp=START,
            reason="ready qualification",
        )
        self.transition(LifecycleState.AUTHORIZED)
        package = self.lifecycle.data["packages"][self.wop.wop_id]
        reservation = Reservation.create(
            wop_id=self.wop.wop_id,
            mission_id=package["mission_id"],
            authority_chain=package["authority_chain"],
            requested_capabilities=package["requested_capabilities"],
            repository_baseline=BASELINE,
            expected_execution_agent="supervised-agent-1",
            created_at=START,
            expires_at=START + timedelta(hours=1),
        )
        self.transition(LifecycleState.RESERVED, reservation)
        self.transition(LifecycleState.READY)

    def prepare(self, agent="supervised-agent-1") -> ExecutionAssignment:
        return self.dispatcher.prepare(
            wop_id=self.wop.wop_id,
            intended_agent=agent,
            expected_evidence=("execution-report", "validation-report"),
            timestamp=START,
            approval_reference="APPROVAL-MISSION-J-001",
            repository_identity=REPOSITORY,
            repository_baseline=BASELINE,
            authorization_record=self.adr,
            platform="linux-amd64",
            protocol_version="ea-v1",
        )

    @staticmethod
    def approval(assignment: ExecutionAssignment, decision="approved") -> HumanApproval:
        return HumanApproval.from_mapping(
            {
                "approval_id": "APPROVAL-MISSION-J-001",
                "assignment_checksum": assignment.data["assignment_checksum"],
                "approver": "human-reviewer",
                "decision": decision,
                "approved_at": "2026-07-25T01:01:00Z",
            }
        )

    def send(self, assignment: ExecutionAssignment):
        return self.dispatcher.dispatch(
            assignment,
            self.approval(assignment),
            repository_identity=REPOSITORY,
            repository_baseline=BASELINE,
            authorization_record=self.adr,
            platform="linux-amd64",
            protocol_version="ea-v1",
        )

    def test_ready_assignment_dispatches_once(self) -> None:
        self.ready()
        assignment = self.prepare()
        event = self.send(assignment)
        self.assertEqual((event["from"], event["to"]), ("Ready", "Dispatched"))
        self.assertEqual(self.dispatcher.status(self.wop.wop_id), "Dispatched")
        self.assertTrue((self.outbox_path / event["delivery_artifact"]).is_file())

    def test_assignment_is_deterministic_and_reproducible(self) -> None:
        self.ready()
        first = self.prepare()
        second = self.prepare()
        self.assertEqual(first.canonical_data, second.canonical_data)
        self.assertEqual(first.to_json(), second.to_json())
        self.assertEqual(
            ExecutionAssignment.from_mapping(first.data).canonical_data,
            first.canonical_data,
        )

    def test_assignment_contains_required_contract_fields(self) -> None:
        self.ready()
        value = self.prepare().data
        self.assertEqual(value["wop_id"], self.wop.wop_id)
        self.assertEqual(value["baseline_commit"], BASELINE)
        self.assertEqual(
            value["authorization_decision_record"], self.adr["decision_digest"]
        )
        self.assertEqual(value["human_approval_reference"], "APPROVAL-MISSION-J-001")
        self.assertEqual(value["required_capabilities"], ["execute"])

    def test_tampered_assignment_fails(self) -> None:
        self.ready()
        value = self.prepare().data
        value["baseline_commit"] = "0" * 40
        with self.assertRaisesRegex(DispatchError, "checksum"):
            ExecutionAssignment.from_mapping(value)

    def test_not_ready_fails_closed(self) -> None:
        self.register()
        with self.assertRaisesRegex(DispatchError, "Ready"):
            self.prepare()

    def test_unknown_agent_fails_closed(self) -> None:
        self.ready()
        with self.assertRaisesRegex(DispatchError, "unknown"):
            self.prepare("missing-agent")

    def test_unqualified_agent_fails_closed(self) -> None:
        self.ready()
        with self.assertRaisesRegex(DispatchError, "not qualified"):
            self.prepare("suspended-agent")

    def test_capability_platform_and_protocol_must_match(self) -> None:
        self.ready()
        for platform, protocol in (("other", "ea-v1"), ("linux-amd64", "ea-v2")):
            with self.subTest(platform=platform, protocol=protocol):
                with self.assertRaisesRegex(DispatchError, "not qualified"):
                    self.dispatcher.prepare(
                        wop_id=self.wop.wop_id,
                        intended_agent="supervised-agent-1",
                        expected_evidence=(),
                        timestamp=START,
                        approval_reference="A",
                        repository_identity=REPOSITORY,
                        repository_baseline=BASELINE,
                        authorization_record=self.adr,
                        platform=platform,
                        protocol_version=protocol,
                    )

    def test_missing_or_denied_human_approval_fails_closed(self) -> None:
        self.ready()
        assignment = self.prepare()
        with self.assertRaisesRegex(DispatchError, "explicit human approval"):
            self.approval(assignment, decision="denied")

    def test_approval_is_bound_to_checksum_and_reference(self) -> None:
        self.ready()
        assignment = self.prepare()
        value = {
            "approval_id": "APPROVAL-MISSION-J-001",
            "assignment_checksum": "0" * 64,
            "approver": "human",
            "decision": "approved",
            "approved_at": "2026-07-25T01:01:00Z",
        }
        with self.assertRaisesRegex(DispatchError, "bind"):
            self.dispatcher.dispatch(
                assignment,
                HumanApproval.from_mapping(value),
                repository_identity=REPOSITORY,
                repository_baseline=BASELINE,
                authorization_record=self.adr,
                platform="linux-amd64",
                protocol_version="ea-v1",
            )

    def test_stale_authorization_and_context_fail_closed(self) -> None:
        self.ready()
        assignment = self.prepare()
        for adr, baseline in (
            ({**self.adr, "enforcement_decision": "REJECTED"}, BASELINE),
            (self.adr, "0" * 40),
        ):
            with self.subTest(adr=adr, baseline=baseline):
                with self.assertRaisesRegex(DispatchError, "authorization"):
                    self.dispatcher.dispatch(
                        assignment,
                        self.approval(assignment),
                        repository_identity=REPOSITORY,
                        repository_baseline=baseline,
                        authorization_record=adr,
                        platform="linux-amd64",
                        protocol_version="ea-v1",
                    )

    def test_duplicate_dispatch_fails_closed(self) -> None:
        self.ready()
        assignment = self.prepare()
        self.send(assignment)
        with self.assertRaisesRegex(DispatchError, "already"):
            self.send(assignment)

    def test_ledger_tampering_fails_on_restart(self) -> None:
        self.ready()
        self.send(self.prepare())
        value = json.loads(self.ledger_path.read_text())
        value["dispatches"][self.wop.wop_id]["to"] = "Executed"
        self.ledger_path.write_text(json.dumps(value), encoding="utf-8")
        with self.assertRaisesRegex(DispatchError, "transition"):
            SupervisedDispatcher(
                lifecycle=self.lifecycle,
                ledger_path=self.ledger_path,
                registry=self.registry,
                outbox=FileOutbox(self.outbox_path),
            )

    def test_cli_validates_and_reports_dispatched(self) -> None:
        self.ready()
        self.send(self.prepare())
        command = [
            str(ROOT / "scripts/wop-dispatchctl"),
            str(self.lifecycle_path),
            str(self.ledger_path),
            str(DISPATCH_FIXTURES / "agents.json"),
            str(self.outbox_path),
        ]
        validate = subprocess.run(command + ["validate"], text=True, capture_output=True)
        self.assertEqual(validate.returncode, 0, validate.stderr)
        status = subprocess.run(
            command + ["status", "--wop", self.wop.wop_id],
            text=True,
            capture_output=True,
        )
        self.assertEqual(status.returncode, 0, status.stderr)
        self.assertEqual(json.loads(status.stdout)["state"], "Dispatched")

    def test_no_execution_monitoring_retry_lease_or_autonomy_api(self) -> None:
        forbidden = {
            "execute", "monitor", "retry", "recover", "acquire_lease",
            "select_automatically", "invoke_codex", "qualify_evidence",
        }
        self.assertTrue(forbidden.isdisjoint(set(dir(self.dispatcher))))


if __name__ == "__main__":
    unittest.main()
