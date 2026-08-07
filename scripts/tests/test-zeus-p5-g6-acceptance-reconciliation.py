#!/usr/bin/env python3
"""Focused tests for importing an already-applied P5-G6 acceptance."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.lib.emp.gate_approval import P5GateAcceptanceService


EXECUTION = {
    "mission_id": "MISSION-BETA-1",
    "wop_id": "WOP-BETA-1",
    "execution_id": "EXECUTION-1",
    "session_id": "CODEX-SESSION-1",
    "provider_id": "PROVIDER-1",
    "provider_session_id": "PROVIDER-SESSION-1",
    "execution_state": "EXECUTING",
    "provider_liveness": "ALIVE",
    "mission_work_state": "STARTED",
    "repository_work_state": "NOT_STARTED",
    "current_work_position": "P5-G6:CONTROLLED_MISSION_WORK",
    "progress_state": "ACTIVE",
    "projection_verification": "PASS",
    "verification_result": "PASS",
    "blockers": [],
    "approvals_required": [],
    "phase": {"id": "P5"},
    "gate": {"id": "P5-G6"},
    "source_records": {"monitoring_record": "runtime://execution-monitoring"},
    "source_digests": {"monitoring_record_digest": "a" * 64},
}


class P5G6AcceptanceReconciliationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        report = self.root / "engineering/evidence/operation-beta"
        report.mkdir(parents=True)
        (report / "p5-g6-controlled-active-execution-foundation-completion-report.md").write_text(
            "\n".join([
                "EXECUTION_ID=EXECUTION-1",
                "P5_G6_OPERATOR_ACCEPTANCE=ACCEPTED",
                "P5_G6_ACCEPTED_AT=2026-08-07T11:36:31Z",
                "TRUE_ACTIVE_P5_G6_DEMONSTRATION=PASS",
                "P5_G6_DISPOSITION=ACCEPTED",
                "PUBLICATION_AUTHORIZED_BY_THIS_ACCEPTANCE=NO",
                "P5_G7_AUTHORIZED_BY_THIS_ACCEPTANCE=NO",
            ]) + "\n"
        )
        self.service = P5GateAcceptanceService(self.root)

    def tearDown(self) -> None:
        self.temp.cleanup()

    @patch("scripts.lib.emp.execution_monitoring.verify", return_value=EXECUTION)
    def test_reconciliation_is_applied_once_and_replay_is_idempotent(self, _verify) -> None:
        record, replay = self.service.reconcile_existing()
        self.assertFalse(replay)
        self.assertEqual(record["decision_origin"], "EXISTING_MANUAL_ACCEPTANCE")
        self.assertFalse(record["new_operator_decision"])
        again, replay = self.service.reconcile_existing()
        self.assertTrue(replay)
        self.assertEqual(record, again)
        self.assertEqual(len(list(self.service.record_directory.glob("*.json"))), 1)

    @patch("scripts.lib.emp.execution_monitoring.verify", return_value=EXECUTION)
    def test_readiness_projects_existing_acceptance_without_deciding(self, _verify) -> None:
        value = self.service.readiness()
        self.assertEqual(value["acceptance_readiness"], "PASS")
        self.assertEqual(value["manual_acceptance_discovered"], "PASS")
        self.assertEqual(value["canonical_disposition"], "PENDING_RECONCILIATION")

    def test_missing_manual_acceptance_fails_closed(self) -> None:
        report = self.root / "engineering/evidence/operation-beta/p5-g6-controlled-active-execution-foundation-completion-report.md"
        report.write_text("EXECUTION_ID=EXECUTION-1\n")
        with self.assertRaisesRegex(Exception, "incomplete"):
            self.service.readiness()


if __name__ == "__main__":
    unittest.main()
