"""Focused qualification for the canonical ``zeus resume`` recovery engine."""

import copy
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts.lib.emp.development_dispatch import automatic_executor
from scripts.lib.emp.stage1_runtime import Stage1Error, Stage1Runtime, _digest


ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "engineering/evidence/operation-beta/zeus-development-mode-recovery-001/fixtures/VALID-DEVELOPMENT-WOP"


class CanonicalRecoveryTests(unittest.TestCase):
    def fixture(self, directory: Path) -> tuple[Path, Path, Path]:
        repository = directory / "repository"
        subprocess.run(["git", "clone", "--no-local", str(ROOT), str(repository)],
                       check=True, capture_output=True, text=True)
        subprocess.run(["git", "-C", str(repository), "switch", "main"],
                       check=True, capture_output=True, text=True)
        package = directory / "package"
        shutil.copytree(FIXTURE, package)
        mission = package / "mission.yaml"
        content = mission.read_text(encoding="utf-8")
        mission.write_text(content.replace(f"repository_identity: {ROOT}",
                                           f"repository_identity: {repository}"), encoding="utf-8")
        publication = ROOT / "engineering/evidence/operation-beta/wop-zdcl-02-publication-aware-baseline-transition-and-canonical-resume-001/PUBLICATION-RECEIPT.json"
        publication_copy = directory / "PUBLICATION-RECEIPT.json"
        shutil.copy2(publication, publication_copy)
        # The fixture is its own published repository. Bind the copied
        # publication evidence to that immutable fixture HEAD so qualification
        # does not depend on a historical production receipt's later baseline.
        publication_value = json.loads(publication_copy.read_text(encoding="utf-8"))
        fixture_head = subprocess.run(["git", "-C", str(repository), "rev-parse", "HEAD"],
                                      check=True, capture_output=True, text=True).stdout.strip()
        publication_value["merge_commit"] = fixture_head
        publication_value["resulting_main"] = fixture_head
        unsigned = dict(publication_value)
        unsigned.pop("receipt_digest", None)
        publication_value["receipt_digest"] = _digest(unsigned)
        publication_copy.write_text(json.dumps(publication_value, indent=2) + "\n", encoding="utf-8")
        return repository, package, publication_copy

    def registry(self, directory: Path, repository: Path) -> Path:
        path = directory / "agents.json"
        path.write_text(json.dumps({"agents": [{
            "agent_id": "recovery-agent", "provider_id": "recovery-provider",
            "active": True, "qualification_status": "QUALIFIED",
            "qualification_evidence": ["QUAL-recovery-agent"],
            "repository_access_scope": [str(repository)]
        }], "registry_digest": "recovery-registry-v1"}), encoding="utf-8")
        return path

    def test_resume_migrates_and_replays_without_new_receipts(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            repository, package, _ = self.fixture(directory)
            runtime = Stage1Runtime(repository, directory / "runtime", operator_resolver=lambda: "test")
            first = runtime.submit_development(package)
            resumed = runtime.resume_transaction(first["instance_id"])
            again = runtime.resume_transaction(first["instance_id"])
            self.assertEqual(resumed["instance_id"], first["instance_id"])
            self.assertEqual(resumed["schema_version"], 3)
            self.assertEqual(resumed["receipts"], again["receipts"])
            self.assertTrue(again["idempotent_recovery"])
            self.assertEqual(again["recovery"]["result"], "PASS")

    def test_authority_and_repository_failures_are_deterministic(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            repository, package, _ = self.fixture(directory)
            runtime = Stage1Runtime(repository, directory / "runtime", operator_resolver=lambda: "test")
            first = runtime.submit_development(package)
            forged = copy.deepcopy(first)
            forged["authority_snapshot"]["package_digest"] = "forged"
            runtime.store.save(forged)
            with self.assertRaisesRegex(Stage1Error, "authority snapshot digest mismatch") as raised:
                runtime.resume_transaction(first["instance_id"])
            self.assertEqual(raised.exception.evidence["reason_code"], "AUTHORITY_CHAIN_INTEGRITY_FAILURE")

    def test_duplicate_dispatch_is_not_reissued(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            repository, package, _ = self.fixture(directory)
            registry = self.registry(directory, repository)
            calls = []
            executor = automatic_executor(repository, registry_path=registry)

            def counted(record):
                calls.append(record["instance_id"])
                return executor(record)

            runtime = Stage1Runtime(repository, directory / "runtime", operator_resolver=lambda: "test",
                                    execution_executor=counted)
            first = runtime.submit_development(package)
            self.assertEqual(first["state"], "DISPATCHED")
            calls.clear()
            second = runtime.resume_transaction(first["instance_id"])
            self.assertEqual(calls, [])
            self.assertEqual(second["receipts"]["dispatch"], first["receipts"]["dispatch"])
            self.assertEqual(second["recovery"]["dispatch"]["provider_id"], "recovery-provider")

    def test_source_package_tamper_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            repository, package, _ = self.fixture(directory)
            runtime = Stage1Runtime(repository, directory / "runtime", operator_resolver=lambda: "test")
            first = runtime.submit_development(package)
            mission = package / "mission.yaml"
            mission.write_text(mission.read_text(encoding="utf-8") + "\n# tampered\n", encoding="utf-8")
            with self.assertRaisesRegex(Stage1Error, "source package digest mismatch") as raised:
                runtime.resume_transaction(first["instance_id"])
            self.assertEqual(raised.exception.evidence["reason_code"], "PACKAGE_DIGEST_MISMATCH")

    def test_authorized_publication_successor_binds_recovery_baseline(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            repository, package, publication = self.fixture(directory)
            runtime = Stage1Runtime(repository, directory / "runtime", operator_resolver=lambda: "test")
            first = runtime.submit_development(package)
            first["repository_baseline"] = "81c82a59e633fbf7dfbc0831c9ffd4298cd64201"
            first.pop("submission_baseline", None)
            first["publication_receipt_path"] = str(publication)
            runtime.store.save(first)
            recovered = runtime.resume_transaction(first["instance_id"])
            transition = recovered["recovery"]["repository_transition"]
            self.assertIn(transition["classification"], {"AUTHORIZED_PUBLICATION_SUCCESSOR", "AUTHORIZED_RECOVERY_BASELINE"})
            self.assertEqual(recovered["submission_baseline"], "81c82a59e633fbf7dfbc0831c9ffd4298cd64201")
            fixture_head = subprocess.run(["git", "-C", str(repository), "rev-parse", "HEAD"],
                                          check=True, capture_output=True, text=True).stdout.strip()
            self.assertEqual(recovered["recovery_baseline"], fixture_head)
            self.assertEqual(recovered["recovery_baseline_binding"]["transition_digest"], transition["transition_digest"])

    def test_implementation_descendant_after_publication_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            repository, package, publication = self.fixture(directory)
            runtime = Stage1Runtime(repository, directory / "runtime", operator_resolver=lambda: "test")
            first = runtime.submit_development(package)
            first["repository_baseline"] = "81c82a59e633fbf7dfbc0831c9ffd4298cd64201"
            first.pop("submission_baseline", None)
            first["publication_receipt_path"] = str(publication)
            runtime.store.save(first)
            target = repository / "scripts/zeus"
            target.write_text(target.read_text(encoding="utf-8") + "\n# unauthorized fixture drift\n", encoding="utf-8")
            subprocess.run(["git", "-C", str(repository), "add", "scripts/zeus"], check=True)
            subprocess.run(["git", "-C", str(repository), "commit", "-m", "fixture implementation drift"],
                           check=True, capture_output=True, text=True)
            with self.assertRaises(Stage1Error) as raised:
                runtime.resume_transaction(first["instance_id"])
            self.assertIn(raised.exception.evidence["reason_code"],
                          {"UNCOMMITTED_WORKING_TREE_DRIFT", "AMBIGUOUS_PUBLICATION_TRANSITION"})

    def test_dirty_working_tree_is_fail_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            repository, package, _ = self.fixture(directory)
            runtime = Stage1Runtime(repository, directory / "runtime", operator_resolver=lambda: "test")
            first = runtime.submit_development(package)
            target = repository / "README.md"
            target.write_text(target.read_text(encoding="utf-8") + "\n# drift\n", encoding="utf-8")
            with self.assertRaises(Stage1Error) as raised:
                runtime.resume_transaction(first["instance_id"])
            self.assertEqual(raised.exception.evidence["reason_code"], "UNCOMMITTED_WORKING_TREE_DRIFT")

    def test_publication_receipt_digest_failure_is_ambiguous(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            repository, package, publication = self.fixture(directory)
            value = json.loads(publication.read_text(encoding="utf-8"))
            value["receipt_digest"] = "forged"
            publication.write_text(json.dumps(value), encoding="utf-8")
            runtime = Stage1Runtime(repository, directory / "runtime", operator_resolver=lambda: "test")
            first = runtime.submit_development(package)
            first["repository_baseline"] = "81c82a59e633fbf7dfbc0831c9ffd4298cd64201"
            first["publication_receipt_path"] = str(publication)
            runtime.store.save(first)
            with self.assertRaises(Stage1Error) as raised:
                runtime.resume_transaction(first["instance_id"])
            self.assertEqual(raised.exception.evidence["reason_code"], "AMBIGUOUS_PUBLICATION_TRANSITION")

    def test_legacy_projection_hydrates_from_receipts_before_recovery(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            repository, package, _ = self.fixture(directory)
            runtime = Stage1Runtime(repository, directory / "runtime", operator_resolver=lambda: "test")
            first = runtime.submit_development(package)
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
            repository, package, _ = self.fixture(directory)
            registry = self.registry(directory, repository)
            runtime = Stage1Runtime(
                repository, directory / "runtime", operator_resolver=lambda: "test",
                execution_executor=automatic_executor(repository, registry_path=registry),
            )
            first = runtime.submit_development(package)
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
