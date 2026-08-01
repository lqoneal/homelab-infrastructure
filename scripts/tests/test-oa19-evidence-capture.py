#!/usr/bin/env python3
"""Independent OA-19 evidence-capture qualification tests."""

from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.lib.emp.evidence_capture import EvidenceCapture, EvidenceCaptureError


class EvidenceCaptureTests(unittest.TestCase):
    def test_required_fields_and_restart_replay(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "evidence.sqlite3"
            capture = EvidenceCapture(path)
            kwargs = dict(record_id="r1", mission_id="OA-19", wop_id="WOP-OA-19-EXECUTION-001", repository_identity="/repo", baseline_commit="a" * 40, agent_identity="agent", command="zeus verify OA-19", stdout="PASS", stderr="", state="COMPLETED", completion_marker="COMPLETE", timestamp="2026-08-01T00:00:00+00:00")
            first = capture.capture(**kwargs)
            duplicate = capture.capture(**kwargs)
            self.assertTrue(first.inserted)
            self.assertFalse(duplicate.inserted)
            self.assertEqual(capture.store.count(), 1)
            self.assertEqual(EvidenceCapture(path).store.count(), 1)

    def test_malformed_input_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            capture = EvidenceCapture(Path(directory) / "evidence.sqlite3")
            kwargs = dict(record_id="r1", mission_id="OA-19", wop_id="WOP-OA-19-EXECUTION-001", repository_identity="/repo", baseline_commit="a" * 40, agent_identity="agent", command="", stdout="PASS", stderr="", state="COMPLETED", completion_marker="COMPLETE", timestamp="2026-08-01T00:00:00+00:00")
            with self.assertRaises(EvidenceCaptureError):
                capture.capture(**kwargs)


if __name__ == "__main__":
    unittest.main()
