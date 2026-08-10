#!/usr/bin/env python3
"""Generate immutable observational authorization decision records."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import uuid
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from scripts.lib.authority.engine import AuthorityGraph
from scripts.lib.authority_wop.compatibility import (
    CompatibilityDecision,
    CompatibilityEvaluator,
    DecisionCode,
    DigestFixtureSignatureVerifier,
)
from scripts.lib.wop.contract import (
    EvaluationState,
    ExecutionLease,
    PublicationReceipt,
    RevocationRecord,
    WorkPackage,
    _parse_time,
    load_mapping,
)


SOFTWARE_VERSIONS = {
    "adr_schema": "1",
    "authority_engine": "1",
    "compatibility_layer": "1",
    "engctl": "0.9.0",
    "eos_platform": "shadow-1",
    "shadow_authorization": "1",
    "wop_contract": "1",
}


def _canonical_json(value: Mapping[str, Any]) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _utc_text(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _digest(value: Mapping[str, Any]) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class AuthorizationDecisionRecord:
    """Immutable evidence for one legacy/Zeus shadow comparison."""

    canonical_data: str

    @classmethod
    def from_mapping(
        cls, value: Mapping[str, Any]
    ) -> "AuthorizationDecisionRecord":
        normalized = json.loads(json.dumps(value))
        return cls(_canonical_json(normalized))

    @property
    def data(self) -> dict[str, Any]:
        return json.loads(self.canonical_data)

    def to_json(self) -> str:
        return json.dumps(
            self.data, indent=2, sort_keys=True, separators=(",", ": ")
        ) + "\n"

    def persist(self, directory: Path | str) -> Path:
        target_dir = Path(directory)
        target_dir.mkdir(parents=True, exist_ok=True)
        target = target_dir / f"{self.data['evaluation_id']}.json"
        serialized = self.to_json()
        try:
            with target.open("x", encoding="utf-8") as stream:
                stream.write(serialized)
                stream.flush()
                os.fsync(stream.fileno())
        except FileExistsError:
            if target.read_text(encoding="utf-8") != serialized:
                raise ValueError(
                    f"immutable ADR collision for {self.data['evaluation_id']}"
                )
        return target


class ShadowAuthorizationService:
    """Compare legacy and Zeus decisions without changing legacy enforcement."""

    def evaluate(
        self,
        *,
        graph: AuthorityGraph,
        wop: WorkPackage,
        state: EvaluationState,
        receipt: PublicationReceipt,
        reference_time: datetime,
        legacy_authorized: bool,
        repository_identity: str,
        repository_baseline_commit: str,
        signature_verifier=DigestFixtureSignatureVerifier(),
        expected_authority_node_id: str | None = None,
        lease: ExecutionLease | None = None,
        revocation: RevocationRecord | None = None,
        enforcement_mode: str | None = None,
    ) -> AuthorizationDecisionRecord:
        zeus = CompatibilityEvaluator().evaluate(
            graph=graph,
            wop=wop,
            state=state,
            receipt=receipt,
            reference_time=reference_time,
            signature_verifier=signature_verifier,
            expected_authority_node_id=expected_authority_node_id,
            lease=lease,
            revocation=revocation,
        )
        if enforcement_mode in ("enforcement", "rollback"):
            context_mismatches = []
            if state.repository != repository_identity:
                context_mismatches.append("repository")
            if state.baseline_commit != repository_baseline_commit:
                context_mismatches.append("baseline_commit")
            if context_mismatches:
                mismatch_text = ",".join(sorted(context_mismatches))
                zeus = replace(
                    zeus,
                    decision=DecisionCode.EXECUTION_CONTEXT_MISMATCH,
                    reasons=(
                        "observed repository context mismatch: " + mismatch_text,
                    ),
                    input_digest=hashlib.sha256(
                        (
                            zeus.input_digest
                            + repository_identity
                            + repository_baseline_commit
                            + mismatch_text
                        ).encode("utf-8")
                    ).hexdigest(),
                )
        return self._record(
            zeus=zeus,
            wop=wop,
            state=state,
            receipt=receipt,
            reference_time=reference_time,
            legacy_authorized=legacy_authorized,
            repository_identity=repository_identity,
            repository_baseline_commit=repository_baseline_commit,
            lease=lease,
            revocation=revocation,
            enforcement_mode=enforcement_mode,
        )

    def validation_failure(
        self,
        *,
        reason: str,
        reference_time: datetime,
        legacy_authorized: bool,
        repository_identity: str,
        repository_baseline_commit: str,
        enforcement_mode: str | None = None,
    ) -> AuthorizationDecisionRecord:
        zeus = CompatibilityDecision(
            decision=DecisionCode.VALIDATION_FAILURE,
            wop_id="",
            authority_node_id="",
            authority_chain=(),
            effective_capabilities=(),
            requested_capabilities=(),
            requested_effects=(),
            reasons=(reason,),
            input_digest=hashlib.sha256(reason.encode("utf-8")).hexdigest(),
        )
        empty_wop = WorkPackage.from_mapping({})
        empty_state = EvaluationState(
            prerequisite_evidence=frozenset(),
            satisfied_dependencies=frozenset(),
            requested_effects=frozenset(),
            principal_id="unknown",
            repository=repository_identity,
            baseline_commit=repository_baseline_commit,
            branch="unknown",
        )
        return self._record(
            zeus=zeus,
            wop=empty_wop,
            state=empty_state,
            receipt=None,
            reference_time=reference_time,
            legacy_authorized=legacy_authorized,
            repository_identity=repository_identity,
            repository_baseline_commit=repository_baseline_commit,
            lease=None,
            revocation=None,
            enforcement_mode=enforcement_mode,
        )

    def _record(
        self,
        *,
        zeus: CompatibilityDecision,
        wop: WorkPackage,
        state: EvaluationState,
        receipt: PublicationReceipt | None,
        reference_time: datetime,
        legacy_authorized: bool,
        repository_identity: str,
        repository_baseline_commit: str,
        lease: ExecutionLease | None,
        revocation: RevocationRecord | None,
        enforcement_mode: str | None,
    ) -> AuthorizationDecisionRecord:
        data = wop.data
        binding = data.get("authority_binding", {})
        if not isinstance(binding, Mapping):
            binding = {}
        context = data.get("execution_context", {})
        if not isinstance(context, Mapping):
            context = {}
        authorized_effects = data.get("authorized_effects", [])
        if not isinstance(authorized_effects, list):
            authorized_effects = []
        prohibited_effects = data.get("prohibited_effects", [])
        if not isinstance(prohibited_effects, list):
            prohibited_effects = []

        prerequisites = data.get("prerequisites", [])
        if not isinstance(prerequisites, list):
            prerequisites = []
        prerequisite_required = sorted(
            str(item.get("evidence_ref"))
            for item in prerequisites
            if isinstance(item, Mapping) and item.get("required") is True
        )
        prerequisite_present = sorted(state.prerequisite_evidence)

        dependencies = data.get("dependencies", [])
        if not isinstance(dependencies, list):
            dependencies = []
        dependency_required = sorted(
            str(item.get("wop_id"))
            for item in dependencies
            if isinstance(item, Mapping) and item.get("required") is True
        )
        dependency_present = sorted(state.satisfied_dependencies)

        legacy = "AUTHORIZED" if legacy_authorized else "REJECTED"
        agree = legacy_authorized == zeus.authorized
        if agree:
            disagreement = "NONE"
            first_divergence = "NONE"
        elif legacy_authorized:
            disagreement = "LEGACY_ALLOW_ZEUS_DENY"
            first_divergence = zeus.decision.value
        else:
            disagreement = "LEGACY_DENY_ZEUS_ALLOW"
            first_divergence = "LEGACY_AUTHORIZATION"

        if enforcement_mode not in (None, "shadow", "enforcement", "rollback"):
            raise ValueError(f"unknown authorization mode: {enforcement_mode}")
        authoritative_source = (
            "ZEUS" if enforcement_mode == "enforcement" else "LEGACY"
        )
        enforcement_decision = (
            "AUTHORIZED" if zeus.authorized else "REJECTED"
            if enforcement_mode == "enforcement"
            else legacy
        )
        if enforcement_mode != "enforcement":
            enforcement_decision = legacy

        decision_material = {
            "authority_chain": list(zeus.authority_chain),
            "authority_node": zeus.authority_node_id,
            "effective_capabilities": list(zeus.effective_capabilities),
            "legacy_decision": legacy,
            "requested_capabilities": list(zeus.requested_capabilities),
            "requested_effects": list(zeus.requested_effects),
            "wop_id": zeus.wop_id,
            "zeus_decision": zeus.decision.value,
            "zeus_input_digest": zeus.input_digest,
        }
        if enforcement_mode is not None:
            decision_material.update(
                {
                    "authoritative_decision_source": authoritative_source,
                    "enforcement_decision": enforcement_decision,
                    "enforcement_mode": enforcement_mode.upper(),
                    "rollback_status": (
                        "ACTIVE" if enforcement_mode == "rollback" else "AVAILABLE"
                    ),
                }
            )
        decision_digest = _digest(decision_material)
        evaluation_material = {
            "decision_digest": decision_digest,
            "evaluation_timestamp": _utc_text(reference_time),
            "repository_baseline_commit": repository_baseline_commit,
            "repository_identity": repository_identity,
        }
        evaluation_id = "ADR-" + str(
            uuid.uuid5(uuid.NAMESPACE_URL, _canonical_json(evaluation_material))
        )

        receipt_valid = bool(
            receipt
            and receipt.wop_id == wop.wop_id
            and receipt.payload_digest == wop.payload_digest
            and receipt.published_at <= reference_time.astimezone(timezone.utc)
        )
        lease_policy = data.get("lease_policy", {})
        maximum_lease = (
            lease_policy.get("maximum_duration_seconds", 0)
            if isinstance(lease_policy, Mapping)
            else 0
        )
        lease_valid = bool(
            lease
            and lease.wop_id == wop.wop_id
            and lease.payload_digest == wop.payload_digest
            and lease.holder_id == state.principal_id
            and lease.issued_at
            <= reference_time.astimezone(timezone.utc)
            < lease.expires_at
            and (lease.expires_at - lease.issued_at).total_seconds()
            <= maximum_lease
        )

        record = {
            "schema_version": 1 if enforcement_mode is None else 2,
            "evaluation_id": evaluation_id,
            "evaluation_timestamp": _utc_text(reference_time),
            "repository_identity": repository_identity,
            "repository_baseline_commit": repository_baseline_commit,
            "authority_node": zeus.authority_node_id,
            "authority_chain": list(zeus.authority_chain),
            "mission": str(binding.get("mission_id", "")),
            "phase": str(binding.get("phase_id", "")),
            "work_item": str(binding.get("work_item_id", "")),
            "wop_id": zeus.wop_id,
            "execution_context": dict(context),
            "requested_capabilities": list(zeus.requested_capabilities),
            "resolved_capabilities": list(zeus.effective_capabilities),
            "authorized_effects": authorized_effects,
            "prohibited_effects": prohibited_effects,
            "prerequisite_evaluation": {
                "required": prerequisite_required,
                "present": prerequisite_present,
                "missing": sorted(
                    set(prerequisite_required) - set(prerequisite_present)
                ),
            },
            "dependency_evaluation": {
                "required": dependency_required,
                "present": dependency_present,
                "missing": sorted(
                    set(dependency_required) - set(dependency_present)
                ),
            },
            "lease_status": "VALID" if lease_valid else "INVALID_OR_ABSENT",
            "receipt_status": "VALID" if receipt_valid else "INVALID_OR_ABSENT",
            "signature_status": (
                "VALID"
                if zeus.decision is not DecisionCode.SIGNATURE_FAILURE
                and bool(wop.data.get("signature"))
                else "INVALID_OR_ABSENT"
            ),
            "revocation_status": "PRESENT" if revocation else "ABSENT",
            "legacy_authorization_decision": legacy,
            "zeus_authorization_decision": zeus.decision.value,
            "agreement_status": "AGREEMENT" if agree else "DISAGREEMENT",
            "disagreement_classification": disagreement,
            "first_divergent_decision_point": first_divergence,
            "structured_reason_code": zeus.decision.value,
            "decision_reasons": list(zeus.reasons),
            "decision_digest": decision_digest,
            "software_versions": SOFTWARE_VERSIONS,
            "shadow_only": enforcement_mode in (None, "shadow"),
            "enforcement_authority": authoritative_source,
            "enforcement_decision": enforcement_decision,
        }
        if enforcement_mode is not None:
            record.update(
                {
                    "enforcement_mode": enforcement_mode.upper(),
                    "authoritative_decision_source": authoritative_source,
                    "legacy_comparison_result": legacy,
                    "rollback_status": (
                        "ACTIVE" if enforcement_mode == "rollback" else "AVAILABLE"
                    ),
                }
            )
        return AuthorizationDecisionRecord.from_mapping(record)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--legacy-decision", choices=("authorized", "rejected"), required=True)
    parser.add_argument("--output-directory", type=Path, required=True)
    parser.add_argument("--at")
    parser.add_argument("--authority-graph", type=Path)
    parser.add_argument("--wop", type=Path)
    parser.add_argument("--state", type=Path)
    parser.add_argument("--receipt", type=Path)
    parser.add_argument("--lease", type=Path)
    parser.add_argument("--revocation", type=Path)
    parser.add_argument("--expected-authority")
    parser.add_argument(
        "--mode",
        choices=("shadow", "enforcement", "rollback"),
        default="shadow",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    now = (
        _parse_time(args.at, "evaluation time")
        if args.at
        else datetime.now(timezone.utc)
    )
    repository = str(args.repository.resolve())
    try:
        baseline = (
            __import__("subprocess")
            .run(
                ["git", "-C", repository, "rev-parse", "HEAD"],
                check=True,
                text=True,
                capture_output=True,
            )
            .stdout.strip()
        )
    except Exception:
        baseline = "unknown"
    legacy_authorized = args.legacy_decision == "authorized"
    service = ShadowAuthorizationService()
    required = (args.authority_graph, args.wop, args.state, args.receipt)
    try:
        if any(path is None for path in required):
            raise ValueError("shadow authorization inputs are incomplete")
        wop = WorkPackage.load(args.wop)
        record = service.evaluate(
            graph=AuthorityGraph.load(args.authority_graph),
            wop=wop,
            state=EvaluationState.from_mapping(load_mapping(args.state, "evaluation")),
            receipt=PublicationReceipt.from_mapping(
                load_mapping(args.receipt, "publication receipt")
            ),
            lease=(
                ExecutionLease.from_mapping(load_mapping(args.lease, "execution lease"))
                if args.lease
                else None
            ),
            revocation=(
                RevocationRecord.from_mapping(
                    load_mapping(args.revocation, "revocation record")
                )
                if args.revocation
                else None
            ),
            reference_time=now,
            legacy_authorized=legacy_authorized,
            repository_identity=repository,
            repository_baseline_commit=baseline,
            expected_authority_node_id=args.expected_authority,
            enforcement_mode=args.mode,
        )
    except Exception as error:
        record = service.validation_failure(
            reason=str(error),
            reference_time=now,
            legacy_authorized=legacy_authorized,
            repository_identity=repository,
            repository_baseline_commit=baseline,
            enforcement_mode=args.mode,
        )
    target = record.persist(args.output_directory)
    print(
        _canonical_json(
            {
                "adr": str(target),
                "agreement": record.data["agreement_status"],
                "enforcement_decision": record.data["enforcement_decision"],
                "shadow_decision": record.data["zeus_authorization_decision"],
            }
        )
    )
    if args.mode == "shadow":
        return 0
    return 0 if record.data["enforcement_decision"] == "AUTHORIZED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
