#!/usr/bin/env python3
"""Mission-admission status count reconstruction and corruption tests."""

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

from scripts.lib.emp.stage1_runtime import (
    MISSION_STATES,
    Stage1Error,
    Stage1Runtime,
    Stage1Store,
    _digest,
)


class MissionCountStatusTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.directory = Path(self.temporary.name) / "stage1"
        self.store = Stage1Store(self.directory)

    def tearDown(self):
        self.temporary.cleanup()

    @staticmethod
    def record(state: str, number: int) -> dict:
        return {
            "instance_id": f"INSTANCE-{number}",
            "mission_id": f"MISSION-{number}",
            "wop_id": f"WOP-{number}",
            "state": state,
        }

    def runtime(self) -> Stage1Runtime:
        return Stage1Runtime(ROOT, self.directory)

    def test_counts_are_derived_from_each_persisted_supported_state(self):
        for number, state in enumerate(MISSION_STATES, 1):
            self.store.save(self.record(state, number))
        status = self.runtime().status()
        self.assertEqual(1, status["schema_version"])
        self.assertEqual(4, status["mission_count"])
        self.assertEqual(
            {state: 1 for state in MISSION_STATES}, status["states"]
        )
        self.assertEqual(status["mission_count"], sum(status["states"].values()))

    def test_restart_reconstructs_identical_counts(self):
        self.store.save(self.record("STAGED", 1))
        self.store.save(self.record("REJECTED", 2))
        first = self.runtime().status()
        restarted = Stage1Runtime(ROOT, self.directory).status()
        self.assertEqual(first, restarted)

    def test_empty_store_reports_zero_deterministically(self):
        expected = {
            "schema_version": 1,
            "mission_count": 0,
            "states": {state: 0 for state in MISSION_STATES},
        }
        self.assertEqual(expected, self.runtime().status())
        self.assertEqual(expected, Stage1Runtime(ROOT, self.directory).status())

    def test_digest_corruption_fails_closed(self):
        saved = self.store.save(self.record("STAGED", 1))
        path = self.directory / "missions" / f"{saved['instance_id']}.json"
        value = json.loads(path.read_text())
        value["state"] = "REJECTED"
        path.write_text(json.dumps(value))
        with self.assertRaisesRegex(Stage1Error, "digest mismatch"):
            self.runtime().status()

    def test_integrity_valid_unknown_state_fails_closed(self):
        value = self.record("UNKNOWN", 1)
        value["state_digest"] = _digest(value)
        path = self.directory / "missions/INSTANCE-1.json"
        path.parent.mkdir(parents=True)
        path.write_text(json.dumps(value))
        with self.assertRaisesRegex(Stage1Error, "lifecycle value invalid"):
            self.runtime().status()

    def test_integrity_valid_instance_path_mismatch_fails_closed(self):
        value = self.record("STAGED", 1)
        value["state_digest"] = _digest(value)
        path = self.directory / "missions/DIFFERENT.json"
        path.parent.mkdir(parents=True)
        path.write_text(json.dumps(value))
        with self.assertRaisesRegex(Stage1Error, "instance/path mismatch"):
            self.runtime().status()

    def test_cli_status_fails_closed_on_corrupt_override_store(self):
        value = self.record("UNKNOWN", 1)
        value["state_digest"] = _digest(value)
        path = self.directory / "missions/INSTANCE-1.json"
        path.parent.mkdir(parents=True)
        path.write_text(json.dumps(value))
        environment = dict(os.environ)
        environment["ZEUS_STAGE1_STATE"] = str(self.directory)
        result = subprocess.run(
            [str(ROOT / "scripts/zeus"), "status", "--json"],
            cwd=ROOT,
            env=environment,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(78, result.returncode)
        self.assertIn("runtime state lifecycle value invalid", result.stderr)


if __name__ == "__main__":
    unittest.main()
