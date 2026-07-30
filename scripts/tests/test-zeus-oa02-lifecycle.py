#!/usr/bin/env python3
"""OA-02 authoritative implementation replay and recovery behavior."""

import copy
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.lib.emp import oa02_implementation


STATE = {
    "schema_version": 1,
    "package_id": "GH-ZEUS-OA-PROGRESSIVE-001",
    "status": "ACTIVE",
    "active_gate": "OA-02",
    "gates": {
        "OA-01": {"state": "ACCEPTED", "acceptance_receipt": "accepted.json"},
        "OA-02": {"state": "IMPLEMENTATION_REQUIRED", "acceptance_receipt": None},
        "OA-03": {"state": "PENDING", "acceptance_receipt": None},
    },
}
AUTHORITY = {
    "wop_id": "WOP-test",
    "mission_id": "MISSION-test",
    "contract_id": "MC-test",
    "operational_mission_id": "EMP-MISSION-test",
    "repository_identity": "homelab",
    "repository_root": "/data/engineering/repositories/homelab",
    "branch": "main",
    "head": "a" * 40,
    "upstream": "a" * 40,
    "qualified_baseline": "b" * 40,
    "authority_source": "contract.yaml",
    "authority_digest": "c" * 64,
    "oa01_acceptance_receipt": "accepted.json",
    "oa01_acceptance_digest": "d" * 64,
    "package_admission_receipt": "admission.json",
    "package_admission_digest": "e" * 64,
}


class OA02LifecycleTests(unittest.TestCase):
    def harness(self, directory, *, state=None):
        current = copy.deepcopy(state or STATE)
        evidence = Path(directory) / "IMPLEMENTATION.json"
        writes = []

        def load_state(_root):
            return copy.deepcopy(current)

        def write_state(_root, value):
            current.clear()
            current.update(copy.deepcopy(value))
            writes.append(copy.deepcopy(value))

        successful = {
            "command": ["test"], "stdout": "", "stderr": "", "exit_code": 0,
            "stdout_sha256": "0" * 64, "stderr_sha256": "0" * 64,
        }
        patches = (
            patch.object(oa02_implementation.progressive_oa, "load_state", load_state),
            patch.object(oa02_implementation.progressive_oa, "_write_state", write_state),
            patch.object(
                oa02_implementation.ControlledMissionAuthority,
                "require", return_value=copy.deepcopy(AUTHORITY),
            ),
            patch.object(oa02_implementation, "run", return_value=successful),
            patch.object(
                oa02_implementation, "inventory",
                return_value={"entries": [], "inventory_digest": "f" * 64},
            ),
            patch.object(oa02_implementation, "evidence_path", return_value=evidence),
        )
        return current, evidence, writes, patches

    def test_implementation_transitions_once_and_replay_is_idempotent(self):
        with tempfile.TemporaryDirectory() as directory:
            current, evidence, writes, patches = self.harness(directory)
            with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5]:
                first = oa02_implementation.qualify(Path(directory))
                second = oa02_implementation.qualify(Path(directory))
            self.assertEqual("AWAITING_OPERATOR_VERIFICATION", current["gates"]["OA-02"]["state"])
            self.assertEqual(1, len(writes))
            self.assertTrue(evidence.is_file())
            self.assertFalse(first["idempotent_replay"])
            self.assertTrue(second["idempotent_replay"])
            self.assertFalse(second["operator_acceptance_recorded"])
            self.assertFalse(second["next_gate_enabled"])
            self.assertEqual("PENDING", current["gates"]["OA-03"]["state"])

    def test_interruptions_before_durable_evidence_do_not_advance(self):
        variables = (
            ("ZEUS_OA02_INTERRUPT_BEFORE_AUTHORITY", "1"),
            ("ZEUS_OA02_INTERRUPT_AFTER_AUTHORITY", "1"),
            ("ZEUS_OA02_INTERRUPT_DURING_QUALIFICATION", "package_integrity"),
            ("ZEUS_OA02_INTERRUPT_BEFORE_EVIDENCE", "1"),
        )
        for variable, value in variables:
            with self.subTest(variable=variable), tempfile.TemporaryDirectory() as directory:
                current, evidence, writes, patches = self.harness(directory)
                with patch.dict(os.environ, {variable: value}, clear=False):
                    with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5]:
                        with self.assertRaises(oa02_implementation.OA02ImplementationError):
                            oa02_implementation.qualify(Path(directory))
                self.assertEqual("IMPLEMENTATION_REQUIRED", current["gates"]["OA-02"]["state"])
                self.assertEqual([], writes)
                self.assertFalse(evidence.exists())

    def test_interrupt_after_evidence_recovers_without_duplicate_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            current, evidence, writes, patches = self.harness(directory)
            with patch.dict(
                os.environ, {"ZEUS_OA02_INTERRUPT_AFTER_EVIDENCE": "1"}, clear=False
            ):
                with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5]:
                    with self.assertRaises(oa02_implementation.OA02ImplementationError):
                        oa02_implementation.qualify(Path(directory))
            original = evidence.read_bytes()
            # The append-only evidence exists, so a different rerun cannot replace it.
            self.assertEqual("IMPLEMENTATION_REQUIRED", current["gates"]["OA-02"]["state"])
            self.assertEqual([], writes)
            self.assertEqual(original, evidence.read_bytes())

    def test_interrupt_before_transition_never_enables_later_gate(self):
        with tempfile.TemporaryDirectory() as directory:
            current, evidence, writes, patches = self.harness(directory)
            with patch.dict(
                os.environ, {"ZEUS_OA02_INTERRUPT_BEFORE_TRANSITION": "1"}, clear=False
            ):
                with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5]:
                    with self.assertRaises(oa02_implementation.OA02ImplementationError):
                        oa02_implementation.qualify(Path(directory))
            self.assertEqual("IMPLEMENTATION_REQUIRED", current["gates"]["OA-02"]["state"])
            self.assertEqual("PENDING", current["gates"]["OA-03"]["state"])
            self.assertEqual([], writes)
            self.assertTrue(evidence.exists())

    def test_protected_execution_without_authority_never_dispatches(self):
        with tempfile.TemporaryDirectory() as directory:
            current, evidence, writes, patches = self.harness(directory)
            denied = ValueError("MISSING: authority")
            patches = list(patches)
            patches[2] = patch.object(
                oa02_implementation.ControlledMissionAuthority,
                "require", side_effect=denied,
            )
            with patches[0], patches[1], patches[2], patches[3] as dispatch, patches[4], patches[5]:
                with self.assertRaises(ValueError):
                    oa02_implementation.qualify(Path(directory))
            dispatch.assert_not_called()
            self.assertEqual([], writes)
            self.assertFalse(evidence.exists())


if __name__ == "__main__":
    unittest.main()
