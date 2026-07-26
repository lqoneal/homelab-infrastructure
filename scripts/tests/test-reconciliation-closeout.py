#!/usr/bin/env python3
"""Regression tests for atomic reconciliation and WOP closeout."""

from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.lib.emp.evidence_qualification import (
    DigestFixtureSignatureVerifier,
    EvidenceItem,
    EvidencePackage,
    QualificationContract,
    QualificationEngine,
)
from scripts.lib.emp.reconciliation import (
    AuthoritativeStateStore,
    CompletionRecord,
    ReconciliationEngine,
    ReconciliationError,
    ReconciliationPlan,
    ReconciliationUpdate,
    digest,
    identifier,
)
from scripts.lib.emp.wop_dispatch import ExecutionAssignment


REPOSITORY = str(ROOT)
BASELINE_BEFORE = "d4085b315c0288213622ebcb6fa0f276b4e52099"
BASELINE_AFTER = "a" * 40
NOW = datetime(2026, 7, 25, 4, 0, tzinfo=timezone.utc)
MISSION = "EMP-MISSION-ZEUS-RECONCILIATION"
WOP = "WOP-723e4567-e89b-42d3-a456-426614174000"
SESSION = "SESSION-823e4567-e89b-42d3-a456-426614174000"


class ReconciliationCloseoutTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.state_path = Path(temporary.name) / "authoritative-state.json"
        package = {
            "authority_chain": ["work-package", "mission", "governance"],
            "authorization_decision_digest": "1" * 64,
            "repository_baseline": BASELINE_BEFORE,
            "repository_identity": REPOSITORY,
            "mission_id": MISSION,
            "requested_capabilities": ["execute"],
            "wop_digest": "2" * 64,
            "wop_id": WOP,
        }
        self.assignment = ExecutionAssignment.create(
            package=package,
            intended_agent="supervised-agent-1",
            expected_evidence=("completion-evidence",),
            dispatch_timestamp=NOW,
            approval_reference="APPROVAL-MISSION-M-001",
        )
        self.session = {
            "session_id": SESSION,
            "assignment_id": self.assignment.data["assignment_id"],
            "repository_identity": REPOSITORY,
            "baseline_commit": BASELINE_BEFORE,
            "execution_agent_identity": "supervised-agent-1",
            "current_execution_state": "Completed",
        }
        self.artifacts = {"completion-evidence": b"qualified result"}
        item = EvidenceItem.create(
            artifact_identifier="completion-evidence",
            artifact_type="completion-report",
            producing_component="qualified-execution-agent",
            content=self.artifacts["completion-evidence"],
            wop_objective="closeout-objective",
            verification_requirement="completion-verification",
            classification="required",
        )
        self.evidence_package = EvidencePackage.create(
            assignment=self.assignment,
            execution_session_id=SESSION,
            execution_agent_identity="supervised-agent-1",
            evidence_items=(item,),
            required_evidence=("completion-evidence",),
            produced_evidence=("completion-evidence",),
            completion_metadata={
                "completed_verification_steps": ["regression"],
                "execution_complete": True,
            },
            package_timestamp=NOW,
            signature_key_id="mission-m-fixture",
        )
        self.contract = QualificationContract.from_mapping(
            {
                "assignment_id": self.assignment.data["assignment_id"],
                "baseline_commit": BASELINE_BEFORE,
                "expected_evidence": ["completion-evidence"],
                "mission_id": MISSION,
                "objectives": {
                    "closeout-objective": ["completion-evidence"],
                },
                "prohibited_evidence": [],
                "repository_identity": REPOSITORY,
                "required_evidence": ["completion-evidence"],
                "required_verification_steps": ["regression"],
                "wop_id": WOP,
            }
        )
        self.report = QualificationEngine().evaluate(
            evidence_package=self.evidence_package,
            artifacts=self.artifacts,
            contract=self.contract,
            assignment=self.assignment,
            execution_session=self.session,
            signature_verifier=DigestFixtureSignatureVerifier(),
        )
        self.assertEqual(self.report.data["qualification_decision"], "PASS")
        self.initial_values = {
            "project-state": (
                "project_state",
                {"current_status": "executing", "mission": MISSION},
            ),
            "work-registry": (
                "work_registry",
                {"wops": {WOP: "Qualified"}},
            ),
            "mission-registry": (
                "mission_registry",
                {"missions": {MISSION: "active"}},
            ),
            "wop-lifecycle": (
                "wop_lifecycle",
                {
                    "history": [
                        "Ready",
                        "Dispatched",
                        "Executing",
                        "Qualified",
                    ],
                    "state": "Qualified",
                },
            ),
            "execution-session": (
                "execution_session",
                {"closeout_status": "Qualified", "session_id": SESSION},
            ),
            "qualification-history": (
                "qualification_history",
                {
                    "qualification_reports": [
                        self.report.data["qualification_id"]
                    ]
                },
            ),
            "resume-state": (
                "resume_state",
                {
                    "current_engineering_status": "qualified",
                    "pending_work": [MISSION],
                },
            ),
            "progress": (
                "progress_tracking",
                {"completed_wop": None},
            ),
            "controlled-doc": (
                "controlled_document",
                {"status": "pre-closeout", "wop": WOP},
            ),
        }
        state = {
            "schema_version": 1,
            "store_id": "EMP-AUTHORITATIVE-ENGINEERING-STATE",
            "records": {
                record_id: {
                    "record_id": record_id,
                    "record_kind": kind,
                    "revision": digest(value),
                    "value": copy.deepcopy(value),
                }
                for record_id, (kind, value) in self.initial_values.items()
            },
            "completion_records": {},
        }
        AuthoritativeStateStore(self.state_path).save(state)
        self.engine = ReconciliationEngine(AuthoritativeStateStore(self.state_path))

    def resulting_values(self):
        return {
            "project-state": {"current_status": "reconciled", "mission": MISSION},
            "work-registry": {"wops": {WOP: "Closed"}},
            "mission-registry": {"missions": {MISSION: "completed"}},
            "wop-lifecycle": {
                "history": [
                    "Ready",
                    "Dispatched",
                    "Executing",
                    "Qualified",
                    "Reconciling",
                    "Closed",
                ],
                "state": "Closed",
            },
            "execution-session": {
                "closeout_status": "Closed",
                "session_id": SESSION,
            },
            "qualification-history": {
                "qualification_reports": [self.report.data["qualification_id"]],
                "reconciliation_consumptions": [WOP],
            },
            "resume-state": {
                "completed_mission": MISSION,
                "completed_mission_phase": "Zeus Operational Alpha",
                "completed_wop": WOP,
                "current_engineering_status": "reconciled",
                "next_eligible_mission": "EMP-MISSION-N",
                "pending_work": ["EMP-MISSION-N"],
            },
            "progress": {
                "completed_wop": WOP,
                "qualification_report_id": self.report.data["qualification_id"],
            },
            "controlled-doc": {"status": "closeout-published", "wop": WOP},
        }

    def plan(self, *, mutate=None, scope=None):
        values = self.resulting_values()
        if mutate:
            values.update(mutate)
        updates = [
            ReconciliationUpdate(
                target_record=record_id,
                record_kind=self.initial_values[record_id][0],
                expected_current_revision=digest(self.initial_values[record_id][1]),
                resulting_value=value,
                modification_reason="qualified WOP closeout",
            )
            for record_id, value in values.items()
        ]
        return ReconciliationPlan.create(
            wop_id=WOP,
            qualification_report_id=self.report.data["qualification_id"],
            updates=updates,
            declared_scope=scope or tuple(values),
            approval_reference="APPROVAL-RECONCILIATION-M-001",
        )

    def execute(self, plan=None, report=None, **changes):
        arguments = {
            "plan": plan or self.plan(),
            "qualification_report": report or self.report,
            "evidence_package": self.evidence_package,
            "assignment": self.assignment,
            "execution_session": self.session,
            "artifacts": self.artifacts,
            "repository_identity": REPOSITORY,
            "baseline_before": BASELINE_BEFORE,
            "baseline_after": BASELINE_AFTER,
            "mission_id": MISSION,
            "wop_id": WOP,
            "completion_timestamp": NOW,
            "reconciliation_summary": "nine scoped records reconciled atomically",
            "wop_declared_scope": tuple(self.resulting_values()),
        }
        arguments.update(changes)
        return self.engine.execute(**arguments)

    def test_pass_qualification_reconciles_all_scoped_records(self) -> None:
        completion = self.execute()
        state = self.engine.state
        self.assertEqual(len(state["records"]), 9)
        self.assertEqual(len(state["completion_records"]), 1)
        self.assertEqual(
            state["records"]["wop-lifecycle"]["value"]["state"], "Closed"
        )
        self.assertEqual(
            state["records"]["resume-state"]["value"]["next_eligible_mission"],
            "EMP-MISSION-N",
        )
        self.assertEqual(
            completion.data["modified_authoritative_records"],
            sorted(self.resulting_values()),
        )

    def test_non_pass_report_fails_without_modification(self) -> None:
        failed = QualificationEngine().evaluate(
            evidence_package=self.evidence_package,
            artifacts=self.artifacts,
            contract=self.contract,
            assignment=self.assignment,
            execution_session={
                **self.session,
                "current_execution_state": "Running",
            },
            signature_verifier=DigestFixtureSignatureVerifier(),
        )
        self.assertEqual(failed.data["qualification_decision"], "FAIL")
        before = self.state_path.read_bytes()
        with self.assertRaisesRegex(ReconciliationError, "PASS"):
            self.execute(report=failed)
        self.assertEqual(self.state_path.read_bytes(), before)

    def test_scope_enforcement_rejects_unauthorized_target(self) -> None:
        with self.assertRaisesRegex(ReconciliationError, "outside WOP"):
            self.plan(scope=tuple(self.resulting_values())[:-1])

    def test_plan_is_deterministic_and_immutable(self) -> None:
        first = self.plan()
        second = self.plan()
        self.assertEqual(first.canonical_data, second.canonical_data)
        value = first.data
        value["targets"][0]["modification_reason"] = "tampered"
        with self.assertRaisesRegex(ReconciliationError, "digest"):
            ReconciliationPlan.from_mapping(value)

    def test_stale_revision_fails_atomically(self) -> None:
        plan = self.plan()
        value = plan.data
        value["targets"][0]["expected_current_revision"] = "0" * 64
        identity_material = {
            key: item
            for key, item in value.items()
            if key not in {"plan_id", "plan_digest"}
        }
        value["plan_id"] = identifier("RECONCILIATION", identity_material)
        unsigned = {key: item for key, item in value.items() if key != "plan_digest"}
        value["plan_digest"] = digest(unsigned)
        before = self.state_path.read_bytes()
        with self.assertRaises(ReconciliationError):
            self.execute(plan=ReconciliationPlan.from_mapping(value))
        self.assertEqual(self.state_path.read_bytes(), before)

    def test_consistency_failure_rolls_back_all_records(self) -> None:
        plan = self.plan(
            mutate={
                "resume-state": {
                    "completed_wop": "wrong",
                    "completed_mission": MISSION,
                    "current_engineering_status": "reconciled",
                    "next_eligible_mission": "EMP-MISSION-N",
                    "pending_work": [],
                }
            }
        )
        before = self.state_path.read_bytes()
        with self.assertRaisesRegex(ReconciliationError, "resume"):
            self.execute(plan=plan)
        self.assertEqual(self.state_path.read_bytes(), before)
        self.assertEqual(self.engine.state["completion_records"], {})

    def test_persistence_failure_rolls_back_logical_transaction(self) -> None:
        delegate = AuthoritativeStateStore(self.state_path)

        class FailingStore:
            @staticmethod
            def load():
                return delegate.load()

            @staticmethod
            def save(_value):
                raise OSError("injected persistence failure")

        engine = ReconciliationEngine(FailingStore())
        before_disk = self.state_path.read_bytes()
        before_memory = engine.state
        with self.assertRaisesRegex(OSError, "injected"):
            engine.execute(
                plan=self.plan(),
                qualification_report=self.report,
                evidence_package=self.evidence_package,
                assignment=self.assignment,
                execution_session=self.session,
                artifacts=self.artifacts,
                repository_identity=REPOSITORY,
                baseline_before=BASELINE_BEFORE,
                baseline_after=BASELINE_AFTER,
                mission_id=MISSION,
                wop_id=WOP,
                completion_timestamp=NOW,
                reconciliation_summary="injected atomic failure",
                wop_declared_scope=tuple(self.resulting_values()),
            )
        self.assertEqual(self.state_path.read_bytes(), before_disk)
        self.assertEqual(engine.state, before_memory)

    def test_repeated_reconciliation_is_idempotent(self) -> None:
        first = self.execute()
        after_first = self.state_path.read_bytes()
        second = self.execute()
        self.assertEqual(first.canonical_data, second.canonical_data)
        self.assertEqual(self.state_path.read_bytes(), after_first)

    def test_completion_record_is_deterministic_and_tamper_evident(self) -> None:
        completion = self.execute()
        restarted = ReconciliationEngine(AuthoritativeStateStore(self.state_path))
        stored = restarted.state["completion_records"][
            completion.data["completion_id"]
        ]
        self.assertEqual(
            CompletionRecord.from_mapping(stored).canonical_data,
            completion.canonical_data,
        )
        stored["reconciliation_summary"] = "tampered"
        with self.assertRaisesRegex(ReconciliationError, "digest"):
            CompletionRecord.from_mapping(stored)

    def test_wop_closes_only_after_successful_consistency_verification(self) -> None:
        before = self.engine.state
        self.assertEqual(
            before["records"]["wop-lifecycle"]["value"]["state"], "Qualified"
        )
        self.execute()
        after = self.engine.state
        self.assertEqual(
            after["records"]["wop-lifecycle"]["value"]["history"][-2:],
            ["Reconciling", "Closed"],
        )

    def test_controlled_document_changes_only_when_declared(self) -> None:
        completion = self.execute()
        self.assertIn(
            "controlled-doc", completion.data["modified_authoritative_records"]
        )
        self.assertEqual(
            self.engine.state["records"]["controlled-doc"]["value"]["status"],
            "closeout-published",
        )

    def test_execution_rejects_scope_expansion_or_disagreement(self) -> None:
        before = self.state_path.read_bytes()
        with self.assertRaisesRegex(ReconciliationError, "scope binding"):
            self.execute(wop_declared_scope=("project-state",))
        self.assertEqual(self.state_path.read_bytes(), before)

    def test_artifact_digest_gate_fails_without_modification(self) -> None:
        before = self.state_path.read_bytes()
        with self.assertRaisesRegex(ReconciliationError, "artifact digest"):
            self.execute(artifacts={"completion-evidence": b"tampered"})
        self.assertEqual(self.state_path.read_bytes(), before)

    def test_repository_baseline_assignment_session_and_wop_gates(self) -> None:
        changes = (
            {"repository_identity": "/wrong"},
            {"baseline_before": "0" * 40},
            {"wop_id": "WOP-wrong"},
            {"mission_id": "MISSION-wrong"},
            {"execution_session": {**self.session, "session_id": "SESSION-wrong"}},
        )
        for change in changes:
            with self.subTest(change=change):
                before = self.state_path.read_bytes()
                with self.assertRaises(ReconciliationError):
                    self.execute(**change)
                self.assertEqual(self.state_path.read_bytes(), before)

    def test_report_and_package_digest_gates(self) -> None:
        package_value = self.evidence_package.data
        package_value["package_checksum"] = "0" * 64
        before = self.state_path.read_bytes()
        with self.assertRaises(ReconciliationError):
            self.execute(
                evidence_package=EvidencePackage(json.dumps(package_value))
            )
        self.assertEqual(self.state_path.read_bytes(), before)

    def test_resume_and_progress_are_immediately_consistent(self) -> None:
        completion = self.execute()
        state = self.engine.state["records"]
        resume = state["resume-state"]["value"]
        progress = state["progress"]["value"]
        self.assertEqual(resume["completed_wop"], WOP)
        self.assertEqual(resume["completed_mission"], MISSION)
        self.assertEqual(progress["completed_wop"], WOP)
        self.assertEqual(
            progress["qualification_report_id"],
            completion.data["qualification_report_id"],
        )

    def test_cli_validates_reconciled_state(self) -> None:
        self.execute()
        result = subprocess.run(
            [
                str(ROOT / "scripts/reconcile-closeoutctl"),
                str(self.state_path),
                "validate",
            ],
            text=True,
            capture_output=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("9 records, 1 completions", result.stdout)

    def test_no_autonomous_selection_dispatch_execution_or_generation_api(self) -> None:
        forbidden = {
            "select_mission",
            "dispatch",
            "execute_wop",
            "generate_wop",
            "plan_mission",
            "prioritize_mission",
        }
        self.assertTrue(forbidden.isdisjoint(set(dir(self.engine))))


if __name__ == "__main__":
    unittest.main()
