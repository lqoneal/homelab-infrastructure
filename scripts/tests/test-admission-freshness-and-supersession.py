#!/usr/bin/env python3
"""BETA-03E admission freshness and supersession qualification."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.lib.emp.mission_admission_runtime import (  # noqa: E402
    AdmissionStateStore,
    MissionAdmissionRuntime,
)
from scripts.lib.emp.mission_execution_runtime import (  # noqa: E402
    ExecutionStateStore,
    MissionExecutionError,
    MissionExecutionRuntime,
)


OLD_ADMISSION = "MISSION-ADMISSION-b014c252-901b-5166-9722-8964b341da12"
OLD_EXECUTION = "MISSION-EXECUTION-8c444488-9ee3-5e03-949f-dc750a0b918c"
SUBMISSION = "ZEUS-MISSION-06a7fcf8-a8b3-54bd-8469-0f05f9d41e57"
AT = datetime(2026, 8, 1, 22, 0, tzinfo=timezone.utc)


class AdmissionFreshnessTests(unittest.TestCase):
    def current_baseline(self):
        return subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip()

    def request(self):
        return {
            "mode": "qualification",
            "mission_id": "ZDCL-01",
            "repository": str(ROOT),
            "submitter_identity": "loneal",
            "principal_id": "loneal",
            "submission_id": SUBMISSION,
        }

    def test_new_admission_binds_submission_and_current_baseline(self):
        with tempfile.TemporaryDirectory() as directory:
            store = AdmissionStateStore(Path(directory) / "admissions")
            state = MissionAdmissionRuntime(ROOT, store).start(self.request(), at=AT)
            self.assertNotEqual(state["admission_id"], OLD_ADMISSION)
            self.assertEqual(state["request"]["submission_id"], SUBMISSION)
            self.assertEqual(state["request"]["repository_baseline"], self.current_baseline())
            binding = state["artifacts"]["authority_context"]["admission"]
            self.assertEqual(binding["submission_id"], SUBMISSION)
            self.assertEqual(binding["repository"]["baseline_commit"], state["request"]["repository_baseline"])

    def test_replacement_records_lineage_without_mutating_history(self):
        with tempfile.TemporaryDirectory() as directory:
            admission_dir = Path(directory) / "admissions"
            admission_dir.mkdir()
            old_path = ROOT / ".zeus/runtime/mission-admissions" / f"{OLD_ADMISSION}.json"
            shutil.copy2(old_path, admission_dir / old_path.name)
            state = MissionAdmissionRuntime(ROOT, AdmissionStateStore(admission_dir)).start(self.request(), at=AT)
            lineage = state["supersession"]
            self.assertEqual(lineage["prior_admission_id"], OLD_ADMISSION)
            self.assertEqual(lineage["cancelled_execution_id"], OLD_EXECUTION)
            self.assertEqual(lineage["previous_baseline"], "bf47128d100a22cd08be9f112c45b04125b6945b")
            self.assertEqual(lineage["replacement_baseline"], self.current_baseline())
            self.assertEqual(json.loads(old_path.read_text())["state_digest"], json.loads((admission_dir / old_path.name).read_text())["state_digest"])

    def test_stale_admission_cannot_start_execution(self):
        with tempfile.TemporaryDirectory() as directory:
            execution_store = ExecutionStateStore(Path(directory) / "executions")
            runtime = MissionExecutionRuntime(
                ROOT,
                execution_store,
                AdmissionStateStore(ROOT / ".zeus/runtime/mission-admissions"),
            )
            with self.assertRaisesRegex(MissionExecutionError, "stale admission"):
                runtime.start(OLD_ADMISSION, at=AT)
            self.assertEqual(list((Path(directory) / "executions").glob("*.json")), [])


if __name__ == "__main__":
    unittest.main()
