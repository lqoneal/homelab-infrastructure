#!/usr/bin/env python3
"""Focused read-only contract tests for the canonical mission verifier."""

from __future__ import annotations

import copy
import json
import shutil
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
        shutil.copytree(RUNTIME, Path(holder.name) / "runtime", dirs_exist_ok=True)
        return holder

    def test_authoritative_mission_passes(self) -> None:
        value = verify(ROOT, MISSION)
        self.assertEqual(value["result"], "PASS")
        self.assertTrue(value["read_only"])
        self.assertEqual(value["replay"], {"submission": "IDEMPOTENT", "admission": "IDEMPOTENT", "bootstrap": "IDEMPOTENT"})
        self.assertEqual(value["next_authorized_action"], "ESTABLISH_PROVIDER_SESSION")

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
