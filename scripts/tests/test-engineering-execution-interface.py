#!/usr/bin/env python3
import copy
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.lib.eos.execution_interface import (  # noqa: E402
    ExecutionInterface,
    ExecutionInterfaceError,
)


class ExecutionInterfaceTests(unittest.TestCase):
    def setUp(self):
        self.interface = ExecutionInterface(ROOT)
        self.contract = dict(self.interface.mission("P2-038-CORRECTIVE"))

    def _resolve_with(self, **changes):
        contract = copy.deepcopy(self.contract)
        for key, value in changes.items():
            contract[key] = value
        with mock.patch.object(self.interface, "mission", return_value=contract):
            return self.interface.resolve("P2-038-CORRECTIVE")

    def test_manifest_is_bindings_and_routes_not_semantic_policy(self):
        self.assertEqual(
            set(self.interface.manifest),
            {
                "schema_version",
                "interface_id",
                "operational_owner",
                "metadata_model",
                "authority_resolution",
                "operational_execution_contract",
                "legacy_mission_projection",
                "semantic_bindings",
                "routes",
            },
        )
        serialized = yaml.safe_dump(self.interface.manifest)
        for forbidden in (
            "\nautomatic:",
            "\napproval:",
            "\nlifecycle:",
            "\nminimal_handoff:",
            "\ncommand_authority:",
        ):
            self.assertNotIn(forbidden, serialized)

    def test_discovery_resolves_exact_controlled_owner_revisions(self):
        owners = self.interface._resolve_owners()
        self.assertEqual(owners["execution_contract"]["document_id"], "SPEC-0005")
        self.assertEqual(owners["execution_contract"]["revision"], "2.2")
        self.assertTrue(all(item["path"] for item in owners.values()))

    def test_missing_duplicated_and_unavailable_owner_fail_closed(self):
        original = copy.deepcopy(self.interface.manifest)
        with self.subTest("missing"):
            self.interface.manifest["semantic_bindings"]["execution_contract"][
                "revision"
            ] = "999"
            with self.assertRaises(ExecutionInterfaceError):
                self.interface._resolve_owners()
        self.interface.manifest = copy.deepcopy(original)
        with self.subTest("duplicated"):
            documents = self.interface._controlled_documents()
            documents["SPEC-0005"].append(copy.deepcopy(documents["SPEC-0005"][0]))
            with mock.patch.object(
                self.interface, "_controlled_documents", return_value=documents
            ), self.assertRaises(ExecutionInterfaceError):
                self.interface._resolve_owners()
        with self.subTest("unavailable"):
            documents = self.interface._controlled_documents()
            documents["SPEC-0005"][0]["status"] = "Retired"
            with mock.patch.object(
                self.interface, "_controlled_documents", return_value=documents
            ), self.assertRaises(ExecutionInterfaceError):
                self.interface._resolve_owners()

    def test_snapshot_is_repository_complete_and_blockers_are_derived(self):
        snapshot = self.interface.snapshot("P2-038-CORRECTIVE")
        self.assertEqual(snapshot["repository"]["head"], self.interface._git("rev-parse", "HEAD"))
        self.assertIn("changed_paths", snapshot["repository"])
        self.assertIn("controlled_owners", snapshot)
        self.assertIn("review_gates", snapshot)
        self.assertIn("wop", snapshot)
        self.assertEqual(snapshot["blockers"], [])
        invalid = copy.deepcopy(self.contract["wop"])
        invalid["applicability"] = "unknown"
        self.assertIn("WOP_APPLICABILITY_UNRESOLVED", self._resolve_with(wop=invalid)["blockers"])

    def test_framework_implementation_requires_review_and_corrective_approval(self):
        gates = copy.deepcopy(self.contract["review_gates"])
        gates["corrective_assessment"]["state"] = "pending"
        blocked = self._resolve_with(review_gates=gates)
        self.assertIn(
            "REVIEW_GATE_CORRECTIVE_ASSESSMENT_NOT_APPROVED", blocked["blockers"]
        )
        gates = copy.deepcopy(self.contract["review_gates"])
        gates["corrective_implementation"]["state"] = "pending"
        blocked = self._resolve_with(review_gates=gates)
        self.assertIn(
            "REVIEW_GATE_CORRECTIVE_IMPLEMENTATION_NOT_APPROVED",
            blocked["blockers"],
        )

    def test_prior_authority_cannot_substitute_for_corrective_approval(self):
        authority = copy.deepcopy(self.contract["authority"])
        authority["reference"] = "Operator Mission Directive - P2-038"
        authority["applies_to"] = "P2-038"
        snapshot = self._resolve_with(authority=authority)
        self.assertIn("AUTHORITY_TARGET_MISMATCH", snapshot["blockers"])
        self.assertFalse(self.contract["authority"]["reusable_for_other_missions"])

    def test_command_permission_is_not_engineering_decision_authority(self):
        snapshot = self.interface.snapshot("P2-038-CORRECTIVE")
        permissions = snapshot["command_permissions"]
        decisions = snapshot["authority"]["engineering_decisions"]
        self.assertNotIn("architecture", permissions["automatic"])
        self.assertEqual(decisions["controlled_document_activation"], "prohibited")
        self.assertEqual(decisions["operator_acceptance"], "not_recorded")
        self.assertEqual(decisions["publication"], "prohibited")
        self.assertEqual(decisions["dispatch"], "prohibited")

    def test_minimal_handoff_uses_canonical_snapshot_pipeline(self):
        path = ROOT / "engineering/execution/fixtures/minimal-handoff.yaml"
        with mock.patch.object(
            self.interface, "resolve", wraps=self.interface.resolve
        ) as resolver:
            with self.assertRaises(ExecutionInterfaceError):
                self.interface.validate_handoff(path)
        resolver.assert_called_once_with("P2-038-CORRECTIVE")
        self.assertEqual(
            self.interface.snapshot("P2-038-CORRECTIVE")["next_authorized_action"],
            "REQUEST_P2_038_CORRECTIVE_ACCEPTANCE",
        )

    def test_structurally_valid_handoff_fails_for_blocked_completed_or_unauthorized_state(self):
        path = ROOT / "engineering/execution/fixtures/minimal-handoff.yaml"
        base = self.interface.snapshot("P2-038-CORRECTIVE")
        active = copy.deepcopy(base)
        active["mission"]["status"] = "ACTIVE"
        active["next_authorized_action"] = "EXECUTE_P2_038_CORRECTIVE"
        with mock.patch.object(self.interface, "resolve", return_value=active):
            self.assertEqual(self.interface.validate_handoff(path)["result"], "PASS")
        cases = {
            "blocked": {"blockers": ["TEST_BLOCKER"]},
            "completed": {"mission": {**base["mission"], "status": "COMPLETED"}},
            "unauthorized": {"next_authorized_action": "REQUEST_ACCEPTANCE"},
        }
        for name, mutation in cases.items():
            with self.subTest(name=name):
                snapshot = copy.deepcopy(base)
                snapshot.update(mutation)
                with mock.patch.object(
                    self.interface, "resolve", return_value=snapshot
                ), self.assertRaises(ExecutionInterfaceError):
                    self.interface.validate_handoff(path)

    def test_wop_applicability_and_validity_are_enforced(self):
        for wop in (
            {"applicability": "applicable", "references": [], "reason": ""},
            {"applicability": "not_applicable", "references": [], "reason": ""},
        ):
            with self.subTest(wop=wop):
                self.assertTrue(self._resolve_with(wop=wop)["blockers"])

    def test_implementation_completion_is_not_acceptance_or_activation(self):
        authority = self.contract["authority"]["engineering_decisions"]
        lifecycle = self.contract["lifecycle"]
        self.assertEqual(lifecycle["acceptance_status"], "not_recorded")
        self.assertEqual(authority["operator_acceptance"], "not_recorded")
        self.assertEqual(authority["controlled_document_activation"], "prohibited")

    def test_qualification_reports_complete_operational_state(self):
        result = self.interface.qualify("P2-038-CORRECTIVE")
        self.assertEqual(result["result"], "PASS")
        self.assertEqual(result["mission_contract_count"], 1)
        self.assertEqual(result["lifecycle_state"], "completed")
        self.assertEqual(result["implementation_status"], "complete")
        self.assertEqual(result["acceptance_status"], "not_recorded")
        self.assertEqual(result["blockers"], [])
        self.assertEqual(
            result["approvals"]["operator_acceptance"]["state"], "not_recorded"
        )
        self.assertEqual(
            result["next_authorized_action"],
            "REQUEST_P2_038_CORRECTIVE_ACCEPTANCE",
        )

    def test_unknown_mission_fails_closed(self):
        with self.assertRaises(ExecutionInterfaceError):
            self.interface.snapshot("P2-UNKNOWN")


if __name__ == "__main__":
    unittest.main()
