#!/usr/bin/env python3
"""Mission N0 WOP admission controller regression tests."""

from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.lib.emp.wop_admission import (  # noqa: E402
    AdmissionController,
    AdmissionLedger,
    REQUIRED_SECTIONS,
    submission_digest,
    verify_accepted_record,
)


class AdmissionTests(unittest.TestCase):
    repository = str(ROOT)
    evaluated_at = datetime(2026, 7, 25, 18, 0, tzinfo=timezone.utc)

    def valid_submission(self):
        value = {
            "schema_version": 1,
            "document_type": "EngineeringWorkOrder",
            "wop_id": "WOP-12345678-1234-4234-9234-123456789abc",
            "mission_id": "ZEUS-N0",
            "phase_id": "ADMISSION-CONTROL",
            "revision": 1,
            "status": "Active",
            "title": "Admission qualification fixture",
            "repository_identity": self.repository,
            "submitter_identity": "qualification-fixture",
            "approval": {
                "authority": "human-approver",
                "reference": "APPROVAL-N0-001",
                "date": "2026-07-25",
                "authorized_lifecycle_state": "Active",
            },
            "execution_package_references": {
                "authority_node_id": "work-package",
                "authorization_decision_record": "ADR-fixture",
                "immutable_wop": "engineering/wop/fixtures/valid-wop.yaml",
            },
            "authoritative_references": [
                "PROC-0001@1.11", "TPL-0001@1.7", "STD-0000", "STD-0001",
                "STD-0002", "STD-0003", "STD-0004",
            ],
            "sections": {name: f"qualified {name}" for name in REQUIRED_SECTIONS},
        }
        value["submission_digest"] = submission_digest(value)
        return value

    def decide(self, value):
        return AdmissionController().decide(
            value, expected_repository=self.repository, evaluated_at=self.evaluated_at
        )

    def test_valid_submission_is_accepted_deterministically(self):
        first = self.decide(self.valid_submission())
        second = self.decide(self.valid_submission())
        self.assertEqual(first.canonical_data, second.canonical_data)
        self.assertEqual(first.data["admission_decision"], "ACCEPTED")
        self.assertEqual(first.data["validation_summary"]["failure_count"], 0)

    def test_incomplete_submission_reports_every_failure(self):
        value = self.valid_submission()
        del value["approval"]
        del value["sections"]["scope"]
        del value["execution_package_references"]["immutable_wop"]
        value["submission_digest"] = submission_digest(value)
        result = self.decide(value).data
        fields = {failure["field"] for failure in result["validation_failures"]}
        self.assertEqual(result["admission_decision"], "RESUBMISSION_REQUIRED")
        self.assertTrue({"approval", "sections.scope",
                         "execution_package_references.immutable_wop"} <= fields)
        self.assertEqual(len(result["execution_status"]), 5)
        self.assertIn("required_submission_format", result)

    def test_malformed_and_unauthorized_submissions_fail_closed(self):
        value = self.valid_submission()
        value["wop_id"] = "bad"
        value["status"] = "Draft"
        value["repository_identity"] = "/different/repository"
        value["approval"]["authorized_lifecycle_state"] = "Approved"
        value["submission_digest"] = "0" * 64
        codes = {
            failure["reason_code"] for failure in self.decide(value).data[
                "validation_failures"
            ]
        }
        self.assertTrue({
            "INVALID_WOP_IDENTIFIER", "INACTIVE_SUBMISSION",
            "REPOSITORY_IDENTITY_MISMATCH", "APPROVAL_NOT_ACTIVE",
            "SUBMISSION_DIGEST_MISMATCH",
        } <= codes)

    def test_unknown_fields_and_version_fail(self):
        value = self.valid_submission()
        value["schema_version"] = 2
        value["unexpected"] = True
        value["submission_digest"] = submission_digest(value)
        codes = [item["reason_code"] for item in self.decide(value).data["validation_failures"]]
        self.assertIn("UNSUPPORTED_SCHEMA_VERSION", codes)
        self.assertIn("UNRECOGNIZED_TOP_LEVEL_FIELD", codes)

    def test_convergence_lineage_fields_are_admissible(self):
        value = self.valid_submission()
        value["authority_lineage"] = {
            "mode": "AUTHORITY_RECORD", "authority_record_id": "AR-OA-01-001"
        }
        value["convergence_flow_digest"] = "a" * 64
        value["submission_digest"] = submission_digest(value)
        self.assertEqual("ACCEPTED", self.decide(value).data["admission_decision"])

    def test_ledger_is_immutable_and_idempotent(self):
        decision = self.decide(self.valid_submission())
        with tempfile.TemporaryDirectory() as directory:
            ledger = AdmissionLedger(directory)
            path = ledger.record(decision)
            before = path.read_bytes()
            self.assertEqual(ledger.record(decision), path)
            self.assertEqual(path.read_bytes(), before)
            changed = json.loads(decision.canonical_data)
            changed["evaluation_timestamp"] = "2026-07-25T19:00:00Z"
            from scripts.lib.emp.wop_admission import AdmissionDecision
            with self.assertRaises(ValueError):
                ledger.record(AdmissionDecision(json.dumps(changed, sort_keys=True)))

    def test_record_checksum_and_binding_verification(self):
        with tempfile.TemporaryDirectory() as directory:
            path = AdmissionLedger(directory).record(self.decide(self.valid_submission()))
            self.assertTrue(verify_accepted_record(
                path, expected_repository=self.repository,
                expected_wop="WOP-12345678-1234-4234-9234-123456789abc",
            ))
            self.assertFalse(verify_accepted_record(
                path, expected_repository="/wrong"
            ))

    def test_rejected_record_never_unlocks_work_initiation(self):
        value = self.valid_submission()
        value["status"] = "Draft"
        value["submission_digest"] = submission_digest(value)
        with tempfile.TemporaryDirectory() as directory:
            path = AdmissionLedger(directory).record(self.decide(value))
            self.assertFalse(verify_accepted_record(
                path, expected_repository=self.repository
            ))

    def test_cli_accept_and_reject_exit_codes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name, value in (
                ("accepted.yaml", self.valid_submission()),
                ("rejected.yaml", {}),
            ):
                (root / name).write_text(yaml.safe_dump(value), encoding="utf-8")
            common = [
                str(ROOT / "scripts/wop-admissionctl"), "admit",
                "--repository", self.repository, "--ledger", str(root / "ledger"),
                "--at", "2026-07-25T18:00:00Z",
            ]
            accepted = subprocess.run(
                common + ["--submission", str(root / "accepted.yaml")],
                cwd=ROOT, capture_output=True, text=True, check=False,
            )
            rejected = subprocess.run(
                common + ["--submission", str(root / "rejected.yaml")],
                cwd=ROOT, capture_output=True, text=True, check=False,
            )
            self.assertEqual(accepted.returncode, 0, accepted.stderr)
            self.assertEqual(rejected.returncode, 78)
            self.assertEqual(json.loads(rejected.stdout)["admission_decision"],
                             "RESUBMISSION_REQUIRED")

    def test_gate_precedes_repository_inspection_and_authorization(self):
        script = f"""
source '{ROOT}/scripts/lib/eos/platform.sh'
eos_project_root() {{ echo '{ROOT}'; }}
eos_platform_legacy_qualify() {{ echo legacy-ran >'{ROOT}/.n0-forbidden'; }}
eos_work_initiation_authorize() {{ echo zeus-ran >'{ROOT}/.n0-forbidden'; }}
unset EOS_WOP_ADMISSION_RECORD
eos_platform_qualify homelab >/dev/null 2>&1
test "$?" -eq 78
test ! -e '{ROOT}/.n0-forbidden'
"""
        result = subprocess.run(
            ["bash", "-c", script], cwd=ROOT, capture_output=True, text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_controller_has_no_repair_planning_or_execution_paths(self):
        source = (ROOT / "scripts/lib/emp/wop_admission.py").read_text()
        for prohibited in (
            "execute_wop(", "dispatch_work(", "reconcile(", "select_mission(",
            "repair_submission(", "plan_mission(",
        ):
            self.assertNotIn(prohibited, source)


if __name__ == "__main__":
    unittest.main()
