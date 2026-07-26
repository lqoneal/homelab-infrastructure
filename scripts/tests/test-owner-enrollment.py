#!/usr/bin/env python3
"""ZEUS-P2-006 owner enrollment and unsigned publication toolkit tests."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.lib.emp.authority_publication import (  # noqa: E402
    REQUIRED_OWNERS,
    AuthorityPublicationError,
    commissioning_status,
    digest,
    prepare_publication_envelope,
    publication_template,
)
from scripts.lib.emp.owner_enrollment import (  # noqa: E402
    ENROLLMENT_NAMESPACE,
    OwnerEnrollmentError,
    OwnerEnrollmentRegistry,
    enrollment_status,
    prepare_request,
    public_key_details,
)

AT = datetime(2026, 7, 26, 22, 0, tzinfo=timezone.utc)


class OwnerEnrollmentTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.directory = Path(self.temporary.name)
        self.root_key = self.key("enrollment-root")
        root_public = self.root_key.with_suffix(".pub").read_text().strip()
        self.allowed = self.directory / "enrollment-allowed"
        self.allowed.write_text(f"enrollment-authorizer {root_public}\n")
        self.policy = self.directory / "enrollment-policy.yaml"
        self.policy.write_text(
            yaml.safe_dump(
                {
                    "schema_version": 1,
                    "operationally_configured": True,
                    "signature_namespace": ENROLLMENT_NAMESPACE,
                    "allowed_signers_file": str(self.allowed),
                    "authorization_principals": ["enrollment-authorizer"],
                }
            )
        )
        value = {
            "schema_version": 1,
            "revision": 0,
            "operationally_configured": False,
            "enrollments": {},
            "status": "qualification",
        }
        value["registry_digest"] = digest(value)
        self.registry_path = self.directory / "registry.yaml"
        self.registry_path.write_text(yaml.safe_dump(value, sort_keys=True))
        self.registry = OwnerEnrollmentRegistry(
            ROOT, policy_path=self.policy, registry_path=self.registry_path
        )
        self.counter = 0

    def tearDown(self):
        self.temporary.cleanup()

    def key(self, name):
        path = self.directory / name
        subprocess.run(
            ["ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-f", str(path)],
            check=True,
        )
        return path

    def sign_request(self, request):
        self.counter += 1
        path = self.directory / f"request-{self.counter}.json"
        path.write_text(json.dumps(request, sort_keys=True, separators=(",", ":")))
        subprocess.run(
            [
                "ssh-keygen", "-Y", "sign", "-q",
                "-f", str(self.root_key),
                "-n", ENROLLMENT_NAMESPACE,
                str(path),
            ],
            check=True,
        )
        return path, Path(str(path) + ".sig")

    def enroll(self, owner, principal, key):
        request = prepare_request(
            action="enroll",
            owner=owner,
            principal=principal,
            authorization_reference="ENROLLMENT-AUTHORIZATION-QUALIFIED",
            requested_at=AT,
            public_key_path=key.with_suffix(".pub"),
        )
        path, signature = self.sign_request(request)
        return self.registry.apply(
            request_path=path,
            signature=signature,
            signer="enrollment-authorizer",
        )

    def test_public_keys_enroll_with_external_authorization_and_compile(self):
        for index, owner in enumerate(sorted(REQUIRED_OWNERS), start=1):
            self.enroll(owner, f"owner-{index}", self.key(f"owner-{index}"))
        status = self.registry.verify()
        self.assertTrue(status["registry_digest_valid"])
        self.assertTrue(status["trust_compilation_ready"])
        output = self.registry.compile_trust(self.directory / "candidate-trust")
        policy = yaml.safe_load(Path(output["policy"]).read_text())
        self.assertTrue(policy["operationally_configured"])
        self.assertTrue(policy["candidate_only"])
        self.assertEqual(set(policy["owners"]), REQUIRED_OWNERS)
        self.assertFalse(
            (ROOT / "engineering/authority/owner-trust-policy.yaml").read_text()
            .splitlines()[1]
            .endswith("true")
        )

    def test_rotation_suspension_and_retirement_are_authorized(self):
        owner = sorted(REQUIRED_OWNERS)[0]
        first = self.enroll(owner, "owner-primary", self.key("owner-primary"))
        rotate = prepare_request(
            action="rotate",
            owner=owner,
            principal="owner-rotated",
            authorization_reference="ROTATION-AUTHORIZATION",
            requested_at=AT,
            public_key_path=self.key("owner-rotated").with_suffix(".pub"),
            target_enrollment_id=first["enrollment_id"],
        )
        path, signature = self.sign_request(rotate)
        second = self.registry.apply(
            request_path=path, signature=signature, signer="enrollment-authorizer"
        )
        data = yaml.safe_load(self.registry_path.read_text())
        self.assertEqual(
            data["enrollments"][first["enrollment_id"]]["lifecycle_state"],
            "rotated",
        )
        suspend = prepare_request(
            action="suspend",
            owner=owner,
            principal="owner-rotated",
            authorization_reference="SUSPENSION-AUTHORIZATION",
            requested_at=AT,
            target_enrollment_id=second["enrollment_id"],
        )
        path, signature = self.sign_request(suspend)
        result = self.registry.apply(
            request_path=path, signature=signature, signer="enrollment-authorizer"
        )
        self.assertEqual(result["lifecycle_state"], "suspended")

        third = self.enroll(owner, "owner-retire", self.key("owner-retire"))
        retire = prepare_request(
            action="retire",
            owner=owner,
            principal="owner-retire",
            authorization_reference="RETIREMENT-AUTHORIZATION",
            requested_at=AT,
            target_enrollment_id=third["enrollment_id"],
        )
        path, signature = self.sign_request(retire)
        result = self.registry.apply(
            request_path=path, signature=signature, signer="enrollment-authorizer"
        )
        self.assertEqual(result["lifecycle_state"], "retired")

    def test_private_key_and_unsigned_or_tampered_requests_fail_closed(self):
        with self.assertRaisesRegex(OwnerEnrollmentError, "public keys"):
            public_key_details(self.root_key)
        owner = sorted(REQUIRED_OWNERS)[0]
        request = prepare_request(
            action="enroll",
            owner=owner,
            principal="owner",
            authorization_reference="AUTHORIZATION",
            requested_at=AT,
            public_key_path=self.key("owner").with_suffix(".pub"),
        )
        path, signature = self.sign_request(request)
        changed = json.loads(path.read_text())
        changed["authorization_reference"] = "CHANGED"
        path.write_text(json.dumps(changed))
        with self.assertRaises(OwnerEnrollmentError):
            self.registry.apply(
                request_path=path,
                signature=signature,
                signer="enrollment-authorizer",
            )

    def test_publication_templates_and_approval_support_never_sign_or_approve(self):
        template = publication_template("approval_authority")
        self.assertTrue(template["unsigned_template"])
        self.assertIsNone(template["payload"]["decision"])
        with self.assertRaisesRegex(AuthorityPublicationError, "missing"):
            prepare_publication_envelope(
                record_type="approval_authority",
                record_id="APPROVAL-OWNER-SUPPLIED",
                record_revision=1,
                signer_principal="governance-owner",
                published_at=AT,
                payload={},
            )
        payload = {
            "reference": "APPROVAL-OWNER-SUPPLIED",
            "authority": "Engineering Governance",
            "decision": "GRANTED",
            "decision_at": "2026-07-26T21:00:00Z",
            "authorized_lifecycle_state": "Active",
            "scope_digest": "a" * 64,
        }
        envelope = prepare_publication_envelope(
            record_type="approval_authority",
            record_id=payload["reference"],
            record_revision=1,
            signer_principal="governance-owner",
            published_at=AT,
            payload=payload,
        )
        self.assertEqual(envelope["owner"], "Engineering Governance decision registry")
        self.assertNotIn("signature", envelope)

    def test_diagnostics_distinguish_enrollment_and_publication_blockers(self):
        owner_status = enrollment_status(ROOT)
        self.assertFalse(owner_status["trust_compilation_ready"])
        status = commissioning_status(ROOT)
        codes = {item["code"] for item in status["blockers"]}
        self.assertIn("ENROLLMENT_ROOT_NOT_CONFIGURED", codes)
        self.assertIn("OWNER_ENROLLMENT_MISSING", codes)
        self.assertIn("UNSIGNED_PUBLICATION_MISSING", codes)
        self.assertIn("GOVERNANCE_APPROVAL_PUBLICATION_MISSING", codes)


if __name__ == "__main__":
    unittest.main()
