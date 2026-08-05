#!/usr/bin/env python3
"""Disposable qualification for autonomous dispatch and provider launch."""

import tempfile
import unittest
from pathlib import Path

from scripts.lib.emp.autonomous_dispatch import (
    AutonomousDispatchController,
    LaunchStore,
)


class AutonomousDispatchTests(unittest.TestCase):
    def authoritative(self):
        dispatch = {
            "receipt_id": "DISPATCH-1", "receipt_digest": "d" * 64,
            "instance_id": "ZEUS-EXECUTION-1", "provider_id": "provider-1",
            "agent_id": "agent-1", "authority_snapshot_digest": "a" * 64,
        }
        return {
            "instance_id": "ZEUS-EXECUTION-1", "wop_id": "WOP-1", "mission_id": "MISSION-1",
            "execution_mode": "DEVELOPMENT", "effect_profile": "DEVELOPMENT-TEST",
            "authority_snapshot": {"authority_snapshot_digest": "a" * 64},
            "receipts": {"dispatch": dispatch, "provider_selection": {
                "transaction_id": "ZEUS-EXECUTION-1", "provider_id": "provider-1", "agent_id": "agent-1",
            }},
        }

    def test_missing_adapter_fails_closed_and_replays(self):
        with tempfile.TemporaryDirectory() as temp:
            controller = AutonomousDispatchController(LaunchStore(Path(temp)))
            first = controller.reconcile(self.authoritative())
            second = controller.reconcile(self.authoritative())
            self.assertEqual(first["state"], "LAUNCH_BLOCKED")
            self.assertEqual(first["blockers"], ["PROVIDER_LAUNCH_ADAPTER_UNAVAILABLE"])
            self.assertEqual(second["launch_id"], first["launch_id"])
            self.assertFalse(second["replay"])

    def test_launch_ack_session_and_replay_are_idempotent(self):
        with tempfile.TemporaryDirectory() as temp:
            controller = AutonomousDispatchController(LaunchStore(Path(temp)))
            calls = []

            def launcher(request):
                calls.append(request["attempt"])
                return {"acknowledged": True, "process_id": 101, "process_group_id": 101,
                        "health_digest": "h" * 64}

            def session(binding):
                return {"session_id": "SESSION-1", "execution_id": binding["transaction_id"]}

            first = controller.reconcile(self.authoritative(), provider_launcher=launcher,
                                         session_materializer=session)
            second = controller.reconcile(self.authoritative(), provider_launcher=launcher,
                                          session_materializer=session)
            self.assertEqual(first["state"], "EXECUTING")
            self.assertEqual(first["session_id"], "SESSION-1")
            self.assertEqual(second["state"], "EXECUTING")
            self.assertTrue(second["replay"])
            self.assertEqual(calls, [1])

    def test_retry_exhaustion_and_session_failure_cleanup(self):
        with tempfile.TemporaryDirectory() as temp:
            controller = AutonomousDispatchController(LaunchStore(Path(temp)), max_retries=1)
            calls = []

            def failing(_request):
                calls.append(1)
                raise RuntimeError("provider unavailable")

            failed = controller.reconcile(self.authoritative(), provider_launcher=failing)
            self.assertEqual(failed["state"], "LAUNCH_FAILED")
            self.assertEqual(len(calls), 2)

            cleaned = []
            recovered = controller.reconcile(
                {**self.authoritative(), "instance_id": "ZEUS-EXECUTION-2",
                 "receipts": {"dispatch": {**self.authoritative()["receipts"]["dispatch"], "instance_id": "ZEUS-EXECUTION-2"},
                               "provider_selection": {**self.authoritative()["receipts"]["provider_selection"], "transaction_id": "ZEUS-EXECUTION-2"}}},
                provider_launcher=lambda _request: {"acknowledged": True, "process_id": 2,
                                                      "process_group_id": 2, "health_digest": "h" * 64},
                session_materializer=lambda _binding: (_ for _ in ()).throw(RuntimeError("session unavailable")),
                cleanup=lambda value: cleaned.append(value["process_id"]),
            )
            self.assertEqual(recovered["state"], "ROLLBACK_REQUIRED")
            self.assertEqual(cleaned, [2])


if __name__ == "__main__":
    unittest.main()
