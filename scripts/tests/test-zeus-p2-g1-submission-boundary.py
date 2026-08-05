#!/usr/bin/env python3
"""Focused P2-G1 canonical submission-boundary tests."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
import sys
sys.path.insert(0, str(ROOT))

from scripts.lib.emp.repository_identity import resolve  # noqa: E402
from scripts.lib.emp.submission_boundary import SubmissionError, submit  # noqa: E402
from scripts.lib.emp.submission_verification import verify_submission_pair  # noqa: E402


class CountingBoundary:
    def __init__(self):
        self.calls = 0

    def invoke(self, request):
        self.calls += 1
        return {"result": "PASS", "invocations": 1, "request_id": request["admission_request_id"]}


class SubmissionBoundaryTests(unittest.TestCase):
    def authored(self, directory: Path, *, operation="BETA", repository=None, readiness="ADMISSION_READY") -> Path:
        source = directory / "mission.yaml"
        source.write_text("mission: P2 test source\n", encoding="utf-8")
        output = directory / "WOP-BETA-P2TEST.md"
        output.write_text("# WOP-BETA-P2TEST\n\nCanonical submission boundary test.\n", encoding="utf-8")
        identity = resolve(ROOT)
        trace = {
            "result": "PASS", "readiness": readiness, "wop_id": "WOP-BETA-P2TEST",
            "mission_id": "MISSION-BETA-P2TEST", "operation": operation,
            "repository": repository or identity,
            "source": {"path": str(source), "digest": hashlib.sha256(source.read_bytes()).hexdigest()},
            "template": {"digest": "a" * 64}, "context": {"digest": "b" * 64},
            "output_digest": hashlib.sha256(output.read_bytes()).hexdigest(),
            "blockers": [],
        }
        output.with_suffix(output.suffix + ".traceability.json").write_text(
            json.dumps(trace, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        return output

    def test_submission_is_deterministic_and_requests_admission_once(self):
        with tempfile.TemporaryDirectory(prefix="zeus-p2-submit-") as name:
            directory = Path(name)
            wop = self.authored(directory)
            boundary = CountingBoundary()
            first = submit(wop, repository=ROOT, store_directory=directory / "store", admission_boundary=boundary)
            second = submit(wop, repository=ROOT, store_directory=directory / "store", admission_boundary=boundary)
            self.assertEqual(first["submission_state"], "ADMISSION_REQUESTED")
            self.assertEqual(first["submission_result"], "PASS")
            self.assertEqual(first["next_action"], "EVALUATE_MISSION_ADMISSION")
            self.assertEqual(first["submission_id"], second["submission_id"])
            self.assertEqual(first["receipt_digest"], second["receipt_digest"])
            self.assertEqual(second["duplicate_submission"], "IDEMPOTENT")
            self.assertEqual(boundary.calls, 1)
            self.assertFalse((directory / "store" / "requests" / f"{first['admission_request_id']}.json").exists())
            verification = verify_submission_pair(first, second)
            self.assertEqual(verification["result"], "PASS", verification["errors"])
            self.assertNotIn("submission_receipt", verification)

    def test_cli_records_request_without_running_admission(self):
        with tempfile.TemporaryDirectory(prefix="zeus-p2-cli-") as name:
            directory = Path(name)
            wop = self.authored(directory)
            environment = {**os.environ, "ZEUS_RUNTIME_ROOT": str(directory / "runtime"), "ZEUS_NO_INTRO": "1"}
            command = ["python3", str(ROOT / "scripts/zeus"), "submit", str(wop), "--json"]
            result = subprocess.run(command,
                                    cwd=ROOT, env=environment, text=True, capture_output=True, check=False)
            self.assertEqual(result.returncode, 0, result.stderr)
            value = json.loads(result.stdout)
            replay_result = subprocess.run(command, cwd=ROOT, env=environment, text=True, capture_output=True, check=False)
            self.assertEqual(replay_result.returncode, 0, replay_result.stderr)
            replay = json.loads(replay_result.stdout)
            self.assertEqual(value["submission_state"], "ADMISSION_REQUESTED")
            self.assertEqual(value["next_action"], "EVALUATE_MISSION_ADMISSION")
            verification = verify_submission_pair(value, replay, runtime_root=directory / "runtime" / "submissions")
            self.assertEqual(verification["result"], "PASS", verification["errors"])
            self.assertTrue(verification["checks"]["receipt_path"])
            self.assertTrue(verification["checks"]["receipt_type"])
            self.assertFalse(list((directory / "runtime" / "mission-admissions").glob("*.json")))

    def test_readiness_and_provenance_fail_closed(self):
        with tempfile.TemporaryDirectory(prefix="zeus-p2-invalid-") as name:
            directory = Path(name)
            missing = directory / "missing.md"
            missing.write_text("WOP-BETA-MISSING\n", encoding="utf-8")
            with self.assertRaises(SubmissionError) as error:
                submit(missing, repository=ROOT, store_directory=directory / "missing-store")
            self.assertEqual(error.exception.evidence.get("reason_code"), "PROVENANCE_MISSING")
            wop = self.authored(directory, readiness="BLOCKED")
            with self.assertRaises(SubmissionError) as error:
                submit(wop, repository=ROOT, store_directory=directory / "store")
            self.assertEqual(error.exception.evidence["traceability"]["readiness"], "BLOCKED")
            wop = self.authored(directory)
            wop.write_text(wop.read_text(encoding="utf-8") + "altered\n", encoding="utf-8")
            with self.assertRaises(SubmissionError) as error:
                submit(wop, repository=ROOT, store_directory=directory / "store2")
            self.assertEqual(error.exception.evidence.get("result"), "FAIL")

    def test_operation_and_repository_identity_fail_closed(self):
        with tempfile.TemporaryDirectory(prefix="zeus-p2-identity-") as name:
            directory = Path(name)
            wop = self.authored(directory, operation="ALPHA")
            with self.assertRaises(SubmissionError) as error:
                submit(wop, repository=ROOT, store_directory=directory / "store")
            self.assertEqual(error.exception.evidence.get("reason_code"), "OPERATION_BETA_REQUIRED")
            wop = self.authored(directory, repository={"canonical_repository_identity": "/tmp/not-homelab"})
            with self.assertRaises(SubmissionError) as error:
                submit(wop, repository=ROOT, store_directory=directory / "store2")
            self.assertEqual(error.exception.evidence.get("reason_code"), "REPOSITORY_IDENTITY_MISMATCH")


if __name__ == "__main__":
    unittest.main()
