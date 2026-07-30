#!/usr/bin/env python3
"""Regression tests for the Progressive OA successive-gate controller."""

import hashlib
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.lib.emp import progressive_oa, progressive_runtime_support


class ProgressiveOATest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.package = self.root / progressive_oa.PACKAGE_PATH
        self.package.mkdir(parents=True)
        gates = []
        for number in range(1, 31):
            gates.append({
                "gate_id": f"OA-{number:02d}",
                "title": f"Gate {number}",
                "mission_objective": f"Objective {number}",
                "capability_being_established": f"Capability {number}",
                "authoritative_source_references": ["source"],
                "rationale": "required",
                "exact_success_criteria": ["PASS"],
                "required_evidence": ["evidence"],
            })
        (self.package / "gate-specification.yaml").write_text(
            yaml.safe_dump({"gates": gates})
        )
        (self.package / "MANIFEST.sha256").write_text("fixture manifest\n")

    def tearDown(self):
        os.environ.pop("ZEUS_PROGRESSIVE_OA_STATE", None)
        self.temporary.cleanup()

    def _prepare_oa04(self):
        state = progressive_oa.load_state(self.root)
        state["active_gate"] = "OA-04"
        for number in range(1, 4):
            item = state["gates"][f"OA-{number:02d}"]
            item["state"] = "ACCEPTED"
            item["acceptance_receipt"] = f"prior-{number}"
        state["gates"]["OA-04"]["state"] = "AWAITING_OPERATOR_VERIFICATION"
        progressive_oa._write_state(self.root, state)
        directory = self.package / "runtime/evidence/OA-04"
        directory.mkdir(parents=True, exist_ok=True)
        evidence = {"assertions": {"result": "PASS"}}
        evidence["canonical_evidence_digest"] = hashlib.sha256(
            json.dumps(
                evidence, sort_keys=True, separators=(",", ":")
            ).encode()
        ).hexdigest()
        (directory / "VERIFICATION.json").write_text(
            json.dumps(evidence, indent=2, sort_keys=True) + "\n"
        )
        marker = {
            "schema_version": 1,
            "package_id": progressive_oa.PACKAGE,
            "gate_id": "OA-04",
            "verification_result": "PASS",
            "evidence_digest": evidence["canonical_evidence_digest"],
        }
        marker["marker_digest"] = hashlib.sha256(
            json.dumps(
                marker, sort_keys=True, separators=(",", ":")
            ).encode()
        ).hexdigest()
        (directory / "VERIFIED").write_text(
            json.dumps(marker, indent=2, sort_keys=True) + "\n"
        )
        return state, directory / "VERIFIED"

    def _accept(self, operator="operator", at="2026-07-29T05:00:00Z"):
        with mock.patch(
            "scripts.lib.emp.oa04_gate_verification.validate_marker",
            return_value={"verification_result": "PASS"},
        ):
            return progressive_oa.decide(
                self.root, "OA-04", "ACCEPTED", operator, at
            )

    def _current(self):
        state = progressive_oa.load_state(self.root)
        locator = state["gates"]["OA-04"]["acceptance_receipt"]
        return state, Path(locator) if locator else None

    def test_controller_selects_only_first_gate_and_replays(self):
        first = progressive_oa.controller(self.root)
        second = progressive_oa.controller(self.root)
        self.assertEqual(first["active_gate"], "OA-01")
        self.assertEqual(first, second)
        state = progressive_oa.load_state(self.root)
        self.assertEqual(state["gates"]["OA-01"]["state"], "IMPLEMENTATION_REQUIRED")
        self.assertEqual(state["gates"]["OA-02"]["state"], "PENDING")

    def test_no_existing_receipt_creates_unique_acceptance(self):
        self._prepare_oa04()
        receipt, replay = self._accept()
        state, path = self._current()
        self.assertFalse(replay)
        self.assertTrue(path.is_file())
        self.assertRegex(path.name, r"^accepted-[0-9a-f]{64}\.json$")
        self.assertEqual(
            receipt["evidence_digest"],
            json.loads((path.parents[2] / "evidence/OA-04/VERIFICATION.json").read_text())[
                "canonical_evidence_digest"
            ],
        )
        self.assertEqual(state["gates"]["OA-04"]["state"], "ACCEPTED")

    def test_current_matching_receipt_replays(self):
        self._prepare_oa04()
        first, _ = self._accept()
        second, replay = self._accept()
        self.assertTrue(replay)
        self.assertEqual(first, second)

    def test_superseded_current_receipt_is_rejected(self):
        self._prepare_oa04()
        receipt, _ = self._accept()
        state, path = self._current()
        (path.parent / "superseded.json").write_text(json.dumps({
            "decision": "SUPERSEDED",
            "historical_receipt": path.name,
            "historical_receipt_digest": receipt["receipt_digest"],
        }))
        with self.assertRaisesRegex(
            progressive_oa.ProgressiveOAError, "superseded"
        ):
            self._accept()

    def test_historical_different_evidence_is_not_replayed(self):
        _, marker = self._prepare_oa04()
        directory = self.package / "runtime/decisions/OA-04"
        directory.mkdir(parents=True)
        historical = {
            "schema_version": 1,
            "package_id": progressive_oa.PACKAGE,
            "gate_id": "OA-04",
            "decision": "ACCEPTED",
            "operator": "operator",
            "decided_at": "earlier",
            "evidence_marker_sha256": hashlib.sha256(b"old").hexdigest(),
        }
        historical["receipt_digest"] = progressive_oa._receipt_digest(historical)
        old = directory / "accepted.json"
        old.write_text(json.dumps(historical, sort_keys=True) + "\n")
        before = old.read_bytes()
        receipt, replay = self._accept()
        self.assertFalse(replay)
        self.assertEqual(old.read_bytes(), before)
        self.assertEqual(receipt["evidence_marker_sha256"],
                         hashlib.sha256(marker.read_bytes()).hexdigest())

    def test_receipt_exists_but_gate_not_accepted_is_not_replay(self):
        self._prepare_oa04()
        historical = self.package / "runtime/decisions/OA-04/accepted.json"
        historical.parent.mkdir(parents=True)
        historical.write_text('{"decision":"ACCEPTED"}\n')
        _, replay = self._accept()
        self.assertFalse(replay)

    def test_runtime_without_receipt_reference_fails_current_lookup(self):
        self._prepare_oa04()
        state = progressive_oa.load_state(self.root)
        state["gates"]["OA-04"]["state"] = "ACCEPTED"
        state["active_gate"] = "OA-05"
        progressive_oa._write_state(self.root, state)
        with self.assertRaisesRegex(
            progressive_oa.ProgressiveOAError, "current acceptance receipt"
        ):
            progressive_oa.verify_receipt(self.root, "OA-04")
        with self.assertRaisesRegex(
            progressive_oa.ProgressiveOAError, "current acceptance receipt"
        ):
            self._accept()

    def test_receipt_digest_mismatch_fails_closed(self):
        self._prepare_oa04()
        self._accept()
        _, path = self._current()
        value = json.loads(path.read_text())
        value["operator"] = "tampered"
        path.write_text(json.dumps(value))
        with self.assertRaisesRegex(
            progressive_oa.ProgressiveOAError, "integrity"
        ):
            self._accept()

    def test_verification_evidence_digest_mismatch_fails_closed(self):
        self._prepare_oa04()
        self._accept()
        _, path = self._current()
        value = json.loads(path.read_text())
        value["evidence_digest"] = hashlib.sha256(b"different evidence").hexdigest()
        value["receipt_digest"] = progressive_oa._receipt_digest(value)
        path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
        with self.assertRaisesRegex(
            progressive_oa.ProgressiveOAError, "evidence digest mismatch"
        ):
            self._accept()

    def test_lifecycle_binding_to_another_gate_receipt_fails_closed(self):
        self._prepare_oa04()
        self._accept()
        state, path = self._current()
        value = json.loads(path.read_text())
        value["gate_id"] = "OA-05"
        value["receipt_digest"] = progressive_oa._receipt_digest(value)
        other = path.parent.parent / "OA-05" / "accepted-fixture.json"
        other.parent.mkdir(parents=True)
        other.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
        state["gates"]["OA-04"]["acceptance_receipt"] = str(other)
        progressive_oa._write_state(self.root, state)
        with self.assertRaisesRegex(
            progressive_oa.ProgressiveOAError, "package, gate, or decision mismatch"
        ):
            self._accept()

    def test_runtime_lifecycle_regression_fails_closed(self):
        self._prepare_oa04()
        self._accept()
        state = progressive_oa.load_state(self.root)
        state["active_gate"] = "OA-04"
        progressive_oa._write_state(self.root, state)
        with self.assertRaisesRegex(
            progressive_oa.ProgressiveOAError,
            "runtime lifecycle binding is inconsistent",
        ):
            self._accept()

    def test_runtime_intermediate_gate_gap_fails_closed(self):
        self._prepare_oa04()
        self._accept()
        state = progressive_oa.load_state(self.root)
        state["active_gate"] = "OA-06"
        progressive_oa._write_state(self.root, state)
        with self.assertRaisesRegex(
            progressive_oa.ProgressiveOAError,
            "runtime lifecycle binding is inconsistent",
        ):
            self._accept()

    def test_marker_digest_mismatch_fails_closed(self):
        self._prepare_oa04()
        self._accept()
        _, marker = self._prepare_oa04()
        value = json.loads(marker.read_text())
        value["marker_digest"] = "changed-marker"
        marker.write_text(json.dumps(value))
        state = progressive_oa.load_state(self.root)
        state["gates"]["OA-04"]["state"] = "ACCEPTED"
        state["active_gate"] = "OA-05"
        # Preserve the original receipt reference restored by _prepare_oa04.
        receipts = list((self.package / "runtime/decisions/OA-04").glob("accepted-*"))
        state["gates"]["OA-04"]["acceptance_receipt"] = str(receipts[0])
        progressive_oa._write_state(self.root, state)
        with self.assertRaisesRegex(
            progressive_oa.ProgressiveOAError, "marker"
        ):
            self._accept()

    def test_operator_mismatch_fails_closed(self):
        self._prepare_oa04()
        self._accept("operator-a")
        with self.assertRaisesRegex(
            progressive_oa.ProgressiveOAError, "operator mismatch"
        ):
            self._accept("operator-b")

    def test_new_receipt_preserves_historical_receipt_and_supersedence(self):
        self._prepare_oa04()
        directory = self.package / "runtime/decisions/OA-04"
        directory.mkdir(parents=True)
        historical = directory / "accepted.json"
        supersedence = directory / "superseded.json"
        historical.write_bytes(b"historical bytes\n")
        supersedence.write_bytes(b"supersedence bytes\n")
        self._accept()
        self.assertEqual(historical.read_bytes(), b"historical bytes\n")
        self.assertEqual(supersedence.read_bytes(), b"supersedence bytes\n")

    def test_new_acceptance_advances_exactly_one_gate(self):
        self._prepare_oa04()
        self._accept()
        state, _ = self._current()
        self.assertEqual(state["active_gate"], "OA-05")
        self.assertEqual(state["gates"]["OA-05"]["state"], "PENDING")
        self.assertEqual(state["gates"]["OA-06"]["state"], "PENDING")

    def test_oa05_remains_pending_before_corrected_acceptance(self):
        self._prepare_oa04()
        state = progressive_oa.load_state(self.root)
        self.assertEqual(state["active_gate"], "OA-04")
        self.assertEqual(state["gates"]["OA-05"]["state"], "PENDING")

    def test_replay_after_corrected_acceptance_returns_new_receipt(self):
        self._prepare_oa04()
        first, _ = self._accept()
        _, path = self._current()
        second, replay = self._accept()
        self.assertTrue(replay)
        self.assertEqual(first, second)
        self.assertIn(first["receipt_digest"], path.name)

    def test_acceptance_has_no_execution_or_declaration_effect(self):
        self._prepare_oa04()
        before = set(self.package.rglob("*"))
        self._accept()
        after = set(self.package.rglob("*"))
        additions = {path.name for path in after - before}
        self.assertFalse(
            additions & {"dispatch.json", "mission-execution.json",
                         "declaration.json", "baseline-freeze.json"}
        )
        self.assertFalse(progressive_oa.status(self.root)["declaration_authorized"])

    def test_interruption_before_receipt_persistence_has_no_acceptance(self):
        self._prepare_oa04()
        with mock.patch(
            "scripts.lib.emp.progressive_runtime_support._persist_receipt",
            side_effect=OSError("interrupted"),
        ), self.assertRaises(OSError):
            self._accept()
        state, path = self._current()
        self.assertIsNone(path)
        self.assertEqual(state["active_gate"], "OA-04")

    def test_interruption_after_receipt_persistence_recovers_one_receipt(self):
        self._prepare_oa04()
        original = progressive_runtime_support._write_state
        with mock.patch(
            "scripts.lib.emp.progressive_runtime_support._write_state",
            side_effect=OSError("interrupted"),
        ), self.assertRaises(OSError):
            self._accept()
        receipts = list((self.package / "runtime/decisions/OA-04").glob("accepted-*"))
        self.assertEqual(len(receipts), 1)
        with mock.patch(
            "scripts.lib.emp.progressive_runtime_support._write_state",
            side_effect=original,
        ):
            _, replay = self._accept(at="2026-07-29T05:01:00Z")
        self.assertFalse(replay)
        self.assertEqual(
            len(list((self.package / "runtime/decisions/OA-04").glob("accepted-*"))),
            1,
        )
        state, path = self._current()
        self.assertEqual(state["active_gate"], "OA-05")
        self.assertEqual(path, receipts[0])


if __name__ == "__main__":
    unittest.main()
