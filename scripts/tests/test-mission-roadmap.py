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


if __name__ == "__main__":
    unittest.main()
