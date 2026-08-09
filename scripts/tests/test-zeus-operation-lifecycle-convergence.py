#!/usr/bin/env python3
"""Gate 1 qualification for Operation Beta/lifecycle projection convergence."""
from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.lib.eos import operational_beta  # noqa: E402


MISSION = "ZEUS-EXECUTION-LIFECYCLE-COMPLETION-01"
WOP = "WOP-ZEUS-EXECUTION-LIFECYCLE-COMPLETION-001"


def lifecycle_index(*entries):
    return {"result": "PASS", "missions": list(entries), "read_only": True}


def listed(mission_id=MISSION, state="READY_FOR_CONTROLLED_EXECUTION"):
    return {
        "mission_id": mission_id, "wop_id": WOP,
        "lifecycle_state": state,
        "next_authorized_action": "BEGIN_CONTROLLED_MISSION_WORK",
    }


def resolved(mission_id=MISSION, state="READY_FOR_CONTROLLED_EXECUTION"):
    return {
        "result": "PASS", "mission_id": mission_id, "wop_id": WOP,
        "submission_id": "SUBMISSION-1", "admission_id": "ADMISSION-1",
        "bootstrap_id": "BOOTSTRAP-1", "dispatch_id": "DISPATCH-1",
        "provider_id": "PROVIDER-1", "provider_session_id": "SESSION-1",
        "provider_invocation_id": "INVOCATION-1", "execution_id": "EXECUTION-1",
        "execution_session_id": "EXECUTION-SESSION-1", "lifecycle_state": state,
        "mission_work_started": False, "repository_work_started": False,
        "next_authorized_action": "BEGIN_CONTROLLED_MISSION_WORK",
        "canonical_lifecycle_owner": "RECEIPT_BACKED_CANONICAL_LIFECYCLE_CHAIN",
        "canonical_state_source": "P5_EXECUTION_START_RECEIPT",
        "execution_started": False,
    }


class OperationLifecycleConvergenceTests(unittest.TestCase):
    def current(self, index=None, state=None):
        index = index or lifecycle_index(listed())
        state = state or resolved()
        with patch("scripts.lib.emp.canonical_lifecycle_resolver.submitted_missions", return_value=index), \
             patch("scripts.lib.emp.canonical_lifecycle_resolver.resolve", return_value=state):
            return operational_beta._canonical_current_execution(ROOT)

    def test_active_receipt_state_preserves_mission_wop_state_action_and_work_boundary(self):
        value = self.current()["current_execution"]
        self.assertEqual(MISSION, value["mission_id"])
        self.assertEqual(WOP, value["wop_id"])
        self.assertEqual("READY_FOR_CONTROLLED_EXECUTION", value["lifecycle_state"])
        self.assertEqual("BEGIN_CONTROLLED_MISSION_WORK", value["lifecycle_next_action"])
        self.assertFalse(value["mission_work_started"])
        self.assertFalse(value["repository_work_started"])

    def test_current_gate_mapping_is_deterministic(self):
        mapping = self.current()["current_execution"]["current_gate_mapping"]
        self.assertEqual(4, mapping["wop_gate"])
        self.assertEqual("CONTROLLED-EXECUTION-AND-RECOVERY", mapping["wop_gate_id"])
        self.assertEqual("OB-ZEUS-G01", mapping["operation_gate_id"])

    def test_active_lifecycle_overrides_stale_future_roadmap_for_current_execution(self):
        current = self.current()["current_execution"]
        with patch.object(operational_beta, "_canonical_current_execution",
                          return_value={"result": "PASS", "current_execution": current,
                                        "blockers": [], "canonical_lifecycle_index": {}}):
            value = operational_beta.operation(ROOT)
        self.assertEqual(MISSION, value["current_executable_mission"])
        self.assertEqual("CAGF-01", value["future_recommended_mission"])
        self.assertNotEqual(value["current_executable_mission"], value["future_recommended_mission"])

    def test_planning_candidate_cannot_create_execution_authority(self):
        with patch.object(operational_beta, "_canonical_current_execution",
                          return_value={"result": "PASS", "current_execution": None,
                                        "blockers": [], "canonical_lifecycle_index": {}}):
            value = operational_beta.operation(ROOT)
        self.assertIsNone(value["current_executable_mission"])
        self.assertEqual("CAGF-01", value["future_recommended_mission"])

    def test_conflicting_active_missions_fail_closed(self):
        value = self.current(lifecycle_index(listed(), listed("ANOTHER-MISSION")))
        self.assertEqual("FAIL", value["result"])
        self.assertIsNone(value["current_execution"])
        self.assertEqual("MULTIPLE_CURRENT_EXECUTABLE_MISSIONS", value["blockers"][0]["code"])

    def test_duplicate_current_mission_claim_fails_closed(self):
        value = self.current(lifecycle_index(listed(), copy.deepcopy(listed())))
        self.assertEqual("FAIL", value["result"])
        self.assertEqual("MULTIPLE_CURRENT_EXECUTABLE_MISSIONS", value["blockers"][0]["code"])

    def test_historical_and_unresolved_records_do_not_become_current(self):
        history = listed("HISTORICAL-MISSION", "CLOSED")
        unresolved = listed("LEGACY-MISSION", "UNRESOLVED")
        value = self.current(lifecycle_index(history, unresolved, listed()))
        self.assertEqual(MISSION, value["current_execution"]["mission_id"])

    def test_index_resolver_contradiction_fails_closed(self):
        state = resolved()
        state["wop_id"] = "WOP-CONFLICT"
        value = self.current(state=state)
        self.assertEqual("FAIL", value["result"])
        self.assertEqual("BETA_CURRENT_LIFECYCLE_CONTRADICTION", value["blockers"][0]["code"])

    def test_replay_is_idempotent(self):
        first = self.current()
        second = self.current()
        self.assertEqual(first, second)

    def test_stage_local_next_action_does_not_override_global_lifecycle_action(self):
        current = self.current()["current_execution"]
        with patch.object(operational_beta, "operation", return_value={
            "result": "PASS", "missions": operational_beta._cards_with_dependencies(ROOT),
            "current_platform_mission": operational_beta._current_mission(ROOT),
            "current_executable_mission": MISSION, "current_execution": current,
            "current_wop": WOP, "current_lifecycle_state": "READY_FOR_CONTROLLED_EXECUTION",
            "current_gate_mapping": current["current_gate_mapping"],
            "lifecycle_next_action": "BEGIN_CONTROLLED_MISSION_WORK",
            "runtime_recovery_action": "SUPERSEDE_CODEX_SESSION", "metrics": {},
            "authoritative_sources": [], "blockers": [],
        }), patch.object(operational_beta, "_mission_projection", return_value={
            "current_execution": {"next_authorized_action": "SUBMIT_CAGF"},
            "historical_admissions": [], "historical_executions": [],
        }):
            value = operational_beta.next_action(ROOT)
        self.assertEqual("BEGIN_CONTROLLED_MISSION_WORK", value["next_authorized_action"])

    def test_runtime_recovery_action_is_distinct_from_lifecycle_next_action(self):
        current = self.current()["current_execution"]
        current["runtime_recovery_action"] = "SUPERSEDE_CODEX_SESSION"
        self.assertEqual("BEGIN_CONTROLLED_MISSION_WORK", current["lifecycle_next_action"])
        self.assertEqual("SUPERSEDE_CODEX_SESSION", current["runtime_recovery_action"])

    def test_gate_one_and_gate_four_crosswalks_are_independently_present(self):
        catalog = yaml.safe_load((ROOT / operational_beta.GATE_CATALOG).read_text())
        rows = [row for row in catalog["wop_gate_crosswalk"] if row["wop_id"] == WOP]
        by_gate = {row["wop_gate"]: row for row in rows}
        self.assertEqual("OB-ARCH-G01", by_gate[1]["operation_gate_id"])
        self.assertEqual("LIFECYCLE-AUTHORITY-CONVERGENCE", by_gate[1]["wop_gate_id"])
        self.assertEqual("OB-ZEUS-G01", by_gate[4]["operation_gate_id"])


if __name__ == "__main__":
    unittest.main()
