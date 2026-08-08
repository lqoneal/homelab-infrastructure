#!/usr/bin/env python3
"""GAP-008 proof for canonical interruption, checkpoint, and resume recovery."""

from __future__ import annotations

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
BASELINE = "32796dffb43a47f4f9516a0936fe89f0bec0ee80"
SOURCE_DIGEST = "460a4baeca153b05ee2cb0ade4a70a03b8ff2b8ca9e17a9074d0e44137d392d9"

sys.path.insert(0, str(ROOT))

from scripts.lib.emp.canonical_mission_aggregate import aggregate  # noqa: E402
from scripts.lib.emp.canonical_recovery import (  # noqa: E402
    RecoveryError,
    create_checkpoint,
    record_interruption,
    request_resume,
    resolve,
)
from scripts.lib.emp.wop_canonicalization import canonicalize  # noqa: E402


class Gap008RecoveryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.holder = Path(self.enterContext(tempfile.TemporaryDirectory(prefix="zeus-wave3-recovery-")))
        self.runtime = self.holder / "runtime"
        self.lifecycle = {
            "result": "PASS", "mission_id": MISSION, "wop_id": WOP,
            "submission_id": "SUBMISSION-01", "source_digest": SOURCE_DIGEST,
            "repository_identity": str(ROOT), "repository_baseline": BASELINE,
            "execution_started": True, "lifecycle_state": "EXECUTING",
            "next_authorized_action": "MONITOR_EXECUTION",
        }

    def _checkpoint(self, *, status: str = "RESUMABLE", completed: list[str] | None = None,
                    current: list[str] | None = None) -> dict:
        return create_checkpoint(
            self.runtime, mission_id=MISSION, wop_id=WOP, execution_id="EXECUTION-01",
            provider_id="PROVIDER-01", session_id="SESSION-01", repository_identity=str(ROOT),
            repository_baseline=BASELINE, source_digest=SOURCE_DIGEST,
            lifecycle_position={"state": "EXECUTING", "gate": "P5-G6"},
            evidence_position={"last_receipt": "EVIDENCE-03", "sequence": 3},
            completed_work_units=completed or ["P5-G5"],
            current_work_units=current or ["P5-G6"], checkpoint_status=status,
        )

    def test_checkpoint_interruption_resume_is_deterministic_and_idempotent(self) -> None:
        first = self._checkpoint()
        replay = self._checkpoint()
        self.assertEqual(first["checkpoint"], replay["checkpoint"])
        self.assertEqual(replay["checkpoint_replay"], "IDEMPOTENT")
        interruption = record_interruption(
            self.runtime, checkpoint_id=first["checkpoint_id"], cause="heartbeat_expired",
            observed_at="2026-08-07T18:00:00Z", provider_process_state="DEAD",
            session_process_state="DEAD", heartbeat_expired=True,
            repository_mutation_state="MUTATED", lifecycle_receipt_state="ABSENT",
        )
        interruption_replay = record_interruption(
            self.runtime, checkpoint_id=first["checkpoint_id"], cause="heartbeat_expired",
            observed_at="2026-08-07T18:00:00Z", provider_process_state="DEAD",
            session_process_state="DEAD", heartbeat_expired=True,
            repository_mutation_state="MUTATED", lifecycle_receipt_state="ABSENT",
        )
        self.assertEqual(interruption["interruption"], interruption_replay["interruption"])
        self.assertEqual(interruption_replay["interruption_replay"], "IDEMPOTENT")
        self.assertEqual(interruption["interruption"]["mutation_receipt_order"], "MUTATION_BEFORE_RECEIPT")
        resolved = resolve(ROOT, MISSION, runtime_root=self.runtime, lifecycle=self.lifecycle)
        self.assertEqual(resolved["result"], "PASS")
        self.assertEqual(resolved["resume_eligibility"], "READY")
        self.assertEqual(resolved["resume_execution_id"], "EXECUTION-01")
        resumed = request_resume(self.runtime, resolved=resolved)
        replayed = request_resume(self.runtime, resolved=resolved)
        self.assertEqual(resumed["resume"], replayed["resume"])
        self.assertEqual(replayed["resume_replay"], "IDEMPOTENT")
        self.assertEqual(resumed["resume"]["resume_execution_id"], "EXECUTION-01")
        self.assertTrue(resumed["resume"]["duplicate_execution_prevented"])
        self.assertEqual(resumed["resume"]["completed_work_units_skipped"], ["P5-G5"])

    def test_missing_checkpoint_fails_closed_for_resume_but_is_truthful(self) -> None:
        value = resolve(ROOT, MISSION, runtime_root=self.runtime, lifecycle=self.lifecycle)
        self.assertEqual(value["result"], "PASS")
        self.assertEqual(value["recovery_state"], "NOT_STARTED")
        self.assertEqual(value["monitoring_state"], "NOT_STARTED")
        self.assertEqual(value["resume_eligibility"], "NOT_AVAILABLE")
        with self.assertRaises(RecoveryError) as error:
            request_resume(self.runtime, resolved=value)
        self.assertEqual(error.exception.code, "RESUME_NOT_ELIGIBLE")

    def test_multiple_checkpoints_fail_closed(self) -> None:
        self._checkpoint(completed=["P5-G5"], current=["P5-G6"])
        self._checkpoint(completed=["P5-G5", "P5-G6"], current=["P5-G7"])
        value = resolve(ROOT, MISSION, runtime_root=self.runtime, lifecycle=self.lifecycle)
        self.assertEqual(value["result"], "FAIL")
        self.assertEqual(value["blockers"][0]["code"], "CHECKPOINT_CARDINALITY_CONFLICT")

    def test_digest_identity_and_baseline_mismatch_fail_closed(self) -> None:
        created = self._checkpoint()
        path = self.runtime / "recovery-checkpoints" / f"{created['checkpoint_id']}.json"
        value = json.loads(path.read_text(encoding="utf-8"))
        value["repository_baseline"] = "other-baseline"
        path.write_text(json.dumps(value) + "\n", encoding="utf-8")
        result = resolve(ROOT, MISSION, runtime_root=self.runtime, lifecycle=self.lifecycle)
        self.assertEqual(result["result"], "FAIL")
        self.assertEqual(result["blockers"][0]["code"], "CHECKPOINT_DIGEST_MISMATCH")

    def test_source_digest_mismatch_with_valid_checkpoint_digest_fails_closed(self) -> None:
        created = create_checkpoint(
            self.runtime, mission_id=MISSION, wop_id=WOP, execution_id="EXECUTION-01",
            provider_id="PROVIDER-01", session_id="SESSION-01", repository_identity=str(ROOT),
            repository_baseline=BASELINE, source_digest="different-source",
            lifecycle_position={"state": "EXECUTING", "gate": "P5-G6"},
            evidence_position={"last_receipt": "EVIDENCE-03", "sequence": 3},
            completed_work_units=["P5-G5"], current_work_units=["P5-G6"],
        )
        result = resolve(ROOT, MISSION, runtime_root=self.runtime, lifecycle=self.lifecycle)
        self.assertEqual(result["result"], "FAIL")
        self.assertEqual(result["blockers"][0]["code"], "RECOVERY_IDENTITY_MISMATCH")
        self.assertEqual(created["checkpoint"]["source_digest"], "different-source")

    def test_stale_checkpoint_fails_closed(self) -> None:
        self._checkpoint(status="STALE")
        value = resolve(ROOT, MISSION, runtime_root=self.runtime, lifecycle=self.lifecycle)
        self.assertEqual(value["result"], "FAIL")
        self.assertEqual(value["blockers"][0]["code"], "CHECKPOINT_STALE")

    def test_historical_checkpoint_is_not_resumable(self) -> None:
        self._checkpoint(status="RECONCILED")
        value = resolve(ROOT, MISSION, runtime_root=self.runtime, lifecycle=self.lifecycle)
        self.assertEqual(value["result"], "PASS")
        self.assertEqual(value["recovery_state"], "HISTORICAL")
        self.assertEqual(value["resume_eligibility"], "NO")
        self.assertEqual(value["provider_session_liveness"], "HISTORICAL")

    def test_pre_admission_mission_aggregate_has_no_recovery_records_and_cli_is_read_only(self) -> None:
        source = self.holder / "source-wop.md"
        shutil.copy2(SOURCE, source)
        canonicalize(source, ROOT)
        environment = {**os.environ, "ZEUS_RUNTIME_ROOT": str(self.runtime), "ZEUS_NO_INTRO": "1",
                       "PYTHONDONTWRITEBYTECODE": "1"}
        submitted = subprocess.run(
            [str(ROOT / "scripts/zeus"), "submit", str(source), "--repository", str(ROOT), "--json"],
            cwd=ROOT, env=environment, text=True, capture_output=True, check=False,
        )
        self.assertEqual(submitted.returncode, 0, submitted.stderr)
        before = sorted(str(path.relative_to(self.runtime)) for path in self.runtime.rglob("*"))
        value = aggregate(ROOT, MISSION, runtime_root=self.runtime)
        self.assertEqual(value["result"], "PASS")
        self.assertEqual(value["recovery_state"], "NOT_STARTED")
        self.assertEqual(value["resume_eligibility"], "NOT_AVAILABLE")
        native = subprocess.run(
            [str(ROOT / "scripts/zeus"), "mission", "recovery", MISSION, "--json"],
            cwd=ROOT, env=environment, text=True, capture_output=True, check=False,
        )
        self.assertEqual(native.returncode, 0, native.stderr)
        self.assertEqual(json.loads(native.stdout)["recovery_state"], "NOT_STARTED")
        after = sorted(str(path.relative_to(self.runtime)) for path in self.runtime.rglob("*"))
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
