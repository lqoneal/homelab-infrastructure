#!/usr/bin/env python3
"""Qualification for read-only Progressive lifecycle projection."""

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts.lib.emp import oa02_lifecycle, progressive_lifecycle
from scripts.lib.emp.progressive_gate import ProgressiveGateError


def state(**overrides):
    value = {
        "package_id": "GH-ZEUS-OA-PROGRESSIVE-001",
        "repository": "/repository",
        "current_gate": "OA-02",
        "gate_id": "OA-02",
        "gate_state": "AWAITING_OPERATOR_VERIFICATION",
        "verification_state": "VERIFIED",
        "predecessor_state": "VALID",
        "receipt_state": "ABSENT",
        "receipt": None,
    }
    value.update(overrides)
    return value


class FakeService:
    def __init__(self, value=None, error=None):
        self.value = value or state()
        self.error = error
        self.calls = []

    def gate_state(self, gate_id):
        self.calls.append(gate_id)
        if self.error:
            raise self.error
        return dict(self.value)


class ProgressiveLifecycleProjectionTests(unittest.TestCase):
    def test_verified_lifecycle_is_deterministic_and_read_only(self):
        service = FakeService()
        projector = progressive_lifecycle.ProgressiveLifecycleProjector(
            Path("/repository"), service=service
        )
        first = projector.project("OA-02")
        second = projector.project("OA-02")
        self.assertEqual(first, second)
        self.assertEqual(
            "VERIFIED_AWAITING_OPERATOR_ACCEPTANCE",
            first["lifecycle_state"],
        )
        self.assertEqual("DECIDE_OA-02", first["next_action"])
        self.assertEqual(["OA-02", "OA-02"], service.calls)

    def test_accepted_lifecycle_projects_canonical_receipt(self):
        projector = progressive_lifecycle.ProgressiveLifecycleProjector(
            Path("/repository"),
            service=FakeService(
                state(
                    current_gate="OA-03",
                    gate_state="ACCEPTED",
                    receipt_state="VALID",
                    receipt="/repository/accepted.json",
                )
            ),
        )
        value = projector.project("OA-02")
        self.assertEqual("ACCEPTED", value["lifecycle_state"])
        self.assertEqual("COMPLETE", value["next_action"])

    def test_invalid_accepted_projection_fails_closed(self):
        projector = progressive_lifecycle.ProgressiveLifecycleProjector(
            Path("/repository"),
            service=FakeService(state(gate_state="ACCEPTED")),
        )
        with self.assertRaisesRegex(
            progressive_lifecycle.ProgressiveLifecycleError,
            "no canonical valid receipt",
        ):
            projector.project("OA-02")

    def test_conflicting_nonaccepted_projection_fails_closed(self):
        projector = progressive_lifecycle.ProgressiveLifecycleProjector(
            Path("/repository"),
            service=FakeService(
                state(
                    receipt_state="VALID",
                    receipt="/repository/conflicting.json",
                )
            ),
        )
        with self.assertRaisesRegex(
            progressive_lifecycle.ProgressiveLifecycleError,
            "non-accepted lifecycle",
        ):
            projector.project("OA-02")

    def test_stale_and_replay_inconsistent_authority_fail_closed(self):
        for message in (
            "acceptance receipt package manifest mismatch",
            "runtime lifecycle binding is inconsistent",
        ):
            with self.subTest(message=message):
                projector = progressive_lifecycle.ProgressiveLifecycleProjector(
                    Path("/repository"),
                    service=FakeService(error=ProgressiveGateError(message)),
                )
                with self.assertRaisesRegex(
                    progressive_lifecycle.ProgressiveLifecycleError,
                    message,
                ):
                    projector.project("OA-02")

    def test_oa02_verify_preserves_idempotent_projection_interface(self):
        projection = {
            "decision_digest": "a" * 64,
            "verification_record": None,
            "result": "NOT_READY",
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "OA-02.verification.json"
            with mock.patch.object(
                oa02_lifecycle, "resolve", return_value=projection
            ):
                first, replay = oa02_lifecycle.verify(Path(directory), path)
                second, duplicate = oa02_lifecycle.verify(Path(directory), path)
        self.assertFalse(replay)
        self.assertTrue(duplicate)
        self.assertEqual(first, second)
        self.assertEqual("LIFECYCLE_PROJECTION", first["artifact_role"])


if __name__ == "__main__":
    unittest.main()
