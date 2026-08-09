#!/usr/bin/env python3
"""Qualification for the CAGF-01 native identity-binding corrective."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.lib.emp import managed_handoff  # noqa: E402
from scripts.lib.emp.wop_packaging import _stage1_tree_digest, adapt_canonical_package  # noqa: E402
from scripts.lib.eos import operational_beta  # noqa: E402
from scripts.lib.wop.canonical_package import (  # noqa: E402
    canonical_identity_records,
    load,
    package_digest,
)


WOP = "WOP-OB-CAGF-G01-CANONICAL-001"
GATE = "OB-CAGF-G01"
MISSION = "CAGF-01"
HISTORICAL = "MISSION-BETA-562F443E16C69401"
REVISION_1 = ROOT / "engineering/work-orders/WOP-OB-CAGF-G01-CANONICAL-001/canonical-wop-package.yaml"
REVISION_2 = ROOT / "engineering/work-orders/WOP-OB-CAGF-G01-CANONICAL-001/revisions/2/canonical-wop-package.yaml"


class Cagf01IdentityBindingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.runtime = Path(self.temp.name) / "runtime"
        self.runtime.mkdir()

    def tearDown(self) -> None:
        self.temp.cleanup()

    def resolve(self, text: str, runtime: Path | None = None) -> dict:
        return managed_handoff.resolve_handoff(ROOT, text, runtime_root=runtime or self.runtime)

    def test_native_cagf01_mission_discovery_and_binding(self):
        value = operational_beta.mission_state(ROOT, MISSION)
        self.assertEqual((value["mission_id"], value["family"]), (MISSION, "CAGF"))
        self.assertEqual(value["classification"], "ELIGIBLE")
        self.assertEqual(value["readiness"], "ELIGIBLE")
        self.assertEqual(value["missing_dependencies"], [])
        self.assertEqual(value["canonical_binding"]["wop_id"], WOP)
        self.assertEqual(value["canonical_binding"]["gate_id"], GATE)

    def test_corrected_revision_identity_and_requirement_count(self):
        package = load(REVISION_2)
        identity = package["package_identity"]
        self.assertEqual(identity["mission_id"], MISSION)
        self.assertEqual(identity["wop_id"], WOP)
        self.assertEqual(identity["gate_id"], GATE)
        self.assertEqual(identity["revision"], 2)
        self.assertEqual(len(package["requirements"]), 12)
        self.assertEqual(package_digest(package), package["integrity"]["package_digest"])

    def test_revision_1_is_byte_preserved_and_history_is_non_reusable(self):
        baseline = subprocess.check_output(["git", "show", "HEAD:engineering/work-orders/WOP-OB-CAGF-G01-CANONICAL-001/canonical-wop-package.yaml"], cwd=ROOT)
        self.assertEqual(REVISION_1.read_bytes(), baseline)
        records = canonical_identity_records(ROOT)
        historical = [item for item in records["historical_records"] if item["revision"] == 1]
        self.assertEqual(len(historical), 1)
        self.assertEqual(historical[0]["mission_id"], HISTORICAL)
        self.assertEqual(historical[0]["native_beta_binding"], "NONE")
        self.assertEqual(historical[0]["revision_state"], "HISTORICAL")

    def test_no_historical_mission_alias(self):
        value = self.resolve(f"Mission: {HISTORICAL}\n")
        self.assertEqual(value["blocker"], "HANDOFF_BINDING_CONTRADICTION")
        self.assertNotEqual(value.get("mission_id"), MISSION)

    def test_managed_handoff_mission_only_resolution(self):
        value = self.resolve(f"Mission: {MISSION}\n")
        self.assertEqual(value["blocker"], "HANDOFF_EXECUTION_UNAVAILABLE")
        self.assertEqual(value["binding"], {"mission": "PASS", "wop": "PASS", "gate": "PASS"})
        self.assertEqual(value["next_authorized_action"], "SUBMIT_EXISTING_CAGF01_WOP_THROUGH_ZEUS")

    def test_managed_handoff_wop_only_resolution(self):
        value = self.resolve(f"WOP: {WOP}\nGate: {GATE}\n")
        self.assertEqual((value["mission_id"], value["wop_id"], value["gate_id"]), (MISSION, WOP, GATE))
        self.assertEqual(value["blocker"], "HANDOFF_EXECUTION_UNAVAILABLE")

    def test_managed_handoff_explicit_tuple_resolution(self):
        value = self.resolve(f"Mission: {MISSION}\nWOP: {WOP}\nGate: {GATE}\n")
        self.assertEqual((value["mission_id"], value["wop_id"], value["gate_id"]), (MISSION, WOP, GATE))
        self.assertEqual(value["binding"]["mission"], "PASS")

    def test_zero_candidate_fails_closed(self):
        value = self.resolve("Mission: CAGF-99\n")
        self.assertEqual(value["blocker"], "HANDOFF_BINDING_CONTRADICTION")

    def test_multiple_candidate_fails_closed(self):
        directory = self.runtime / "execution-start-transactions"
        directory.mkdir()
        for number in (1, 2):
            (directory / f"candidate-{number}.json").write_text(json.dumps({
                "mission_id": MISSION, "wop_id": WOP, "gate_id": GATE,
                "execution_id": f"EXECUTION-CAGF-{number}",
                "execution_start_state": "READY_FOR_CONTROLLED_EXECUTION",
            }), encoding="utf-8")
        value = self.resolve(f"Mission: {MISSION}\n", self.runtime)
        self.assertEqual(value["blocker"], "HANDOFF_RESOLUTION_AMBIGUOUS")

    def test_conflicting_mission_identity_fails_closed(self):
        value = self.resolve(f"Mission: {MISSION}\nWOP: WOP-NOT-CAGF\n")
        self.assertEqual(value["blocker"], "HANDOFF_BINDING_CONTRADICTION")

    def test_invalid_gate_identity_fails_closed(self):
        value = self.resolve(f"Mission: {MISSION}\nWOP: {WOP}\nGate: GATE-NOT-CAGF\n")
        self.assertEqual(value["blocker"], "HANDOFF_BINDING_CONTRADICTION")

    def test_invalid_wop_identity_fails_closed(self):
        value = self.resolve(f"Mission: {MISSION}\nWOP: WOP-NOT-CAGF\nGate: {GATE}\n")
        self.assertEqual(value["blocker"], "HANDOFF_BINDING_CONTRADICTION")

    def test_published_is_distinct_from_submitted(self):
        identity = canonical_identity_records(ROOT)["records"][0]
        self.assertEqual(identity["wop_published"], "YES")
        self.assertEqual(identity["wop_submitted"], "NO")
        self.assertEqual(identity["separate_wop_authorization_required"], "NO")
        self.assertEqual(self.resolve(f"Mission: {MISSION}\n")["wop_submitted"], "NO")

    def test_current_catalog_has_one_native_candidate_and_preserved_old_digest(self):
        catalog = canonical_identity_records(ROOT)
        current = [item for item in catalog["records"] if item["wop_id"] == WOP]
        historical = [item for item in catalog["historical_records"] if item["wop_id"] == WOP]
        self.assertEqual(len(current), 1)
        self.assertEqual(len(historical), 1)
        self.assertEqual(current[0]["mission_id"], MISSION)
        self.assertNotEqual(current[0]["canonical_package_digest"], historical[0]["canonical_package_digest"])

    def test_native_next_action_reuses_existing_wop(self):
        value = operational_beta.next_action(ROOT, "CAGF")
        self.assertIn("SUBMIT_EXISTING_CAGF01_WOP_THROUGH_ZEUS", value["next_authorized_action"])
        self.assertNotIn("Publish a separately authorized WOP", value["next_authorized_action"])

    def test_submission_authority_requires_no_second_authorization(self):
        package = load(REVISION_2)
        self.assertEqual(package["lifecycle_binding"]["separate_wop_authorization_required"], "NO")
        self.assertEqual(package["lifecycle_binding"]["next_authorized_action"], "SUBMIT_EXISTING_CAGF01_WOP_THROUGH_ZEUS")

    def test_stage1_adapter_preserves_corrected_provenance(self):
        with tempfile.TemporaryDirectory() as directory:
            first, info = adapt_canonical_package(REVISION_2, Path(directory), repository_root=ROOT)
            mission = yaml.safe_load((first / "mission.yaml").read_text(encoding="utf-8"))
            manifest = yaml.safe_load((first / "manifests/immutable-manifest.yaml").read_text(encoding="utf-8"))
            traceability = json.loads((first / "traceability.json").read_text(encoding="utf-8"))
            self.assertEqual(mission["mission_id"], MISSION)
            self.assertEqual(mission["canonical_package_digest"], info["canonical_package_digest"])
            self.assertEqual(manifest["canonical_package_digest"], package_digest(load(REVISION_2)))
            self.assertEqual(manifest["canonical_source_digest"], info["source_digest"])
            self.assertEqual(mission["canonical_gate_id"], GATE)
            self.assertEqual(manifest["stage1_tree_digest"], _stage1_tree_digest(first))
            self.assertEqual(traceability["stage1"]["tree_digest"], manifest["stage1_tree_digest"])

    def test_stage1_adapter_replay_is_idempotent(self):
        with tempfile.TemporaryDirectory() as directory:
            first, first_info = adapt_canonical_package(REVISION_2, Path(directory), repository_root=ROOT)
            second, second_info = adapt_canonical_package(REVISION_2, Path(directory), repository_root=ROOT)
            self.assertEqual(first, second)
            self.assertFalse(first_info["replayed"])
            self.assertTrue(second_info["replayed"])
            self.assertEqual(first_info["canonical_package_digest"], second_info["canonical_package_digest"])


if __name__ == "__main__":
    unittest.main()
