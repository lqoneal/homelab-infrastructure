#!/usr/bin/env python3
"""Focused P3-G1 canonical Zeus admission verification tests."""

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

from scripts.lib.emp.mission_admission_boundary import (  # noqa: E402
    MissionAdmissionBoundaryError,
    admit,
)
from scripts.lib.emp.mission_admission_verification import verify_admission_replay  # noqa: E402


class MissionAdmissionBoundaryTests(unittest.TestCase):
    def authored_and_submitted(self, directory: Path):
        source = directory / "mission.yaml"
        source.write_text(
            "schema_version: '1.0'\noperation: BETA\nmission:\n"
            "  title: P3 Admission Verification\n"
            "  objective: Verify canonical Mission Admission\n"
            "  repository: homelab\n"
            "  scope:\n    include: [admission foundation]\n    exclude: [execution, publication]\n"
            "  restrictions: [fail closed]\n"
            "  acceptance_criteria: [deterministic admission replay]\n"
            "  validation: [focused tests pass]\n"
            "  evidence: [admission receipt and journal]\n",
            encoding="utf-8",
        )
        environment = {**os.environ, "ZEUS_NO_INTRO": "1", "PYTHONDONTWRITEBYTECODE": "1"}
        wop = directory / "wop.md"
        authored = subprocess.run(
            [sys.executable, str(ROOT / "scripts/zeus"), "wop", "template", str(source), "--output", str(wop), "--json"],
            cwd=ROOT, env=environment, text=True, capture_output=True, check=False,
        )
        self.assertEqual(authored.returncode, 0, authored.stderr)
        runtime = directory / "runtime"
        submitted = subprocess.run(
            [sys.executable, str(ROOT / "scripts/zeus"), "--runtime-root", str(runtime), "submit", str(wop), "--json"],
            cwd=ROOT, env=environment, text=True, capture_output=True, check=False,
        )
        self.assertEqual(submitted.returncode, 0, submitted.stderr)
        return wop, json.loads(submitted.stdout), runtime, environment

    def admission_command(self, wop: Path, submission: dict, runtime: Path):
        return [sys.executable, str(ROOT / "scripts/zeus"), "--runtime-root", str(runtime),
                "admit", submission["receipt_path"], "--wop", str(wop), "--json"]

    def test_canonical_operator_replay_verifies_complete_admission(self):
        with tempfile.TemporaryDirectory(prefix="zeus-p3-canonical-") as name:
            directory = Path(name)
            wop, submission, runtime, environment = self.authored_and_submitted(directory)
            command = self.admission_command(wop, submission, runtime)
            first_result = subprocess.run(command, cwd=ROOT, env=environment, text=True, capture_output=True, check=False)
            replay_result = subprocess.run(command, cwd=ROOT, env=environment, text=True, capture_output=True, check=False)
            self.assertEqual(first_result.returncode, 0, first_result.stderr)
            self.assertEqual(replay_result.returncode, 0, replay_result.stderr)
            first, replay = json.loads(first_result.stdout), json.loads(replay_result.stdout)
            verified = verify_admission_replay(first, replay, runtime_root=runtime, wop=wop, repository=ROOT)
            self.assertEqual(verified["result"], "PASS")
            self.assertEqual(first["transaction_type"], "mission-admission")
            self.assertTrue(verified["bootstrap_boundary"]["bootstrap_eligible"])
            self.assertEqual(verified["bootstrap_boundary"]["next_action"], "EVALUATE_BOOTSTRAP_ELIGIBILITY")
            self.assertEqual(replay["duplicate_admission"], "IDEMPOTENT")

    def test_canonical_artifact_loss_fails_closed(self):
        with tempfile.TemporaryDirectory(prefix="zeus-p3-missing-artifact-") as name:
            directory = Path(name)
            wop, submission, runtime, environment = self.authored_and_submitted(directory)
            command = self.admission_command(wop, submission, runtime)
            first = json.loads(subprocess.run(command, cwd=ROOT, env=environment, text=True,
                                              capture_output=True, check=True).stdout)
            replay = json.loads(subprocess.run(command, cwd=ROOT, env=environment, text=True,
                                               capture_output=True, check=True).stdout)
            Path(first["mission_contract"]["path"]).unlink()
            with self.assertRaises(ValueError):
                verify_admission_replay(first, replay, runtime_root=runtime, wop=wop, repository=ROOT)

    def test_canonical_artifact_digest_mismatch_fails_closed(self):
        with tempfile.TemporaryDirectory(prefix="zeus-p3-digest-mismatch-") as name:
            directory = Path(name)
            wop, submission, runtime, environment = self.authored_and_submitted(directory)
            command = self.admission_command(wop, submission, runtime)
            first = json.loads(subprocess.run(command, cwd=ROOT, env=environment, text=True,
                                              capture_output=True, check=True).stdout)
            replay = json.loads(subprocess.run(command, cwd=ROOT, env=environment, text=True,
                                               capture_output=True, check=True).stdout)
            first["package"]["digest"] = "0" * 64
            with self.assertRaises(ValueError):
                verify_admission_replay(first, replay, runtime_root=runtime, wop=wop, repository=ROOT)

    def test_persisted_artifact_content_change_fails_closed(self):
        with tempfile.TemporaryDirectory(prefix="zeus-p3-content-tamper-") as name:
            directory = Path(name)
            wop, submission, runtime, environment = self.authored_and_submitted(directory)
            command = self.admission_command(wop, submission, runtime)
            first = json.loads(subprocess.run(command, cwd=ROOT, env=environment, text=True,
                                              capture_output=True, check=True).stdout)
            replay = json.loads(subprocess.run(command, cwd=ROOT, env=environment, text=True,
                                               capture_output=True, check=True).stdout)
            package_path = Path(first["package"]["path"])
            package = json.loads(package_path.read_text(encoding="utf-8"))
            package["execution_created"] = True
            package_path.write_text(json.dumps(package, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                verify_admission_replay(first, replay, runtime_root=runtime, wop=wop, repository=ROOT)

    def test_required_artifact_cardinality_and_downstream_absence(self):
        with tempfile.TemporaryDirectory(prefix="zeus-p3-artifacts-") as name:
            directory = Path(name)
            wop, submission, runtime, environment = self.authored_and_submitted(directory)
            command = self.admission_command(wop, submission, runtime)
            first = json.loads(subprocess.run(command, cwd=ROOT, env=environment, text=True, capture_output=True, check=True).stdout)
            replay = json.loads(subprocess.run(command, cwd=ROOT, env=environment, text=True, capture_output=True, check=True).stdout)
            verified = verify_admission_replay(first, replay, runtime_root=runtime, wop=wop, repository=ROOT)
            self.assertEqual(verified["checks"]["downstream_artifacts"], "NONE")
            for count in verified["checks"]["artifact_counts"].values():
                self.assertEqual(count, 1)
            self.assertFalse(list((runtime / "mission-executions").glob("*.json")))

    def test_altered_receipt_and_wop_fail_closed(self):
        with tempfile.TemporaryDirectory(prefix="zeus-p3-invalid-") as name:
            directory = Path(name)
            wop, submission, runtime, _ = self.authored_and_submitted(directory)
            receipt = Path(submission["receipt_path"])
            altered = json.loads(receipt.read_text())
            altered["mission_id"] = "MISSION-BETA-ALTERED"
            altered_receipt = directory / "altered.json"
            altered_receipt.write_text(json.dumps(altered), encoding="utf-8")
            with self.assertRaises(MissionAdmissionBoundaryError):
                admit(altered_receipt, wop=wop, repository=ROOT, runtime_root=runtime)
            wop.write_text(wop.read_text() + "altered\n", encoding="utf-8")
            with self.assertRaises(MissionAdmissionBoundaryError):
                admit(receipt, wop=wop, repository=ROOT, runtime_root=directory / "runtime-2")

    def test_canonical_command_does_not_create_execution(self):
        with tempfile.TemporaryDirectory(prefix="zeus-p3-no-execution-") as name:
            directory = Path(name)
            wop, submission, runtime, environment = self.authored_and_submitted(directory)
            result = subprocess.run(self.admission_command(wop, submission, runtime), cwd=ROOT, env=environment, text=True, capture_output=True, check=False)
            self.assertEqual(result.returncode, 0, result.stderr)
            value = json.loads(result.stdout)
            self.assertEqual(value["admission_state"], "ADMISSION_COMPLETE")
            self.assertEqual(value["admission_result"], "PASS")
            self.assertFalse(list((runtime / "mission-executions").glob("*.json")))


if __name__ == "__main__":
    unittest.main()
