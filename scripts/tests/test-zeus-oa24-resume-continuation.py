#!/usr/bin/env python3
"""Regression coverage for OA-24 CAP-024."""

import tempfile
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.lib.emp.resume_continuation import ContinuationError, ContinuationStore, create_state


class ResumeContinuationTests(unittest.TestCase):
    def state(self):
        return create_state(execution_id="EXEC-1", mission_id="OA-24", repository="/canonical", baseline="baseline", authority="OA-24", operator="operator", operations=[
            {"operation_id": "OP-1", "sequence": 1, "state": "COMPLETED", "effect_applied": True},
            {"operation_id": "OP-2", "sequence": 2, "state": "INCOMPLETE", "effect_applied": False},
        ])

    def test_reconstructs_first_incomplete_and_replays_idempotently(self):
        with tempfile.TemporaryDirectory() as directory:
            store = ContinuationStore(Path(directory)); state = self.state()
            saved, created = store.save_state(state)
            first, first_created = store.resume("EXEC-1", mission_id="OA-24", baseline="baseline", at="2026-08-01T15:00:00Z")
            replay, replay_created = store.resume("EXEC-1", mission_id="OA-24", baseline="baseline", at="2026-08-01T15:00:00Z")
            self.assertTrue(created and first_created and not replay_created)
            self.assertEqual(first, replay)
            self.assertEqual(first["first_incomplete_operation"], "OP-2")
            self.assertFalse(first["effects_applied"])

    def test_mismatched_binding_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            store = ContinuationStore(Path(directory)); store.save_state(self.state())
            with self.assertRaises(ContinuationError):
                store.resume("EXEC-1", mission_id="OA-24", baseline="other", at="2026-08-01T15:00:00Z")

    def test_divergent_state_replay_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            store = ContinuationStore(Path(directory)); state = self.state(); store.save_state(state)
            changed = dict(state); changed["operations"] = list(state["operations"])
            changed["operations"][1] = dict(changed["operations"][1], operation_id="OP-X")
            with self.assertRaises(ContinuationError):
                store.save_state(changed)


if __name__ == "__main__":
    unittest.main()
