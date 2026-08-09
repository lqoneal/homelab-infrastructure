"""Focused P5-G2 dispatch-boundary qualification tests."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts.lib.emp.dispatch_foundation import DispatchFoundationError, STAGE_DIRS, _found, _verify_set


ROOT = Path(__file__).resolve().parents[2]
MISSION = "MISSION-BETA-562F443E16C69401"
RUNTIME = Path("/home/loneal/.local/state/zeus-runtime/homelab-6bd83f9079d6fc57")


def mission_artifact(directory: Path, mission_id: str) -> Path:
    for path in sorted(directory.glob("DISPATCH-*.json")):
        if json.loads(path.read_text()).get("mission_id") == mission_id:
            return path
    raise AssertionError(f"no dispatch artifact for {mission_id} in {directory}")


def lifecycle_artifact_snapshot() -> dict[str, str]:
    """Ignore unrelated Codex transcript SQLite activity in the shared runtime."""
    snapshot: dict[str, str] = {}
    for stage in STAGE_DIRS.values():
        for path in sorted((RUNTIME / stage).glob("*.json")):
            snapshot[str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
    return snapshot


def run(*args: str) -> dict:
    result = subprocess.run([str(ROOT / "scripts/zeus"), *args, "--json"], cwd=ROOT, text=True, capture_output=True, check=True)
    return json.loads(result.stdout)


class P5G2DispatchTests(unittest.TestCase):
    def test_dispatch_and_replay_are_deterministic(self) -> None:
        first = run("dispatch", "verify", MISSION)
        second = run("dispatch", "create", MISSION)
        self.assertEqual(first["result"], "PASS")
        self.assertEqual(second["result"], "PASS")
        self.assertEqual(second["dispatch_id"], "DISPATCH-6ab02bcc-6402-51c9-a9cf-12b8746a0873")
        self.assertEqual(second["duplicate_dispatch"], "IDEMPOTENT")
        self.assertEqual(second["next_authorized_action"], "ESTABLISH_PROVIDER_SESSION")
        self.assertEqual(second["mission_id"], MISSION)
        self.assertFalse(second["provider_invoked"])
        self.assertFalse(second["provider_session_created"])
        self.assertFalse(second["execution_started"])

    def test_exact_artifact_cardinality_and_read_only_verify(self) -> None:
        before = lifecycle_artifact_snapshot()
        value = run("dispatch", "verify", MISSION)
        after = lifecycle_artifact_snapshot()
        self.assertEqual(value["result"], "PASS")
        self.assertTrue(value["read_only"])
        self.assertEqual(len(value["artifacts"]), 6)
        self.assertEqual(before, after)

    def test_forged_partial_state_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            for key, stage in STAGE_DIRS.items():
                source = mission_artifact(RUNTIME / stage, MISSION)
                destination = runtime / stage / source.name
                destination.parent.mkdir(parents=True)
                shutil.copy2(source, destination)
            forged = runtime / STAGE_DIRS["dispatch_receipt"] / mission_artifact(RUNTIME / STAGE_DIRS["dispatch_receipt"], MISSION).name
            value = json.loads(forged.read_text())
            value["result"] = "FORGED"
            forged.write_text(json.dumps(value))
            with self.assertRaises(DispatchFoundationError) as error:
                _verify_set(runtime, _found(runtime, MISSION))
            self.assertEqual(error.exception.code, "DISPATCH_DIGEST_MISMATCH")


if __name__ == "__main__":
    unittest.main()
