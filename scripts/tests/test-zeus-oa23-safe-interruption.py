#!/usr/bin/env python3
"""Regression coverage for OA-23 CAP-023."""

import tempfile
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.lib.emp.safe_interruption import PauseStore, SafeInterruptionError, authorize_pause, observe


class SafeInterruptionTests(unittest.TestCase):
    def record(self, **overrides):
        values = dict(request_id="TEST-PAUSE-001", mission_id="OA-23", target="operation",
                      repository="/canonical", baseline="baseline", authority="OA-23",
                      operator="operator", authorized=True, requested_at="2026-08-01T13:00:00Z",
                      expires_at="2026-08-01T14:00:00Z", at="2026-08-01T13:01:00Z")
        values.update(overrides)
        return authorize_pause(**values)

    def test_durable_idempotent_pause_and_observation(self):
        with tempfile.TemporaryDirectory() as directory:
            store = PauseStore(Path(directory))
            record = self.record()
            saved, created = store.save(record)
            replay, replay_created = store.save(record)
            self.assertTrue(created)
            self.assertFalse(replay_created)
            self.assertEqual(saved, replay)
            self.assertEqual(saved, store.load(record["request_id"]))
            self.assertFalse(observe(saved, at="2026-08-01T13:02:00Z")["completion_inferred"])

    def test_invalid_requests_fail_closed(self):
        with self.assertRaises(SafeInterruptionError):
            self.record(authorized=False)
        with self.assertRaises(SafeInterruptionError):
            self.record(at="2026-08-01T15:00:00Z")
        with self.assertRaises(SafeInterruptionError):
            self.record(mission_id="OA-24")

    def test_divergent_replay_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            store = PauseStore(Path(directory))
            store.save(self.record())
            with self.assertRaises(SafeInterruptionError):
                store.save(self.record(target="different-operation"))


if __name__ == "__main__":
    unittest.main()
