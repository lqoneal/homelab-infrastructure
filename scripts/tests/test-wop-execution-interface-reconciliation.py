#!/usr/bin/env python3
"""Qualification for canonical WOP compatibility and active execution lookup."""

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
EXECUTION = ROOT / ".zeus/runtime/mission-executions/MISSION-EXECUTION-8c444488-9ee3-5e03-949f-dc750a0b918c.json"


class WopExecutionInterfaceTests(unittest.TestCase):
    def test_status_resolves_the_single_active_execution(self):
        with tempfile.TemporaryDirectory() as directory:
            store = Path(directory)
            shutil.copy2(EXECUTION, store / EXECUTION.name)
            env = os.environ.copy()
            env.update({"ZEUS_TESTING": "1", "ZEUS_EXECUTION_STORE": str(store),
                        "ZEUS_OPERATOR_STATE": str(store / "operator-state.json")})
            result = subprocess.run(
                [str(ROOT / "scripts/zeus"), "execute-mission", "status"],
                cwd=ROOT, env=env, capture_output=True, text=True, check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)["execution_id"], EXECUTION.stem)

    def test_status_requires_an_id_when_active_execution_is_ambiguous(self):
        with tempfile.TemporaryDirectory() as directory:
            store = Path(directory)
            for suffix in ("a", "b"):
                state = json.loads(EXECUTION.read_text(encoding="utf-8"))
                state["execution_id"] = f"MISSION-EXECUTION-{suffix}"
                # The fixture is intentionally used only to test selection; the
                # state digest is recomputed by the runtime's canonical rules.
                from scripts.lib.emp.authority_resolution import digest
                material = dict(state)
                material.pop("state_digest", None)
                state["state_digest"] = digest(material)
                (store / f"{state['execution_id']}.json").write_text(
                    json.dumps(state), encoding="utf-8"
                )
            env = os.environ.copy()
            env.update({"ZEUS_TESTING": "1", "ZEUS_EXECUTION_STORE": str(store),
                        "ZEUS_OPERATOR_STATE": str(store / "operator-state.json")})
            result = subprocess.run(
                [str(ROOT / "scripts/zeus"), "execute-mission", "status"],
                cwd=ROOT, env=env, capture_output=True, text=True, check=False,
            )
            self.assertEqual(result.returncode, 78)
            self.assertIn("multiple active executions", result.stderr)


if __name__ == "__main__":
    unittest.main()
