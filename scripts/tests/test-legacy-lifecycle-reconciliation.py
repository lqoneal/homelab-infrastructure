#!/usr/bin/env python3
"""Focused tests for the bounded pre-Mission-Contract reconciliation."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.lib.emp import legacy_lifecycle_reconciliation as legacy


class LegacyLifecycleReconciliationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        report = self.root / legacy.REPORT
        report.parent.mkdir(parents=True)
        report.write_text("\n".join([
            "P5_G6_OPERATOR_ACCEPTANCE=ACCEPTED",
            "TRUE_ACTIVE_P5_G6_DEMONSTRATION=PASS",
            "P5_G6_DISPOSITION=ACCEPTED",
            "PUBLICATION_AUTHORIZED_BY_THIS_ACCEPTANCE=NO",
            "P5_G7_AUTHORIZED_BY_THIS_ACCEPTANCE=NO",
        ]) + "\n", encoding="utf-8")
        acceptance = {
            "record_type": "ACCEPTANCE_RECONCILIATION", "mission_id": legacy.MISSION,
            "execution_id": legacy.EXECUTION, "wop_id": legacy.WOP, "gate_id": "P5-G6",
            "new_operator_decision": False, "publication_authorized": False,
        }
        acceptance["record_digest"] = legacy._digest(acceptance)
        path = self.root / legacy.ACCEPTANCE
        path.parent.mkdir(parents=True)
        path.write_text(json.dumps(acceptance), encoding="utf-8")
        self.transaction = {"mission_id": legacy.MISSION, "execution_id": legacy.EXECUTION, "wop_id": legacy.WOP}
        self.monitoring = {**self.transaction, "repository_work_started": False}

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _authority(self):
        return {"operation_id": "OPERATION-BETA", "current_platform_mission": {"mission_id": "BETA-04"},
                "next_authorized_action": "Publish a separately authorized WOP for CAGF-01, then submit and admit it through Zeus."}

    @patch("scripts.lib.emp.mission_contract_discovery.discover", return_value={"applicable_candidate_count": 0})
    @patch("scripts.lib.eos.operational_beta.authority")
    @patch("scripts.lib.emp.legacy_lifecycle_reconciliation._git", side_effect=["commit", ""])
    def test_verified_legacy_facts_project_historical_terminal_state(self, _git, authority, _contracts):
        authority.return_value = self._authority()
        value = legacy.inspect(self.root, self.root / "runtime", transaction=self.transaction, monitoring=self.monitoring)
        projected = legacy.overlay({"next_authorized_action": "CONTINUE_CONTROLLED_MISSION_WORK"}, value)
        self.assertEqual(value["disposition"], "RECONCILED_HISTORICAL")
        self.assertEqual(projected["next_authorized_action"], "OPERATOR_REVIEW_LEGACY_LIFECYCLE_RECONCILIATION")
        self.assertEqual(projected["execution_state"], "RECONCILED_HISTORICAL")
        self.assertFalse(projected["execution_monitoring_active"])

    @patch("scripts.lib.emp.mission_contract_discovery.discover", return_value={"applicable_candidate_count": 1})
    @patch("scripts.lib.eos.operational_beta.authority")
    @patch("scripts.lib.emp.legacy_lifecycle_reconciliation._git", side_effect=["commit", ""])
    def test_modern_contract_cardinality_remains_fail_closed(self, _git, authority, _contracts):
        authority.return_value = self._authority()
        with self.assertRaisesRegex(Exception, "CARDINALITY"):
            legacy.inspect(self.root, self.root / "runtime", transaction=self.transaction, monitoring=self.monitoring)

    @patch("scripts.lib.emp.mission_contract_discovery.discover", return_value={"applicable_candidate_count": 0})
    @patch("scripts.lib.eos.operational_beta.authority")
    @patch("scripts.lib.emp.legacy_lifecycle_reconciliation._git", side_effect=["commit", ""])
    def test_repository_work_or_contradictory_binding_fails_closed(self, _git, authority, _contracts):
        authority.return_value = self._authority()
        with self.assertRaisesRegex(Exception, "REPOSITORY_WORK"):
            legacy.inspect(self.root, self.root / "runtime", transaction=self.transaction,
                           monitoring={**self.monitoring, "repository_work_started": True})

    def test_reconciliation_receipt_replays_idempotently_without_contract(self):
        with patch.object(legacy, "inspect", return_value={"disposition": "RECONCILED_HISTORICAL", "acceptance_record": "x"}):
            first = legacy.reconcile(self.root, self.root / "runtime", transaction=self.transaction, monitoring=self.monitoring, approve=True)
            second = legacy.reconcile(self.root, self.root / "runtime", transaction=self.transaction, monitoring=self.monitoring, approve=True)
        self.assertEqual(first["replay"], "NOT_REPLAYED")
        self.assertEqual(second["replay"], "IDEMPOTENT")
        self.assertEqual(len(list((self.root / "runtime" / legacy.RECEIPT_DIR).glob("*.json"))), 1)
        self.assertFalse(first["receipt"]["mission_contract_created"])

    def test_read_only_reconciliation_has_no_receipt_and_is_distinct(self):
        with patch.object(legacy, "inspect", return_value={"disposition": "RECONCILED_HISTORICAL", "acceptance_record": "x"}):
            value = legacy.reconcile(self.root, self.root / "runtime", transaction=self.transaction,
                                     monitoring=self.monitoring, approve=False)
        self.assertTrue(value["read_only"])
        self.assertFalse(value["approved_persistence_requested"])
        self.assertEqual(value["replay"], "NOT_PERSISTED")
        self.assertIsNone(value["receipt"])
        self.assertFalse((self.root / "runtime" / legacy.RECEIPT_DIR).exists())

    def test_malformed_acceptance_fails_closed(self):
        (self.root / legacy.ACCEPTANCE).write_text("{}", encoding="utf-8")
        with self.assertRaisesRegex(Exception, "DIGEST"):
            legacy.inspect(self.root, self.root / "runtime", transaction=self.transaction, monitoring=self.monitoring)


if __name__ == "__main__":
    unittest.main()
