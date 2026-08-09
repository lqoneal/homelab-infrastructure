#!/usr/bin/env python3
"""Focused proof of identity-preserving Zeus submit canonicalization."""

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

from scripts.lib.emp.wop_canonicalization import CanonicalizationError, canonicalize, classify  # noqa: E402


SOURCE = ROOT / "engineering/work-orders/WOP-ZEUS-EXECUTION-LIFECYCLE-COMPLETION-001/source-wop.md"
EXPECTED_DIGEST = "460a4baeca153b05ee2cb0ade4a70a03b8ff2b8ca9e17a9074d0e44137d392d9"
WOP_ID = "WOP-ZEUS-EXECUTION-LIFECYCLE-COMPLETION-001"
MISSION_ID = "ZEUS-EXECUTION-LIFECYCLE-COMPLETION-01"


class AutomaticCanonicalizationTests(unittest.TestCase):
    def copy_source(self, directory: Path) -> Path:
        source = directory / "source-wop.md"
        shutil.copy2(SOURCE, source)
        return source

    def invoke(self, runtime: Path, *args: str) -> subprocess.CompletedProcess[str]:
        environment = {**os.environ, "ZEUS_RUNTIME_ROOT": str(runtime), "ZEUS_NO_INTRO": "1", "PYTHONDONTWRITEBYTECODE": "1"}
        return subprocess.run([sys.executable, str(ROOT / "scripts/zeus"), *args], cwd=ROOT, env=environment, text=True, capture_output=True, check=False)

    def test_first_canonicalization_preserves_source_and_identity(self) -> None:
        with tempfile.TemporaryDirectory(prefix="zeus-canonicalize-") as name:
            directory = Path(name)
            source = self.copy_source(directory)
            before = source.read_bytes()
            first = canonicalize(source, ROOT)
            second = canonicalize(source, ROOT)
            trace = json.loads((source.with_suffix(".md.traceability.json")).read_text(encoding="utf-8"))
            self.assertEqual(hashlib.sha256(before).hexdigest(), EXPECTED_DIGEST)
            self.assertEqual(source.read_bytes(), before)
            self.assertEqual(first["classification"], "DEVELOPMENT_SOURCE_PROMOTABLE")
            self.assertFalse(first["replayed"])
            self.assertTrue(second["replayed"])
            self.assertEqual(trace["wop_id"], WOP_ID)
            self.assertEqual(trace["mission_id"], MISSION_ID)
            self.assertEqual(trace["source"]["digest"], EXPECTED_DIGEST)
            self.assertEqual(trace["output_digest"], EXPECTED_DIGEST)
            self.assertTrue(trace["canonicalization"]["source_bytes_preserved"])

    def test_conflicting_and_changed_provenance_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory(prefix="zeus-canonicalize-invalid-") as name:
            directory = Path(name)
            source = self.copy_source(directory)
            canonicalize(source, ROOT)
            sidecar = source.with_suffix(".md.traceability.json")
            value = json.loads(sidecar.read_text(encoding="utf-8"))
            value["mission_id"] = "CONFLICTING-MISSION-01"
            sidecar.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            with self.assertRaises(CanonicalizationError):
                canonicalize(source, ROOT)
            sidecar.unlink()
            canonicalize(source, ROOT)
            source.write_bytes(source.read_bytes() + b"\nchanged")
            with self.assertRaises(CanonicalizationError):
                canonicalize(source, ROOT)

    def test_cli_routes_repository_options_to_p2_and_replay_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory(prefix="zeus-canonicalize-cli-") as name:
            directory = Path(name)
            runtime = directory / "runtime"
            source = self.copy_source(directory)
            first = self.invoke(runtime, "submit", str(source), "--repository", str(ROOT), "--baseline", "32796dffb43a47f4f9516a0936fe89f0bec0ee80", "--impact", "bounded", "--affected-repository", str(ROOT), "--resources-available", "--json")
            self.assertEqual(first.returncode, 0, first.stderr)
            first_value = json.loads(first.stdout)
            replay = self.invoke(runtime, "submit", str(source), "--json")
            self.assertEqual(replay.returncode, 0, replay.stderr)
            replay_value = json.loads(replay.stdout)
            self.assertEqual(first_value["submission_state"], "ADMISSION_REQUESTED")
            self.assertEqual(first_value["next_action"], "EVALUATE_MISSION_ADMISSION")
            self.assertEqual(first_value["canonicalization"], "PASS")
            self.assertEqual(first_value["authored_provenance"], "DERIVED")
            self.assertEqual(first_value["wop_id"], WOP_ID)
            self.assertEqual(first_value["mission_id"], MISSION_ID)
            self.assertTrue(first_value["wop_source_unchanged"])
            self.assertEqual(replay_value["duplicate_submission"], "IDEMPOTENT")
            self.assertEqual(replay_value["submission_id"], first_value["submission_id"])
            self.assertEqual(len(list((runtime / "submissions/receipts").glob("*.json"))), 1)
            self.assertEqual(len(list((runtime / "submissions/requests").glob("*.json"))), 1)
            self.assertFalse(list((runtime / "mission-admissions").glob("*.json")))

    def test_generic_approval_cannot_select_legacy_for_current_source(self) -> None:
        with tempfile.TemporaryDirectory(prefix="zeus-canonicalize-approval-") as name:
            directory = Path(name)
            runtime = directory / "runtime"
            source = self.copy_source(directory)
            result = self.invoke(runtime, "submit", str(source), "--repository", str(ROOT), "--approval", "operator", "--json")
            self.assertEqual(result.returncode, 78)
            self.assertIn("generic --approval", result.stderr)
            self.assertFalse(source.with_suffix(".md.traceability.json").exists())

    def test_explicit_package_directory_is_legacy_class(self) -> None:
        with tempfile.TemporaryDirectory(prefix="zeus-classify-") as name:
            directory = Path(name)
            package = directory / "legacy-package"
            package.mkdir()
            self.assertEqual(classify(package, ROOT)["classification"], "LEGACY_SUPPORTED")

    def test_native_p2_mission_views_are_read_only_and_consistent(self) -> None:
        with tempfile.TemporaryDirectory(prefix="zeus-native-p2-") as name:
            directory = Path(name)
            runtime = directory / "runtime"
            source = self.copy_source(directory)
            result = self.invoke(runtime, "submit", str(source), "--json")
            self.assertEqual(result.returncode, 0, result.stderr)
            for action in ("show", "state", "authority", "blockers", "next", "snapshot"):
                value = self.invoke(runtime, "mission", action, MISSION_ID, "--json")
                self.assertEqual(value.returncode, 0, value.stderr)
                projection = json.loads(value.stdout)
                self.assertEqual(projection["mission_id"], MISSION_ID)
                self.assertEqual(projection["wop_id"], WOP_ID) if "wop_id" in projection else None
            snapshot = json.loads(self.invoke(runtime, "mission", "snapshot", MISSION_ID, "--json").stdout)
            self.assertEqual(snapshot["lifecycle_state"], "ADMISSION_REQUESTED")
            self.assertEqual(snapshot["authority"]["wop_authority"], "operator-submitted WOP")
            self.assertFalse(snapshot["authority"]["generic_second_approval_required"])
            self.assertEqual(snapshot["next_authorized_action"], "EVALUATE_MISSION_ADMISSION")


if __name__ == "__main__":
    unittest.main()
