#!/usr/bin/env python3
"""Focused tests for the shared read-only publication resolver."""

from __future__ import annotations

import subprocess
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.lib.eos import canonical_baseline
from scripts.lib.eos.canonical_baseline import resolve


ROOT = Path(__file__).resolve().parents[2]
EOS = Path("/data/engineering")


def commit(ref: str) -> str:
    return subprocess.run(["git", "-C", str(ROOT), "rev-parse", ref], capture_output=True, text=True, check=True).stdout.strip()


class CanonicalBaselineResolutionTests(unittest.TestCase):
    def test_current_publication_equals_mission_provenance(self):
        value = resolve(ROOT, EOS, mission_provenance_baseline=commit("HEAD"))
        self.assertEqual(value["result"], "PASS")
        self.assertEqual(value["mission_baseline_relationship"], "EQUAL")
        self.assertEqual(value["baseline_relationship"], "IDENTICAL")
        self.assertTrue(value["provenance_valid"])

    def test_current_publication_descends_from_mission_provenance(self):
        value = resolve(ROOT, EOS, mission_provenance_baseline="df7fcd9a42e87a8bf09722a903dfb3753d60d856")
        self.assertEqual(value["result"], "PASS")
        self.assertEqual(value["mission_baseline_relationship"], "ANCESTOR")
        self.assertEqual(value["baseline_relationship"], "ANCESTOR")
        self.assertEqual(value["provenance_baseline"], "df7fcd9a42e87a8bf09722a903dfb3753d60d856")

    def test_unrelated_and_missing_provenance_fail_closed(self):
        unrelated = resolve(ROOT, EOS, mission_provenance_baseline="0000000000000000000000000000000000000001")
        self.assertEqual(unrelated["result"], "FAIL")
        self.assertIn("MISSION_PROVENANCE_BASELINE_MISSING", {e["code"] for e in unrelated["errors"]})
        missing = resolve(ROOT, EOS, mission_provenance_baseline=None)
        self.assertEqual(missing["checks"]["mission_provenance"], "PASS")

    def test_eos_and_publication_are_current(self):
        value = resolve(ROOT, EOS)
        self.assertEqual(value["current_head"], commit("HEAD"))
        self.assertEqual(value["published_head"], value["current_head"])
        self.assertEqual(value["eos_baseline"], value["current_head"])
        self.assertEqual(value["publication_parity"], "PASS")
        self.assertEqual(value["eos_parity"], "PASS")

    def test_head_must_equal_origin_main(self):
        current = commit("HEAD")
        with patch.object(canonical_baseline, "_git", side_effect=[(current, None), ("1" * 40, None), ("main", None)]):
            value = resolve(ROOT, EOS)
        self.assertEqual(value["result"], "FAIL")
        self.assertIn("PUBLICATION_PARITY_FAILURE", {e["code"] for e in value["errors"]})

    def test_stale_eos_fails_closed(self):
        with patch.object(canonical_baseline, "_git", side_effect=[("2" * 40, None), ("2" * 40, None), ("main", None)]):
            value = resolve(ROOT, EOS)
        self.assertEqual(value["result"], "FAIL")
        self.assertIn("EOS_BASELINE_MISMATCH", {e["code"] for e in value["errors"]})

    def test_runtime_identity_mismatch_fails_closed(self):
        value = resolve(ROOT, EOS, runtime_identity={"repository": "/other", "repository_id": "other", "repository_fingerprint": "x", "repository_identity": "other"})
        self.assertEqual(value["result"], "FAIL")
        self.assertIn("RUNTIME_REPOSITORY_BINDING_MISMATCH", {e["code"] for e in value["errors"]})


if __name__ == "__main__":
    unittest.main()
