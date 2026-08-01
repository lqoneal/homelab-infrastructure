#!/usr/bin/env python3
"""Qualification for the canonical Progressive gate primitives."""

import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import yaml

from scripts.lib.emp import progressive_gate, progressive_oa


class ProgressiveGatePrimitiveTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name).resolve()
        self.package = self.root / progressive_oa.PACKAGE_PATH
        self.package.mkdir(parents=True)
        gates = [
            {
                "gate_id": f"OA-{number:02d}",
                "title": f"Gate {number}",
                "mission_objective": "fixture",
                "capability_being_established": "fixture",
                "authoritative_source_references": [],
                "required_evidence": [],
            }
            for number in range(1, 31)
        ]
        (self.package / "gate-specification.yaml").write_text(
            yaml.safe_dump({"gates": gates})
        )
        (self.package / "MANIFEST.sha256").write_text("fixture manifest\n")
        self._write_state()
        self._write_marker("OA-01")
        self._write_marker("OA-02")
        self._write_receipt("OA-01")

    def tearDown(self):
        self.temporary.cleanup()

    def _write_state(self):
        state = progressive_oa.load_state(self.root)
        state["active_gate"] = "OA-02"
        state["gates"]["OA-01"]["state"] = "ACCEPTED"
        state["gates"]["OA-02"]["state"] = "AWAITING_OPERATOR_VERIFICATION"
        progressive_oa._write_state(self.root, state)

    def _write_marker(self, gate_id):
        directory = self.package / "runtime/evidence" / gate_id
        directory.mkdir(parents=True, exist_ok=True)
        evidence = {"assertions": {"result": "PASS"}}
        evidence["canonical_evidence_digest"] = hashlib.sha256(
            json.dumps(evidence, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        (directory / "VERIFICATION.json").write_text(
            json.dumps(evidence, indent=2, sort_keys=True) + "\n"
        )
        marker = {
            "schema_version": 1,
            "package_id": progressive_oa.PACKAGE,
            "gate_id": gate_id,
            "verification_result": "PASS",
            "evidence_digest": evidence["canonical_evidence_digest"],
        }
        marker["marker_digest"] = progressive_oa._receipt_digest(
            {"receipt_digest": "", **marker}
        )
        # _receipt_digest omits receipt_digest, the same canonical JSON rule.
        (directory / "VERIFIED").write_text(
            json.dumps(marker, indent=2, sort_keys=True) + "\n"
        )
        return directory / "VERIFIED"

    def _write_receipt(self, gate_id):
        marker_path = self.package / "runtime/evidence" / gate_id / "VERIFIED"
        marker = json.loads(marker_path.read_text())
        receipt = {
            "schema_version": 2,
            "package_id": progressive_oa.PACKAGE,
            "gate_id": gate_id,
            "decision": "ACCEPTED",
            "operator": "operator",
            "decided_at": "2026-07-29T00:00:00Z",
            "package_manifest_sha256": hashlib.sha256(
                (self.package / "MANIFEST.sha256").read_bytes()
            ).hexdigest(),
            "evidence_marker_sha256": hashlib.sha256(
                marker_path.read_bytes()
            ).hexdigest(),
            "evidence_digest": marker["evidence_digest"],
            "marker_digest": marker["marker_digest"],
        }
        receipt["receipt_digest"] = progressive_oa._receipt_digest(receipt)
        path = (
            self.package / "runtime/decisions" / gate_id
            / f"accepted-{receipt['receipt_digest']}.json"
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
        state = progressive_oa.load_state(self.root)
        state["gates"][gate_id]["acceptance_receipt"] = str(path)
        progressive_oa._write_state(self.root, state)
        return path

    def test_valid_receipt_predecessor_replay_and_gate_state(self):
        first = progressive_gate.validate_receipt(self.root, "OA-01")
        second = progressive_gate.validate_receipt(self.root, "OA-01")
        predecessor = progressive_gate.predecessor_state(self.root, "OA-02")
        state = progressive_gate.gate_state(self.root, "OA-02")
        self.assertEqual(first, second)
        self.assertTrue(first["replay_safe"])
        self.assertEqual(predecessor["predecessor_state"], "VALID")
        self.assertEqual(state["current_gate"], "OA-02")
        self.assertEqual(state["verification_state"], "VERIFIED")
        self.assertEqual(state["receipt_state"], "ABSENT")

    def test_missing_receipt_fails_closed(self):
        state = progressive_oa.load_state(self.root)
        state["gates"]["OA-01"]["acceptance_receipt"] = None
        progressive_oa._write_state(self.root, state)
        with self.assertRaises(progressive_gate.ProgressiveGateError):
            progressive_gate.validate_receipt(self.root, "OA-01")

    def test_corrupted_receipt_and_digest_mismatch_fail_closed(self):
        path = Path(
            progressive_oa.load_state(self.root)["gates"]["OA-01"][
                "acceptance_receipt"
            ]
        )
        receipt = json.loads(path.read_text())
        receipt["operator"] = "corrupt"
        path.write_text(json.dumps(receipt))
        with self.assertRaisesRegex(
            progressive_gate.ProgressiveGateError, "integrity"
        ):
            progressive_gate.validate_receipt(self.root, "OA-01")

    def test_stale_receipt_fails_closed(self):
        (self.package / "MANIFEST.sha256").write_text("new manifest\n")
        with self.assertRaisesRegex(
            progressive_gate.ProgressiveGateError, "manifest"
        ):
            progressive_gate.validate_receipt(self.root, "OA-01")

    def test_invalid_predecessor_fails_closed(self):
        state = progressive_oa.load_state(self.root)
        state["gates"]["OA-01"]["state"] = "PENDING"
        progressive_oa._write_state(self.root, state)
        with self.assertRaisesRegex(
            progressive_gate.ProgressiveGateError, "not accepted"
        ):
            progressive_gate.predecessor_state(self.root, "OA-02")

    def test_incorrect_gate_binding_fails_closed(self):
        path = Path(
            progressive_oa.load_state(self.root)["gates"]["OA-01"][
                "acceptance_receipt"
            ]
        )
        receipt = json.loads(path.read_text())
        receipt["gate_id"] = "OA-02"
        receipt["receipt_digest"] = progressive_oa._receipt_digest(receipt)
        path.write_text(json.dumps(receipt))
        with self.assertRaisesRegex(
            progressive_gate.ProgressiveGateError, "gate"
        ):
            progressive_gate.validate_receipt(self.root, "OA-01")

    def test_evidence_digest_mismatch_fails_closed(self):
        path = Path(
            progressive_oa.load_state(self.root)["gates"]["OA-01"][
                "acceptance_receipt"
            ]
        )
        receipt = json.loads(path.read_text())
        receipt["evidence_digest"] = "0" * 64
        receipt["receipt_digest"] = progressive_oa._receipt_digest(receipt)
        path.write_text(json.dumps(receipt))
        with self.assertRaisesRegex(
            progressive_gate.ProgressiveGateError, "evidence digest"
        ):
            progressive_gate.validate_receipt(self.root, "OA-01")

    def test_replay_conflict_fails_closed(self):
        receipt_path = Path(
            progressive_oa.load_state(self.root)["gates"]["OA-01"][
                "acceptance_receipt"
            ]
        )
        receipt = json.loads(receipt_path.read_text())
        superseded = receipt_path.parent / "superseded.json"
        superseded.write_text(json.dumps({
            "decision": "SUPERSEDED",
            "historical_receipt": receipt_path.name,
            "historical_receipt_digest": receipt["receipt_digest"],
        }))
        with self.assertRaisesRegex(
            progressive_gate.ProgressiveGateError, "superseded"
        ):
            progressive_gate.validate_receipt(self.root, "OA-01")

    def test_repository_qualification_fails_closed(self):
        with self.assertRaisesRegex(
            progressive_gate.ProgressiveGateError, "qualified repository"
        ):
            progressive_gate.gate_state(self.root / "other")

    def test_canonical_verification_dispatch_is_deterministic(self):
        self._write_marker("OA-02")
        expected = {"gate_id": "OA-02", "replay": True}
        with mock.patch(
            "scripts.lib.emp.oa02_gate_verification.verify",
            return_value=expected,
        ):
            first = progressive_gate.verify(self.root, "OA-02")
            second = progressive_gate.verify(self.root, "OA-02")
        self.assertEqual(first, second)
        self.assertEqual(first["verification_result"], "PASS")

    def test_unimplemented_verifier_fails_closed(self):
        with self.assertRaisesRegex(
            progressive_gate.ProgressiveGateError, "not implemented"
        ):
            progressive_gate.verify(self.root, "OA-08")

    def _activate_oa01_for_decision(self):
        state = progressive_oa.load_state(self.root)
        state["active_gate"] = "OA-01"
        state["status"] = "ACTIVE"
        state["gates"]["OA-01"] = {
            "state": "AWAITING_OPERATOR_VERIFICATION",
            "acceptance_receipt": None,
        }
        progressive_oa._write_state(self.root, state)

    def test_service_facade_approve_and_idempotent_replay(self):
        self._activate_oa01_for_decision()
        service = progressive_gate.ProgressiveGateService(self.root)
        first, replay = service.approve(
            "OA-01", "operator", "2026-07-29T00:00:00Z"
        )
        second, duplicate = service.record_acceptance(
            "OA-01", "operator", "2026-07-29T01:00:00Z"
        )
        self.assertFalse(replay)
        self.assertTrue(duplicate)
        self.assertEqual(first, second)
        self.assertEqual(
            service.validate_receipt("OA-01")["receipt_digest"],
            first["receipt_digest"],
        )

    def test_service_facade_decline_and_duplicate_request(self):
        self._activate_oa01_for_decision()
        service = progressive_gate.decision_service(self.root)
        first, replay = service.decline(
            "OA-01", "operator", "2026-07-29T00:00:00Z"
        )
        second, duplicate = service.decline(
            "OA-01", "operator", "2026-07-29T01:00:00Z"
        )
        self.assertFalse(replay)
        self.assertTrue(duplicate)
        self.assertEqual(first, second)
        self.assertEqual(progressive_oa.load_state(self.root)["status"],
                         "STOPPED_FAIL_CLOSED")

    def test_conflicting_rejection_receipt_fails_closed(self):
        self._activate_oa01_for_decision()
        service = progressive_gate.ProgressiveGateService(self.root)
        service.decline("OA-01", "operator", "2026-07-29T00:00:00Z")
        path = self.package / "runtime/decisions/OA-01/rejected.json"
        receipt = json.loads(path.read_text())
        receipt["operator"] = "other"
        path.write_text(json.dumps(receipt))
        with self.assertRaisesRegex(
            progressive_gate.ProgressiveGateError, "integrity"
        ):
            service.decline("OA-01", "operator")

    def test_stale_rejection_receipt_fails_closed(self):
        self._activate_oa01_for_decision()
        service = progressive_gate.ProgressiveGateService(self.root)
        service.decline("OA-01", "operator", "2026-07-29T00:00:00Z")
        (self.package / "MANIFEST.sha256").write_text("changed manifest\n")
        with self.assertRaisesRegex(
            progressive_gate.ProgressiveGateError, "conflicting"
        ):
            service.decline("OA-01", "operator")

    def test_malformed_decision_fails_before_persistence(self):
        self._activate_oa01_for_decision()
        service = progressive_gate.ProgressiveGateService(self.root)
        with self.assertRaisesRegex(
            progressive_gate.ProgressiveGateError,
            "ACCEPTED or REJECTED",
        ):
            service.decide("OA-01", "APPROVED", "operator")
        self.assertFalse(
            (self.package / "runtime/decisions/OA-01/approved.json").exists()
        )

    def test_legacy_decide_delegates_to_canonical_service(self):
        self._activate_oa01_for_decision()
        expected = ({"decision": "ACCEPTED"}, False)
        with mock.patch.object(
            progressive_gate.ProgressiveGateService,
            "decide",
            return_value=expected,
        ) as delegated:
            actual = progressive_oa.decide(
                self.root, "OA-01", "ACCEPTED", "operator", None
            )
        self.assertEqual(actual, expected)
        delegated.assert_called_once_with(
            "OA-01", "ACCEPTED", "operator", None
        )


if __name__ == "__main__":
    unittest.main()
