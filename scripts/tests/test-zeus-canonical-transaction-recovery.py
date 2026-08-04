"""Focused qualification for the canonical ``zeus resume`` recovery engine."""

import copy
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from scripts.lib.emp.development_dispatch import automatic_executor
from scripts.lib.emp.stage1_runtime import Stage1Error, Stage1Runtime


ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "engineering/evidence/operation-beta/zeus-development-mode-recovery-001/fixtures/VALID-DEVELOPMENT-WOP"


class CanonicalRecoveryTests(unittest.TestCase):
    def registry(self, directory: Path) -> Path:
        path = directory / "agents.json"
        path.write_text(json.dumps({"agents": [{
            "agent_id": "recovery-agent", "provider_id": "recovery-provider",
            "active": True, "qualification_status": "QUALIFIED",
            "qualification_evidence": ["QUAL-recovery-agent"],
            "repository_access_scope": [str(ROOT)]
        }], "registry_digest": "recovery-registry-v1"}), encoding="utf-8")
        return path

    def test_resume_migrates_and_replays_without_new_receipts(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            runtime = Stage1Runtime(ROOT, directory / "runtime", operator_resolver=lambda: "test")
            first = runtime.submit_development(FIXTURE)
            resumed = runtime.resume_transaction(first["instance_id"])
            again = runtime.resume_transaction(first["instance_id"])
            self.assertEqual(resumed["instance_id"], first["instance_id"])
            self.assertEqual(resumed["schema_version"], 3)
            self.assertEqual(resumed["receipts"], again["receipts"])
            self.assertTrue(again["idempotent_recovery"])
            self.assertEqual(again["recovery"]["result"], "PASS")

    def test_authority_and_repository_failures_are_deterministic(self):
        with tempfile.TemporaryDirectory() as temporary:
            runtime = Stage1Runtime(ROOT, Path(temporary) / "runtime", operator_resolver=lambda: "test")
            first = runtime.submit_development(FIXTURE)
            forged = copy.deepcopy(first)
            forged["authority_snapshot"]["package_digest"] = "forged"
            runtime.store.save(forged)
            with self.assertRaisesRegex(Stage1Error, "authority snapshot digest mismatch") as raised:
                runtime.resume_transaction(first["instance_id"])
            self.assertEqual(raised.exception.evidence["reason_code"], "AUTHORITY_CHAIN_INTEGRITY_FAILURE")

    def test_duplicate_dispatch_is_not_reissued(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            registry = self.registry(directory)
            calls = []
            executor = automatic_executor(ROOT, registry_path=registry)

            def counted(record):
                calls.append(record["instance_id"])
                return executor(record)

            runtime = Stage1Runtime(ROOT, directory / "runtime", operator_resolver=lambda: "test",
                                    execution_executor=counted)
            first = runtime.submit_development(FIXTURE)
            self.assertEqual(first["state"], "DISPATCHED")
            calls.clear()
            second = runtime.resume_transaction(first["instance_id"])
            self.assertEqual(calls, [])
            self.assertEqual(second["receipts"]["dispatch"], first["receipts"]["dispatch"])
            self.assertEqual(second["recovery"]["dispatch"]["provider_id"], "recovery-provider")

    def test_source_package_tamper_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            package = directory / "package"
            shutil.copytree(FIXTURE, package)
            runtime = Stage1Runtime(ROOT, directory / "runtime", operator_resolver=lambda: "test")
            first = runtime.submit_development(package)
            mission = package / "mission.yaml"
            mission.write_text(mission.read_text(encoding="utf-8") + "\n# tampered\n", encoding="utf-8")
            with self.assertRaisesRegex(Stage1Error, "source package digest mismatch") as raised:
                runtime.resume_transaction(first["instance_id"])
            self.assertEqual(raised.exception.evidence["reason_code"], "PACKAGE_DIGEST_MISMATCH")

    def test_legacy_projection_hydrates_from_receipts_before_recovery(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            runtime = Stage1Runtime(ROOT, directory / "runtime", operator_resolver=lambda: "test")
            first = runtime.submit_development(FIXTURE)
            legacy = copy.deepcopy(first)
            for field in ("source", "source_digest", "package", "package_digest", "registration",
                          "phases", "lifecycle_integrity", "pending_phase", "next_action"):
                legacy.pop(field, None)
            legacy["schema_version"] = 2
            runtime.store.save(legacy)
            recovered = runtime.resume_transaction(first["instance_id"])
            self.assertEqual(recovered["instance_id"], first["instance_id"])
            self.assertEqual(recovered["package_digest"], first["package_digest"])
            self.assertEqual(recovered["source_digest"], first["source_digest"])
            self.assertEqual(recovered["registration"]["registration_id"], first["registration"]["registration_id"])
            self.assertEqual(recovered["hydration"]["schema_version"], 1)
            self.assertTrue(recovered["hydration"]["unresolved"])
            self.assertEqual(recovered["schema_version"], 3)

    def test_legacy_invalid_dispatch_without_snapshot_reconciles(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            registry = self.registry(directory)
            runtime = Stage1Runtime(
                ROOT, directory / "runtime", operator_resolver=lambda: "test",
                execution_executor=automatic_executor(ROOT, registry_path=registry),
            )
            first = runtime.submit_development(FIXTURE)
            legacy = copy.deepcopy(first)
            legacy.pop("authority_snapshot", None)
            legacy["receipts"]["dispatch"] = {
                "receipt_id": first["receipts"]["dispatch"]["receipt_id"],
                "receipt_type": "dispatch",
                "agent_id": "historical-agent",
            }
            runtime.store.save(legacy)
            recovered = runtime.resume_transaction(first["instance_id"])
            self.assertEqual(recovered["state"], "AWAITING_EXECUTION_DISPATCH")
            self.assertTrue(any(item.get("type") == "receiptless-dispatch-recovery"
                                for item in recovered.get("evidence", [])))
            historical = recovered["evidence"][-1]["historical_dispatch"]
            self.assertEqual(historical["receipt_id"], first["receipts"]["dispatch"]["receipt_id"])


if __name__ == "__main__":
    unittest.main()
