#!/usr/bin/env python3
"""OA-03 deterministic discovery, fail-closed, replay, and recovery tests."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml

from scripts.lib.emp import mission_contract_discovery as discovery


def contract(identifier: str, lifecycle: str = "active") -> dict:
    return {
        "contract_id": identifier,
        "mission_id": "MISSION",
        "lifecycle": lifecycle,
    }


class MissionContractDiscoveryTests(unittest.TestCase):
    def harness(self, values):
        temporary = tempfile.TemporaryDirectory()
        root = Path(temporary.name)
        store = root / "engineering/mission-contracts/contracts"
        store.mkdir(parents=True)
        for name, value in values:
            (store / name).write_text(yaml.safe_dump(value), encoding="utf-8")
        return temporary, root

    def resolve(self, root, result, validation=None):
        return patch.object(
            discovery.Resolver, "resolve", return_value=result
        ), patch.object(
            discovery, "validate", side_effect=validation or (lambda value, base: [])
        )

    def test_exactly_one_applicable_contract_is_deterministic_and_replay_safe(self):
        temporary, root = self.harness([
            ("z-suspended.yaml", contract("OLD", "suspended")),
            ("a-active.yaml", contract("CURRENT")),
        ])
        self.addCleanup(temporary.cleanup)
        resolved = {
            "resolution": "AUTHORIZED", "active_count": 1,
            "contract": contract("CURRENT"),
            "contract_path": "engineering/mission-contracts/contracts/a-active.yaml",
        }
        patches = self.resolve(root, resolved)
        with patches[0], patches[1]:
            first = discovery.require(root)
            second = discovery.require(root)
        self.assertEqual("CURRENT", first["contract_id"])
        self.assertEqual(first["discovery_digest"], second["discovery_digest"])
        self.assertEqual(
            ["engineering/mission-contracts/contracts/a-active.yaml",
             "engineering/mission-contracts/contracts/z-suspended.yaml"],
            [item["locator"] for item in first["candidates"]],
        )

    def test_missing_and_ambiguous_fail_closed(self):
        for status, expected in (
            ("NO_AUTHORIZED_WORK", "MISSING"),
            ("AMBIGUOUS_AUTHORITY", "AMBIGUOUS"),
        ):
            with self.subTest(status=status):
                temporary, root = self.harness([])
                with temporary:
                    patches = self.resolve(root, {
                        "resolution": status,
                        "active_count": 0 if status == "NO_AUTHORIZED_WORK" else 2,
                    })
                    with patches[0], patches[1]:
                        result = discovery.discover(root)
                    self.assertEqual(expected, result["resolution"])
                    self.assertFalse(result["protected_effects_allowed"])

    def test_malformed_unauthorized_and_incomplete_fail_closed(self):
        cases = (
            (["broken"], "MALFORMED"),
            (["approvals.activation: approved required"], "UNAUTHORIZED"),
            (["scope: required"], "INCOMPLETE"),
        )
        for errors, expected in cases:
            with self.subTest(expected=expected):
                temporary, root = self.harness([("candidate.yaml", contract("C"))])
                with temporary:
                    patches = self.resolve(
                        root,
                        {"resolution": "INVALID_CONTRACT", "active_count": 1},
                        lambda value, base: errors,
                    )
                    with patches[0], patches[1]:
                        result = discovery.discover(root)
                    self.assertEqual(expected, result["resolution"])
                    self.assertEqual("STOP_FAIL_CLOSED", result["next_authorized_action"])

    def test_stale_mismatched_inactive_revoked_and_conflicted_fail_closed(self):
        cases = (
            ("BASELINE_MISMATCH", "STALE"),
            ("BRANCH_MISMATCH", "MISMATCHED"),
            ("SUSPENDED_AUTHORITY", "INACTIVE"),
            ("REVOKED_AUTHORITY", "REVOKED"),
            ("DIRTY_TREE_NOT_AUTHORIZED", "CONFLICTED"),
        )
        for status, expected in cases:
            with self.subTest(status=status):
                temporary, root = self.harness([("candidate.yaml", contract("C"))])
                with temporary:
                    patches = self.resolve(
                        root, {"resolution": status, "active_count": 1}
                    )
                    with patches[0], patches[1]:
                        result = discovery.discover(root)
                    self.assertEqual(expected, result["resolution"])
                    self.assertFalse(result["discovered"])

    def test_failure_does_not_write_or_call_protected_effect(self):
        temporary, root = self.harness([])
        with temporary:
            effect = unittest.mock.Mock()
            patches = self.resolve(
                root, {"resolution": "NO_AUTHORIZED_WORK", "active_count": 0}
            )
            with patches[0], patches[1]:
                with self.assertRaises(discovery.MissionContractDiscoveryError):
                    discovery.require(root)
            effect.assert_not_called()
            self.assertEqual([], list(root.rglob("IMPLEMENTATION.json")))


if __name__ == "__main__":
    unittest.main()
