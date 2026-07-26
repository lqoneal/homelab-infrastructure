#!/usr/bin/env python3
"""Pure offline compatibility evaluation for authority graphs and WOPs."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Mapping

from scripts.lib.authority.engine import AuthorityGraph
from scripts.lib.wop.contract import (
    EvaluationState,
    ExecutionLease,
    PublicationReceipt,
    RevocationRecord,
    SignatureVerifier,
    WorkPackage,
    WorkPackageError,
    _parse_time,
    load_mapping,
)


class DecisionCode(str, Enum):
    AUTHORIZED = "AUTHORIZED"
    INVALID_WOP = "INVALID_WOP"
    INVALID_AUTHORITY_GRAPH = "INVALID_AUTHORITY_GRAPH"
    UNKNOWN_AUTHORITY = "UNKNOWN_AUTHORITY"
    AUTHORITY_BINDING_MISMATCH = "AUTHORITY_BINDING_MISMATCH"
    CAPABILITY_NOT_AUTHORIZED = "CAPABILITY_NOT_AUTHORIZED"
    EXECUTION_CONTEXT_MISMATCH = "EXECUTION_CONTEXT_MISMATCH"
    EFFECT_NOT_AUTHORIZED = "EFFECT_NOT_AUTHORIZED"
    PROHIBITED_EFFECT_REQUESTED = "PROHIBITED_EFFECT_REQUESTED"
    PREREQUISITE_FAILURE = "PREREQUISITE_FAILURE"
    DEPENDENCY_FAILURE = "DEPENDENCY_FAILURE"
    EXPIRED = "EXPIRED"
    REVOKED = "REVOKED"
    INVALID_LEASE = "INVALID_LEASE"
    INVALID_PUBLICATION_RECEIPT = "INVALID_PUBLICATION_RECEIPT"
    SIGNATURE_FAILURE = "SIGNATURE_FAILURE"
    VALIDATION_FAILURE = "VALIDATION_FAILURE"


DECISION_PRECEDENCE = (
    DecisionCode.INVALID_WOP,
    DecisionCode.INVALID_AUTHORITY_GRAPH,
    DecisionCode.UNKNOWN_AUTHORITY,
    DecisionCode.AUTHORITY_BINDING_MISMATCH,
    DecisionCode.SIGNATURE_FAILURE,
    DecisionCode.INVALID_PUBLICATION_RECEIPT,
    DecisionCode.EXPIRED,
    DecisionCode.REVOKED,
    DecisionCode.INVALID_LEASE,
    DecisionCode.EXECUTION_CONTEXT_MISMATCH,
    DecisionCode.PREREQUISITE_FAILURE,
    DecisionCode.DEPENDENCY_FAILURE,
    DecisionCode.CAPABILITY_NOT_AUTHORIZED,
    DecisionCode.PROHIBITED_EFFECT_REQUESTED,
    DecisionCode.EFFECT_NOT_AUTHORIZED,
    DecisionCode.VALIDATION_FAILURE,
)


def _canonical_json(value: Mapping[str, Any]) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _time_text(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


class DigestFixtureSignatureVerifier:
    """Deterministic test-only signature adapter; never production trust."""

    def verify(
        self, algorithm: str, key_id: str, signature: str, payload_digest: str
    ) -> bool:
        return (
            algorithm == "sha256-digest-fixture"
            and key_id == "mission-f-offline-fixture"
            and signature == payload_digest
        )


@dataclass(frozen=True)
class CompatibilityDecision:
    """Exactly one deterministic terminal authorization decision."""

    decision: DecisionCode
    wop_id: str
    authority_node_id: str
    authority_chain: tuple[str, ...]
    effective_capabilities: tuple[str, ...]
    requested_capabilities: tuple[str, ...]
    requested_effects: tuple[str, ...]
    reasons: tuple[str, ...]
    input_digest: str

    @property
    def authorized(self) -> bool:
        return self.decision is DecisionCode.AUTHORIZED

    def to_mapping(self) -> dict[str, Any]:
        return {
            "authority_chain": list(self.authority_chain),
            "authority_node_id": self.authority_node_id,
            "authorized": self.authorized,
            "decision": self.decision.value,
            "effective_capabilities": list(self.effective_capabilities),
            "input_digest": self.input_digest,
            "reasons": list(self.reasons),
            "requested_capabilities": list(self.requested_capabilities),
            "requested_effects": list(self.requested_effects),
            "wop_id": self.wop_id,
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_mapping(), sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ) + "\n"


class CompatibilityEvaluator:
    """Side-effect-free adapter combining Mission D and Mission E models."""

    def evaluate(
        self,
        *,
        graph: AuthorityGraph,
        wop: WorkPackage,
        state: EvaluationState,
        receipt: PublicationReceipt,
        reference_time: datetime,
        signature_verifier: SignatureVerifier | None,
        expected_authority_node_id: str | None = None,
        lease: ExecutionLease | None = None,
        revocation: RevocationRecord | None = None,
    ) -> CompatibilityDecision:
        findings: dict[DecisionCode, list[str]] = {}

        def add(code: DecisionCode, reason: str) -> None:
            findings.setdefault(code, []).append(reason)

        data = wop.data
        binding = data.get("authority_binding", {})
        authority_node_id = (
            str(binding.get("authority_node_id", ""))
            if isinstance(binding, Mapping)
            else ""
        )
        effects = data.get("authorized_effects", [])
        requested_capabilities = tuple(
            sorted(
                {
                    str(item.get("kind"))
                    for item in effects
                    if isinstance(item, Mapping)
                    and isinstance(item.get("kind"), str)
                    and item.get("kind")
                }
            )
        )
        authority_chain: tuple[str, ...] = ()
        effective_capabilities: tuple[str, ...] = ()

        structural_errors = wop.validation_errors()
        if structural_errors:
            for error in structural_errors:
                add(DecisionCode.INVALID_WOP, error)

        graph_errors = graph.validation_errors()
        if graph_errors:
            for error in graph_errors:
                add(DecisionCode.INVALID_AUTHORITY_GRAPH, error)
        elif authority_node_id not in graph.nodes:
            add(
                DecisionCode.UNKNOWN_AUTHORITY,
                f"authority node does not resolve: {authority_node_id}",
            )
        else:
            resolution = graph.resolve(authority_node_id)
            authority_chain = resolution.path
            effective_capabilities = tuple(sorted(resolution.effective_capabilities))

        if (
            expected_authority_node_id is not None
            and authority_node_id != expected_authority_node_id
        ):
            add(
                DecisionCode.AUTHORITY_BINDING_MISMATCH,
                "WOP authority binding does not match evaluation authority",
            )

        if signature_verifier is None:
            add(DecisionCode.SIGNATURE_FAILURE, "signature verifier is required")
        elif not structural_errors:
            signature_errors = wop.validation_errors(signature_verifier)
            if "signature verification failed" in signature_errors:
                add(DecisionCode.SIGNATURE_FAILURE, "signature verification failed")

        now = reference_time.astimezone(timezone.utc)
        if (
            receipt.wop_id != wop.wop_id
            or receipt.payload_digest != wop.payload_digest
            or receipt.published_at > now
        ):
            add(
                DecisionCode.INVALID_PUBLICATION_RECEIPT,
                "publication receipt does not validly bind the WOP at evaluation time",
            )

        try:
            valid_from = _parse_time(data.get("valid_from"), "valid_from")
            expires_at = _parse_time(data.get("expires_at"), "expires_at")
            if now < valid_from or now >= expires_at:
                add(DecisionCode.EXPIRED, "WOP is outside its validity interval")
        except WorkPackageError as error:
            for item in error.errors:
                add(DecisionCode.INVALID_WOP, item)

        if revocation is not None:
            permitted_revokers = set(
                data.get("revocation_policy", {}).get("authority_node_ids", [])
            )
            if (
                revocation.wop_id == wop.wop_id
                and revocation.payload_digest == wop.payload_digest
                and revocation.authority_node_id in permitted_revokers
                and revocation.revoked_at <= now
            ):
                add(DecisionCode.REVOKED, "WOP has an effective revocation")
            elif (
                revocation.wop_id != wop.wop_id
                or revocation.payload_digest != wop.payload_digest
                or revocation.authority_node_id not in permitted_revokers
            ):
                add(DecisionCode.VALIDATION_FAILURE, "invalid revocation record")

        lease_policy = data.get("lease_policy", {})
        lease_required = (
            isinstance(lease_policy, Mapping) and lease_policy.get("required") is True
        )
        if lease_required and lease is None:
            add(DecisionCode.INVALID_LEASE, "required execution lease is absent")
        if lease is not None:
            maximum = (
                lease_policy.get("maximum_duration_seconds", 0)
                if isinstance(lease_policy, Mapping)
                else 0
            )
            if (
                lease.wop_id != wop.wop_id
                or lease.payload_digest != wop.payload_digest
                or lease.holder_id != state.principal_id
                or not (lease.issued_at <= now < lease.expires_at)
                or (lease.expires_at - lease.issued_at).total_seconds() > maximum
            ):
                add(DecisionCode.INVALID_LEASE, "execution lease is invalid")

        context = data.get("execution_context", {})
        if isinstance(context, Mapping):
            mismatches = sorted(
                field
                for field in ("principal_id", "repository", "baseline_commit", "branch")
                if context.get(field) != getattr(state, field)
            )
            if mismatches:
                add(
                    DecisionCode.EXECUTION_CONTEXT_MISMATCH,
                    "execution context mismatch: " + ",".join(mismatches),
                )

        required_prerequisites = {
            item.get("evidence_ref")
            for item in data.get("prerequisites", [])
            if isinstance(item, Mapping) and item.get("required") is True
        }
        missing_prerequisites = sorted(
            required_prerequisites - state.prerequisite_evidence
        )
        if missing_prerequisites:
            add(
                DecisionCode.PREREQUISITE_FAILURE,
                "unsatisfied prerequisites: " + ",".join(missing_prerequisites),
            )

        required_dependencies = {
            item.get("wop_id")
            for item in data.get("dependencies", [])
            if isinstance(item, Mapping) and item.get("required") is True
        }
        missing_dependencies = sorted(
            required_dependencies - state.satisfied_dependencies
        )
        if missing_dependencies:
            add(
                DecisionCode.DEPENDENCY_FAILURE,
                "unsatisfied dependencies: " + ",".join(missing_dependencies),
            )

        missing_capabilities = sorted(
            set(requested_capabilities) - set(effective_capabilities)
        )
        if missing_capabilities and not graph_errors and authority_node_id in graph.nodes:
            add(
                DecisionCode.CAPABILITY_NOT_AUTHORIZED,
                "capabilities outside resolved authority: "
                + ",".join(missing_capabilities),
            )

        authorized_effects = {
            item.get("effect_id")
            for item in effects
            if isinstance(item, Mapping) and isinstance(item.get("effect_id"), str)
        }
        prohibited_effects = set(data.get("prohibited_effects", []))
        prohibited = sorted(state.requested_effects & prohibited_effects)
        unauthorized = sorted(state.requested_effects - authorized_effects)
        if prohibited:
            add(
                DecisionCode.PROHIBITED_EFFECT_REQUESTED,
                "prohibited effects requested: " + ",".join(prohibited),
            )
        if unauthorized:
            add(
                DecisionCode.EFFECT_NOT_AUTHORIZED,
                "effects outside WOP manifest: " + ",".join(unauthorized),
            )

        terminal = next(
            (code for code in DECISION_PRECEDENCE if findings.get(code)),
            DecisionCode.AUTHORIZED,
        )
        reasons = tuple(sorted(set(findings.get(terminal, ()))))
        input_digest = self._input_digest(
            graph=graph,
            wop=wop,
            state=state,
            receipt=receipt,
            lease=lease,
            revocation=revocation,
            reference_time=now,
            expected_authority_node_id=expected_authority_node_id,
        )
        return CompatibilityDecision(
            decision=terminal,
            wop_id=wop.wop_id,
            authority_node_id=authority_node_id,
            authority_chain=authority_chain,
            effective_capabilities=effective_capabilities,
            requested_capabilities=requested_capabilities,
            requested_effects=tuple(sorted(state.requested_effects)),
            reasons=reasons,
            input_digest=input_digest,
        )

    @staticmethod
    def _input_digest(
        *,
        graph: AuthorityGraph,
        wop: WorkPackage,
        state: EvaluationState,
        receipt: PublicationReceipt,
        lease: ExecutionLease | None,
        revocation: RevocationRecord | None,
        reference_time: datetime,
        expected_authority_node_id: str | None,
    ) -> str:
        value = {
            "expected_authority_node_id": expected_authority_node_id,
            "graph": graph.to_mapping(),
            "lease": (
                {
                    "expires_at": _time_text(lease.expires_at),
                    "holder_id": lease.holder_id,
                    "issued_at": _time_text(lease.issued_at),
                    "lease_id": lease.lease_id,
                    "payload_digest": lease.payload_digest,
                    "wop_id": lease.wop_id,
                }
                if lease
                else None
            ),
            "receipt": {
                "payload_digest": receipt.payload_digest,
                "published_at": _time_text(receipt.published_at),
                "publisher_id": receipt.publisher_id,
                "receipt_id": receipt.receipt_id,
                "wop_id": receipt.wop_id,
            },
            "reference_time": _time_text(reference_time),
            "revocation": (
                {
                    "authority_node_id": revocation.authority_node_id,
                    "payload_digest": revocation.payload_digest,
                    "reason": revocation.reason,
                    "revocation_id": revocation.revocation_id,
                    "revoked_at": _time_text(revocation.revoked_at),
                    "wop_id": revocation.wop_id,
                }
                if revocation
                else None
            ),
            "state": {
                "baseline_commit": state.baseline_commit,
                "branch": state.branch,
                "prerequisite_evidence": sorted(state.prerequisite_evidence),
                "principal_id": state.principal_id,
                "repository": state.repository,
                "requested_effects": sorted(state.requested_effects),
                "satisfied_dependencies": sorted(state.satisfied_dependencies),
            },
            "wop": wop.to_mapping(),
        }
        return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("graph", type=Path)
    parser.add_argument("wop", type=Path)
    parser.add_argument("state", type=Path)
    parser.add_argument("receipt", type=Path)
    parser.add_argument("--lease", type=Path)
    parser.add_argument("--revocation", type=Path)
    parser.add_argument("--expected-authority")
    parser.add_argument("--at", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        graph = AuthorityGraph.load(args.graph)
        wop = WorkPackage.load(args.wop)
        state = EvaluationState.from_mapping(load_mapping(args.state, "evaluation"))
        receipt = PublicationReceipt.from_mapping(
            load_mapping(args.receipt, "publication receipt")
        )
        lease = (
            ExecutionLease.from_mapping(load_mapping(args.lease, "execution lease"))
            if args.lease
            else None
        )
        revocation = (
            RevocationRecord.from_mapping(
                load_mapping(args.revocation, "revocation record")
            )
            if args.revocation
            else None
        )
        decision = CompatibilityEvaluator().evaluate(
            graph=graph,
            wop=wop,
            state=state,
            receipt=receipt,
            lease=lease,
            revocation=revocation,
            reference_time=_parse_time(args.at, "evaluation time"),
            expected_authority_node_id=args.expected_authority,
            signature_verifier=DigestFixtureSignatureVerifier(),
        )
    except Exception as error:
        decision = CompatibilityDecision(
            decision=DecisionCode.VALIDATION_FAILURE,
            wop_id="",
            authority_node_id="",
            authority_chain=(),
            effective_capabilities=(),
            requested_capabilities=(),
            requested_effects=(),
            reasons=(str(error),),
            input_digest=hashlib.sha256(str(error).encode("utf-8")).hexdigest(),
        )
    sys.stdout.write(decision.to_json())
    return 0 if decision.authorized else 1


if __name__ == "__main__":
    raise SystemExit(main())
