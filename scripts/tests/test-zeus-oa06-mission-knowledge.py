#!/usr/bin/env python3
"""OA-06 mission knowledge and recommendation qualification."""
from __future__ import annotations
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.lib.eos import mission_knowledge

class OA06MissionKnowledgeTests(unittest.TestCase):
    def test_accepted_oa06_exposes_the_controlled_oa07_successor(self):
        first = mission_knowledge.recommend(ROOT)
        self.assertEqual("PASS", first["result"])
        self.assertEqual("OA-08", first["recommended_mission"])
        self.assertEqual(first, mission_knowledge.recommend(ROOT))

    def test_readiness_explains_prerequisites_without_independent_ordering(self):
        value = mission_knowledge.readiness(ROOT, "OA-06")
        self.assertEqual("COMPLETED", value["classification"])
        self.assertEqual(["OA-05"], value["dependencies"])
        self.assertEqual([], value["missing_dependencies"])
        self.assertEqual([], value["missing_capabilities"])

    def test_operator_services_are_emm_bound(self):
        for arguments in (("mission", "recommend"), ("mission", "explain", "OA-06"), ("mission", "dependency-graph")):
            result = subprocess.run([str(ROOT / "scripts/zeus"), *arguments], cwd=ROOT, text=True, capture_output=True, check=False)
            self.assertEqual(0, result.returncode, result.stderr)

if __name__ == "__main__":
    unittest.main()
