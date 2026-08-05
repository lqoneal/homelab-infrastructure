#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.lib.emp.admission_supersession import (
    AdmissionSupersessionError, _successor_id, resolve_for_start,
)
from scripts.lib.emp.authority_resolution import digest
from scripts.lib.emp.mission_admission_runtime import AdmissionStateStore
from scripts.lib.emp.mission_execution_runtime import ExecutionStateStore


class AdmissionSupersessionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / "repo"
        self.root.mkdir()
        run = lambda *args: subprocess.run(args, cwd=self.root, check=True, capture_output=True, text=True)
        run("git", "init", "-b", "main")
        run("git", "config", "user.email", "test@example.invalid")
        run("git", "config", "user.name", "Test")
        (self.root / "README.md").write_text("old\n")
        run("git", "add", "README.md"); run("git", "commit", "-m", "admitted baseline")
        self.old = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=self.root, text=True).strip()
        (self.root / "scripts").mkdir()
        (self.root / "scripts" / "zeus").write_text("published corrective\n")
        run("git", "add", "scripts/zeus"); run("git", "commit", "-m", "governed publication")
        self.new = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=self.root, text=True).strip()
        run("git", "update-ref", "refs/remotes/origin/main", self.new)
        self.admissions = Path(self.temp.name) / "admissions"
        self.executions = Path(self.temp.name) / "executions"
        self.admission_id = "EMM-DEV-ADMISSION-PREDECESSOR"
        self.transaction = "ZEUS-DEVELOPMENT-TRANSACTION-001"
        self.admission = {
            "schema_version": 1, "runtime_version": "test", "admission_id": self.admission_id,
            "status": "DECIDED", "admission_state": "ADMITTED", "stage1_identity": self.transaction,
            "package_digest": "package", "source_digest": "source", "authority_snapshot_digest": "authority",
            "request": {"mode": "qualification", "mission_id": "MISSION-001", "repository": str(self.root),
                        "repository_baseline": self.old, "submission_id": self.transaction},
            "artifacts": {"repository_baseline": self.old,
                          "wop_result": {"wop": {"wop_id": "WOP-001", "mission_id": "MISSION-001", "submission_digest": "submission"}},
                          "admission_decision": {"admission_decision": "QUALIFICATION_ONLY"}},
        }
        AdmissionStateStore(self.admissions).save(self.admission)
        self.execution = {"execution_id": "ZEUS-DEVELOPMENT-EXECUTION-001", "admission_id": self.admission_id,
                          "repository": str(self.root), "repository_baseline": self.old, "state": "Pending",
                          "evidence": []}
        ExecutionStateStore(self.executions).save(self.execution)
        self.stage1 = {"instance_id": self.transaction, "package_digest": "package", "source_digest": "source",
                       "authority_snapshot": {"authority_snapshot_digest": "authority"}}

    def tearDown(self):
        self.temp.cleanup()

    def test_creates_successor_rebinds_execution_and_replays(self):
        result = resolve_for_start(self.root, self.admissions, self.executions, self.admission_id,
                                   stage1_transaction=self.stage1)
        successor_id = result["admission_id"]
        self.assertNotEqual(self.admission_id, successor_id)
        predecessor = AdmissionStateStore(self.admissions).load(self.admission_id)
        successor = AdmissionStateStore(self.admissions).load(successor_id)
        execution = ExecutionStateStore(self.executions).load(self.execution["execution_id"])
        self.assertEqual("SUPERSEDED", predecessor["status"])
        self.assertEqual(successor_id, predecessor["superseded_by"])
        self.assertEqual(self.admission_id, successor["supersedes"])
        self.assertEqual(successor_id, execution["admission_id"])
        replay = resolve_for_start(self.root, self.admissions, self.executions, self.admission_id,
                                   stage1_transaction=self.stage1)
        self.assertEqual(successor_id, replay["admission_id"])
        self.assertTrue(replay["replayed"])

    def test_dirty_and_unauthorized_transitions_fail_closed(self):
        (self.root / "dirty.txt").write_text("dirty\n")
        with self.assertRaises(AdmissionSupersessionError):
            resolve_for_start(self.root, self.admissions, self.executions, self.admission_id, stage1_transaction=self.stage1)
        (self.root / "dirty.txt").unlink()
        run = lambda *args: subprocess.run(args, cwd=self.root, check=True, capture_output=True, text=True)
        (self.root / "application.py").write_text("unauthorized\n")
        run("git", "add", "application.py"); run("git", "commit", "-m", "unauthorized implementation")
        current = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=self.root, text=True).strip()
        run("git", "update-ref", "refs/remotes/origin/main", current)
        with self.assertRaises(AdmissionSupersessionError):
            resolve_for_start(self.root, self.admissions, self.executions, self.admission_id, stage1_transaction=self.stage1)

    def test_conflicting_successor_fails_closed(self):
        successor_id = _successor_id(self.transaction, self.new, "package", "authority")
        conflicting = dict(self.admission)
        conflicting["admission_id"] = successor_id
        conflicting["supersedes"] = "OTHER"
        AdmissionStateStore(self.admissions).save(conflicting)
        with self.assertRaises(AdmissionSupersessionError):
            resolve_for_start(self.root, self.admissions, self.executions, self.admission_id, stage1_transaction=self.stage1)

    def test_unpublished_and_persistence_failure_fail_closed(self):
        with self.assertRaises(AdmissionSupersessionError):
            resolve_for_start(self.root, self.admissions, self.executions, self.admission_id,
                              stage1_transaction=self.stage1, published_baseline=self.old)
        with patch("scripts.lib.emp.admission_supersession._atomic_json_updates",
                   side_effect=AdmissionSupersessionError("injected persistence failure")):
            with self.assertRaises(AdmissionSupersessionError):
                resolve_for_start(self.root, self.admissions, self.executions, self.admission_id,
                                  stage1_transaction=self.stage1)
        predecessor = AdmissionStateStore(self.admissions).load(self.admission_id)
        self.assertEqual("ADMITTED", predecessor["admission_state"])
        self.assertEqual([self.admission_id + ".json"], [path.name for path in self.admissions.glob("*.json")])

    def test_stale_terminal_successor_creates_one_next_generation(self):
        first = resolve_for_start(self.root, self.admissions, self.executions, self.admission_id,
                                  stage1_transaction=self.stage1)
        first_id = first["admission_id"]
        run = lambda *args: subprocess.run(args, cwd=self.root, check=True, capture_output=True, text=True)
        (self.root / "scripts" / "zeus").write_text("second published corrective\n")
        run("git", "add", "scripts/zeus")
        run("git", "commit", "-m", "second governed publication")
        second_baseline = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=self.root, text=True).strip()
        run("git", "update-ref", "refs/remotes/origin/main", second_baseline)

        second = resolve_for_start(self.root, self.admissions, self.executions, self.admission_id,
                                   stage1_transaction=self.stage1)
        second_id = second["admission_id"]
        self.assertNotEqual(first_id, second_id)
        self.assertEqual(first_id, second["predecessor"]["admission_id"])
        self.assertEqual(second_id, AdmissionStateStore(self.admissions).load(first_id)["superseded_by"])
        self.assertEqual(second_id, resolve_for_start(
            self.root, self.admissions, self.executions, self.admission_id,
            stage1_transaction=self.stage1)["admission_id"])
        self.assertEqual(3, len(list(self.admissions.glob("*.json"))))


if __name__ == "__main__":
    unittest.main()
