#!/usr/bin/env python3
"""Regression checks for controlled dirty-tree initiation."""

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.lib.emp.wop_admission import AdmissionController, submission_digest
from scripts.lib.eos.working_tree_baseline import BaselineError, validate
from scripts.lib.wop.contract import WorkPackage


class ControlledWorkingTreeBaselineTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        subprocess.run(["git", "init", "-q", self.root], check=True)
        subprocess.run(["git", "-C", self.root, "config", "user.name", "test"], check=True)
        subprocess.run(["git", "-C", self.root, "config", "user.email", "test@example.invalid"], check=True)
        (self.root / "candidate").write_text("base\n")
        subprocess.run(["git", "-C", self.root, "add", "candidate"], check=True)
        subprocess.run(["git", "-C", self.root, "commit", "-qm", "baseline"], check=True)
        (self.root / "candidate").write_text("controlled\n")
        status_digest = hashlib.sha256()
        status_digest.update(b" M candidate\0")
        status_digest.update(hashlib.sha256(b"controlled\n").digest())
        self.contract = self.root / "contract.json"
        self.contract.write_text(json.dumps({
            "baseline_head": subprocess.check_output(
                ["git", "-C", self.root, "rev-parse", "HEAD"], text=True
            ).strip(),
            "baseline_path_count": 1,
            "baseline_status_sha256": status_digest.hexdigest(),
            "handoff_paths": ["contract.json"],
        }))

    def tearDown(self):
        self.temporary.cleanup()

    def test_authorized_dirty_baseline_with_empty_index_passes(self):
        self.assertEqual(validate(self.root, self.contract)["decision"], "AUTHORIZED_DIRTY_TREE")

    def test_baseline_mutation_and_staging_fail_closed(self):
        (self.root / "candidate").write_text("changed again\n")
        with self.assertRaises(BaselineError):
            validate(self.root, self.contract)
        subprocess.run(["git", "-C", self.root, "add", "candidate"], check=True)
        with self.assertRaises(BaselineError):
            validate(self.root, self.contract)


class AuthorizationInputResolutionTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.directory = Path(self.temporary.name)
        fixtures = ROOT / "engineering/authorization/fixtures"
        head = subprocess.check_output(
            ["git", "-C", ROOT, "rev-parse", "HEAD"], text=True
        ).strip()

        wop = yaml.safe_load((fixtures / "enforcement-wop.yaml").read_text())
        wop["execution_context"]["baseline_commit"] = head
        wop["payload_digest"] = "0" * 64
        wop["signature"]["value"] = "0" * 64
        digest = WorkPackage.from_mapping(wop).calculated_digest()
        wop["payload_digest"] = digest
        wop["signature"]["value"] = digest

        state = yaml.safe_load((fixtures / "enforcement-evaluation.yaml").read_text())
        state["baseline_commit"] = head
        receipt = yaml.safe_load((fixtures / "enforcement-receipt.yaml").read_text())
        receipt["payload_digest"] = digest
        lease = yaml.safe_load((fixtures / "enforcement-lease.yaml").read_text())
        lease["payload_digest"] = digest
        values = {"wop.yaml": wop, "state.yaml": state, "receipt.yaml": receipt, "lease.yaml": lease}
        for name, value in values.items():
            (self.directory / name).write_text(yaml.safe_dump(value), encoding="utf-8")

        submission = yaml.safe_load(
            (ROOT / "engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/submission.yaml").read_text()
        )
        submission["wop_id"] = wop["wop_id"]
        submission["mission_id"] = "AUTHORIZATION-INPUT-RESOLUTION-001"
        submission["submission_digest"] = submission_digest(submission)
        decision = AdmissionController().decide(
            submission,
            expected_repository=str(ROOT),
            evaluated_at=__import__("datetime").datetime(
                2026, 7, 25, tzinfo=__import__("datetime").timezone.utc
            ),
        )
        self.admission = self.directory / "admission.json"
        self.admission.write_text(decision.to_json())
        self.manifest = self.directory / "inputs.json"
        self.manifest.write_text(json.dumps({
            "schema_version": 1,
            "document_type": "ZeusAuthorizationBundle",
            "admission_record": str(self.admission),
            "authority_graph": str(ROOT / "engineering/authority/fixtures/valid.yaml"),
            "wop": str(self.directory / "wop.yaml"),
            "state": str(self.directory / "state.yaml"),
            "receipt": str(self.directory / "receipt.yaml"),
            "lease": str(self.directory / "lease.yaml"),
            "expected_authority": "work-package",
        }))

    def tearDown(self):
        self.temporary.cleanup()

    def _qualify(self, manifest=None):
        selected = manifest or self.manifest
        script = f"""
source '{ROOT}/scripts/lib/eos/platform.sh'
eos_project_root() {{ echo '{ROOT}'; }}
eos_platform_legacy_qualify() {{ return 0; }}
export EOS_AUTHORIZATION_INPUT_MANIFEST='{selected}'
export EOS_SHADOW_ADR_DIR='{self.directory}/adr'
export EOS_SHADOW_EVALUATION_TIME='2026-07-25T00:15:00+00:00'
eos_platform_qualify homelab
"""
        return subprocess.run(
            ["bash", "-c", script], cwd=ROOT, text=True,
            capture_output=True, check=False,
        )

    def test_valid_admission_and_complete_inputs_authorize(self):
        result = self._qualify()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        adr = next((self.directory / "adr").glob("ADR-*.json"))
        value = json.loads(adr.read_text())
        self.assertEqual(value["enforcement_decision"], "AUTHORIZED")
        self.assertEqual(value["zeus_authorization_decision"], "AUTHORIZED")

    def test_mismatched_admission_fails_closed(self):
        value = json.loads(self.manifest.read_text())
        value["admission_record"] = str(
            ROOT / "engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/admission/"
            "ADMISSION-f01c0c2d-8edb-5567-ad19-8d0f4344909f.json"
        )
        mismatch = self.directory / "mismatch.json"
        mismatch.write_text(json.dumps(value))
        self.assertEqual(self._qualify(mismatch).returncode, 78)

    def test_missing_authorization_inputs_fail_closed(self):
        value = json.loads(self.manifest.read_text())
        del value["receipt"]
        incomplete = self.directory / "incomplete.json"
        incomplete.write_text(json.dumps(value))
        self.assertEqual(self._qualify(incomplete).returncode, 78)


if __name__ == "__main__":
    unittest.main()
