#!/usr/bin/env python3
"""Regression entry point for the independently qualified OA-16 capability."""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.lib.emp import progressive_oa  # noqa: E402


class OA16ExecutionStartTests(unittest.TestCase):
    def test_durable_start_and_eens_qualification(self):
        marker_path, marker = progressive_oa._marker_binding(ROOT, "OA-16")
        self.assertEqual(marker_path.name, "VERIFIED")
        self.assertEqual(marker["verification_result"], "PASS")
        self.assertTrue(marker["evidence_digest"])


if __name__ == "__main__":
    unittest.main()
