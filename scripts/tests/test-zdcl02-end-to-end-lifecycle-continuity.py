#!/usr/bin/env python3
"""Isolated end-to-end qualification for the ZDCL-02 lifecycle corrective."""

import copy
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
from scripts.lib.emp.stage1_runtime import Stage1Runtime
from scripts.lib.emp.development_dispatch import automatic_executor

FIXTURE = ROOT / "engineering/evidence/operation-beta/zeus-development-mode-recovery-001/fixtures/VALID-DEVELOPMENT-WOP"


class ZDCL02ContinuityQualificationTests(unittest.TestCase):
    def _runtime(self, directory, *, executor=None):
        return Stage1Runtime(ROOT, directory, operator_resolver=lambda: "qualification-agent",
                             execution_executor=executor)

    def _registry(self, directory):
        path = directory / "agents.json"
        path.write_text(json.dumps({"agents": [{
            "agent_id": "synthetic-agent-01", "active": True,
            "qualification_status": "QUALIFIED",
            "qualification_evidence": ["QUAL-synthetic-agent-01"],
            "repository_access_scope": [str(ROOT)]
        }], "registry_digest": "synthetic-registry-v1"}), encoding="utf-8")
        return path

    def test_healthy_submission_creates_one_snapshot_and_receipt_backed_dispatch(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            runtime = self._runtime(root / "stage1", executor=automatic_executor(ROOT, registry_path=self._registry(root)))
            result = runtime.submit_development(FIXTURE)
            self.assertEqual(result["state"], "DISPATCHED")
            snapshot = result["authority_snapshot"]["authority_snapshot_digest"]
            self.assertTrue(snapshot)
            self.assertEqual(result["receipts"]["dispatch"]["authority_snapshot_digest"], snapshot)
            self.assertEqual(result["next_action"], "Await provider launch acknowledgment before EXECUTING")
            admission = root / "mission-admissions" / f"{result['receipts']['admission']['admission_id']}.json"
            execution = root / "mission-executions" / f"{result['instance_id']}.json"
            self.assertTrue(admission.exists())
            self.assertTrue(execution.exists())
            self.assertEqual(result["runtime_projection_state"], "VERIFIED")
            self.assertEqual(result["runtime_reconciliation"]["execution_id"], result["instance_id"])
            reconciliation_receipt = root / result["runtime_reconciliation"]["receipt_path"].removeprefix(str(root) + "/")
            self.assertTrue(reconciliation_receipt.exists())
            receipt = json.loads(reconciliation_receipt.read_text(encoding="utf-8"))
            self.assertEqual(receipt["transaction_id"], result["instance_id"])
            self.assertEqual(receipt["new_lifecycle_state"], "DISPATCHED_RUNTIME_VERIFIED")
            self.assertEqual(receipt["records_verified"], [str(admission), str(execution)])

    def test_replayed_dispatch_repairs_missing_derived_projections_without_resubmission(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            runtime = self._runtime(root / "stage1", executor=automatic_executor(ROOT, registry_path=self._registry(root)))
            first = runtime.submit_development(FIXTURE)
            admission = root / "mission-admissions" / f"{first['receipts']['admission']['admission_id']}.json"
            execution = root / "mission-executions" / f"{first['instance_id']}.json"
            admission.unlink()
            execution.unlink()
            replay = runtime.submit_development(FIXTURE)
            self.assertTrue(replay["idempotent_replay"])
            self.assertEqual(replay["instance_id"], first["instance_id"])
            self.assertTrue(admission.exists())
            self.assertTrue(execution.exists())
            self.assertEqual(replay["receipts"], first["receipts"])

    def test_projection_persistence_failure_blocks_submission_before_success(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            runtime = self._runtime(root / "stage1", executor=automatic_executor(ROOT, registry_path=self._registry(root)))
            import scripts.lib.emp.runtime_reconciliation as reconciliation_module
            original = reconciliation_module.reconcile

            def fail_reconciliation(*_args, **_kwargs):
                raise ValueError("injected projection persistence failure")

            reconciliation_module.reconcile = fail_reconciliation
            try:
                result = runtime.submit_development(FIXTURE)
            finally:
                reconciliation_module.reconcile = original
            self.assertEqual(result["state"], "BLOCKED")
            self.assertEqual(result["pending_phase"], "EXECUTION_PERSISTED")
            self.assertEqual(result["failure"]["classification"], "RUNTIME_PROJECTION_PERSISTENCE_FAILURE")
            self.assertFalse((root / "mission-admissions").exists())
            self.assertFalse((root / "mission-executions").exists())

    def test_all_transaction_identifiers_resolve_same_record(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            runtime = self._runtime(root / "stage1")
            result = runtime.submit_development(FIXTURE)
            identifiers = [result["instance_id"], result["mission_id"], result["wop_id"],
                           result["package_digest"], result["receipts"]["validation"]["source_digest"],
                           result["registration"]["registration_id"]]
            for identifier in identifiers:
                self.assertEqual(runtime.resolve_transaction(identifier)["instance_id"], result["instance_id"])

    def test_duplicate_submission_is_idempotent(self):
        with tempfile.TemporaryDirectory() as temp:
            runtime = self._runtime(Path(temp) / "stage1")
            first = runtime.submit_development(FIXTURE)
            second = runtime.submit_development(FIXTURE)
            self.assertEqual(first["instance_id"], second["instance_id"])
            self.assertTrue(second["idempotent_replay"])

    def test_provider_output_cannot_advance_without_receipts(self):
        with tempfile.TemporaryDirectory() as temp:
            def forged(_record):
                return {"dispatch_receipt": {"receipt_id": "forged", "state": "EXECUTING"}}
            result = self._runtime(Path(temp) / "stage1", executor=forged).submit_development(FIXTURE)
            self.assertEqual(result["state"], "AWAITING_EXECUTION_DISPATCH")
            self.assertNotIn("dispatch", result["receipts"])

    def test_authority_conflict_blocks_before_dispatch(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            registry = self._registry(root)
            runtime = self._runtime(root / "stage1", executor=automatic_executor(ROOT, registry_path=registry))
            # A conflicting source authority is rejected before any runtime record is created.
            conflicting = root / "conflicting"
            import shutil
            shutil.copytree(FIXTURE, conflicting)
            mission = conflicting / "mission.yaml"
            mission.write_text(mission.read_text(encoding="utf-8") + "authority: Foreign Authority\n", encoding="utf-8")
            with self.assertRaises(Exception) as raised:
                runtime.submit_development(conflicting)
            self.assertEqual(getattr(raised.exception, "evidence", {}).get("reason_code"), "AUTHORITY_CHAIN_INTEGRITY_FAILURE")
            self.assertFalse((root / "stage1").exists())

    def test_receiptless_dispatch_rolls_back_and_preserves_evidence(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            runtime = self._runtime(root / "stage1", executor=automatic_executor(ROOT, registry_path=self._registry(root)))
            result = runtime.submit_development(FIXTURE)
            forged = copy.deepcopy(result)
            forged["receipts"]["dispatch"].pop("authority_snapshot_digest")
            runtime.store.save(forged)
            resumed = runtime.resume_transaction(result["instance_id"])
            self.assertEqual(resumed["state"], "AWAITING_EXECUTION_DISPATCH")
            self.assertEqual(resumed["pending_phase"], "DISPATCHED")
            self.assertTrue(any(item.get("type") == "receiptless-dispatch-recovery" for item in resumed.get("evidence", [])))

    def test_digest_projection_and_state_digest_are_deterministic(self):
        with tempfile.TemporaryDirectory() as temp:
            runtime = self._runtime(Path(temp) / "stage1")
            source_fixture = ROOT / "engineering/work-orders/WOP-ZDCL-02-ZEUS-PROVIDER-NEUTRAL-EXECUTION-CONTROL-001/ebeec97412e405e26b721c09"
            result = runtime.submit_development(source_fixture)
            self.assertEqual(result["receipts"]["packaging"]["source_digest"], result["source_digest"])
            self.assertNotEqual(result["source_digest"], result["package_digest"])
            first_digest = result["state_digest"]
            replay = runtime.submit_development(source_fixture)
            self.assertEqual(replay["state_digest"], first_digest)

    def test_recovery_does_not_invoke_execution_and_requires_new_snapshot(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            calls = []
            registry = self._registry(root)
            def executor(record):
                calls.append(record["authority_snapshot"]["authority_snapshot_id"])
                return automatic_executor(ROOT, registry_path=registry)(record)
            runtime = self._runtime(root / "stage1", executor=executor)
            result = runtime.submit_development(FIXTURE)
            original_snapshot = result["authority_snapshot"]["authority_snapshot_digest"]
            calls.clear()
            forged = copy.deepcopy(result)
            forged["receipts"]["dispatch"].pop("authority_snapshot_digest")
            runtime.store.save(forged)
            recovered = runtime.resume_transaction(result["instance_id"])
            self.assertEqual(recovered["state"], "AWAITING_EXECUTION_DISPATCH")
            self.assertEqual(calls, [])
            redispatched = runtime.resume_transaction(result["instance_id"])
            self.assertEqual(redispatched["state"], "DISPATCHED")
            self.assertTrue(calls)
            self.assertTrue(redispatched["authority_snapshot"]["authority_snapshot_digest"])
            self.assertNotEqual(redispatched["authority_snapshot"]["authority_snapshot_digest"], original_snapshot)

    def test_incomplete_provider_selection_and_launch_ack_are_not_authoritative(self):
        with tempfile.TemporaryDirectory() as temp:
            runtime = self._runtime(Path(temp) / "stage1")
            result = runtime.submit_development(FIXTURE)
            forged = copy.deepcopy(result)
            forged["state"] = "DISPATCHED"
            forged["phases"] = forged["phases"] + ["DISPATCHED"]
            forged["receipts"]["dispatch"] = {"agent_id": "forged"}
            runtime.store.save(forged)
            recovered = runtime.resume_transaction(result["instance_id"])
            self.assertEqual(recovered["state"], "AWAITING_EXECUTION_DISPATCH")
            execution = copy.deepcopy(recovered)
            execution["state"] = "EXECUTING"
            execution["phases"] = execution["phases"] + ["EXECUTING"]
            execution["receipts"]["execution"] = {"execution_id": "without-ack"}
            runtime.store.save(execution)
            with self.assertRaises(Exception):
                runtime.store.find(result["instance_id"])


if __name__ == "__main__":
    unittest.main()
