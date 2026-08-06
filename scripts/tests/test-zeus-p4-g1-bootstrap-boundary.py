#!/usr/bin/env python3
"""Focused P4-G1 bootstrap foundation tests."""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.lib.emp.bootstrap_boundary import BootstrapBoundaryError, bootstrap  # noqa: E402
from scripts.lib.emp.bootstrap_verification import verify_bootstrap_replay  # noqa: E402


def p3_test_module():
    path = ROOT / "scripts/tests/test-zeus-p3-g1-mission-admission-boundary.py"
    spec = importlib.util.spec_from_file_location("p3_tests", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class BootstrapBoundaryTests(unittest.TestCase):
    def setup_admission(self, directory: Path):
        helper = p3_test_module().MissionAdmissionBoundaryTests()
        wop, submission, runtime, environment = helper.authored_and_submitted(directory)
        command = helper.admission_command(wop, submission, runtime)
        first = json.loads(subprocess.run(command, cwd=ROOT, env=environment, text=True,
                                          capture_output=True, check=True).stdout)
        replay = json.loads(subprocess.run(command, cwd=ROOT, env=environment, text=True,
                                           capture_output=True, check=True).stdout)
        return wop, submission, runtime, environment, first, replay

    def bootstrap_command(self, admission_path: Path, runtime: Path):
        return [sys.executable, str(ROOT / "scripts/zeus"), "--runtime-root", str(runtime),
                "bootstrap", "admission", str(admission_path), "--json"]

    def cli(self, *arguments):
        return subprocess.run(
            [sys.executable, str(ROOT / "scripts/zeus"), *arguments],
            cwd=ROOT, text=True, capture_output=True,
        )

    def test_bootstrap_mode_is_required_and_help_is_explicit(self):
        result = self.cli("bootstrap")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("BOOTSTRAP_MODE_REQUIRED", result.stderr)
        self.assertIn("bootstrap admission", result.stderr)
        self.assertIn("bootstrap operational", result.stderr)
        help_result = self.cli("bootstrap", "--help")
        self.assertEqual(help_result.returncode, 0)
        self.assertIn("admission", help_result.stdout)
        self.assertIn("operational", help_result.stdout)

    def test_explicit_operational_mode_routes_to_legacy_bootstrap(self):
        with tempfile.TemporaryDirectory(prefix="zeus-p4-operational-") as name:
            result = self.cli("--runtime-root", name, "bootstrap", "operational", "--json")
            self.assertEqual(result.returncode, 0, result.stderr)
            value = json.loads(result.stdout)
            self.assertEqual(value["bootstrap_mode"], "OPERATIONAL")
            self.assertEqual(value["evidence_type"], "zeus-operational-bootstrap")

    def test_admission_input_cannot_fall_back_to_operational(self):
        result = self.cli("bootstrap", "operational", "not-an-admission.json", "--json")
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("LEGACY_OPERATIONAL_BOOTSTRAP", result.stdout)

    def test_conflicting_modes_fail_closed(self):
        result = self.cli("bootstrap", "admission", "admission.json", "operational")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unrecognized arguments", result.stderr)

    def test_operational_options_cannot_enter_admission_mode(self):
        result = self.cli("bootstrap", "admission", "admission.json", "--operational")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unrecognized arguments", result.stderr)

    def test_malformed_admission_does_not_fall_back(self):
        with tempfile.TemporaryDirectory(prefix="zeus-p4-malformed-argument-") as name:
            path = Path(name) / "malformed.json"
            path.write_text("{}", encoding="utf-8")
            result = self.cli("--runtime-root", name, "bootstrap", "admission", str(path), "--json")
            self.assertNotEqual(result.returncode, 0)
            self.assertNotIn("LEGACY_OPERATIONAL_BOOTSTRAP", result.stdout)

    def test_bootstrap_verify_rejects_legacy_response(self):
        with tempfile.TemporaryDirectory(prefix="zeus-p4-verify-legacy-") as name:
            directory = Path(name)
            first = directory / "first.json"
            replay = directory / "replay.json"
            legacy = {"evidence_type": "zeus-operational-bootstrap", "bootstrap_mode": "OPERATIONAL"}
            first.write_text(json.dumps(legacy), encoding="utf-8")
            replay.write_text(json.dumps(legacy), encoding="utf-8")
            result = self.cli("--runtime-root", name, "bootstrap-verify", str(first), str(replay), "--json")
            self.assertNotEqual(result.returncode, 0)
            self.assertNotIn('"result": "PASS"', result.stdout)

    def test_successful_bootstrap_and_read_only_replay_verification(self):
        with tempfile.TemporaryDirectory(prefix="zeus-p4-success-") as name:
            directory = Path(name)
            _, _, runtime, environment, admission, _ = self.setup_admission(directory)
            admission_path = runtime / "admissions" / f"{admission['admission_id']}.json"
            command = self.bootstrap_command(admission_path, runtime)
            first = json.loads(subprocess.run(command, cwd=ROOT, env=environment, text=True,
                                              capture_output=True, check=True).stdout)
            replay = json.loads(subprocess.run(command, cwd=ROOT, env=environment, text=True,
                                               capture_output=True, check=True).stdout)
            before = {path: path.read_bytes() for path in runtime.rglob("*.json")}
            verified = verify_bootstrap_replay(first, replay, runtime_root=runtime, repository=ROOT)
            after = {path: path.read_bytes() for path in runtime.rglob("*.json")}
            self.assertEqual(verified["result"], "PASS")
            self.assertEqual(first["bootstrap_state"], "READY_FOR_EXECUTION_PROVIDER")
            self.assertTrue(first["provider_ready"])
            self.assertEqual(first["next_action"], "EVALUATE_EXECUTION_PROVIDER")
            self.assertEqual(replay["duplicate_bootstrap"], "IDEMPOTENT")
            self.assertEqual(before, after)
            self.assertFalse(first["provider_selected"])
            self.assertFalse(first["dispatch_created"])
            self.assertFalse(first["execution_started"])

    def test_partial_transaction_recovery_is_idempotent(self):
        with tempfile.TemporaryDirectory(prefix="zeus-p4-recovery-") as name:
            directory = Path(name)
            _, _, runtime, _, admission, _ = self.setup_admission(directory)
            admission_path = runtime / "admissions" / f"{admission['admission_id']}.json"
            first = bootstrap(admission_path, repository=ROOT, runtime_root=runtime)
            transaction_path = runtime / "bootstraps" / f"{first['bootstrap_id']}.json"
            transaction_path.unlink()
            recovered = bootstrap(admission_path, repository=ROOT, runtime_root=runtime)
            self.assertEqual(recovered["bootstrap_id"], first["bootstrap_id"])
            self.assertEqual(recovered["transaction_digest"], first["transaction_digest"])
            self.assertEqual(len(list((runtime / "execution-records").glob("*.json"))), 1)

    def test_altered_admission_transaction_fails_closed(self):
        with tempfile.TemporaryDirectory(prefix="zeus-p4-admission-tamper-") as name:
            directory = Path(name)
            _, _, runtime, _, admission, _ = self.setup_admission(directory)
            path = runtime / "admissions" / f"{admission['admission_id']}.json"
            value = json.loads(path.read_text())
            value["bootstrap_eligible"] = False
            path.write_text(json.dumps(value), encoding="utf-8")
            with self.assertRaises(BootstrapBoundaryError):
                bootstrap(path, repository=ROOT, runtime_root=runtime)

    def test_artifact_tamper_and_missing_artifact_fail_closed(self):
        with tempfile.TemporaryDirectory(prefix="zeus-p4-artifact-tamper-") as name:
            directory = Path(name)
            _, _, runtime, _, admission, _ = self.setup_admission(directory)
            admission_path = runtime / "admissions" / f"{admission['admission_id']}.json"
            first = bootstrap(admission_path, repository=ROOT, runtime_root=runtime)
            record = Path(first["execution_record"]["path"])
            value = json.loads(record.read_text())
            value["provider_ready"] = False
            record.write_text(json.dumps(value), encoding="utf-8")
            with self.assertRaises(BootstrapBoundaryError):
                bootstrap(admission_path, repository=ROOT, runtime_root=runtime)

    def test_each_admission_artifact_tamper_fails_closed(self):
        for directory_name in ("packages", "mission-contracts", "execution-authority", "receipts", "journals"):
            with self.subTest(directory=directory_name), tempfile.TemporaryDirectory(prefix="zeus-p4-admission-artifact-") as name:
                directory = Path(name)
                _, _, runtime, _, admission, _ = self.setup_admission(directory)
                artifact_path = next((runtime / directory_name).glob("*.json"))
                value = json.loads(artifact_path.read_text())
                field = "execution_created" if directory_name == "packages" else "operation"
                value[field] = True if field == "execution_created" else "ALPHA"
                artifact_path.write_text(json.dumps(value), encoding="utf-8")
                admission_path = runtime / "admissions" / f"{admission['admission_id']}.json"
                with self.assertRaises(BootstrapBoundaryError):
                    bootstrap(admission_path, repository=ROOT, runtime_root=runtime)

    def test_repository_and_admission_identity_mismatch_fail_closed(self):
        with tempfile.TemporaryDirectory(prefix="zeus-p4-identity-") as name:
            directory = Path(name)
            _, _, runtime, _, admission, _ = self.setup_admission(directory)
            admission_path = runtime / "admissions" / f"{admission['admission_id']}.json"
            with self.assertRaises(BootstrapBoundaryError):
                bootstrap(admission_path, repository=directory, runtime_root=runtime)

    def test_conflicting_execution_record_and_missing_artifact_fail_closed(self):
        with tempfile.TemporaryDirectory(prefix="zeus-p4-conflict-") as name:
            directory = Path(name)
            _, _, runtime, _, admission, _ = self.setup_admission(directory)
            admission_path = runtime / "admissions" / f"{admission['admission_id']}.json"
            first = bootstrap(admission_path, repository=ROOT, runtime_root=runtime)
            extra = runtime / "execution-records" / "CONFLICT.json"
            extra.write_text(json.dumps({"artifact_digest": "0" * 64}), encoding="utf-8")
            with self.assertRaises(BootstrapBoundaryError):
                bootstrap(admission_path, repository=ROOT, runtime_root=runtime)
            extra.unlink()
            Path(first["bootstrap_journal"]["path"]).unlink()
            with self.assertRaises(BootstrapBoundaryError):
                bootstrap(admission_path, repository=ROOT, runtime_root=runtime)

    def test_no_downstream_artifacts_and_exact_cardinality(self):
        with tempfile.TemporaryDirectory(prefix="zeus-p4-boundary-") as name:
            directory = Path(name)
            _, _, runtime, _, admission, _ = self.setup_admission(directory)
            admission_path = runtime / "admissions" / f"{admission['admission_id']}.json"
            first = bootstrap(admission_path, repository=ROOT, runtime_root=runtime)
            for directory_name in ("bootstraps", "execution-records", "bootstrap-receipts", "bootstrap-journals", "provider-readiness"):
                self.assertEqual(len(list((runtime / directory_name).glob("*.json"))), 1)
            self.assertFalse(any((runtime / name).exists() for name in
                                 ("providers", "provider-sessions", "dispatch", "executions")))
            self.assertEqual(first["provider_readiness"]["digest"],
                             json.loads(Path(first["provider_readiness"]["path"]).read_text())["artifact_digest"])

    def test_legacy_mission_execution_records_are_excluded_from_p4_boundary(self):
        with tempfile.TemporaryDirectory(prefix="zeus-p4-legacy-store-") as name:
            directory = Path(name)
            _, _, runtime, environment, admission, _ = self.setup_admission(directory)
            admission_path = runtime / "admissions" / f"{admission['admission_id']}.json"
            command = self.bootstrap_command(admission_path, runtime)
            first = json.loads(subprocess.run(command, cwd=ROOT, env=environment, text=True,
                                              capture_output=True, check=True).stdout)
            legacy = runtime / "mission-executions" / "LEGACY-EXECUTION.json"
            legacy.parent.mkdir(parents=True, exist_ok=True)
            legacy.write_text(json.dumps({"lifecycle": "legacy-operational"}), encoding="utf-8")
            replay = json.loads(subprocess.run(command, cwd=ROOT, env=environment, text=True,
                                               capture_output=True, check=True).stdout)
            verified = verify_bootstrap_replay(first, replay, runtime_root=runtime, repository=ROOT)
            self.assertEqual(verified["result"], "PASS")
            self.assertEqual(verified["downstream_artifacts"], "NONE")


if __name__ == "__main__":
    unittest.main()
