#!/usr/bin/env python3
"""ZEUS-P2-003 Authority Resolution Runtime qualification tests."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.lib.authority.engine import AuthorityGraph  # noqa: E402
from scripts.lib.emp.authority_resolution import (  # noqa: E402
    AuthorityResolutionError,
    AuthorityResolutionRuntime,
    digest,
    validate_bundle,
)
from scripts.lib.emp.wop_admission import AdmissionController  # noqa: E402
from scripts.lib.emp.wop_service import OperationalWopService  # noqa: E402

AT = datetime(2026, 7, 26, 12, 0, tzinfo=timezone.utc)
MISSION = "EMP-MISSION-ZEUS-OPERATIONAL-ALPHA"
PHASE = "EMP-PHASE-ZEUS-OPERATIONAL-ALPHA"
WORK = "EMP-WORK-ZEUS-P2-003-QUALIFICATION"
PRINCIPAL = "loneal"
GRAPH_PATH = "engineering/authority/fixtures/valid.yaml"


def record(record_id: str, owner: str, **values):
    return {
        "record_id": record_id,
        "record_revision": 1,
        "owner": owner,
        **values,
    }


def authoritative_state() -> dict:
    head = subprocess.run(
        ["git", "-C", str(ROOT), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    graph = AuthorityGraph.load(ROOT / GRAPH_PATH)
    resolution = graph.resolve("work-package")
    chain = list(resolution.path)
    capabilities = sorted(resolution.effective_capabilities)
    authority_digest = digest(
        {"graph_id": graph.graph_id, "chain": chain, "capabilities": capabilities}
    )
    scope_digest = digest(
        {"mission_id": MISSION, "phase_id": PHASE, "work_item_id": WORK}
    )
    references = [
        "PROC-0001@1.11",
        "TPL-0001@1.7",
        "STD-0000",
        "STD-0001",
        "STD-0002",
        "STD-0003",
        "STD-0004",
    ]
    manifest_material = {
        "manifest_id": "GOVERNING-ZEUS-WOP-1",
        "manifest_revision": 1,
        "references": references,
    }
    return {
        "schema_version": 1,
        "operationally_configured": True,
        "missions": {
            MISSION: record(
                MISSION, "Lawrence O'Neal", lifecycle_state="active"
            )
        },
        "phases": {
            PHASE: record(
                PHASE,
                "Lawrence O'Neal",
                mission_id=MISSION,
                lifecycle_state="active",
            )
        },
        "work_items": {
            WORK: record(
                WORK,
                "Lawrence O'Neal",
                mission_id=MISSION,
                phase_id=PHASE,
                lifecycle_state="qualified",
                qualification_status="QUALIFIED",
                qualification_record="QUAL-ZEUS-P2-003",
                revision=1,
                approval_reference="APPROVAL-ZEUS-P2-003",
                authority_binding_id="AUTHORITY-BINDING-ZEUS-P2-003",
                scope_digest=scope_digest,
            )
        },
        "repositories": {
            "homelab": record(
                "REPOSITORY-HOMELAB",
                "Lawrence O'Neal",
                repository_id="REPOSITORY-HOMELAB",
                canonical_locator=str(ROOT),
                baseline_commit=head,
                assertion_id="REPOSITORY-ASSERTION-ZEUS-P2-003",
            )
        },
        "approvals": {
            "APPROVAL-ZEUS-P2-003": record(
                "APPROVAL-ZEUS-P2-003",
                "Lawrence O'Neal",
                reference="APPROVAL-ZEUS-P2-003",
                authority="Human Engineering Authority",
                decision="GRANTED",
                decision_at="2026-07-26T11:00:00Z",
                authorized_lifecycle_state="Active",
                scope_digest=scope_digest,
            )
        },
        "authority_bindings": {
            "AUTHORITY-BINDING-ZEUS-P2-003": record(
                "AUTHORITY-BINDING-ZEUS-P2-003",
                "Lawrence O'Neal",
                graph_path=GRAPH_PATH,
                authority_node_id="work-package",
                graph_version=graph.graph_id,
                chain=chain,
                capabilities=capabilities,
                resolution_digest=authority_digest,
            )
        },
        "governing_baselines": {
            "GOVERNING-ZEUS-WOP-1": record(
                "GOVERNING-ZEUS-WOP-1",
                "Lawrence O'Neal",
                lifecycle_state="Active",
                **manifest_material,
                manifest_digest=digest(manifest_material),
            )
        },
        "principals": {
            PRINCIPAL: record(
                PRINCIPAL,
                "Lawrence O'Neal",
                authentication_status="VERIFIED",
                session_id="SESSION-ZEUS-P2-003",
                authentication_record="AUTHN-ZEUS-P2-003",
            )
        },
    }


class AuthorityResolutionRuntimeTests(unittest.TestCase):
    def bundle(self, state=None):
        return AuthorityResolutionRuntime(
            ROOT, state or authoritative_state()
        ).resolve(
            mission_id=MISSION,
            work_item_id=WORK,
            principal_id=PRINCIPAL,
            issued_at=AT,
        )

    def test_resolves_and_seals_complete_bundle(self):
        first = self.bundle()
        second = self.bundle()
        self.assertEqual(first, second)
        self.assertEqual(first["mode"], "operational")
        self.assertEqual(first["mission"]["work_item_id"], WORK)
        self.assertEqual(
            {item["field"] for item in first["provenance"]},
            {
                "mission", "phase", "work_item", "repository", "approval",
                "authority", "governing_baseline", "submitter",
            },
        )
        validate_bundle(first, expected_repository=ROOT, at=AT)

    def test_operational_wop_uses_only_resolved_values(self):
        result = OperationalWopService().generate(
            intent="Implement bounded authority resolution runtime",
            bundle=self.bundle(),
            repository_root=ROOT,
            at=AT,
        )
        wop = result["wop"]
        self.assertTrue(result["authority_resolved"])
        self.assertTrue(result["review_required"])
        self.assertFalse(result["automatically_submitted"])
        self.assertEqual(
            result["authorization_decision_record"]["decision"], "AUTHORIZED"
        )
        self.assertEqual(
            result["authorization_decision_record"]["evaluation_id"],
            wop["execution_package_references"]["authorization_decision_record"],
        )
        self.assertEqual(wop["approval"]["reference"], "APPROVAL-ZEUS-P2-003")
        self.assertEqual(
            wop["execution_package_references"]["authority_node_id"], "work-package"
        )
        self.assertEqual(
            wop["execution_package_references"]["immutable_wop"], wop["wop_id"]
        )
        self.assertTrue(
            wop["execution_package_references"][
                "authorization_decision_record"
            ].startswith("ADR-")
        )
        self.assertEqual(AdmissionController().validate(wop, str(ROOT)), ())

    def test_owner_lifecycle_scope_and_authentication_fail_closed(self):
        mutations = (
            lambda value: value["approvals"]["APPROVAL-ZEUS-P2-003"].update(
                owner="WOP Service"
            ),
            lambda value: value["work_items"][WORK].update(
                lifecycle_state="superseded"
            ),
            lambda value: value["approvals"]["APPROVAL-ZEUS-P2-003"].update(
                scope_digest="0" * 64
            ),
            lambda value: value["principals"][PRINCIPAL].update(
                authentication_status="UNVERIFIED"
            ),
        )
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                state = authoritative_state()
                mutation(state)
                with self.assertRaises(AuthorityResolutionError):
                    self.bundle(state)

    def test_repository_and_authority_disagreement_fail_closed(self):
        for collection, record_id, field, value in (
            ("repositories", "homelab", "baseline_commit", "0" * 40),
            (
                "authority_bindings",
                "AUTHORITY-BINDING-ZEUS-P2-003",
                "resolution_digest",
                "0" * 64,
            ),
        ):
            with self.subTest(field=field):
                state = authoritative_state()
                state[collection][record_id][field] = value
                with self.assertRaises(AuthorityResolutionError):
                    self.bundle(state)

    def test_placeholder_and_tampered_seal_fail_closed(self):
        state = authoritative_state()
        state["approvals"]["APPROVAL-ZEUS-P2-003"][
            "reference"
        ] = "PLACEHOLDER-APPROVAL"
        with self.assertRaisesRegex(AuthorityResolutionError, "placeholder"):
            self.bundle(state)
        bundle = self.bundle()
        bundle["mission"]["intent_revision"] = 2
        with self.assertRaisesRegex(AuthorityResolutionError, "seal"):
            validate_bundle(bundle, expected_repository=ROOT, at=AT)

    def test_incomplete_source_state_fails_closed(self):
        state = authoritative_state()
        del state["approvals"]
        with self.assertRaisesRegex(AuthorityResolutionError, "incomplete"):
            self.bundle(state)

    def test_operational_cli_has_no_manual_authority_inputs(self):
        with tempfile.TemporaryDirectory() as temporary:
            state_path = Path(temporary) / "authority.yaml"
            state_path.write_text(yaml.safe_dump(authoritative_state(), sort_keys=True))
            result = subprocess.run(
                [
                    str(ROOT / "scripts/zeus"),
                    "--state", str(Path(temporary) / "orchestration.json"),
                    "generate-wop",
                    "Implement bounded authority resolution runtime",
                    "--mode", "operational",
                    "--mission", MISSION,
                    "--work-item", WORK,
                    "--principal", PRINCIPAL,
                    "--repository", str(ROOT),
                    "--at", "2026-07-26T12:00:00Z",
                ],
                capture_output=True,
                text=True,
                env={
                    **os.environ,
                    "ZEUS_TESTING": "1",
                    "ZEUS_AUTHORITY_STATE": str(state_path),
                },
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            output = json.loads(result.stdout)
            self.assertTrue(output["authority_resolved"])
            self.assertEqual(
                output["wop"]["approval"]["reference"], "APPROVAL-ZEUS-P2-003"
            )

            rejected = subprocess.run(
                [
                    str(ROOT / "scripts/zeus"),
                    "--state", str(Path(temporary) / "orchestration.json"),
                    "generate-wop", "Invalid override",
                    "--mode", "operational",
                    "--mission", MISSION,
                    "--work-item", WORK,
                    "--principal", PRINCIPAL,
                    "--repository", str(ROOT),
                    "--approval-reference", "MANUAL-ID",
                ],
                capture_output=True,
                text=True,
                env={
                    **os.environ,
                    "ZEUS_TESTING": "1",
                    "ZEUS_AUTHORITY_STATE": str(state_path),
                },
            )
            self.assertEqual(rejected.returncode, 78)
            self.assertIn("rejects caller-supplied authority", rejected.stderr)

    def test_qualification_cli_preserves_placeholders_and_review_boundary(self):
        with tempfile.TemporaryDirectory() as temporary:
            result = subprocess.run(
                [
                    str(ROOT / "scripts/zeus"),
                    "--state", str(Path(temporary) / "orchestration.json"),
                    "generate-wop", "Qualification-only package",
                    "--mission", "ZEUS-P2-003-QUALIFICATION",
                    "--repository", str(ROOT),
                ],
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            output = json.loads(result.stdout)
            self.assertTrue(output["review_required"])
            self.assertFalse(output["automatically_submitted"])
            self.assertEqual(
                output["wop"]["approval"]["reference"],
                "PLACEHOLDER-APPROVAL-REFERENCE",
            )


if __name__ == "__main__":
    unittest.main()
