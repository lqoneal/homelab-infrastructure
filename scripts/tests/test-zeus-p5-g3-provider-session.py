"""Focused P5-G3 provider-session foundation tests."""

from __future__ import annotations

import hashlib
import json
import subprocess
import unittest
from pathlib import Path

from scripts.lib.emp.provider_session import STAGE_DIRS, _found, _verify_set, ProviderSessionError


ROOT = Path(__file__).resolve().parents[2]
MISSION = "MISSION-BETA-562F443E16C69401"
RUNTIME = Path("/home/loneal/.local/state/zeus-runtime/homelab-6bd83f9079d6fc57")


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


class P5G3ProviderSessionTests(unittest.TestCase):
    def test_create_verify_replay_and_boundary(self) -> None:
        first = run("provider-session", "create", MISSION)
        second = run("provider-session", "verify", MISSION)
        replay = run("provider-session", "create", MISSION)
        self.assertEqual(first["result"], "PASS")
        self.assertEqual(second["result"], "PASS")
        self.assertEqual(replay["duplicate_session"], "IDEMPOTENT")
        self.assertEqual(first["session_state"], "READY_FOR_PROVIDER_INVOCATION")
        self.assertEqual(len(first["artifacts"]), 5)
        self.assertFalse(first["provider_invoked"])
        self.assertFalse(first["execution_started"])
        self.assertEqual(first["next_authorized_action"], "INVOKE_PROVIDER")

    def test_read_only_verify_does_not_change_runtime(self) -> None:
        before = lifecycle_artifact_snapshot()
        value = run("provider-session", "verify", MISSION)
        after = lifecycle_artifact_snapshot()
        self.assertEqual(value["result"], "PASS")
        self.assertTrue(value["read_only"])
        self.assertEqual(before, after)

    def test_tamper_fails_closed(self) -> None:
        found = _found(RUNTIME, MISSION)
        target = found["provider_session_receipt"][0][0]
        value = json.loads(target.read_text())
        value["result"] = "FORGED"
        try:
            target.write_text(json.dumps(value))
            with self.assertRaises(ProviderSessionError) as error:
                _verify_set(RUNTIME, _found(RUNTIME, MISSION))
            self.assertEqual(error.exception.code, "PROVIDER_SESSION_DIGEST_MISMATCH")
        finally:
            target.write_text(json.dumps(found["provider_session_receipt"][0][1], indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    unittest.main()
