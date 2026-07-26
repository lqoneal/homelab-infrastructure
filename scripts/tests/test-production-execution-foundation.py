#!/usr/bin/env python3
"""Production-faithful qualification for the P2-019 execution foundation."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.lib.emp.production_execution import (  # noqa: E402
    AuthenticatedEventLog,
    LIFECYCLE_EVENTS,
    LocalAuthenticatedAgent,
    LiveReconciliationAdapters,
    ProductionExecutionError,
    create_evidence_attestation,
    digest,
    dispatch_readiness,
    independently_qualify_evidence,
)
from scripts.lib.emp.work_authority_lifecycle import (  # noqa: E402
    WorkAuthorityError,
    authorize,
    digest as authority_digest,
    transition,
    validate_record,
)

AT = datetime(2026, 7, 26, 23, 30, tzinfo=timezone.utc)
BASELINE = "a" * 40
REPOSITORY = "/production/repository"


class FoundationQualificationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.key = self.root / "agent-key"
        subprocess.run(
            ["ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-f", str(self.key)],
            check=True,
        )
        public = (self.key.with_suffix(".pub")).read_text().strip()
        self.allowed = self.root / "allowed-signers"
        self.allowed.write_text(f"agent {public}\nloneal {public}\n")
        self.activation = {
            "schema_version": 1,
            "dispatcher_id": "ZEUS-PRODUCTION-DISPATCHER",
            "implementation_version": "zeus-production-execution/1",
            "repository_identity": REPOSITORY,
            "repository_baseline": BASELINE,
            "policy_version": 1,
            "status": "ACTIVE",
            "activating_authority": "loneal",
            "activated_at": "2026-07-26T23:30:00Z",
            "supported_mission_classes": ["engineering"],
            "supported_agent_classes": ["local-authenticated"],
            "eens_configuration": "eens",
            "evidence_configuration": "evidence",
            "reconciliation_adapters": ["live"],
            "revoked": False,
            "suspended": False,
        }
        self.activation["record_digest"] = digest(self.activation)
        self.agent = {
            "agent_id": "prod-local-1",
            "agent_type": "local-authenticated",
            "host_identity": "qualification-host",
            "service_identity": "agent",
            "supported_mission_classes": ["engineering"],
            "supported_tools": ["bounded-artifact"],
            "repository_access_scope": [REPOSITORY],
            "execution_constraints": ["qualification-side-effects"],
            "qualification_status": "QUALIFIED",
            "qualification_evidence": ["P2-019-integrated-harness"],
            "active": True,
            "last_validated_at": "2026-07-26T23:30:00Z",
            "trust_binding": "ssh-ed25519-agent",
            "eens_identity": "agent",
            "evidence_signing_identity": "agent",
            "interruption_resume_capable": True,
            "concurrency_limit": 1,
        }
        self.activation_path = self.root / "activation.json"
        self.activation_path.write_text(json.dumps(self.activation))
        unsigned = {
            "schema_version": 2, "registry_id": "production", "agents": [self.agent]
        }
        unsigned["registry_digest"] = digest(unsigned)
        self.registry_path = self.root / "registry.json"
        self.registry_path.write_text(json.dumps(unsigned))
        self.dependencies = [self.root / name for name in ("policy", "eens", "evidence")]
        for path in self.dependencies:
            path.touch()

    def tearDown(self):
        self.temporary.cleanup()

    def test_authorized_and_denied_dispatch_readiness(self):
        ready = dispatch_readiness(
            repository=REPOSITORY, baseline=BASELINE,
            activation_path=self.activation_path, registry_path=self.registry_path,
            mission_class="engineering", required_paths=self.dependencies,
        )
        self.assertTrue(ready["dispatch_permitted"])
        self.assertEqual(ready["eligible_agents"], ["prod-local-1"])
        denied = dispatch_readiness(
            repository=REPOSITORY, baseline="b" * 40,
            activation_path=self.activation_path, registry_path=self.registry_path,
            mission_class="engineering", required_paths=self.dependencies,
        )
        self.assertFalse(denied["dispatch_permitted"])
        self.assertEqual(
            denied["blocking_reasons"][0]["code"], "DISPATCHER_ACTIVATION_INVALID"
        )

    def test_authenticated_invocation_eens_evidence_and_independent_qualification(self):
        assignment = {
            "assignment_id": "EA-1", "intended_execution_agent": "prod-local-1",
            "wop_digest": "",
        }
        wop = {"wop_id": "WOP-1", "mission_id": "MISSION-1", "action": "bounded"}
        assignment["wop_digest"] = digest(wop)
        invocation = LocalAuthenticatedAgent(
            self.agent, self.root / "invocations",
            lambda value: {"status": "COMPLETED", "evidence_locators": ["output"]},
            agent_key=self.key, allowed_signers=self.allowed,
            invoking_principal="loneal",
        )
        token_payload = {
            "assignment_digest": digest(assignment), "invoking_principal": "loneal"
        }
        invocation_signature = self.root / "invocation.sig"
        from scripts.lib.emp.production_execution import sign_ssh
        sign_ssh(
            json.dumps(token_payload, sort_keys=True, separators=(",", ":")).encode(),
            self.key, "zeus-agent-invocation", invocation_signature,
        )
        token = {**token_payload, "signature_path": str(invocation_signature)}
        first = invocation.invoke(assignment, wop, invocation_token=token)
        self.assertEqual(first, invocation.invoke(assignment, wop, invocation_token=token))
        self.assertEqual(first["status"], "COMPLETED")

        log = AuthenticatedEventLog(
            self.root / "events", key=self.key, allowed_signers=self.allowed,
            principal="agent",
        )
        event = log.emit(
            "execution.completed", "MISSION-1", "EA-1", first, at=AT,
            idempotency_key="EA-1:completed",
        )
        self.assertEqual(
            event,
            log.emit("execution.completed", "MISSION-1", "EA-1", first, at=AT,
                     idempotency_key="EA-1:completed"),
        )
        self.assertEqual(len(log.replay("qualifier", self.root / "checkpoint.json")), 1)
        self.assertEqual(log.replay("qualifier", self.root / "checkpoint.json"), [])
        for sequence, event_type in enumerate(LIFECYCLE_EVENTS):
            log.emit(
                event_type, "MISSION-1", "EA-1", {"sequence": sequence}, at=AT,
                idempotency_key=f"EA-1:{event_type}",
            )
        replayed = log.replay("lifecycle-audit", self.root / "lifecycle-checkpoint.json")
        self.assertEqual(
            {item["event_type"] for item in replayed}, set(LIFECYCLE_EVENTS)
        )

        output = b"qualified bounded output"
        evidence = {
            "wop_id": "WOP-1", "mission_id": "MISSION-1",
            "assignment_id": "EA-1", "agent_id": "prod-local-1",
            "repository_identity": REPOSITORY, "repository_baseline": BASELINE,
            "executed_gate": "VERIFY_COMPLETION", "action_record": "bounded",
            "started_at": "2026-07-26T23:29:00Z",
            "completed_at": "2026-07-26T23:30:00Z",
            "output_locator": "output", "output_digest": hashlib.sha256(output).hexdigest(),
            "validation_result": "PASS",
        }
        signature = self.root / "evidence.sig"
        attestation = create_evidence_attestation(
            evidence=evidence, key=self.key, signature_path=signature
        )
        report = independently_qualify_evidence(
            attestation, signature_path=signature, allowed_signers=self.allowed,
            agent_principal="agent", qualifier_principal="zeus-evidence-qualifier",
            expected=evidence,
        )
        self.assertEqual(report["decision"], "PASS")
        adapters = LiveReconciliationAdapters(self.root / "live-records")
        reconciled = adapters.reconcile(
            "mission_state", "missions/MISSION-1.json",
            {"mission_id": "MISSION-1", "state": "QUALIFICATION_COMPLETE"},
            expected_digest=None,
        )
        self.assertEqual(reconciled["status"], "UPDATED")
        replay = adapters.reconcile(
            "mission_state", "missions/MISSION-1.json",
            {"mission_id": "MISSION-1", "state": "QUALIFICATION_COMPLETE"},
            expected_digest=reconciled["digest"],
        )
        self.assertEqual(replay["status"], "UNCHANGED")
        with self.assertRaisesRegex(ProductionExecutionError, "self-qualified"):
            independently_qualify_evidence(
                attestation, signature_path=signature, allowed_signers=self.allowed,
                agent_principal="agent", qualifier_principal="agent", expected=evidence,
            )

    def test_first_qualification_authority_lifecycle_is_strict(self):
        record = {
            "schema_version": 1, "work_id": "ZEUS-P2-019",
            "owner": "Lawrence O'Neal", "principal": "loneal",
            "state": "PLANNED", "authorization_reference": "ZEUS-P2-019",
            "scope": ["production-execution-foundation"],
            "history": [{
                "from": None, "to": "PLANNED",
                "authorization_reference": "ZEUS-P2-019",
                "evidence_reference": "mission-handoff",
                "occurred_at": "2026-07-26T23:30:00Z",
            }],
        }
        record["record_digest"] = authority_digest(record)
        validate_record(record)
        with self.assertRaises(WorkAuthorityError):
            authorize(record, "implementation")
        record = transition(
            record, "AUTHORIZED_FOR_IMPLEMENTATION",
            authorization_reference="ZEUS-P2-019",
            occurred_at=AT, evidence_reference="authenticated-cli-instruction",
        )
        self.assertEqual(authorize(record, "implementation")["work_id"], "ZEUS-P2-019")
        with self.assertRaises(WorkAuthorityError):
            transition(
                record, "QUALIFIED", authorization_reference="invalid-skip",
                occurred_at=AT, evidence_reference="none",
            )


if __name__ == "__main__":
    unittest.main()
