#!/usr/bin/env python3
"""Focused read-only contract tests for the canonical mission verifier."""

from __future__ import annotations

import copy
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.lib.emp.mission_verification_controller import render, verify


ROOT = Path(__file__).resolve().parents[2]
MISSION = "MISSION-BETA-562F443E16C69401"
RUNTIME = Path.home() / ".local/state/zeus-runtime/homelab-6bd83f9079d6fc57"


class MissionVerificationControllerTests(unittest.TestCase):
    def isolated_runtime(self) -> tempfile.TemporaryDirectory:
        holder = tempfile.TemporaryDirectory(prefix="zeus-mission-verify-")
        # Mission verification consumes receipt/runtime artifacts, not the
        # provider's multi-gigabyte Codex installation/cache.  Excluding that
        # non-authoritative directory keeps the relocation fixture bounded.
        shutil.copytree(
            RUNTIME,
            Path(holder.name) / "runtime",
            dirs_exist_ok=True,
            ignore=shutil.ignore_patterns("codex-home"),
        )
        return holder

    def test_authoritative_mission_passes(self) -> None:
        head = subprocess.check_output(
            ["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True
        ).strip()
        steady = {
            "result": "PASS", "head": head, "origin_main": head,
            "eos_baseline": head, "branch": "main", "eos_parity": True,
            "head_origin_parity": True, "index_clean": True,
            "worktree_clean": False,
            "baseline_state_classification": "STEADY_STATE_CONVERGED",
            "authorized_publication_transition": False,
            "publication_transition": None, "errors": [],
        }
        with patch("scripts.lib.emp.mission_verification_controller.project_repository", return_value=steady), \
             patch("scripts.lib.eos.canonical_baseline.project_repository", return_value=steady):
            value = verify(ROOT, MISSION)
        self.assertEqual(value["result"], "PASS")
        self.assertTrue(value["read_only"])
        self.assertEqual(value["replay"], {"submission": "IDEMPOTENT", "admission": "IDEMPOTENT", "bootstrap": "IDEMPOTENT", "provider_session": "IDEMPOTENT", "provider_invocation": "IDEMPOTENT", "execution_start": "IDEMPOTENT"})
        # This fixture is the historical Beta execution chain.  Its current
        # canonical projection stops at the explicit legacy reconciliation
        # boundary rather than exposing the obsolete work selector.
        self.assertEqual(value["next_authorized_action"], "OPERATOR_REVIEW_LEGACY_LIFECYCLE_RECONCILIATION")
        self.assertEqual(value["checks"]["provider_session"], "PASS")
        self.assertEqual(value["replay"]["provider_session"], "IDEMPOTENT")
        self.assertTrue(value["lifecycle"]["provider_session_created"])
        self.assertTrue(value["lifecycle"]["provider_session_authorized"])
        self.assertEqual(value["lifecycle"]["provider_session_id"], "PROVIDER-SESSION-65d0fe07-1d02-562d-9da2-f766f3e87ef4")
        self.assertEqual(value["lifecycle"]["provider_session_state"], "READY_FOR_PROVIDER_INVOCATION")
        self.assertTrue(value["checks"]["provider_invocation"] == "PASS")
        self.assertTrue(value["lifecycle"]["provider_invoked"])
        self.assertTrue(value["lifecycle"]["provider_acknowledged"])
        self.assertEqual(value["lifecycle"]["provider_invocation_state"], "READY_FOR_EXECUTION_START")
        self.assertEqual(value["lifecycle"]["provider_invocation_id"], "PROVIDER-INVOCATION-a02accc6-3ff0-50d2-a4b2-266ca5b51ff6")
        self.assertTrue(value["lifecycle"]["execution_started"])
        self.assertEqual(value["execution_start_provenance_baseline"], "2507b441fdf0d083e35647e6874860365025ae18")
        self.assertEqual(value["invocation_provenance_baseline"], "b37a5fb2e11df8026afeff1bd231902cd54711ac")
        self.assertEqual(value["execution_start_baseline_relationship"], "ANCESTOR")
        self.assertEqual(value["execution_start_integrity"], "PASS")
        self.assertEqual(value["lifecycle"]["execution_start_provenance_baseline"], value["execution_start_provenance_baseline"])
        self.assertEqual(value["lifecycle"]["current_published_baseline"], value["current_published_baseline"])
        self.assertEqual(value["lifecycle"]["execution_started"], value["execution_started"])

    def test_fixture_pass_and_digest_failure(self) -> None:
        holder = self.isolated_runtime()
        self.addCleanup(holder.cleanup)
        runtime = Path(holder.name) / "runtime"
        # Explicit test roots remain supported, but absolute artifact locators
        # from the authoritative materialization must fail closed after a
        # relocation rather than being silently re-bound.
        failed = verify(ROOT, MISSION, runtime_root=runtime)
        self.assertEqual(failed["result"], "FAIL")
        self.assertIn("ARTIFACT_PATH_ESCAPE", {item["code"] for item in failed["blockers"]})

    def test_mission_not_found_is_precise_and_non_mutating(self) -> None:
        value = verify(ROOT, "MISSION-BETA-NOT-FOUND")
        self.assertEqual(value["result"], "FAIL")
        self.assertIn("MISSION_NOT_DISCOVERABLE", {item["code"] for item in value["blockers"]})
        self.assertTrue(value["read_only"])

    def test_oa_active_authority_is_rejected(self) -> None:
        authority = {"authority_framework": "OPERATION_BETA", "active_operation": "BETA", "authority_integrity": "PASS",
                     "authority_resolution": "PASS", "authority_digest_validation": "PASS", "authority_source": "Operation Beta",
                     "oa_authority": "ACTIVE"}
        with patch("scripts.lib.emp.mission_verification_controller.operational_beta.authority", return_value=authority):
            value = verify(ROOT, MISSION)
        self.assertEqual(value["result"], "FAIL")
        self.assertIn("AUTHORITY_INTEGRITY_FAILURE", {item["code"] for item in value["blockers"]})

    def test_human_rendering_and_json_fields(self) -> None:
        value = verify(ROOT, MISSION)
        text = render(value)
        self.assertIn("Zeus Mission Verification", text)
        self.assertIn("Read-only           : YES", text)
        for field in ("schema_version", "checks", "replay", "lifecycle", "blockers"):
            self.assertIn(field, value)


if __name__ == "__main__":
    unittest.main()
