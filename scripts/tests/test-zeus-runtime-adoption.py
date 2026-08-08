#!/usr/bin/env python3
"""Focused proof of durable canonical P2 runtime adoption."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

SOURCE = ROOT / "engineering/work-orders/WOP-ZEUS-EXECUTION-LIFECYCLE-COMPLETION-001/source-wop.md"
EXPECTED_SOURCE_DIGEST = "460a4baeca153b05ee2cb0ade4a70a03b8ff2b8ca9e17a9074d0e44137d392d9"
MISSION = "ZEUS-EXECUTION-LIFECYCLE-COMPLETION-01"
WOP = "WOP-ZEUS-EXECUTION-LIFECYCLE-COMPLETION-001"


class RuntimeAdoptionTests(unittest.TestCase):
    def invoke(self, home: Path, *args: str, runtime: Path | None = None) -> subprocess.CompletedProcess[str]:
        environment = {**os.environ, "HOME": str(home), "ZEUS_NO_INTRO": "1", "PYTHONDONTWRITEBYTECODE": "1"}
        if runtime is not None:
            environment["ZEUS_RUNTIME_ROOT"] = str(runtime)
        else:
            environment.pop("ZEUS_RUNTIME_ROOT", None)
        return subprocess.run(
            [sys.executable, str(ROOT / "scripts/zeus"), *args],
            cwd=ROOT, env=environment, text=True, capture_output=True, check=False,
        )

    def create_transaction(self, directory: Path) -> Path:
        source = directory / "source-wop.md"
        shutil.copy2(SOURCE, source)
        runtime = directory / "transaction-runtime"
        result = self.invoke(directory / "home", "submit", str(source), "--repository", str(ROOT),
                             "--baseline", "32796dffb43a47f4f9516a0936fe89f0bec0ee80",
                             "--impact", "bounded", "--affected-repository", str(ROOT),
                             "--resources-available", "--json", runtime=runtime)
        self.assertEqual(result.returncode, 0, result.stderr)
        value = json.loads(result.stdout)
        self.assertEqual(value["mission_id"], MISSION)
        self.assertEqual(value["wop_id"], WOP)
        self.assertEqual(value["source_digest"], EXPECTED_SOURCE_DIGEST)
        return runtime

    @staticmethod
    def destination(home: Path) -> Path:
        return home / ".local" / "state" / "zeus-runtime" / "homelab-6bd83f9079d6fc57"

    def test_adoption_is_durable_identity_bound_and_replay_safe(self) -> None:
        with tempfile.TemporaryDirectory(prefix="zeus-runtime-adoption-") as name:
            directory = Path(name)
            home = directory / "home"
            transaction = self.create_transaction(directory)
            first = self.invoke(home, "runtime", "adopt", "--source", str(transaction), "--json")
            self.assertEqual(first.returncode, 0, first.stderr)
            first_value = json.loads(first.stdout)
            self.assertEqual(first_value["result"], "PASS")
            self.assertEqual(first_value["action"], "ADOPTED_CANONICAL_SUBMISSION")
            durable = self.destination(home)
            receipt = next((durable / "submissions/receipts").glob("*.json"))
            self.assertEqual(json.loads(receipt.read_text())["mission_id"], MISSION)
            self.assertEqual(json.loads(receipt.read_text())["wop_id"], WOP)
            self.assertEqual(json.loads(receipt.read_text())["source_digest"], EXPECTED_SOURCE_DIGEST)
            self.assertTrue((durable / "canonical-submission-adoption.json").is_file())

            replay = self.invoke(home, "runtime", "adopt", "--source", str(transaction), "--json")
            self.assertEqual(replay.returncode, 0, replay.stderr)
            replay_value = json.loads(replay.stdout)
            self.assertEqual(replay_value["action"], "ALREADY_ADOPTED")
            self.assertEqual(replay_value["adoption_id"], first_value["adoption_id"])
            self.assertEqual(len(list((durable / "submissions/receipts").glob("*.json"))), 1)

            # An equivalent transaction path has the same content-bound
            # adoption identity and cannot create a second durable receipt.
            equivalent = directory / "equivalent-transaction-runtime"
            shutil.copytree(transaction, equivalent)
            replay_other_path = self.invoke(home, "runtime", "adopt", "--source", str(equivalent), "--json")
            self.assertEqual(replay_other_path.returncode, 0, replay_other_path.stderr)
            self.assertEqual(json.loads(replay_other_path.stdout)["action"], "ALREADY_ADOPTED")

            # Hide the transaction workspace; default runtime discovery still
            # resolves the durable repository-bound state.
            hidden = directory / "transaction-runtime.hidden"
            transaction.rename(hidden)
            listed = self.invoke(home, "mission", "list", "--json")
            shown = self.invoke(home, "mission", "snapshot", MISSION, "--json")
            self.assertEqual(listed.returncode, 0, listed.stderr)
            self.assertEqual(shown.returncode, 0, shown.stderr)
            self.assertIn(MISSION, listed.stdout)
            snapshot = json.loads(shown.stdout)
            self.assertEqual(snapshot["mission_id"], MISSION)
            self.assertEqual(snapshot["wop_id"], WOP)
            self.assertEqual(snapshot["lifecycle_state"], "ADMISSION_REQUESTED")
            self.assertEqual(snapshot["next_authorized_action"], "EVALUATE_MISSION_ADMISSION")
            hidden.rename(transaction)

    def test_foreign_repository_binding_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory(prefix="zeus-runtime-adoption-conflict-") as name:
            directory = Path(name)
            transaction = self.create_transaction(directory)
            marker = transaction / "runtime-identity.json"
            value = json.loads(marker.read_text())
            value["repository_fingerprint"] = "foreign"
            marker.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
            result = self.invoke(directory / "home", "runtime", "adopt", "--source", str(transaction), "--json")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("another repository", result.stderr)

    def test_source_digest_remains_unchanged(self) -> None:
        self.assertEqual(hashlib.sha256(SOURCE.read_bytes()).hexdigest(), EXPECTED_SOURCE_DIGEST)


if __name__ == "__main__":
    unittest.main()
