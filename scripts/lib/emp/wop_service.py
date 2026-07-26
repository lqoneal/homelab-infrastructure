#!/usr/bin/env python3
"""Operational WOP finalization from a sealed Authority Resolution Bundle."""

from __future__ import annotations

import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping

from scripts.lib.emp.authority_resolution import (
    AuthorityResolutionError,
    canonical_json,
    digest,
    identifier,
    validate_bundle,
)
from scripts.lib.emp.wop_admission import CONTRACT, submission_digest


class OperationalWopService:
    """Render only; it never approves, submits, admits, dispatches, or executes."""

    def generate(
        self,
        *,
        intent: str,
        bundle: Mapping[str, Any],
        repository_root: Path | str,
        at: datetime,
    ) -> dict[str, Any]:
        validate_bundle(bundle, expected_repository=repository_root, at=at)
        if not intent.strip():
            raise AuthorityResolutionError("WOP intent must be non-empty")
        wop_id = "WOP-" + str(
            uuid.uuid5(
                uuid.NAMESPACE_URL,
                canonical_json(
                    {
                        "reservation": bundle["reservations"]["wop_reservation_id"],
                        "bundle_digest": bundle["bundle_digest"],
                        "intent": intent.strip(),
                    }
                ),
            )
        )
        adr = AuthorizationDecisionService().evaluate(
            bundle=bundle, wop_id=wop_id
        )
        sections = {
            name: self._section(name, intent) for name in CONTRACT["required_sections"]
        }
        value = {
            "schema_version": 1,
            "document_type": "EngineeringWorkOrder",
            "wop_id": wop_id,
            "mission_id": bundle["mission"]["mission_id"],
            "phase_id": bundle["mission"]["phase_id"],
            "revision": bundle["mission"]["intent_revision"],
            "status": "Active",
            "title": intent.strip(),
            "repository_identity": bundle["repository"]["canonical_locator"],
            "submitter_identity": bundle["submitter"]["principal_id"],
            "approval": {
                "authority": bundle["approval"]["authority"],
                "reference": bundle["approval"]["reference"],
                "date": bundle["approval"]["decision_at"],
                "authorized_lifecycle_state": bundle["approval"][
                    "authorized_lifecycle_state"
                ],
            },
            "execution_package_references": {
                "authority_node_id": bundle["authority"]["authority_node_id"],
                "authorization_decision_record": adr["evaluation_id"],
                "immutable_wop": wop_id,
            },
            "authoritative_references": bundle["governing_baseline"]["references"],
            "sections": sections,
        }
        value["submission_digest"] = submission_digest(value)
        return {
            "wop": value,
            "authorization_decision_record": adr,
            "authority_resolution_bundle": dict(bundle),
            "authority_resolved": True,
            "review_required": True,
            "automatically_submitted": False,
            "recommendation": "Review and explicitly submit through Mission Admission.",
        }

    @staticmethod
    def _section(name: str, intent: str) -> str:
        from scripts.lib.emp.reasoning import WopGenerator

        return WopGenerator._section(name, intent)


class AuthorizationDecisionService:
    """Own the deterministic ADR identity; it cannot originate human approval."""

    VERSION = "zeus-authorization-decision/1"

    def evaluate(self, *, bundle: Mapping[str, Any], wop_id: str) -> dict[str, Any]:
        material = {
            "request": bundle["reservations"]["adr_evaluation_request_id"],
            "wop_id": wop_id,
            "bundle_digest": bundle["bundle_digest"],
            "authority_node_id": bundle["authority"]["authority_node_id"],
            "scope_digest": bundle["approval"]["scope_digest"],
        }
        record = {
            "schema_version": 1,
            "evaluation_id": identifier("ADR", material),
            "wop_id": wop_id,
            "resolution_id": bundle["resolution_id"],
            "bundle_digest": bundle["bundle_digest"],
            "authority_node_id": bundle["authority"]["authority_node_id"],
            "decision": "AUTHORIZED",
            "decision_basis": "validated sealed ARB with granted human approval",
            "evaluator_version": self.VERSION,
        }
        record["decision_digest"] = digest(record)
        return record
