#!/usr/bin/env python3
"""Mission P0 Zeus operational bootstrap qualification tests."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.lib.emp.orchestration import (  # noqa: E402
    MissionOrchestrator,
    OrchestrationError,
    OrchestrationStore,
    empty_orchestration_state,
)
from scripts.lib.emp.operational_runtime import (  # noqa: E402
    RUNTIME_RELATIVE_PATH,
    authoritative_state_path,
)


class OperationalBootstrapTests(unittest.TestCase):
    def test_authoritative_location_is_repository_fixed(self):
        self.assertEqual(authoritative_state_path(ROOT), ROOT / RUNTIME_RELATIVE_PATH)

    def test_canonical_initial_state_round_trips(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "state.json"
            store = OrchestrationStore(path)
            store.save(empty_orchestration_state())
            first = MissionOrchestrator(store).data
            second = MissionOrchestrator(OrchestrationStore(path)).data
            self.assertEqual(first, second)

    def test_incompatible_schema_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "state.json"
            value = empty_orchestration_state()
            value["schema_version"] = 2
            path.write_text(json.dumps(value))
            with self.assertRaisesRegex(OrchestrationError, "incompatible"):
                MissionOrchestrator(OrchestrationStore(path))

    def test_corruption_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "state.json"
            path.write_text("{broken")
            with self.assertRaisesRegex(OrchestrationError, "invalid orchestration store"):
                MissionOrchestrator(OrchestrationStore(path))

    def test_structurally_corrupted_mission_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "state.json"
            value = empty_orchestration_state()
            value["missions"]["MISSION-A"] = {"mission_id": "MISSION-A"}
            path.write_text(json.dumps(value))
            with self.assertRaisesRegex(OrchestrationError, "invalid mission"):
                MissionOrchestrator(OrchestrationStore(path))

    def test_cli_override_remains_an_engineering_workflow(self):
        with tempfile.TemporaryDirectory() as temporary:
            state = Path(temporary) / "state.json"
            OrchestrationStore(state).save(empty_orchestration_state())
            result = subprocess.run(
                [str(ROOT / "scripts/zeus"), "--state", str(state), "status"],
                capture_output=True,
                text=True,
                env={**os.environ, "ZEUS_STATE": str(Path(temporary) / "ignored.json")},
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)["staged_missions"], [])

    def test_missing_override_remains_compatible_for_isolated_guidance(self):
        with tempfile.TemporaryDirectory() as temporary:
            result = subprocess.run(
                [
                    str(ROOT / "scripts/zeus"),
                    "--state",
                    str(Path(temporary) / "missing.json"),
                    "show",
                    "wop-template",
                ],
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse((Path(temporary) / "missing.json").exists())


if __name__ == "__main__":
    unittest.main()
