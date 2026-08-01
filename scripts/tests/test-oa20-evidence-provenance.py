#!/usr/bin/env python3
"""Independent OA-20 evidence integrity and provenance tests."""

from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.lib.emp.evidence_capture import EvidenceCapture
from scripts.lib.emp.evidence_provenance import EvidenceProvenance, EvidenceProvenanceError


class EvidenceProvenanceTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name)
        capture = EvidenceCapture(self.root / "capture.sqlite3")
        capture.capture(record_id="r1", mission_id="OA-20", wop_id="WOP-OA-20-EXECUTION-001", repository_identity="/repo", baseline_commit="a" * 40, agent_identity="agent", command="zeus verify OA-20", stdout="PASS", stderr="", state="COMPLETED", completion_marker="COMPLETE", timestamp="2026-08-01T00:00:00+00:00")
        self.record = list(capture.replay())[0].event.payload
        self.kwargs = dict(evidence_record=self.record, repository_identity="/repo", repository_commit="a" * 40, authority_identity="OA20-AUTHORITY", mission_id="OA-20", wop_id="WOP-OA-20-EXECUTION-001", execution_id="OA20-EXECUTION-001", gate_id="OA-20", agent_identity="agent", timestamp="2026-08-01T00:00:01+00:00")

    def tearDown(self):
        self.directory.cleanup()

    def test_binding_is_durable_and_replay_safe(self):
        path = self.root / "provenance.sqlite3"
        binder = EvidenceProvenance(path)
        self.assertTrue(binder.bind(**self.kwargs).inserted)
        self.assertFalse(binder.bind(**self.kwargs).inserted)
        self.assertEqual(EvidenceProvenance(path).store.count(), 1)

    def test_mismatch_and_tampering_fail_closed(self):
        binder = EvidenceProvenance(self.root / "provenance.sqlite3")
        with self.assertRaises(EvidenceProvenanceError):
            binder.bind(**{**self.kwargs, "mission_id": "OA-19"})
        tampered = {**self.record, "command": "tampered"}
        with self.assertRaises(EvidenceProvenanceError):
            binder.bind(**{**self.kwargs, "evidence_record": tampered})
        with self.assertRaises(EvidenceProvenanceError):
            binder.bind(**{**self.kwargs, "authority_identity": ""})


if __name__ == "__main__":
    unittest.main()
