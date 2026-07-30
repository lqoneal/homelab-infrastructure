#!/usr/bin/env python3
"""OA-04 deterministic Mission Resolution qualification."""

import copy
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml

from scripts.lib.emp import mission_resolution


ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "engineering/registry/work-registry.yaml"
WOP = ROOT / "engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/immutable-wop.yaml"
INTERFACE = ROOT / "engineering/execution/execution-interface.yaml"


class MissionResolutionTests(unittest.TestCase):
    def test_positive_resolution_is_complete_deterministic_and_observational(self):
        first = mission_resolution.require(ROOT)
        second = mission_resolution.require(ROOT)
        self.assertEqual(first["resolution_digest"], second["resolution_digest"])
        self.assertEqual("RESOLVED", first["resolution"])
        self.assertEqual(4, len(first["authority_chain"]))
        self.assertFalse(first["execution_agent_dispatched"])
        self.assertFalse(first["mission_executed"])
        self.assertTrue(first["wop"]["wop_id"])
        self.assertEqual(
            "ENGINEERING-EXECUTION-INTERFACE",
            first["execution_definition"]["interface_id"],
        )

    def test_zero_and_multiple_eligible_missions_fail_closed(self):
        eligible = {
            "registry_id": "EMP-WORK-GH-ZEUS-OA-PROGRESSIVE-001",
            "mission_id": "EMP-MISSION-ZEUS-OPERATIONAL-ALPHA",
            "phase_id": "EMP-PHASE-ZEUS-OPERATIONAL-ALPHA",
            "management_state": "active",
        }
        for candidates, expected in (
            ([], "ZERO_ELIGIBLE_MISSIONS"),
            ([eligible, eligible], "MULTIPLE_ELIGIBLE_MISSIONS"),
        ):
            with self.subTest(expected=expected):
                result = mission_resolution.resolve(ROOT, candidates=candidates)
                self.assertEqual(expected, result["resolution"])
                self.assertFalse(result["protected_effects_allowed"])
                self.assertFalse(result["execution_agent_dispatched"])

    def test_repository_branch_and_authority_staleness_fail_closed(self):
        cases = (
            {"repository_identity": "other"},
            {"branch": "other"},
            {"upstream": "0" * 40},
        )
        for observed in cases:
            with self.subTest(observed=observed):
                result = mission_resolution.resolve(ROOT, observed=observed)
                self.assertEqual("STALE_AUTHORITY", result["resolution"])
                self.assertFalse(result["mission_executed"])

    def test_wop_and_execution_interface_changes_fail_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            temporary = Path(directory)
            wop = yaml.safe_load(WOP.read_text(encoding="utf-8"))
            wop["wop_id"] = "CHANGED"
            changed_wop = temporary / "wop.yaml"
            changed_wop.write_text(yaml.safe_dump(wop), encoding="utf-8")
            result = mission_resolution.resolve(ROOT, sources={"wop": changed_wop})
            self.assertEqual("WOP_BINDING_CHANGED", result["resolution"])

            interface = yaml.safe_load(INTERFACE.read_text(encoding="utf-8"))
            interface["interface_id"] = "CHANGED"
            changed_interface = temporary / "interface.yaml"
            changed_interface.write_text(yaml.safe_dump(interface), encoding="utf-8")
            result = mission_resolution.resolve(
                ROOT, sources={"execution_interface": changed_interface}
            )
            self.assertEqual("EXECUTION_INTERFACE_CHANGED", result["resolution"])

    def test_mission_contract_change_fails_closed(self):
        authority = mission_resolution.ControlledMissionAuthority(
            ROOT, expected_gate="OA-04"
        ).require(boundary="test")
        changed = copy.deepcopy(mission_resolution.require_discovery(ROOT))
        changed["contract_id"] = "CHANGED"
        with patch.object(
            mission_resolution.ControlledMissionAuthority,
            "require",
            return_value=authority,
        ), patch.object(
            mission_resolution, "require_discovery", return_value=changed
        ):
            result = mission_resolution.resolve(ROOT)
        self.assertEqual("CONTRACT_CHANGED", result["resolution"])
        self.assertFalse(result["protected_effects_allowed"])

    def test_reconciliation_and_incomplete_mission_fail_closed(self):
        incomplete = {
            "registry_id": "EMP-WORK-GH-ZEUS-OA-PROGRESSIVE-001",
            "management_state": "active",
        }
        result = mission_resolution.resolve(ROOT, candidates=[incomplete])
        self.assertEqual("INCOMPLETE_MISSION", result["resolution"])
        with tempfile.TemporaryDirectory() as directory:
            registry = Path(directory) / "registry.yaml"
            registry.write_text("not: the-registry\n", encoding="utf-8")
            result = mission_resolution.resolve(ROOT, sources={"registry": registry})
        self.assertEqual("ZERO_ELIGIBLE_MISSIONS", result["resolution"])
        original_run = subprocess.run
        def reconcile_failure(arguments, *args, **kwargs):
            if "sync-validate" in arguments:
                return subprocess.CompletedProcess(
                    arguments, 1, stdout="", stderr="drift"
                )
            return original_run(arguments, *args, **kwargs)
        with patch.object(
            mission_resolution.subprocess, "run", side_effect=reconcile_failure
        ):
            result = mission_resolution.resolve(ROOT)
        self.assertEqual("RECONCILIATION_FAILED", result["resolution"])

    def test_failed_resolution_creates_no_runtime_or_execution_effect(self):
        before = {
            path: path.read_bytes()
            for path in (
                ROOT / "engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/state.json",
                ROOT / "engineering/execution/execution-interface.yaml",
            )
        }
        with self.assertRaises(mission_resolution.MissionResolutionError):
            mission_resolution.require(ROOT, candidates=[])
        self.assertEqual(before, {path: path.read_bytes() for path in before})


if __name__ == "__main__":
    unittest.main()
