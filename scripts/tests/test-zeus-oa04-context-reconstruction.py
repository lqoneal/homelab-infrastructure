#!/usr/bin/env python3
"""OA-04 Project and Operational Context Reconstruction qualification."""

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts.lib.emp import project_operational_context as context


ROOT = Path(__file__).resolve().parents[2]


class ContextReconstructionTests(unittest.TestCase):
    def test_complete_repository_only_context_is_deterministic(self):
        first = context.require(ROOT)
        second = context.require(ROOT)
        self.assertEqual(first["context_digest"], second["context_digest"])
        for field in (
            "repository", "project", "phase", "mission", "work_item",
            "governing_authority", "mission_contract", "admitted_wop",
            "gate_lifecycle", "execution_runtime", "mission_admission_runtime",
            "agent_qualification", "eens_integration", "approval_requirements",
            "blockers", "next_authorized_action", "reconciliation",
            "authoritative_sources",
        ):
            self.assertIn(field, first)
        self.assertTrue(first["repository_only"])
        self.assertFalse(first["execution_agent_dispatched"])
        self.assertFalse(first["mission_executed"])

    def test_missing_malformed_and_mismatched_sources_fail_closed(self):
        missing = context.reconstruct(ROOT, sources={"project_state": None})
        self.assertFalse(missing["reconstructed"])
        with tempfile.TemporaryDirectory() as directory:
            malformed = Path(directory) / "state.json"
            malformed.write_text("{", encoding="utf-8")
            result = context.reconstruct(ROOT, sources={"runtime_state": malformed})
            self.assertFalse(result["reconstructed"])
        mismatch = context.reconstruct(ROOT, observed={"branch": "other"})
        self.assertFalse(mismatch["reconstructed"])
        for result in (missing, mismatch):
            self.assertFalse(result["protected_effects_allowed"])
            self.assertEqual("STOP_FAIL_CLOSED", result["next_authorized_action"])

    def test_replay_and_cli_are_observational(self):
        state = ROOT / "engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/state.json"
        before = state.read_bytes()
        first = subprocess.run(
            [str(ROOT / "scripts/zeus"), "context", "reconstruct"],
            cwd=ROOT, text=True, capture_output=True, check=True,
        )
        second = subprocess.run(
            [str(ROOT / "scripts/zeus"), "context", "reconstruct"],
            cwd=ROOT, text=True, capture_output=True, check=True,
        )
        self.assertEqual(json.loads(first.stdout)["context_digest"],
                         json.loads(second.stdout)["context_digest"])
        self.assertEqual(before, state.read_bytes())

    def test_interruption_and_recovery_have_no_durable_boundary(self):
        state = ROOT / "engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/state.json"
        before = state.read_bytes()
        context.require(ROOT)
        self.assertEqual(before, state.read_bytes())
        recovered = context.require(ROOT)
        self.assertEqual("RECONSTRUCTED", recovered["reconstruction"])


if __name__ == "__main__":
    unittest.main()
