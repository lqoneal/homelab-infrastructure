#!/usr/bin/env python3
"""Disposable qualification for the canonical Stage 1 runtime reconciler."""

from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from scripts.lib.emp.runtime_reconciliation import RuntimeReconciliationError, _atomic_install
from scripts.lib.emp.stage1_execution_resolution import resolve


ROOT = Path(__file__).resolve().parents[2]
SOURCE_RUNTIME = Path.home() / ".local/state/zeus-runtime/homelab-6bd83f9079d6fc57"
TRANSACTION = "ZEUS-DEVELOPMENT-5afc9959-aa8d-5dba-86b6-08a8721e1806"
ADMISSION = "EMM-DEV-ADMISSION-21fbb4d8027dadc133d0cdab"


class RuntimeReconciliationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.runtime = Path(self.temp.name)
        for directory in ("stage1/missions", "mission-admissions", "mission-executions", "native-sessions", "evidence"):
            (self.runtime / directory).mkdir(parents=True)
        shutil.copy2(SOURCE_RUNTIME / "stage1/missions" / f"{TRANSACTION}.json",
                     self.runtime / "stage1/missions" / f"{TRANSACTION}.json")

    def tearDown(self):
        self.temp.cleanup()

    def resolve(self, **extra):
        options = {"identifier": TRANSACTION, "execution_id": TRANSACTION,
                   "hydrate": True, "command": "status"}
        options.update(extra)
        return resolve(ROOT, self.runtime / "stage1", self.runtime / "mission-admissions",
                       self.runtime / "mission-executions", **options)

    def test_stage1_only_creates_projections_and_receipt(self):
        result = self.resolve()
        self.assertTrue(result["hydrated"])
        self.assertEqual(result["admission_id"], ADMISSION)
        self.assertEqual(result["execution_id"], TRANSACTION)
        self.assertEqual(len(list((self.runtime / "mission-admissions").glob("*.json"))), 1)
        self.assertEqual(len(list((self.runtime / "mission-executions").glob("*.json"))), 1)
        self.assertEqual(len(list((self.runtime / "evidence/reconciliation-receipts").glob("*.json"))), 1)

    def test_replay_is_idempotent(self):
        first = self.resolve()
        second = self.resolve()
        self.assertFalse(second["hydrated"])
        self.assertTrue(second["reconciliation"]["replayed"])
        self.assertEqual(first["reconciliation"]["reconciliation_id"], second["reconciliation"]["reconciliation_id"])

    def test_admission_only_repairs_execution(self):
        first = self.resolve()
        execution = self.runtime / "mission-executions" / f"{TRANSACTION}.json"
        execution.unlink()
        result = self.resolve()
        self.assertTrue(result["hydrated"])
        self.assertTrue(execution.exists())
        self.assertEqual(result["admission_id"], first["admission_id"])

    def test_corrupt_projection_fails_closed(self):
        self.resolve()
        path = self.runtime / "mission-executions" / f"{TRANSACTION}.json"
        value = json.loads(path.read_text())
        value["stage1_package_digest"] = "tampered"
        path.write_text(json.dumps(value))
        with self.assertRaises(RuntimeReconciliationError):
            self.resolve()

    def test_requested_registration_or_admission_identity_fails_with_operands(self):
        with self.assertRaisesRegex(RuntimeReconciliationError, "canonical_stage1_instance_id"):
            self.resolve(execution_id="EMM-DEV-21fbb4d8027dadc133d0cdab")

    def test_derived_execution_identity_is_repaired_from_stage1_instance(self):
        self.resolve()
        path = self.runtime / "mission-executions" / f"{TRANSACTION}.json"
        value = json.loads(path.read_text())
        value["execution_id"] = "ZEUS-DEVELOPMENT-DERIVED-STALE-001"
        material = dict(value)
        material.pop("state_digest", None)
        from scripts.lib.emp.stage1_execution_resolution import _digest
        value["state_digest"] = _digest(material)
        path.write_text(json.dumps(value))
        result = self.resolve()
        self.assertEqual(result["execution_id"], TRANSACTION)
        repaired = json.loads(path.read_text())
        self.assertEqual(repaired["execution_id"], TRANSACTION)
        self.assertIn("STALE_EXECUTION_PROJECTION", result["reconciliation"]["classification"])

    def test_atomic_install_rolls_back_on_replace_failure(self):
        first = self.runtime / "a.json"
        second = self.runtime / "b.json"
        first.write_text("old-a")
        second.write_text("old-b")
        import scripts.lib.emp.runtime_reconciliation as module
        original = module.os.replace
        calls = {"count": 0}
        def fail_once(source, target):
            calls["count"] += 1
            if calls["count"] == 3:
                raise OSError("injected persistence failure")
            return original(source, target)
        module.os.replace = fail_once
        try:
            with self.assertRaises(RuntimeReconciliationError):
                _atomic_install([(first, {"value": "new-a"}), (second, {"value": "new-b"})])
        finally:
            module.os.replace = original
        self.assertEqual(first.read_text(), "old-a")
        self.assertEqual(second.read_text(), "old-b")


if __name__ == "__main__":
    unittest.main()
