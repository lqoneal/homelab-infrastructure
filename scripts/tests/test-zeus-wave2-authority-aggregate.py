#!/usr/bin/env python3
"""GAP-004/GAP-007 proof for authority adaptation and mission aggregation."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "engineering/work-orders/WOP-ZEUS-EXECUTION-LIFECYCLE-COMPLETION-001/source-wop.md"
MISSION = "ZEUS-EXECUTION-LIFECYCLE-COMPLETION-01"
WOP = "WOP-ZEUS-EXECUTION-LIFECYCLE-COMPLETION-001"
sys.path.insert(0, str(ROOT))

from scripts.lib.emp.canonical_authority_receipt import (  # noqa: E402
    AuthorityReceiptError,
    _digest,
    normalize,
    resolve,
)
from scripts.lib.emp.canonical_mission_aggregate import aggregate  # noqa: E402
from scripts.lib.emp.wop_canonicalization import canonicalize  # noqa: E402


class Wave2AuthorityAggregateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.holder = Path(self.enterContext(tempfile.TemporaryDirectory(prefix="zeus-wave2-")))
        self.source = self.holder / "source-wop.md"
        shutil.copy2(SOURCE, self.source)
        canonicalize(self.source, ROOT)
        self.runtime = self.holder / "runtime"
        env = {**os.environ, "ZEUS_RUNTIME_ROOT": str(self.runtime), "ZEUS_NO_INTRO": "1", "PYTHONDONTWRITEBYTECODE": "1"}
        result = subprocess.run([str(ROOT / "scripts/zeus"), "submit", str(self.source), "--repository", str(ROOT), "--json"],
                                cwd=ROOT, env=env, text=True, capture_output=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.submission_id = json.loads(result.stdout)["submission_id"]

    @staticmethod
    def _write(runtime: Path, directory: str, name: str, value: dict) -> Path:
        path = runtime / directory / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        return path

    def _aggregate(self) -> dict:
        return aggregate(ROOT, MISSION, runtime_root=self.runtime)

    def test_p2_uses_canonical_authority_and_pre_admission_aggregate_is_truthful(self) -> None:
        before = {str(path.relative_to(self.runtime)): hashlib.sha256(path.read_bytes()).hexdigest()
                  for path in self.runtime.rglob("*") if path.is_file()}
        value = self._aggregate()
        self.assertEqual(value["result"], "PASS")
        self.assertEqual(value["authority"]["classification"], "CANONICAL")
        self.assertEqual(value["authority"]["governance_authority"], "operator-submitted WOP")
        self.assertEqual(value["lifecycle_state"], "ADMISSION_REQUESTED")
        self.assertEqual(value["next_authorized_action"], "EVALUATE_MISSION_ADMISSION")
        for family in ("provider", "provider_session", "execution", "process", "monitoring", "evidence"):
            self.assertEqual(value["aggregate"][family]["status"], "NOT_STARTED")
        self.assertEqual(value["aggregate"]["current_execution_readiness"], "NOT_AVAILABLE")
        self.assertEqual(value["aggregate"]["historical_session_execution_leak"], "NONE")
        self.assertEqual(before, {str(path.relative_to(self.runtime)): hashlib.sha256(path.read_bytes()).hexdigest()
                                  for path in self.runtime.rglob("*") if path.is_file()})

    def test_representative_subordinate_records_are_exposed_without_advancing_lifecycle(self) -> None:
        common = {"mission_id": MISSION, "wop_id": WOP,
                  "submission_id": self.submission_id, "provider_id": "provider-test-01"}
        self._write(self.runtime, "provider-selection", "provider.json", {**common, "provider_selection_id": "PROVIDER-SELECTION-01"})
        self._write(self.runtime, "provider-sessions", "session.json", {**common, "provider_session_id": "PROVIDER-SESSION-01", "dispatch_id": "DISPATCH-01"})
        self._write(self.runtime, "execution-monitoring", "monitor.json", {"mission_id": MISSION, "execution_id": "EXECUTION-01", "execution_monitoring_active": False})
        value = self._aggregate()
        self.assertEqual(value["result"], "PASS")
        self.assertEqual(value["lifecycle_state"], "ADMISSION_REQUESTED")
        self.assertEqual(value["aggregate"]["provider"]["identity"], "provider-test-01")
        self.assertEqual(value["aggregate"]["provider_session"]["identity"], "PROVIDER-SESSION-01")
        self.assertEqual(value["aggregate"]["monitoring"]["status"], "UNAVAILABLE_UNTIL_EXECUTION_START")
        self.assertEqual(value["next_authorized_action"], "EVALUATE_MISSION_ADMISSION")

    def test_stale_binding_fails_closed(self) -> None:
        self._write(self.runtime, "provider-sessions", "stale.json", {
            "mission_id": MISSION, "wop_id": "OTHER-WOP", "provider_session_id": "SESSION-STALE"})
        value = self._aggregate()
        self.assertEqual(value["result"], "FAIL")
        self.assertEqual(value["blockers"][0]["code"], "MISSION_AGGREGATE_IDENTITY_MISMATCH")

    def test_historical_stopped_session_cannot_expose_execution_readiness(self) -> None:
        self._write(self.runtime, "codex-sessions", "stopped.json", {
            "mission_id": MISSION, "session_id": "CODEX-OLD", "state": "STOPPED", "provider_pid": 999999})
        value = self._aggregate()
        self.assertEqual(value["result"], "PASS")
        self.assertEqual(value["aggregate"]["current_execution_readiness"], "NOT_AVAILABLE")
        self.assertEqual(value["aggregate"]["process"]["status"], "UNAVAILABLE_UNTIL_EXECUTION_START")
        self.assertEqual(value["aggregate"]["historical_session_execution_leak"], "NONE")
        self.assertTrue(value["aggregate"]["historical_sessions"])

    def test_conflicting_session_binding_fails_closed(self) -> None:
        common = {"mission_id": MISSION, "wop_id": WOP, "submission_id": self.submission_id,
                  "provider_id": "provider-test-01", "dispatch_id": "DISPATCH-01"}
        self._write(self.runtime, "provider-sessions", "one.json", {**common, "provider_session_id": "SESSION-ONE"})
        self._write(self.runtime, "provider-sessions", "two.json", {**common, "provider_session_id": "SESSION-TWO"})
        value = self._aggregate()
        self.assertEqual(value["result"], "FAIL")
        self.assertEqual(value["blockers"][0]["code"], "MISSION_AGGREGATE_IDENTITY_AMBIGUOUS")

    def test_unrelated_records_are_ignored(self) -> None:
        self._write(self.runtime, "provider-sessions", "unrelated.json", {
            "mission_id": "UNRELATED-MISSION-01", "provider_session_id": "UNRELATED-SESSION"})
        value = self._aggregate()
        self.assertEqual(value["result"], "PASS")
        self.assertEqual(value["aggregate"]["provider_session"]["record_count"], 0)

    def test_missing_authoritative_receipt_fails_closed(self) -> None:
        next((self.runtime / "submissions/receipts").glob("*.json")).unlink()
        value = self._aggregate()
        self.assertEqual(value["result"], "FAIL")
        self.assertIn(value["blockers"][0]["code"], {"MISSION_NOT_FOUND", "CANONICAL_SUBMISSION_MISSING", "CANONICAL_LIFECYCLE_UNRESOLVED"})

    def test_legacy_receipt_is_explicitly_adapted(self) -> None:
        snapshot = {"authority_snapshot_id": "SNAPSHOT-01", "wop_id": WOP,
                    "governance_authority": "operator-submitted WOP", "wop_authority": "operator-submitted WOP",
                    "approval_state": "SUBMISSION_AUTHORITY_ESTABLISHED", "resolution": "AUTHORIZED"}
        snapshot["authority_snapshot_digest"] = _digest(snapshot)
        value = normalize({"mission_id": "LEGACY-01", "wop_id": WOP, "receipts": {"authorization": {}},
                           "authority_snapshot": snapshot}, source="stage1")
        self.assertEqual(value["classification"], "STAGE1_LEGACY")
        self.assertEqual(value["resolution"], "COMPATIBILITY_ADAPTER")

    def test_contradictory_authority_receipts_fail_closed(self) -> None:
        canonical = {"mission_id": MISSION, "wop_id": WOP, "submission_id": "SUBMISSION-TEST",
                     "authority": {"governance_authority": "operator-submitted WOP", "wop_authority": "operator-submitted WOP",
                                   "generic_second_approval_required": False, "approval_state": "NOT_REQUIRED_UNLESS_DECLARED_IN_WOP"}}
        canonical["receipt_digest"] = _digest(canonical)
        snapshot = {"authority_snapshot_id": "SNAPSHOT-02", "governance_authority": "OTHER-AUTHORITY",
                    "wop_authority": "OTHER-AUTHORITY", "approval_state": "APPROVED", "resolution": "AUTHORIZED"}
        snapshot["authority_snapshot_digest"] = _digest(snapshot)
        with self.assertRaises(AuthorityReceiptError) as error:
            resolve([("canonical", canonical), ("legacy", {"mission_id": MISSION, "wop_id": WOP,
                                                             "authority_snapshot": snapshot, "receipts": {"authorization": {}}})])
        self.assertEqual(error.exception.code, "AUTHORITY_RECEIPT_CONTRADICTION")

    def test_missing_authority_fails_closed(self) -> None:
        with self.assertRaises(AuthorityReceiptError) as error:
            normalize({"mission_id": MISSION}, source="missing")
        self.assertEqual(error.exception.code, "AUTHORITY_RECEIPT_MISSING")


if __name__ == "__main__":
    unittest.main()
