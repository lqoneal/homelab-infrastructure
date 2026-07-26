#!/usr/bin/env python3
"""ZEUS-P2-004 signed authority publication and activation tests."""

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

from scripts.lib.authority.engine import AuthorityGraph  # noqa: E402
from scripts.lib.emp.authority_publication import (  # noqa: E402
    AuthorityPublicationError,
    AuthorityPublicationFramework,
    RECORD_RULES,
    SIGNATURE_NAMESPACE,
    commissioning_status,
    envelope_identifier,
)
from scripts.lib.emp.authority_resolution import (  # noqa: E402
    AuthorityResolutionRuntime,
    digest,
    load_authority_state,
)

AT = datetime(2026, 7, 26, 20, 0, tzinfo=timezone.utc)
MISSION = "EMP-MISSION-ZEUS-OPERATIONAL-ALPHA"
PHASE = "EMP-PHASE-ZEUS-OPERATIONAL-ALPHA"
WORK = "EMP-WORK-ZEUS-P2-004-QUALIFIED"
PRINCIPAL = "loneal"
GRAPH_PATH = "engineering/authority/fixtures/valid.yaml"

PRINCIPALS = {"Lawrence O'Neal": "loneal"}


class PublicationQualificationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.directory = Path(self.temporary.name)
        self.key = self.directory / "owner-key"
        subprocess.run(
            ["ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-f", str(self.key)],
            check=True,
        )
        public = self.key.with_suffix(".pub").read_text().strip()
        allowed = self.directory / "allowed-signers"
        allowed.write_text(
            "".join(f"{principal} {public}\n" for principal in PRINCIPALS.values())
        )
        self.policy = self.directory / "policy.yaml"
        self.policy.write_text(
            yaml.safe_dump(
                {
                    "schema_version": 1,
                    "operationally_configured": True,
                    "signature_namespace": SIGNATURE_NAMESPACE,
                    "allowed_signers_file": str(allowed),
                    "owners": {
                        owner: {"principals": [principal]}
                        for owner, principal in PRINCIPALS.items()
                    },
                },
                sort_keys=True,
            )
        )
        self.framework = AuthorityPublicationFramework(
            ROOT, policy_path=self.policy
        )
        self.transaction = self.framework.initialize(self.directory / "transaction")
        self.sequence = 0

    def tearDown(self):
        self.temporary.cleanup()

    def envelope(
        self,
        record_type: str,
        record_id: str,
        payload: dict,
        *,
        owner: str | None = None,
    ):
        expected_owner = RECORD_RULES[record_type][1]
        actual_owner = owner or expected_owner
        self.sequence += 1
        value = {
            "schema_version": 1,
            "record_type": record_type,
            "record_id": record_id,
            "record_revision": 1,
            "owner": actual_owner,
            "signer_principal": PRINCIPALS.get(
                actual_owner, "unauthorized-publisher"
            ),
            "published_at": "2026-07-26T19:00:00Z",
            "payload": payload,
            "payload_digest": digest(payload),
        }
        value["envelope_id"] = envelope_identifier(value)
        path = self.directory / f"envelope-{self.sequence}.json"
        path.write_text(json.dumps(value, sort_keys=True, separators=(",", ":")))
        subprocess.run(
            [
                "ssh-keygen", "-Y", "sign", "-q",
                "-f", str(self.key),
                "-n", SIGNATURE_NAMESPACE,
                str(path),
            ],
            check=True,
        )
        return path, Path(str(path) + ".sig")

    def stage(self, record_type: str, record_id: str, payload: dict):
        envelope, signature = self.envelope(record_type, record_id, payload)
        return self.framework.stage(
            transaction=self.transaction,
            envelope_path=envelope,
            signature_path=signature,
        )

    def complete_publication(self):
        head = subprocess.run(
            ["git", "-C", str(ROOT), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        scope_digest = digest(
            {"mission_id": MISSION, "phase_id": PHASE, "work_item_id": WORK}
        )
        graph = AuthorityGraph.load(ROOT / GRAPH_PATH)
        resolution = graph.resolve("work-package")
        chain = list(resolution.path)
        capabilities = sorted(resolution.effective_capabilities)
        authority_digest = digest(
            {"graph_id": graph.graph_id, "chain": chain, "capabilities": capabilities}
        )
        references = [
            "PROC-0001@1.11", "TPL-0001@1.7", "STD-0000", "STD-0001",
            "STD-0002", "STD-0003", "STD-0004",
        ]
        manifest_material = {
            "manifest_id": "GOVERNING-ZEUS-WOP-1",
            "manifest_revision": 1,
            "references": references,
        }
        records = [
            (
                "mission_authority", MISSION,
                {"lifecycle_state": "active"},
            ),
            (
                "phase_authority", PHASE,
                {"mission_id": MISSION, "lifecycle_state": "active"},
            ),
            (
                "work_item_authority", WORK,
                {
                    "mission_id": MISSION,
                    "phase_id": PHASE,
                    "lifecycle_state": "qualified",
                    "qualification_status": "QUALIFIED",
                    "qualification_record": "QUAL-ZEUS-P2-004",
                    "revision": 1,
                    "approval_reference": "APPROVAL-ZEUS-P2-004",
                    "authority_binding_id": "AUTHORITY-BINDING-ZEUS-P2-004",
                    "scope_digest": scope_digest,
                },
            ),
            (
                "repository_identity", "REPOSITORY-HOMELAB",
                {
                    "repository_id": "REPOSITORY-HOMELAB",
                    "canonical_locator": str(ROOT),
                    "assertion_id": "REPOSITORY-ASSERTION-ZEUS-P2-004",
                },
            ),
            (
                "repository_baseline", "REPOSITORY-HOMELAB",
                {"baseline_commit": head},
            ),
            (
                "authority_node", "AUTHORITY-BINDING-ZEUS-P2-004",
                {
                    "graph_path": GRAPH_PATH,
                    "authority_node_id": "work-package",
                    "graph_version": graph.graph_id,
                    "chain": chain,
                    "capabilities": capabilities,
                    "resolution_digest": authority_digest,
                },
            ),
            (
                "approval_authority", "APPROVAL-ZEUS-P2-004",
                {
                    "reference": "APPROVAL-ZEUS-P2-004",
                    "authority": "Human Engineering Authority",
                    "decision": "GRANTED",
                    "decision_at": "2026-07-26T18:00:00Z",
                    "authorized_lifecycle_state": "Active",
                    "scope_digest": scope_digest,
                },
            ),
            (
                "authorization_decision", "ADR-ZEUS-P2-004-PUBLICATION",
                {
                    "decision": "AUTHORIZED",
                    "lifecycle_state": "Active",
                    "decision_digest": digest(
                        {"decision": "AUTHORIZED", "subject": WORK}
                    ),
                },
            ),
            (
                "identity_record", PRINCIPAL,
                {
                    "authentication_status": "VERIFIED",
                    "session_id": "SESSION-ZEUS-P2-004",
                    "authentication_record": "AUTHN-ZEUS-P2-004",
                },
            ),
            (
                "governing_baseline", "GOVERNING-ZEUS-WOP-1",
                {
                    "lifecycle_state": "Active",
                    **manifest_material,
                    "manifest_digest": digest(manifest_material),
                },
            ),
            (
                "operational_configuration", "ZEUS-OPERATIONAL-CONFIGURATION-1",
                {
                    "lifecycle_state": "Active",
                    "mission_id": MISSION,
                    "work_item_id": WORK,
                    "principal_id": PRINCIPAL,
                    "activation_policy": "explicit-publication-command-only",
                },
            ),
        ]
        for record_type, record_id, payload in records:
            self.stage(record_type, record_id, payload)

    def test_complete_signed_publication_activates_and_runtime_accepts(self):
        self.complete_publication()
        readiness = self.framework.verify_readiness(self.transaction, at=AT)
        self.assertEqual(readiness["readiness"], "READY")
        target = self.directory / "active-authority.yaml"
        target.write_text(
            yaml.safe_dump(
                {"schema_version": 1, "operationally_configured": False}
            )
        )
        previous = target.read_bytes()
        with unittest.mock.patch.dict(os.environ, {"ZEUS_TESTING": "1"}):
            receipt = self.framework.activate(
                self.transaction, target=target, at=AT
            )
        self.assertEqual(receipt["state"], "ACTIVATED")
        active = load_authority_state(target)
        self.assertTrue(active["operationally_configured"])
        bundle = AuthorityResolutionRuntime(ROOT, active).resolve(
            mission_id=MISSION,
            work_item_id=WORK,
            principal_id=PRINCIPAL,
            issued_at=AT,
        )
        self.assertEqual(bundle["mode"], "operational")
        rollback = self.framework.rollback(
            self.transaction,
            target=target,
            at=datetime(2026, 7, 26, 21, 0, tzinfo=timezone.utc),
        )
        self.assertEqual(rollback["state"], "ROLLED_BACK")
        self.assertEqual(target.read_bytes(), previous)

    def test_runtime_never_self_enables_staged_candidate(self):
        self.complete_publication()
        candidate = self.framework.build_candidate(self.transaction)
        self.assertFalse(candidate["operationally_configured"])
        with self.assertRaisesRegex(
            Exception, "not operationally configured"
        ):
            AuthorityResolutionRuntime(ROOT, candidate).resolve(
                mission_id=MISSION,
                work_item_id=WORK,
                principal_id=PRINCIPAL,
                issued_at=AT,
            )

    def test_signed_revocation_disables_without_deleting_history(self):
        self.complete_publication()
        target = self.directory / "active-authority.yaml"
        target.write_text(
            yaml.safe_dump(
                {"schema_version": 1, "operationally_configured": False}
            )
        )
        with unittest.mock.patch.dict(os.environ, {"ZEUS_TESTING": "1"}):
            activation = self.framework.activate(
                self.transaction, target=target, at=AT
            )
        envelope, signature = self.envelope(
            "operational_revocation",
            "REVOCATION-ZEUS-P2-004",
            {
                "activation_transaction_id": activation["transaction_id"],
                "decision": "REVOKED",
                "reason": "qualification revocation exercise",
            },
        )
        receipt = self.framework.revoke(
            envelope_path=envelope,
            signature_path=signature,
            target=target,
            receipt_path=self.directory / "revocation-receipt.yaml",
            at=datetime(2026, 7, 26, 20, 30, tzinfo=timezone.utc),
        )
        self.assertEqual(receipt["state"], "REVOKED")
        revoked = load_authority_state(target)
        self.assertFalse(revoked["operationally_configured"])
        self.assertIn("missions", revoked)
        self.assertEqual(
            revoked["revocation"]["record_id"], "REVOCATION-ZEUS-P2-004"
        )

    def test_missing_record_type_prevents_readiness(self):
        self.stage(
            "mission_authority", MISSION, {"lifecycle_state": "active"}
        )
        with self.assertRaisesRegex(
            AuthorityPublicationError, "record types missing"
        ):
            self.framework.verify_readiness(self.transaction, at=AT)

    def test_wrong_owner_and_signature_fail_closed(self):
        envelope, signature = self.envelope(
            "approval_authority",
            "APPROVAL-ZEUS-P2-004",
            {"decision": "GRANTED"},
            owner="Untrusted Owner",
        )
        with self.assertRaisesRegex(AuthorityPublicationError, "does not own"):
            self.framework.stage(
                transaction=self.transaction,
                envelope_path=envelope,
                signature_path=signature,
            )
        good, good_signature = self.envelope(
            "mission_authority", MISSION, {"lifecycle_state": "active"}
        )
        changed = json.loads(good.read_text())
        changed["published_at"] = "2026-07-26T19:30:00Z"
        changed["envelope_id"] = envelope_identifier(changed)
        good.write_text(json.dumps(changed))
        with self.assertRaisesRegex(AuthorityPublicationError, "signature"):
            self.framework.stage(
                transaction=self.transaction,
                envelope_path=good,
                signature_path=good_signature,
            )

    def test_bad_baseline_prevents_activation(self):
        self.complete_publication()
        baseline_envelope = next(
            path
            for path in (self.transaction / "envelopes").glob("*.json")
            if json.loads(path.read_text())["record_type"] == "repository_baseline"
        )
        # Staged records are immutable in normal operation; this simulates storage
        # tampering and proves readiness re-verifies signatures rather than trusting
        # candidate.yaml.
        value = json.loads(baseline_envelope.read_text())
        value["payload"]["baseline_commit"] = "0" * 40
        baseline_envelope.write_text(json.dumps(value))
        with self.assertRaises(AuthorityPublicationError):
            self.framework.verify_readiness(self.transaction, at=AT)

    def test_unconfigured_repository_trust_policy_blocks_publication(self):
        with self.assertRaisesRegex(AuthorityPublicationError, "not configured"):
            AuthorityPublicationFramework(
                ROOT,
                policy_path=ROOT / "engineering/authority/owner-trust-policy.yaml",
            )

    def test_production_commissioning_status_is_blocked_without_owner_inputs(self):
        status = commissioning_status(ROOT)
        self.assertEqual(status["commissioning_state"], "BLOCKED")
        self.assertFalse(status["trust_policy_configured"])
        self.assertFalse(status["authority_source_configured"])
        self.assertEqual(status["allowed_signer_count"], 0)
        codes = {item["code"] for item in status["blockers"]}
        self.assertIn("OWNER_TRUST_NOT_ENROLLED", codes)
        self.assertIn("REQUIRED_RECORD_COLLECTION_EMPTY", codes)


if __name__ == "__main__":
    # unittest.mock is not imported by `import unittest` on every supported Python.
    import unittest.mock

    unittest.main()
