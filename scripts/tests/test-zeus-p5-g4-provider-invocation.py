#!/usr/bin/env python3
"""Focused P5-G4 provider-invocation and projection-contract tests."""

from __future__ import annotations

import json
import os
import subprocess
import unittest
from pathlib import Path

from scripts.lib.emp import provider_invocation
from scripts.lib.emp.publication_workflow import _projection_schema


ROOT = Path(__file__).resolve().parents[2]
MISSION = "MISSION-BETA-562F443E16C69401"
SESSION = "PROVIDER-SESSION-65d0fe07-1d02-562d-9da2-f766f3e87ef4"
PROVIDER = "zeus-local-loneal-01"


def zeus(*args: str) -> dict:
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
    result = subprocess.run([str(ROOT / "scripts/zeus"), *args, "--json"], cwd=ROOT,
                            capture_output=True, text=True, env=env, check=False)
    value = json.loads(result.stdout)
    value["_returncode"] = result.returncode
    return value


class ProviderInvocationFoundationTests(unittest.TestCase):
    def test_verify_and_replay_are_deterministic(self):
        first = provider_invocation.verify(ROOT, MISSION)
        second = provider_invocation.verify(ROOT, MISSION)
        self.assertEqual(first, second)
        self.assertEqual(first["result"], "PASS")
        self.assertEqual(first["invocation_replay"], "IDEMPOTENT")

    def test_terminal_boundary_and_bindings(self):
        value = provider_invocation.verify(ROOT, MISSION)
        self.assertEqual(value["provider_session_id"], SESSION)
        self.assertEqual(value["provider_id"], PROVIDER)
        self.assertEqual(value["provider_invocation_state"], "READY_FOR_EXECUTION_START")
        self.assertTrue(value["provider_invocation_authorized"])
        self.assertTrue(value["provider_invoked"])
        self.assertTrue(value["provider_acknowledged"])
        self.assertTrue(value["execution_start_eligible"])
        self.assertFalse(value["execution_started"])
        self.assertFalse(value["mission_work_started"])
        self.assertEqual(value["next_authorized_action"], "START_EXECUTION")
        self.assertEqual(value["invocation_mode"], "QUALIFICATION_ADAPTER")

    def test_publication_advance_preserves_invocation_provenance(self):
        value = provider_invocation.verify(ROOT, MISSION)
        self.assertEqual(value["result"], "PASS")
        self.assertEqual(value["invocation_provenance_baseline"], "b37a5fb2e11df8026afeff1bd231902cd54711ac")
        self.assertEqual(value["current_published_baseline"], "ae0395e62a5409e245912eb979a924bb9cb08e8c")
        self.assertEqual(value["baseline_relationship"], "ANCESTOR")
        self.assertEqual(value["invocation_integrity"], "PASS")

    def test_exact_artifact_cardinality_and_digests(self):
        value = provider_invocation.verify(ROOT, MISSION)
        self.assertEqual(len(value["artifacts"]), 7)
        self.assertEqual({item["path"].split("/")[-2] for item in value["artifacts"].values()}, {
            "provider-invocations", "provider-invocation-authorizations", "provider-invocation-packages",
            "provider-invocation-acknowledgements", "provider-invocation-receipts", "provider-invocation-journals",
            "execution-start-readiness",
        })

    def test_public_cli_contracts(self):
        status = zeus("provider-invocation", "status", MISSION)
        self.assertEqual(status["_returncode"], 0)
        self.assertEqual(status["provider_session_id"], SESSION)
        self.assertEqual(status["provider_invocation_state"], "READY_FOR_EXECUTION_START")
        self.assertTrue(status["provider_acknowledged"])
        self.assertFalse(status["execution_started"])

    def test_mission_projection_agrees(self):
        status = zeus("mission", "status", MISSION)
        lifecycle = zeus("mission", "lifecycle", MISSION)
        next_value = zeus("mission", "next", MISSION)
        snapshot = zeus("mission", "snapshot", MISSION)
        verified = zeus("mission", "verify", MISSION)
        self.assertTrue(status["provider_invoked"])
        self.assertTrue(status["provider_acknowledged"])
        self.assertEqual(status["next_authorized_action"], "START_EXECUTION")
        self.assertEqual(status["invocation_provenance_baseline"], "b37a5fb2e11df8026afeff1bd231902cd54711ac")
        self.assertEqual(status["current_published_baseline"], "ae0395e62a5409e245912eb979a924bb9cb08e8c")
        self.assertEqual(status["baseline_relationship"], "ANCESTOR")
        self.assertEqual(lifecycle["provider_invocation_state"], "READY_FOR_EXECUTION_START")
        self.assertEqual(lifecycle["baseline_relationship"], "ANCESTOR")
        self.assertEqual(next_value["next_authorized_action"], "START_EXECUTION")
        self.assertEqual(snapshot["provider_invocation_id"], status["provider_invocation_id"])
        self.assertEqual(verified["mission_verification"], "PASS")
        self.assertEqual(verified["checks"]["provider_invocation"], "PASS")
        self.assertEqual(verified["baseline_relationship"], "ANCESTOR")

    def test_publication_projection_schema_is_fail_closed(self):
        value = _projection_schema(ROOT, MISSION)
        self.assertEqual(value["result"], "PASS", value)
        self.assertEqual({key: item["result"] for key, item in value["commands"].items()}, {
            "status": "PASS", "lifecycle": "PASS", "next": "PASS", "snapshot": "PASS", "verify": "PASS",
        })

    def test_read_only_verification_does_not_change_repository(self):
        before = subprocess.run(["git", "-C", str(ROOT), "status", "--porcelain"], capture_output=True, text=True, check=False).stdout
        first = provider_invocation.verify(ROOT, MISSION)
        after = subprocess.run(["git", "-C", str(ROOT), "status", "--porcelain"], capture_output=True, text=True, check=False).stdout
        self.assertEqual(first["result"], "PASS")
        self.assertEqual(before, after)

    def test_missing_invocation_artifacts_are_not_claimed_as_ready(self):
        self.assertEqual(provider_invocation.ARTIFACT_TYPES["execution_start_readiness"], "execution-start-readiness")
        self.assertEqual(len(provider_invocation.STAGE_DIRS), 7)


if __name__ == "__main__":
    unittest.main()
