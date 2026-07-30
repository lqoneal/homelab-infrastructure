#!/usr/bin/env python3
"""Controlled Mission Authority positive and fail-closed matrix."""

import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml

from scripts.lib.emp.controlled_mission_authority import (
    ControlledMissionAuthority,
)
from scripts.lib.eos.mission_contract import Resolver


ROOT = Path(__file__).resolve().parents[2]
CONTRACT = (
    ROOT / "engineering/mission-contracts/contracts/"
    "MC-MISSION-CONTRACT-PUBLICATION-001.yaml"
)


class ControlledAuthorityTests(unittest.TestCase):
    def resolve(self, **kwargs):
        return ControlledMissionAuthority(
            ROOT, expected_gate="OA-04", **kwargs
        ).resolve(boundary="test")

    def assert_denied(self, result, state):
        self.assertFalse(result["authorized"])
        self.assertFalse(result["protected_effects_allowed"])
        self.assertEqual(state, result["resolution"])
        self.assertEqual("STOP_FAIL_CLOSED", result["next_authorized_action"])

    def test_authorized_binding_is_complete_discoverable_and_deterministic(self):
        first = self.resolve()
        second = self.resolve()
        self.assertTrue(first["authorized"])
        self.assertEqual("AUTHORIZED", first["resolution"])
        for key in (
            "mission_id", "contract_id", "operational_mission_id",
            "work_item_id", "wop_id", "wop_locator", "repository_identity",
            "repository_root", "branch", "head", "qualified_baseline",
            "active_gate", "execution_state", "authority_source",
            "authority_digest", "checks", "required_approvals",
        ):
            self.assertTrue(first[key])
        self.assertEqual("OA-04", first["active_gate"])
        self.assertTrue(first["oa02_acceptance_receipt"])
        self.assertTrue(first["oa03_acceptance_receipt"])
        self.assertEqual(first["authority_digest"], second["authority_digest"])

    def test_repository_branch_head_and_root_mismatches_fail_closed(self):
        cases = (
            ({"repository_identity": "other"}, "MISMATCHED"),
            ({"repository_root": "/tmp/not-homelab"}, "MISMATCHED"),
            ({"branch": "other"}, "MISMATCHED"),
            ({"upstream": "0" * 40}, "STALE"),
            ({"remote": "git@example.invalid:other.git"}, "MISMATCHED"),
        )
        for observed, state in cases:
            with self.subTest(observed=observed):
                self.assert_denied(self.resolve(observed=observed), state)

    def test_missing_contract_fails_closed(self):
        with patch.object(
            Resolver, "resolve",
            return_value={"resolution": "NO_AUTHORIZED_WORK"},
        ):
            self.assert_denied(self.resolve(), "MISSING")

    def test_ambiguous_contract_fails_closed(self):
        with patch.object(
            Resolver, "resolve",
            return_value={"resolution": "AMBIGUOUS_AUTHORITY"},
        ):
            self.assert_denied(self.resolve(), "AMBIGUOUS")

    def test_malformed_contract_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "contract.yaml"
            path.write_text("not: [valid\n", encoding="utf-8")
            self.assert_denied(
                self.resolve(sources={"contract": path}), "MALFORMED"
            )

    def test_unauthorized_inactive_and_revoked_contracts_fail_closed(self):
        original = yaml.safe_load(CONTRACT.read_text(encoding="utf-8"))
        cases = (
            ({"approvals": {"activation": "pending", "publication": "approved"}}, "UNAUTHORIZED"),
            ({"lifecycle": "suspended"}, "INACTIVE"),
            ({"lifecycle": "revoked"}, "REVOKED"),
        )
        with tempfile.TemporaryDirectory() as directory:
            for index, (changes, expected) in enumerate(cases):
                value = copy.deepcopy(original)
                value.update(changes)
                value.pop("contract_digest", None)
                path = Path(directory) / f"contract-{index}.yaml"
                path.write_text(yaml.safe_dump(value), encoding="utf-8")
                result = self.resolve(sources={"contract": path})
                # Contract structural validation rejects unapproved active
                # contracts before authorization classification.
                self.assert_denied(result, expected)

    def test_missing_wop_and_admission_fail_closed(self):
        self.assert_denied(self.resolve(sources={"wop": None}), "MISSING")
        self.assert_denied(self.resolve(sources={"admission": None}), "MISSING")

    def test_invalid_admission_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "admission.json"
            path.write_text("{}\n", encoding="utf-8")
            self.assert_denied(
                self.resolve(sources={"admission": path}), "MALFORMED"
            )

    def test_missing_and_invalid_oa01_receipt_fail_closed(self):
        self.assert_denied(
            self.resolve(sources={"oa01_receipt": None}), "MISSING"
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "accepted.json"
            path.write_text(json.dumps({"decision": "ACCEPTED"}), encoding="utf-8")
            self.assert_denied(
                self.resolve(sources={"oa01_receipt": path}), "MALFORMED"
            )

    def test_active_gate_and_later_gate_activity_fail_closed(self):
        state_path = (
            ROOT / "engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/"
            "runtime/state.json"
        )
        original = json.loads(state_path.read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as directory:
            for name, mutate in (
                ("active", lambda value: value.update(active_gate="OA-05")),
                (
                    "later",
                    lambda value: value["gates"]["OA-05"].update(
                        state="IMPLEMENTATION_REQUIRED"
                    ),
                ),
            ):
                value = copy.deepcopy(original)
                mutate(value)
                path = Path(directory) / f"{name}.json"
                path.write_text(json.dumps(value), encoding="utf-8")
                self.assert_denied(
                    self.resolve(sources={"state": path}), "CONFLICTED"
                )

    def test_registry_conflict_and_malformed_state_fail_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            registry = Path(directory) / "registry.yaml"
            registry.write_text("entities: {work_items: []}\n", encoding="utf-8")
            self.assert_denied(
                self.resolve(sources={"registry": registry}), "CONFLICTED"
            )
            state = Path(directory) / "state.json"
            state.write_text("{", encoding="utf-8")
            self.assert_denied(
                self.resolve(sources={"state": state}), "MALFORMED"
            )


if __name__ == "__main__":
    unittest.main()
