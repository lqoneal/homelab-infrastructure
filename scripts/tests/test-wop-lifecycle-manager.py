#!/usr/bin/env python3
"""Regression tests for the EMP WOP Lifecycle Manager."""

from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.lib.emp.wop_lifecycle import (  # noqa: E402
    ApprovalStatus,
    DispatchBoundaryError,
    LifecycleError,
    LifecycleState,
    LifecycleStore,
    QueueStatus,
    Reservation,
    WopLifecycleManager,
)
from scripts.lib.wop.contract import WorkPackage  # noqa: E402


FIXTURES = ROOT / "engineering" / "lifecycle" / "fixtures"
REPOSITORY = str(ROOT)
BASELINE = "553050c7030131a423cc76038a2b5cdd34efd756"
START = datetime(2026, 7, 25, 0, 15, tzinfo=timezone.utc)
PREREQUISITES = {"evidence-mission-h-qualified"}


class WopLifecycleManagerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.state_path = Path(self.temporary.name) / "lifecycle.json"
        self.manager = WopLifecycleManager(LifecycleStore(self.state_path))
        self.wop = WorkPackage.load(FIXTURES / "authorized-wop.yaml")
        self.adr = json.loads(
            (FIXTURES / "authorized-adr.json").read_text(encoding="utf-8")
        )

    def register(
        self,
        *,
        wop=None,
        adr=None,
        priority=10,
        staging_order=1,
        dependencies=(),
        approvals=("human-approval",),
    ):
        return self.manager.register(
            wop=wop or self.wop,
            authorization_record=adr or self.adr,
            repository_identity=REPOSITORY,
            repository_baseline=BASELINE,
            priority=priority,
            staging_order=staging_order,
            mission_dependencies=dependencies,
            required_approvals=approvals,
            required_evidence=("execution-report", "validation-report"),
            reconciliation_updates={
                "project_state": ("record completion",),
                "work_registry": ("update mission status",),
                "controlled_documents": ("publish only if separately authorized",),
                "mission_status": ("mark completed",),
                "completion_evidence": ("retain final report",),
            },
        )

    def transition(self, target, *, wop_id=None, timestamp=None, reservation=None):
        return self.manager.transition(
            wop_id or self.wop.wop_id,
            target,
            authorization_record=self.adr,
            repository_identity=REPOSITORY,
            repository_baseline=BASELINE,
            prerequisite_evidence=PREREQUISITES,
            satisfied_dependencies=(),
            timestamp=timestamp or START,
            actor="mission-i-test",
            reservation=reservation,
        )

    def advance_to_selected(self):
        self.transition(LifecycleState.STAGED)
        self.transition(LifecycleState.ELIGIBLE)
        self.assertEqual(
            self.manager.select_next(completed_missions=()),
            self.wop.data["authority_binding"]["mission_id"],
        )
        self.transition(LifecycleState.SELECTED)

    def approve(self):
        self.manager.set_approval(
            self.wop.wop_id,
            "human-approval",
            ApprovalStatus.APPROVED,
            actor="human-reviewer",
            timestamp=START,
            reason="qualification approval",
        )

    def reservation(self, *, expires=None):
        package = self.manager.data["packages"][self.wop.wop_id]
        return Reservation.create(
            wop_id=self.wop.wop_id,
            mission_id=package["mission_id"],
            authority_chain=package["authority_chain"],
            requested_capabilities=package["requested_capabilities"],
            repository_baseline=BASELINE,
            expected_execution_agent="future-supervised-agent",
            created_at=START,
            expires_at=expires or START + timedelta(hours=1),
        )

    def complete_lifecycle(self):
        self.register()
        self.advance_to_selected()
        self.approve()
        self.transition(LifecycleState.AUTHORIZED)
        reservation = self.reservation()
        self.transition(LifecycleState.RESERVED, reservation=reservation)
        self.transition(LifecycleState.READY, timestamp=START + timedelta(minutes=1))
        return reservation

    def mutate_wop(self, suffix: int, mission_id: str):
        value = copy.deepcopy(self.wop.to_mapping())
        value["wop_id"] = (
            f"WOP-423e4567-e89b-42d3-a456-4266141740{suffix:02d}"
        )
        value["authority_binding"]["mission_id"] = mission_id
        value["payload_digest"] = "0" * 64
        value["signature"]["value"] = "0" * 64
        digest = WorkPackage.from_mapping(value).calculated_digest()
        value["payload_digest"] = digest
        value["signature"]["value"] = digest
        wop = WorkPackage.from_mapping(value)
        adr = copy.deepcopy(self.adr)
        adr["wop_id"] = wop.wop_id
        adr["decision_digest"] = f"{suffix + 1:x}" * 64
        adr["decision_digest"] = adr["decision_digest"][:64]
        return wop, adr

    def test_all_six_transitions_reach_ready_deterministically(self) -> None:
        reservation = self.complete_lifecycle()
        package = self.manager.data["packages"][self.wop.wop_id]
        self.assertEqual(package["state"], "Ready")
        self.assertEqual(len(package["history"]), 6)
        self.assertEqual(
            [(event["from"], event["to"]) for event in package["history"]],
            [
                ("Draft", "Staged"),
                ("Staged", "Eligible"),
                ("Eligible", "Selected"),
                ("Selected", "Authorized"),
                ("Authorized", "Reserved"),
                ("Reserved", "Ready"),
            ],
        )
        self.assertFalse(reservation.grants_authority)
        self.assertFalse(reservation.is_execution_lease)

    def test_invalid_skip_reverse_and_dispatch_fail_closed(self) -> None:
        self.register()
        with self.assertRaisesRegex(LifecycleError, "illegal lifecycle transition"):
            self.transition(LifecycleState.ELIGIBLE)
        self.complete_from_registered()
        with self.assertRaises(DispatchBoundaryError):
            self.transition(LifecycleState.READY)

    def complete_from_registered(self):
        self.advance_to_selected()
        self.approve()
        self.transition(LifecycleState.AUTHORIZED)
        self.transition(LifecycleState.RESERVED, reservation=self.reservation())
        self.transition(LifecycleState.READY, timestamp=START + timedelta(minutes=1))

    def test_registration_requires_zeus_authority_not_repository_state(self) -> None:
        for change in (
            {"authoritative_decision_source": "LEGACY"},
            {"enforcement_decision": "REJECTED"},
            {"repository_baseline_commit": "0" * 40},
        ):
            with self.subTest(change=change):
                adr = copy.deepcopy(self.adr)
                adr.update(change)
                with self.assertRaises(LifecycleError):
                    self.register(adr=adr)
        self.assertEqual(self.manager.data["packages"], {})

    def test_wop_repository_context_must_match_observed_context(self) -> None:
        value = self.wop.to_mapping()
        value["execution_context"]["baseline_commit"] = "0" * 40
        value["payload_digest"] = "0" * 64
        value["signature"]["value"] = "0" * 64
        calculated = WorkPackage.from_mapping(value).calculated_digest()
        value["payload_digest"] = calculated
        value["signature"]["value"] = calculated
        with self.assertRaisesRegex(LifecycleError, "WOP repository baseline"):
            self.register(wop=WorkPackage.from_mapping(value))

    def test_prerequisites_fail_closed(self) -> None:
        self.register()
        self.transition(LifecycleState.STAGED)
        with self.assertRaisesRegex(LifecycleError, "prerequisites"):
            self.manager.transition(
                self.wop.wop_id,
                LifecycleState.ELIGIBLE,
                authorization_record=self.adr,
                repository_identity=REPOSITORY,
                repository_baseline=BASELINE,
                prerequisite_evidence=(),
                timestamp=START,
                actor="test",
            )

    def test_wop_dependencies_fail_closed(self) -> None:
        value = self.wop.to_mapping()
        value["dependencies"] = [
            {
                "wop_id": "WOP-423e4567-e89b-42d3-a456-426614174099",
                "required": True,
            }
        ]
        value["payload_digest"] = "0" * 64
        value["signature"]["value"] = "0" * 64
        calculated = WorkPackage.from_mapping(value).calculated_digest()
        value["payload_digest"] = calculated
        value["signature"]["value"] = calculated
        dependent = WorkPackage.from_mapping(value)
        self.register(wop=dependent)
        self.transition(LifecycleState.STAGED)
        with self.assertRaisesRegex(LifecycleError, "dependencies"):
            self.transition(LifecycleState.ELIGIBLE)

    def test_required_approval_blocks_authorized_state(self) -> None:
        self.register()
        self.advance_to_selected()
        with self.assertRaisesRegex(LifecycleError, "required approvals"):
            self.transition(LifecycleState.AUTHORIZED)
        self.approve()
        self.transition(LifecycleState.AUTHORIZED)

    def test_approval_lifecycle_is_immutable_and_fail_closed(self) -> None:
        self.register()
        checkpoint = self.manager.set_approval(
            self.wop.wop_id,
            "human-approval",
            ApprovalStatus.REJECTED,
            actor="reviewer",
            timestamp=START,
            reason="rejected fixture",
        )
        self.assertEqual(checkpoint["status"], "rejected")
        with self.assertRaises(LifecycleError):
            self.approve()
        superseded = self.manager.set_approval(
            self.wop.wop_id,
            "human-approval",
            ApprovalStatus.SUPERSEDED,
            actor="reviewer",
            timestamp=START,
            reason="new review required",
        )
        self.assertEqual(superseded["status"], "superseded")

    def test_queue_selection_is_deterministic(self) -> None:
        self.register(priority=5, staging_order=2)
        second, second_adr = self.mutate_wop(
            1, "EMP-MISSION-ZEUS-LIFECYCLE-HIGH-PRIORITY"
        )
        self.register(
            wop=second,
            adr=second_adr,
            priority=1,
            staging_order=9,
            approvals=(),
        )
        for wop, adr in ((self.wop, self.adr), (second, second_adr)):
            self.manager.transition(
                wop.wop_id,
                LifecycleState.STAGED,
                authorization_record=adr,
                repository_identity=REPOSITORY,
                repository_baseline=BASELINE,
                timestamp=START,
                actor="test",
            )
            self.manager.transition(
                wop.wop_id,
                LifecycleState.ELIGIBLE,
                authorization_record=adr,
                repository_identity=REPOSITORY,
                repository_baseline=BASELINE,
                prerequisite_evidence=PREREQUISITES,
                timestamp=START,
                actor="test",
            )
        self.assertEqual(
            self.manager.select_next(()),
            "EMP-MISSION-ZEUS-LIFECYCLE-HIGH-PRIORITY",
        )

    def test_blocked_and_deferred_queue_entries_are_not_selected(self) -> None:
        self.register()
        self.transition(LifecycleState.STAGED)
        self.transition(LifecycleState.ELIGIBLE)
        mission = self.wop.data["authority_binding"]["mission_id"]
        for status in (QueueStatus.BLOCKED, QueueStatus.DEFERRED):
            self.manager.set_queue_status(mission, status)
            with self.assertRaisesRegex(LifecycleError, "no eligible mission"):
                self.manager.select_next(())
            self.manager.set_queue_status(mission, QueueStatus.STAGED)

    def test_queue_dependency_graph_controls_selection(self) -> None:
        self.register(dependencies=("EMP-MISSION-PREREQUISITE",))
        self.transition(LifecycleState.STAGED)
        self.transition(LifecycleState.ELIGIBLE)
        with self.assertRaisesRegex(LifecycleError, "no eligible mission"):
            self.manager.select_next(())
        self.assertEqual(
            self.manager.select_next(("EMP-MISSION-PREREQUISITE",)),
            self.wop.data["authority_binding"]["mission_id"],
        )

    def test_reservation_is_planning_only_and_must_match(self) -> None:
        self.register()
        self.advance_to_selected()
        self.approve()
        self.transition(LifecycleState.AUTHORIZED)
        reservation = self.reservation()
        value = reservation.to_mapping()
        self.assertTrue(value["planning_only"])
        self.assertFalse(value["grants_authority"])
        self.assertFalse(value["is_execution_lease"])
        invalid = Reservation.create(
            wop_id=reservation.wop_id,
            mission_id=reservation.mission_id,
            authority_chain=reservation.authority_chain,
            requested_capabilities=("publish",),
            repository_baseline=BASELINE,
            expected_execution_agent="agent",
            created_at=START,
            expires_at=START + timedelta(hours=1),
        )
        with self.assertRaisesRegex(LifecycleError, "reservation does not match"):
            self.transition(LifecycleState.RESERVED, reservation=invalid)

    def test_expired_reservation_blocks_ready(self) -> None:
        self.register()
        self.advance_to_selected()
        self.approve()
        self.transition(LifecycleState.AUTHORIZED)
        reservation = self.reservation(expires=START + timedelta(minutes=1))
        self.transition(LifecycleState.RESERVED, reservation=reservation)
        with self.assertRaisesRegex(LifecycleError, "reservation is expired"):
            self.transition(
                LifecycleState.READY, timestamp=START + timedelta(minutes=2)
            )

    def test_restart_and_resume_reconstruct_identically(self) -> None:
        self.complete_lifecycle()
        expected = self.manager.reconstruct(self.wop.wop_id)
        restarted = WopLifecycleManager(LifecycleStore(self.state_path))
        self.assertEqual(restarted.reconstruct(self.wop.wop_id), expected)
        self.assertEqual(expected["state"], "Ready")
        self.assertIsNone(expected["pending_transition"])
        self.assertEqual(expected["reservation_status"], "planned")

    def test_tampered_event_is_rejected_on_restart(self) -> None:
        self.register()
        self.transition(LifecycleState.STAGED)
        value = json.loads(self.state_path.read_text())
        value["packages"][self.wop.wop_id]["history"][0]["actor"] = "tampered"
        self.state_path.write_text(json.dumps(value), encoding="utf-8")
        with self.assertRaisesRegex(LifecycleError, "digest mismatch"):
            WopLifecycleManager(LifecycleStore(self.state_path))

    def test_persistence_is_deterministic(self) -> None:
        self.register()
        first = self.state_path.read_bytes()
        self.manager.save()
        second = self.state_path.read_bytes()
        self.assertEqual(first, second)

    def test_evidence_tracking_does_not_qualify(self) -> None:
        self.register()
        self.manager.record_expected_evidence(
            self.wop.wop_id, ("execution-report",)
        )
        plans = self.manager.data["packages"][self.wop.wop_id]["evidence_plan"]
        self.assertEqual(set(plans), {state.value for state in LifecycleState})
        plan = plans["Draft"]
        self.assertEqual(plan["produced"], ["execution-report"])
        self.assertEqual(plan["missing"], ["validation-report"])
        self.assertFalse(plan["qualification_performed"])

    def test_reconciliation_is_planning_only(self) -> None:
        package = self.register()
        self.assertEqual(
            sorted(package["reconciliation_plan"]),
            [
                "completion_evidence",
                "controlled_documents",
                "mission_status",
                "project_state",
                "work_registry",
            ],
        )
        self.assertFalse(package["reconciliation_performed"])

    def test_cli_validates_and_resumes_persisted_state(self) -> None:
        self.complete_lifecycle()
        validate = subprocess.run(
            [str(ROOT / "scripts/wop-lifecyclectl"), str(self.state_path), "validate"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(validate.returncode, 0, validate.stderr)
        resume = subprocess.run(
            [
                str(ROOT / "scripts/wop-lifecyclectl"),
                str(self.state_path),
                "resume",
                "--wop",
                self.wop.wop_id,
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(resume.returncode, 0, resume.stderr)
        self.assertEqual(json.loads(resume.stdout)["state"], "Ready")

    def test_no_dispatch_execution_or_live_lease_api_exists(self) -> None:
        forbidden = {
            "dispatch",
            "execute",
            "acquire_execution_lease",
            "invoke_codex",
            "qualify_evidence",
            "perform_reconciliation",
        }
        self.assertTrue(forbidden.isdisjoint(set(dir(self.manager))))


if __name__ == "__main__":
    unittest.main()
