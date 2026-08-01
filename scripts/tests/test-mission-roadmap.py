#!/usr/bin/env python3
"""Regression coverage for the convergence-derived Operational Alpha roadmap."""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.lib.eos import mission_knowledge


class MissionRoadmapTests(unittest.TestCase):
    def test_authoritative_roadmap_is_complete(self):
        roadmap = mission_knowledge.authoritative_roadmap(ROOT)
        self.assertEqual(list(roadmap["objectives"]), [f"OA-{n:02d}" for n in range(1, 31)])

    def test_model_provenance_verifies(self):
        result = mission_knowledge.roadmap_verification(ROOT)
        self.assertEqual(result["result"], "PASS")
        self.assertEqual(result["roadmap_id"], "ZEUS-OA-ROADMAP-002")

    def test_projection_is_read_only_and_complete(self):
        projection = mission_knowledge.roadmap(ROOT)
        self.assertEqual(projection["provenance_verification"]["result"], "PASS")
        self.assertEqual([item["mission_id"] for item in projection["missions"]], [f"OA-{n:02d}" for n in range(1, 31)])

    def test_current_mission_and_blocker_are_model_derived(self):
        current = mission_knowledge.current(ROOT)
        self.assertEqual(current["mission_id"], "OA-19")
        self.assertEqual(current["lifecycle"], "CURRENT")
        readiness = mission_knowledge.readiness(ROOT, "OA-19")
        self.assertEqual(readiness["classification"], "ELIGIBLE")
        self.assertEqual(readiness["missing_capabilities"], [])
        self.assertEqual(readiness["missing_outcome_capabilities"], ["ZEUS-OA-CAP-018"])
        self.assertEqual(readiness["missing_dependencies"], [])

    def test_all_missions_have_consistent_model_projection(self):
        model = mission_knowledge.load(ROOT)
        for mission_id in model["mission_sequence"]:
            value = mission_knowledge.state(ROOT, mission_id)
            self.assertEqual(value["mission_id"], mission_id)
            self.assertEqual(value["authoritative_source"], mission_knowledge.PATH)

    def test_next_action_is_current_wop_projection(self):
        value = mission_knowledge.next_action(ROOT)
        self.assertEqual(value["current_mission"], "OA-19")
        self.assertEqual(value["next_authorized_action"]["wop"], "WOP-OA-19-EXECUTION-001")


if __name__ == "__main__":
    unittest.main()
