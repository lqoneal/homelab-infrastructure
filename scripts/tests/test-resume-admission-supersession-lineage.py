#!/usr/bin/env python3
"""Disposable qualification for read-only resume admission lineage."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.lib.emp.admission_supersession import (  # noqa: E402
    AdmissionSupersessionError,
    resolve_for_resume,
)
from scripts.lib.emp.mission_admission_runtime import AdmissionStateStore  # noqa: E402
from scripts.lib.emp.stage1_execution_resolution import resolve  # noqa: E402
from scripts.lib.emp.stage1_runtime import Stage1Store  # noqa: E402


class ResumeAdmissionLineageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        base = Path(self.temp.name)
        self.repo = base / "repo"
        self.repo.mkdir()
        run = lambda *args: subprocess.run(args, cwd=self.repo, check=True, capture_output=True, text=True)
        run("git", "init", "-b", "main")
        run("git", "config", "user.email", "test@example.invalid")
        run("git", "config", "user.name", "Test")
        (self.repo / "README.md").write_text("admitted\n")
        run("git", "add", "README.md")
        run("git", "commit", "-m", "admitted baseline")
        self.old = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=self.repo, text=True).strip()
        (self.repo / "scripts").mkdir()
        (self.repo / "scripts" / "zeus").write_text("published corrective\n")
        run("git", "add", "scripts/zeus")
        run("git", "commit", "-m", "governed publication")
        self.current = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=self.repo, text=True).strip()
        run("git", "update-ref", "refs/remotes/origin/main", self.current)

        self.base = base
        self.admissions = base / "admissions"
        self.executions = base / "executions"
        self.stage1 = base / "stage1"
        self.predecessor_id = "EMM-DEV-ADMISSION-PREDECESSOR"
        self.successor_id = "EMM-DEV-ADMISSION-SUCCESSOR"
        self.transaction_id = "ZEUS-DEVELOPMENT-TRANSACTION-001"
        wop = {"wop_id": "WOP-001", "mission_id": "MISSION-001", "submission_digest": "submission"}
        common = {
            "schema_version": 1, "runtime_version": "test", "status": "DECIDED",
            "stage1_identity": self.transaction_id, "transaction_id": self.transaction_id,
            "package_digest": "package", "source_digest": "source",
            "authority_snapshot_digest": "authority",
            "request": {"mode": "qualification", "mission_id": "MISSION-001",
                         "repository": str(self.repo), "submission_id": self.transaction_id},
            "artifacts": {"wop_result": {"wop": wop},
                          "admission_decision": {"admission_decision": "QUALIFICATION_ONLY"}},
        }
        predecessor = {**deepcopy(common), "admission_id": self.predecessor_id,
                       "admission_state": "SUPERSEDED", "superseded_by": self.successor_id}
        predecessor["request"]["repository_baseline"] = self.old
        predecessor["artifacts"]["repository_baseline"] = self.old
        successor = {**deepcopy(common), "admission_id": self.successor_id,
                     "admission_state": "ADMITTED", "supersedes": self.predecessor_id}
        successor["request"]["repository_baseline"] = self.current
        successor["artifacts"]["repository_baseline"] = self.current
        store = AdmissionStateStore(self.admissions)
        store.save(predecessor)
        store.save(successor)
        self.record = {
            "schema_version": 3, "lifecycle_integrity": "RECEIPT_BACKED_V1",
            "instance_id": self.transaction_id, "mission_id": "MISSION-001", "wop_id": "WOP-001",
            "state": "ADMITTED", "repository": str(self.repo), "execution_mode": "DEVELOPMENT",
            "package": str(base / "package"), "package_digest": "package", "source_digest": "source",
            "repository_baseline": self.old, "authority_snapshot": {"authority_snapshot_digest": "authority"},
            "phases": ["VALIDATED", "ADMITTED", "EXECUTING"],
            "receipts": {"validation": {"source_digest": "source"},
                         "admission": {"admission_id": self.predecessor_id},
                         "execution": {"execution_id": self.transaction_id}},
        }
        package = base / "package"
        package.mkdir()
        (package / "mission.yaml").write_text("mission_id: MISSION-001\nwop_id: WOP-001\n")
        Stage1Store(self.stage1).save(self.record)

    def tearDown(self):
        self.temp.cleanup()

    def test_successor_and_predecessor_alias_resolve_without_mutation(self):
        before = {path: path.read_bytes() for path in self.admissions.glob("*.json")}
        result = resolve(self.repo, self.stage1, self.admissions, self.executions,
                         admission_id=self.predecessor_id, execution_id=self.transaction_id)
        self.assertEqual(self.successor_id, result["admission_id"])
        self.assertEqual([self.predecessor_id, self.successor_id], result["admission_lineage"]["lineage"])
        direct = resolve_for_resume(self.repo, self.admissions, self.successor_id,
                                    stage1_transaction=self.record)
        self.assertEqual(self.successor_id, direct["admission_id"])
        self.assertEqual(before, {path: path.read_bytes() for path in self.admissions.glob("*.json")})

    def test_stale_terminal_chain_reconciles_atomically(self):
        run = lambda *args: subprocess.run(args, cwd=self.repo, check=True, capture_output=True, text=True)
        (self.repo / "scripts" / "zeus").write_text("second governed publication\n")
        run("git", "add", "scripts/zeus")
        run("git", "commit", "-m", "second governed publication")
        current = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=self.repo, text=True).strip()
        run("git", "update-ref", "refs/remotes/origin/main", current)
        result = resolve(self.repo, self.stage1, self.admissions, self.executions,
                         admission_id=self.predecessor_id, execution_id=self.transaction_id,
                         hydrate=True, require_lineage_environment=True)
        self.assertEqual(3, len(result["admission_lineage"]["lineage"]))
        terminal = result["admission_id"]
        replay = resolve(self.repo, self.stage1, self.admissions, self.executions,
                         admission_id=self.predecessor_id, execution_id=self.transaction_id,
                         hydrate=True, require_lineage_environment=True)
        self.assertEqual(terminal, replay["admission_id"])
        self.assertEqual(3, len(list(self.admissions.glob("*.json"))))

    def test_unrelated_and_broken_lineage_fail_closed(self):
        with self.assertRaises(AdmissionSupersessionError):
            resolve_for_resume(self.repo, self.admissions, "EMM-DEV-ADMISSION-OTHER",
                               stage1_transaction=self.record)
        store = AdmissionStateStore(self.admissions)
        broken = store.load(self.predecessor_id)
        broken["superseded_by"] = "EMM-DEV-ADMISSION-MISSING"
        store.save(broken)
        with self.assertRaises(AdmissionSupersessionError):
            resolve_for_resume(self.repo, self.admissions, self.predecessor_id,
                               stage1_transaction=self.record)

    def test_digest_mismatch_fails_closed(self):
        store = AdmissionStateStore(self.admissions)
        successor = store.load(self.successor_id)
        successor["source_digest"] = "different-source"
        store.save(successor)
        with self.assertRaises(AdmissionSupersessionError):
            resolve_for_resume(self.repo, self.admissions, self.successor_id,
                               stage1_transaction=self.record)

    def test_missing_generic_authority_uses_receipt_backed_stage1_binding(self):
        store = AdmissionStateStore(self.admissions)
        successor = store.load(self.successor_id)
        successor.pop("authority_snapshot_digest")
        store.save(successor)
        record = deepcopy(self.record)
        record.pop("authority_snapshot")
        record["receipts"]["authorization"] = {"authority_snapshot_digest": "authority"}
        result = resolve_for_resume(self.repo, self.admissions, self.successor_id,
                                    stage1_transaction=record)
        self.assertEqual(self.successor_id, result["admission_id"])

    def test_missing_canonical_authority_fails_closed(self):
        record = deepcopy(self.record)
        record.pop("authority_snapshot")
        with self.assertRaisesRegex(AdmissionSupersessionError, "authority snapshot digest is absent"):
            resolve_for_resume(self.repo, self.admissions, self.successor_id,
                               stage1_transaction=record)

    def test_conflicting_generic_authority_fails_closed(self):
        store = AdmissionStateStore(self.admissions)
        successor = store.load(self.successor_id)
        successor["authority_snapshot_digest"] = "different-authority"
        store.save(successor)
        with self.assertRaisesRegex(AdmissionSupersessionError, "authority snapshot digest differs"):
            resolve_for_resume(self.repo, self.admissions, self.successor_id,
                               stage1_transaction=self.record)

    def test_conflicting_authorization_receipt_fails_closed(self):
        record = deepcopy(self.record)
        record["receipts"]["authorization"] = {"authority_snapshot_digest": "different-authority"}
        with self.assertRaisesRegex(AdmissionSupersessionError, "differs within Stage 1"):
            resolve_for_resume(self.repo, self.admissions, self.successor_id,
                               stage1_transaction=record)

    def test_missing_generic_source_digest_uses_stage1_binding(self):
        store = AdmissionStateStore(self.admissions)
        successor = store.load(self.successor_id)
        successor.pop("source_digest")
        store.save(successor)
        result = resolve_for_resume(self.repo, self.admissions, self.successor_id,
                                    stage1_transaction=self.record)
        self.assertEqual(self.successor_id, result["admission_id"])

    def test_missing_canonical_source_digest_fails_closed(self):
        record = deepcopy(self.record)
        record.pop("source_digest")
        record["receipts"].pop("validation")
        with self.assertRaises(AdmissionSupersessionError):
            resolve_for_resume(self.repo, self.admissions, self.successor_id,
                               stage1_transaction=record)

    def test_stage1_receipt_and_transaction_source_conflict_fails_closed(self):
        record = deepcopy(self.record)
        record["source_digest"] = "different-source"
        with self.assertRaises(AdmissionSupersessionError):
            resolve_for_resume(self.repo, self.admissions, self.successor_id,
                               stage1_transaction=record)

    def test_projection_package_operand_mismatch_fails_closed(self):
        store = AdmissionStateStore(self.admissions)
        successor = store.load(self.successor_id)
        successor["stage1_package_digest"] = "package"
        successor["package_digest"] = "projection-digest"
        store.save(successor)
        with self.assertRaises(AdmissionSupersessionError):
            resolve_for_resume(self.repo, self.admissions, self.successor_id,
                               stage1_transaction=self.record)

    def test_stage1_package_operand_mismatch_fails_closed(self):
        record = deepcopy(self.record)
        record["package_digest"] = "modified-stage1-package"
        with self.assertRaises(AdmissionSupersessionError):
            resolve_for_resume(self.repo, self.admissions, self.successor_id,
                               stage1_transaction=record)

    def test_ambiguous_and_circular_lineage_fail_closed(self):
        store = AdmissionStateStore(self.admissions)
        duplicate = store.load(self.successor_id)
        duplicate["admission_id"] = "EMM-DEV-ADMISSION-DUPLICATE"
        store.save(duplicate)
        with self.assertRaises(AdmissionSupersessionError):
            resolve_for_resume(self.repo, self.admissions, self.predecessor_id,
                               stage1_transaction=self.record)
        (self.admissions / "EMM-DEV-ADMISSION-DUPLICATE.json").unlink()
        successor = store.load(self.successor_id)
        successor["superseded_by"] = self.predecessor_id
        store.save(successor)
        with self.assertRaises(AdmissionSupersessionError):
            resolve_for_resume(self.repo, self.admissions, self.predecessor_id,
                               stage1_transaction=self.record)


if __name__ == "__main__":
    unittest.main()
