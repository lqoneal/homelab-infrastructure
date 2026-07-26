#!/usr/bin/env python3
"""ZEUS-P2-007 unified Mission Admission Runtime tests."""

from __future__ import annotations

import json
import os
import runpy
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.lib.emp.mission_admission_runtime import (  # noqa: E402
    STAGES,
    AdmissionStateStore,
    MissionAdmissionError,
    MissionAdmissionRuntime,
)

AT = datetime(2026, 7, 26, 23, 0, tzinfo=timezone.utc)


class MissionAdmissionRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.directory = Path(self.temporary.name)
        self.store = AdmissionStateStore(self.directory / "admissions")
        self.runtime = MissionAdmissionRuntime(ROOT, self.store)

    def tearDown(self):
        self.temporary.cleanup()

    def qualification_request(self):
        return {
            "mode": "qualification",
            "intent": "Qualify the unified mission admission pipeline",
            "mission_id": "ZEUS-P2-007-QUALIFICATION",
            "phase_id": "MISSION-ADMISSION",
            "repository": str(ROOT),
        }

    def test_qualification_traverses_complete_pipeline_without_eligibility(self):
        state = self.runtime.start(self.qualification_request(), at=AT)
        self.assertEqual(state["status"], "DECIDED")
        self.assertEqual(state["completed_stages"], list(STAGES))
        self.assertEqual(len(state["evidence"]), len(STAGES))
        self.assertEqual(
            state["artifacts"]["admission_decision"]["admission_decision"],
            "QUALIFICATION_ONLY",
        )
        self.assertFalse(
            state["artifacts"]["submission_eligibility"]["submission_eligible"]
        )
        self.assertTrue(
            state["artifacts"]["wop_result"]["wop"]["approval"]["reference"].startswith(
                "PLACEHOLDER-"
            )
        )
        self.assertFalse(
            state["artifacts"]["wop_result"]["automatically_submitted"]
        )

    def test_interruption_resume_and_replay_are_idempotent(self):
        interrupted = self.runtime.start(
            self.qualification_request(), at=AT, max_stages=3
        )
        self.assertEqual(interrupted["status"], "INTERRUPTED")
        self.assertEqual(interrupted["completed_stages"], list(STAGES[:3]))
        evidence = list(interrupted["evidence"])
        resumed = self.runtime.run(interrupted["admission_id"], at=AT)
        self.assertEqual(resumed["status"], "DECIDED")
        self.assertEqual(resumed["evidence"][:3], evidence)
        self.assertEqual(len(resumed["evidence"]), len(STAGES))
        replay = self.runtime.run(interrupted["admission_id"], at=AT)
        self.assertEqual(replay, resumed)

    def test_production_operational_path_fails_at_authority_gate(self):
        request = {
            "mode": "operational",
            "intent": "Prepare a supervised operational WOP",
            "mission_id": "EMP-MISSION-ZEUS-OPERATIONAL-ALPHA",
            "work_item_id": "EMP-WORK-ZEUS-P2-005-AUTHORITY-COMMISSIONING",
            "principal_id": "loneal",
            "repository": str(ROOT),
        }
        state = self.runtime.start(request, at=AT)
        self.assertEqual(state["status"], "BLOCKED")
        self.assertEqual(state["current_stage"], "AUTHORITY_RESOLUTION")
        self.assertEqual(
            state["failure"]["category"], "OPERATIONAL_READINESS_BLOCKER"
        )
        diagnostics = state["failure"]["diagnostics"]
        self.assertEqual(
            diagnostics["commissioning"]["commissioning_state"], "BLOCKED"
        )
        self.assertIn(
            "Lawrence O'Neal",
            diagnostics["owner_enrollment"]["missing_owners"],
        )
        self.assertNotIn("wop_result", state["artifacts"])

    def test_simulated_commissioned_source_reaches_admission_decision(self):
        fixture = runpy.run_path(
            str(ROOT / "scripts/tests/test-authority-resolution-runtime.py")
        )
        source = fixture["authoritative_state"]()
        source_path = self.directory / "authority.yaml"
        source_path.write_text(yaml.safe_dump(source, sort_keys=True))
        runtime = MissionAdmissionRuntime(
            ROOT,
            self.store,
            authority_state_path=source_path,
            commissioning_probe=lambda root: {"commissioning_state": "READY"},
            enrollment_probe=lambda root: {
                "trust_compilation_ready": True,
                "missing_owners": [],
            },
        )
        state = runtime.start(
            {
                "mode": "operational",
                "intent": "Prepare a supervised operational WOP",
                "mission_id": fixture["MISSION"],
                "work_item_id": fixture["WORK"],
                "principal_id": fixture["PRINCIPAL"],
                "repository": str(ROOT),
            },
            at=fixture["AT"],
        )
        self.assertEqual(state["status"], "DECIDED")
        decision = state["artifacts"]["admission_decision"]
        self.assertEqual(decision["admission_decision"], "ACCEPTED")
        self.assertTrue(decision["submission_eligible"])
        self.assertFalse(decision["automatically_submitted"])
        self.assertFalse(decision["dispatch_permitted"])

    def test_repository_mismatch_and_state_corruption_fail_closed(self):
        request = self.qualification_request()
        request["repository"] = str(self.directory)
        state = self.runtime.start(request, at=AT)
        self.assertEqual(state["status"], "BLOCKED")
        self.assertEqual(state["failure"]["category"], "REPOSITORY_FAILURE")

        good = self.runtime.start(self.qualification_request(), at=AT, max_stages=1)
        path = self.store.path(good["admission_id"])
        value = json.loads(path.read_text())
        value["status"] = "DECIDED"
        path.write_text(json.dumps(value))
        with self.assertRaisesRegex(MissionAdmissionError, "digest"):
            self.store.load(good["admission_id"])

    def test_zeus_cli_runs_and_resumes_qualification_pipeline(self):
        store = self.directory / "cli-admissions"
        state = self.directory / "orchestration.json"
        command = [
            str(ROOT / "scripts/zeus"),
            "--state", str(state),
            "admit-mission", "start",
            "--mode", "qualification",
            "--intent", "Qualify Zeus admission CLI",
            "--mission", "ZEUS-P2-007-CLI",
            "--phase", "MISSION-ADMISSION",
            "--repository", str(ROOT),
            "--at", "2026-07-26T23:00:00Z",
            "--max-stages", "2",
        ]
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            env={
                **os.environ,
                "ZEUS_TESTING": "1",
                "ZEUS_ADMISSION_STORE": str(store),
            },
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        interrupted = json.loads(result.stdout)
        self.assertEqual(interrupted["status"], "INTERRUPTED")
        resumed = subprocess.run(
            [
                str(ROOT / "scripts/zeus"),
                "--state", str(state),
                "admit-mission", "resume",
                "--admission-id", interrupted["admission_id"],
                "--at", "2026-07-26T23:00:00Z",
            ],
            capture_output=True,
            text=True,
            env={
                **os.environ,
                "ZEUS_TESTING": "1",
                "ZEUS_ADMISSION_STORE": str(store),
            },
        )
        self.assertEqual(resumed.returncode, 0, resumed.stderr)
        self.assertEqual(json.loads(resumed.stdout)["status"], "DECIDED")


if __name__ == "__main__":
    unittest.main()
