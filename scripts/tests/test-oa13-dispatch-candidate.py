#!/usr/bin/env python3
"""Regression coverage for OA-13 dispatch-candidate preparation."""
import copy
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.lib.emp.dispatch_candidate import create, validate


ROOT = Path(__file__).resolve().parents[2]


class OA13DispatchCandidateTests(unittest.TestCase):
    def candidate(self):
        recommendation = {
            "result": "PASS", "recommended_mission": "OA-13",
            "readiness": {"prerequisite_capabilities": ["ZEUS-OA-CAP-012"]},
        }
        agents = {"agents": [{
            "active": True, "qualification_status": "QUALIFIED",
            "agent_id": "test-agent",
            "execution_constraints": ["controlled-wop-only"],
        }]}
        with patch("scripts.lib.emp.dispatch_candidate.mission_knowledge.recommend", return_value=recommendation), \
             patch("scripts.lib.emp.dispatch_candidate.agent_registry", return_value=agents):
            return create(ROOT)

    def test_candidate_is_deterministic_and_non_executing(self):
        first = self.candidate()
        second = self.candidate()
        self.assertEqual(first, second)
        self.assertFalse(first["execution_started"])
        self.assertFalse(first["protected_effect_authorized"])
        with patch("scripts.lib.emp.dispatch_candidate.mission_knowledge.recommend", return_value={"result": "PASS", "recommended_mission": "OA-13", "readiness": {"prerequisite_capabilities": ["ZEUS-OA-CAP-012"]}}), \
             patch("scripts.lib.emp.dispatch_candidate.agent_registry", return_value={"agents": [{"active": True, "qualification_status": "QUALIFIED", "agent_id": "test-agent", "execution_constraints": ["controlled-wop-only"]}]}):
            self.assertEqual(validate(ROOT, first), first)

    def test_execution_flags_fail_closed(self):
        candidate = self.candidate()
        malformed = copy.deepcopy(candidate)
        malformed["execution_started"] = True
        with self.assertRaises(ValueError):
            with patch("scripts.lib.emp.dispatch_candidate.mission_knowledge.recommend", return_value={"result": "PASS", "recommended_mission": "OA-13", "readiness": {"prerequisite_capabilities": ["ZEUS-OA-CAP-012"]}}), \
                 patch("scripts.lib.emp.dispatch_candidate.agent_registry", return_value={"agents": [{"active": True, "qualification_status": "QUALIFIED", "agent_id": "test-agent", "execution_constraints": ["controlled-wop-only"]}]}):
                validate(ROOT, malformed)


if __name__ == "__main__":
    unittest.main()
