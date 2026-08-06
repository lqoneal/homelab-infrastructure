"""Disposable-runtime coverage for the P5-G6 reconciliation controller."""

from __future__ import annotations

import json
import subprocess
import tempfile
import time
import unittest
from pathlib import Path

from scripts.lib.emp import codex_reconciliation
from scripts.lib.emp.production_execution import digest


ROOT = Path(__file__).resolve().parents[2]


class ReconciliationTests(unittest.TestCase):
    def _record(self, runtime: Path, process: subprocess.Popen[bytes], *, state: str = "STOPPED") -> Path:
        record = runtime / "codex-interactive-sessions" / "CODEX-SESSION-TEST.json"
        record.parent.mkdir(parents=True)
        identity = codex_reconciliation.process_identity(process.pid)
        value = {"schema_version": 1, "record_type": "AUTHORITATIVE_INTERACTIVE_SESSION",
                 "contract": {"id": "ZEUS-P5-G6-CODEX-INTERACTIVE", "version": "1"},
                 "session_id": "CODEX-SESSION-TEST", "mission_id": "MISSION-TEST",
                 "state": state, "pid": process.pid, "pid_identity": identity,
                 "repository": str(ROOT), "repository_id": "homelab-test",
                 "repository_identity": "git@example/homelab", "path": str(record)}
        value["state_digest"] = digest({key: item for key, item in value.items() if key != "state_digest"})
        record.write_text(json.dumps(value), encoding="utf-8")
        return record

    def test_dry_run_is_read_only_and_classifies_live_terminal_process(self):
        with tempfile.TemporaryDirectory(prefix="p5g6-runtime-test-") as temporary:
            runtime = Path(temporary)
            process = subprocess.Popen(["sleep", "30"])
            try:
                self._record(runtime, process)
                result = codex_reconciliation.reconcile(ROOT, runtime_root=runtime)
                self.assertTrue(result["read_only"])
                self.assertEqual(result["reconciliation"]["entries"][0]["disposition"], "ORPHAN_LIVE_PROCESS")
                self.assertTrue(process.poll() is None)
                self.assertFalse(list((runtime / codex_reconciliation.RECEIPT_DIR).glob("*.json")))
            finally:
                process.terminate(); process.wait(timeout=3)

    def test_approved_reconciliation_terminates_with_receipt_and_replays(self):
        with tempfile.TemporaryDirectory(prefix="p5g6-runtime-test-") as temporary:
            runtime = Path(temporary)
            process = subprocess.Popen(["sleep", "30"])
            self._record(runtime, process)
            result = codex_reconciliation.reconcile(ROOT, runtime_root=runtime, approve=True)
            self.assertEqual(result["reconciliation"]["termination_receipts"][0]["result"], "PASS")
            self.assertIsNotNone(process.poll())
            replay = codex_reconciliation.reconcile(ROOT, runtime_root=runtime, approve=True)
            self.assertTrue(replay["replayed"])
            self.assertEqual(replay["reconciliation"]["reconciliation_id"], result["reconciliation"]["reconciliation_id"])

    def test_unverified_live_process_is_never_mutation_eligible(self):
        with tempfile.TemporaryDirectory(prefix="p5g6-runtime-test-") as temporary:
            runtime = Path(temporary)
            process = subprocess.Popen(["sleep", "30"])
            try:
                record = self._record(runtime, process)
                value = json.loads(record.read_text(encoding="utf-8"))
                value.pop("pid_identity")
                value["state_digest"] = digest({key: item for key, item in value.items() if key != "state_digest"})
                record.write_text(json.dumps(value), encoding="utf-8")
                result = codex_reconciliation.reconcile(ROOT, runtime_root=runtime, approve=True)
                entry = result["reconciliation"]["entries"][0]
                self.assertEqual(entry["disposition"], "ORPHAN_IDENTITY_UNVERIFIED")
                self.assertTrue(process.poll() is None)
            finally:
                process.terminate(); process.wait(timeout=3)

    def test_duplicate_mission_records_report_cardinality_conflict(self):
        with tempfile.TemporaryDirectory(prefix="p5g6-runtime-test-") as temporary:
            runtime = Path(temporary)
            directory = runtime / "codex-interactive-sessions"
            directory.mkdir(parents=True)
            for suffix in ("A", "B"):
                value = {"schema_version": 1, "record_type": "AUTHORITATIVE_INTERACTIVE_SESSION",
                         "contract": {"id": "ZEUS-P5-G6-CODEX-INTERACTIVE", "version": "1"},
                         "session_id": f"CODEX-SESSION-{suffix}", "mission_id": "MISSION-DUP",
                         "state": "STOPPED", "pid": None, "repository": str(ROOT),
                         "repository_id": "homelab-test", "repository_identity": "git@example/homelab"}
                value["state_digest"] = digest(value)
                (directory / f"{suffix}.json").write_text(json.dumps(value), encoding="utf-8")
            result = codex_reconciliation.reconcile(ROOT, runtime_root=runtime)
            self.assertEqual(result["reconciliation"]["cardinality"]["MISSION-DUP"]["observed"], 2)
            self.assertTrue(all(item["disposition"] == "ORPHAN_CARDINALITY_CONFLICT"
                                for item in result["reconciliation"]["entries"]))


if __name__ == "__main__":
    unittest.main()
