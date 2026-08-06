#!/usr/bin/env python3
"""Focused P5-G5 qualification execution-start tests."""

from __future__ import annotations

import json
import os
import subprocess
import unittest
from pathlib import Path

from scripts.lib.emp import execution_start
from scripts.lib.emp.publication_workflow import AUTHORIZED_CANDIDATE_PATHS, _projection_schema, _scope

ROOT = Path(__file__).resolve().parents[2]
MISSION = "MISSION-BETA-562F443E16C69401"
INVOCATION = "PROVIDER-INVOCATION-a02accc6-3ff0-50d2-a4b2-266ca5b51ff6"


def zeus(*args: str) -> dict:
    result = subprocess.run([str(ROOT / "scripts/zeus"), *args, "--json"], cwd=ROOT,
                            capture_output=True, text=True,
                            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}, check=False)
    value = json.loads(result.stdout)
    value["_returncode"] = result.returncode
    return value


class ExecutionStartFoundationTests(unittest.TestCase):
    def test_terminal_state_is_bounded_and_provider_bound(self):
        value = execution_start.verify(ROOT, MISSION)
        self.assertEqual(value["result"], "PASS")
        self.assertEqual(value["execution_start_state"], "READY_FOR_CONTROLLED_EXECUTION")
        self.assertTrue(value["execution_start_authorized"])
        self.assertTrue(value["execution_session_created"])
        self.assertTrue(value["execution_started"])
        self.assertTrue(value["provider_process_bound"])
        self.assertEqual(value["provider_invocation_id"], INVOCATION)
        self.assertEqual(value["execution_adapter_mode"], "QUALIFICATION_ADAPTER")
        self.assertFalse(value["mission_work_started"])
        self.assertFalse(value["repository_work_started"])
        self.assertFalse(value["execution_monitoring_active"])
        self.assertFalse(value["completion_reported"])
        self.assertEqual(value["next_authorized_action"], "BEGIN_CONTROLLED_MISSION_WORK")

    def test_identity_and_replay_are_stable(self):
        first = execution_start.verify(ROOT, MISSION)
        second = execution_start.verify(ROOT, MISSION)
        self.assertEqual(first, second)
        self.assertEqual(first["execution_start_replay"], "IDEMPOTENT")
        self.assertEqual(first["execution_id"], "EXECUTION-START-5a6fec74-3c4b-5271-8c96-4cc89fe8855e")
        self.assertEqual(len(first["artifacts"]), 8)

    def test_cli_surfaces_and_projection_schema(self):
        status = zeus("execution-start", "status", MISSION)
        session = zeus("execution-start", "session", MISSION)
        self.assertEqual(status["_returncode"], 0)
        self.assertEqual(session["_returncode"], 0)
        self.assertEqual(status["execution_start_state"], "READY_FOR_CONTROLLED_EXECUTION")
        self.assertEqual(session["execution_session_created"], True)
        schema = _projection_schema(ROOT, MISSION)
        self.assertEqual(schema["result"], "PASS", schema)
        self.assertEqual(schema["commands"]["execution_start"]["result"], "PASS")

    def test_read_only_verification_does_not_change_repository(self):
        before = subprocess.run(["git", "-C", str(ROOT), "status", "--porcelain"], capture_output=True, text=True, check=False).stdout
        value = execution_start.verify(ROOT, MISSION)
        after = subprocess.run(["git", "-C", str(ROOT), "status", "--porcelain"], capture_output=True, text=True, check=False).stdout
        self.assertEqual(value["result"], "PASS")
        self.assertEqual(before, after)

    def test_p5_g5_candidate_scope_converges_and_is_authorized(self):
        expected = sorted(set(
            subprocess.run(["git", "diff", "--name-only"], cwd=ROOT, capture_output=True,
                           text=True, check=True).stdout.splitlines()
            + subprocess.run(["git", "ls-files", "--others", "--exclude-standard"], cwd=ROOT,
                              capture_output=True, text=True, check=True).stdout.splitlines()
        ))
        scope = _scope(ROOT)
        self.assertEqual(scope["result"], "PASS", scope)
        self.assertTrue(scope["authorized"])
        self.assertEqual(scope["unauthorized_paths"], [])
        self.assertEqual(sorted(scope["paths"]), expected)
        self.assertIn(
            "engineering/evidence/operation-beta/p5-g5-execution-start-foundation-completion-report.md",
            AUTHORIZED_CANDIDATE_PATHS,
        )

    def test_scope_authorization_remains_fail_closed_for_unrelated_paths(self):
        unrelated = {
            "engineering/evidence/operation-beta/unrelated.md",
            "scripts/lib/emp/unrelated_lifecycle.py",
            "engineering/mission-output/result.json",
        }
        self.assertEqual(unrelated & AUTHORIZED_CANDIDATE_PATHS, set())


if __name__ == "__main__":
    unittest.main()
