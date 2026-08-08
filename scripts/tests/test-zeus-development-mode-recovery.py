#!/usr/bin/env python3
"""Qualification for the bounded Development Mode recovery path."""

import copy
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]

import sys
sys.path.insert(0, str(ROOT))
from scripts.lib.emp.stage1_runtime import Stage1Error, Stage1Runtime
from scripts.lib.emp.development_dispatch import automatic_executor


FIXTURE = ROOT / "engineering/evidence/operation-beta/zeus-development-mode-recovery-001/fixtures/VALID-DEVELOPMENT-WOP"


class DevelopmentModeRecoveryTests(unittest.TestCase):
    def runtime(self, directory):
        return Stage1Runtime(ROOT, directory, operator_resolver=lambda: "loneal")

    def clean_repository(self, directory: Path) -> Path:
        """Clone the tracked fixture so recovery is not masked by this checkout's dirt."""
        repository = directory / "repository"
        subprocess.run(
            ["git", "clone", "--no-local", str(ROOT), str(repository)],
            check=True, capture_output=True, text=True,
        )
        return repository

    def test_valid_submission_stops_before_unsubstantiated_execution(self):
        with tempfile.TemporaryDirectory() as temporary:
            result = self.runtime(Path(temporary) / "stage1").submit_development(FIXTURE)
            self.assertEqual(result["state"], "AWAITING_EXECUTION_DISPATCH")
            self.assertEqual(result["phases"], ["VALIDATED", "PACKAGED", "REGISTERED", "AUTHORIZED", "ADMITTED"])
            self.assertEqual(result["next_action"], "Dispatch to a qualified Development execution agent")
            self.assertNotIn("execution", result["receipts"])
            self.assertEqual(result["execution_mode"], "DEVELOPMENT")
            self.assertEqual(result["authorization"]["authority_source"], "operator-submitted WOP")
            self.assertTrue(result["registration"]["registration_id"].startswith("EMM-DEV-"))
            self.assertEqual(result["provenance"]["repository"], str(ROOT))

    def test_submission_is_authoritative_without_redundant_governance_declaration(self):
        with tempfile.TemporaryDirectory() as temporary:
            package = Path(temporary) / "package"
            shutil.copytree(FIXTURE, package)
            for relative in ("mission.yaml", "manifests/immutable-manifest.yaml"):
                path = package / relative
                value = yaml.safe_load(path.read_text(encoding="utf-8"))
                value.pop("governance_authority", None)
                path.write_text(yaml.safe_dump(value, sort_keys=False), encoding="utf-8")
            result = self.runtime(Path(temporary) / "stage1").submit_development(package)
            self.assertIn(result["state"], {"AWAITING_EXECUTION_DISPATCH", "DISPATCHED"})
            self.assertEqual(result["authorization"]["decision"], "SUBMISSION_AUTHORITY_ESTABLISHED")
            self.assertEqual(result["authority_snapshot"]["approval_state"], "NOT_REQUIRED_UNLESS_DECLARED_IN_WOP")
            self.assertNotIn("execution", result["receipts"])
            self.assertNotIn("publication", result["receipts"])

    def test_submission_does_not_create_execution_or_publication_authority(self):
        with tempfile.TemporaryDirectory() as temporary:
            result = self.runtime(Path(temporary) / "stage1").submit_development(FIXTURE)
            self.assertEqual(result["authorization"]["decision"], "SUBMISSION_AUTHORITY_ESTABLISHED")
            self.assertNotEqual(result["state"], "EXECUTING")
            self.assertNotIn("execution", result["receipts"])
            self.assertNotIn("publication", result["receipts"])
            self.assertIn("PRODUCTION", result["authority_snapshot"]["prohibited_effects"])

    def test_repeated_submission_is_idempotent(self):
        with tempfile.TemporaryDirectory() as temporary:
            runtime = self.runtime(Path(temporary) / "stage1")
            first = runtime.submit_development(FIXTURE)
            second = runtime.submit_development(FIXTURE)
            self.assertEqual(first["instance_id"], second["instance_id"])
            self.assertEqual(first["package_digest"], second["package_digest"])
            self.assertTrue(second["idempotent_replay"])

    def test_interrupted_submission_resumes(self):
        with tempfile.TemporaryDirectory() as temporary:
            runtime = self.runtime(Path(temporary) / "stage1")
            interrupted = runtime.submit_development(FIXTURE, interrupt_after="QUALIFIED")
            self.assertEqual(interrupted["state"], "AWAITING_EXECUTION_DISPATCH")
            resumed = runtime.submit_development(FIXTURE)
            self.assertEqual(resumed["state"], "AWAITING_EXECUTION_DISPATCH")
            self.assertEqual(resumed["phases"][-1], "ADMITTED")

    def test_receipts_are_required_for_downstream_phases(self):
        with tempfile.TemporaryDirectory() as temporary:
            result = self.runtime(Path(temporary) / "stage1").submit_development(FIXTURE)
            self.assertEqual(set(result["receipts"]), {"validation", "packaging", "registration", "authorization", "admission"})
            self.assertNotIn("dispatch", result["receipts"])
            self.assertNotIn("qualification", result["receipts"])
            self.assertNotIn("publication", result["receipts"])
            self.assertNotIn("synchronization", result["receipts"])
            self.assertNotIn("closeout", result["receipts"])

    def test_receipt_backed_store_rejects_false_terminal_state(self):
        with tempfile.TemporaryDirectory() as temporary:
            runtime = self.runtime(Path(temporary) / "stage1")
            result = runtime.submit_development(FIXTURE)
            forged = copy.deepcopy(result)
            forged["state"] = "CLOSED"
            forged["phases"] = forged["phases"] + ["CLOSED"]
            runtime.store.save(forged)
            with self.assertRaises(Stage1Error):
                runtime.store.find(result["instance_id"])

    def test_unqualified_dispatch_result_stays_pending(self):
        with tempfile.TemporaryDirectory() as temporary:
            runtime = Stage1Runtime(
                ROOT, Path(temporary) / "stage1", operator_resolver=lambda: "loneal",
                execution_executor=lambda _record: {"dispatch_receipt": {"receipt_id": "missing-agent"}},
            )
            result = runtime.submit_development(FIXTURE)
            self.assertEqual(result["state"], "AWAITING_EXECUTION_DISPATCH")
            self.assertNotIn("dispatch", result["receipts"])

    def test_invalid_submission_has_no_state_mutation(self):
        with tempfile.TemporaryDirectory() as temporary:
            bad = Path(temporary) / "bad"
            shutil.copytree(FIXTURE, bad)
            mission = bad / "mission.yaml"
            text = mission.read_text().replace("execution_mode: DEVELOPMENT", "execution_mode: OPERATIONAL")
            mission.write_text(text)
            state = Path(temporary) / "stage1"
            with self.assertRaises(Stage1Error):
                self.runtime(state).submit_development(bad)
            self.assertFalse(state.exists())

    def test_protected_baselines_are_bound(self):
        with tempfile.TemporaryDirectory() as temporary:
            result = self.runtime(Path(temporary) / "stage1").submit_development(FIXTURE)
            self.assertEqual(set(result["protected_baselines"]), {"OA-v1.0.0", "OB-PLAN-v1.0.0"})

    def test_conflicting_authority_source_blocks_before_state_mutation(self):
        with tempfile.TemporaryDirectory() as temporary:
            bad = Path(temporary) / "bad"
            shutil.copytree(FIXTURE, bad)
            mission = bad / "mission.yaml"
            mission.write_text(mission.read_text() + "authority: Other Authority\n", encoding="utf-8")
            state = Path(temporary) / "stage1"
            with self.assertRaises(Stage1Error) as raised:
                self.runtime(state).submit_development(bad)
            self.assertEqual(raised.exception.evidence.get("reason_code"), "AUTHORITY_CHAIN_INTEGRITY_FAILURE")
            self.assertFalse(state.exists())

    def test_dispatch_is_bound_to_one_authority_snapshot(self):
        with tempfile.TemporaryDirectory() as temporary:
            registry = Path(temporary) / "agents.json"
            registry.write_text(json.dumps({"agents": [{
                "agent_id": "provider-a", "active": True,
                "qualification_status": "QUALIFIED",
                "qualification_evidence": ["QUAL-provider-a"],
                "repository_access_scope": [str(ROOT)]
            }], "registry_digest": "registry-digest"}), encoding="utf-8")
            runtime = Stage1Runtime(
                ROOT, Path(temporary) / "stage1", operator_resolver=lambda: "loneal",
                execution_executor=automatic_executor(ROOT, registry_path=registry),
            )
            result = runtime.submit_development(FIXTURE)
            self.assertEqual(result["state"], "DISPATCHED")
            self.assertTrue(result["authority_snapshot"]["authority_snapshot_digest"])
            self.assertEqual(result["receipts"]["dispatch"]["authority_snapshot_digest"], result["authority_snapshot"]["authority_snapshot_digest"])
            self.assertIn("provider_selection", result["receipts"])

    def test_receiptless_dispatched_state_rolls_back_on_resume(self):
        with tempfile.TemporaryDirectory() as temporary:
            repository = self.clean_repository(Path(temporary))
            fixture = repository / FIXTURE.relative_to(ROOT)
            registry = Path(temporary) / "agents.json"
            registry.write_text(json.dumps({"agents": [{
                "agent_id": "provider-a", "active": True,
                "qualification_status": "QUALIFIED",
                "qualification_evidence": ["QUAL-provider-a"],
                "repository_access_scope": [str(repository)]
            }], "registry_digest": "registry-digest"}), encoding="utf-8")
            runtime = Stage1Runtime(
                repository, Path(temporary) / "stage1", operator_resolver=lambda: "loneal",
                execution_executor=automatic_executor(repository, registry_path=registry),
            )
            result = runtime.submit_development(fixture)
            forged = copy.deepcopy(result)
            forged["receipts"]["dispatch"].pop("authority_snapshot_digest")
            runtime.store.save(forged)
            resumed = runtime.resume_transaction(result["instance_id"])
            self.assertEqual(resumed["state"], "AWAITING_EXECUTION_DISPATCH")
            self.assertEqual(resumed["pending_phase"], "DISPATCHED")
            self.assertIn("receiptless-dispatch-recovery", [item["type"] for item in resumed["evidence"]])


if __name__ == "__main__":
    unittest.main()
