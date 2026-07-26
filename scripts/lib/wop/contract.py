#!/usr/bin/env python3
"""Validate and evaluate immutable offline Work Package contracts."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Protocol

import yaml
from yaml.constructor import ConstructorError


WOP_ID = re.compile(
    r"^WOP-[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
)
OBJECT_ID = re.compile(
    r"^[A-Z]+-[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
)
SHA256 = re.compile(r"^[0-9a-f]{64}$")
COMMIT = re.compile(r"^[0-9a-f]{40}$")


class WorkPackageError(ValueError):
    """Raised when a Work Package or its offline evaluation fails closed."""

    def __init__(self, errors: Iterable[str]) -> None:
        self.errors = tuple(sorted(set(errors)))
        super().__init__("; ".join(self.errors))


class UniqueKeyLoader(yaml.SafeLoader):
    """YAML loader that rejects duplicate mapping keys."""


def _construct_unique_mapping(
    loader: UniqueKeyLoader, node: yaml.MappingNode, deep: bool = False
) -> dict[Any, Any]:
    mapping: dict[Any, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in mapping:
            raise ConstructorError(
                "while constructing a mapping",
                node.start_mark,
                f"duplicate key: {key}",
                key_node.start_mark,
            )
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


UniqueKeyLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _construct_unique_mapping,
)


def _parse_time(value: Any, field: str) -> datetime:
    if not isinstance(value, str) or not value:
        raise WorkPackageError([f"{field} must be an ISO-8601 timestamp"])
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise WorkPackageError([f"{field} must be an ISO-8601 timestamp"]) from error
    if parsed.tzinfo is None:
        raise WorkPackageError([f"{field} must include a timezone"])
    return parsed.astimezone(timezone.utc)


def _string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise WorkPackageError([f"{field} must be a non-empty string"])
    return value


def _string_tuple(value: Any, field: str, nonempty: bool = False) -> tuple[str, ...]:
    if not isinstance(value, list) or any(
        not isinstance(item, str) or not item for item in value
    ):
        raise WorkPackageError([f"{field} must be a list of non-empty strings"])
    if nonempty and not value:
        raise WorkPackageError([f"{field} must not be empty"])
    if len(value) != len(set(value)):
        raise WorkPackageError([f"{field} must not contain duplicates"])
    return tuple(value)


def _mapping_tuple(
    value: Any, field: str, nonempty: bool = False
) -> tuple[Mapping[str, Any], ...]:
    if not isinstance(value, list) or any(not isinstance(item, Mapping) for item in value):
        raise WorkPackageError([f"{field} must be a list of mappings"])
    if nonempty and not value:
        raise WorkPackageError([f"{field} must not be empty"])
    return tuple(value)


def _canonical_json(value: Mapping[str, Any]) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


class SignatureVerifier(Protocol):
    """External signature verification interface; no trust store is embedded."""

    def verify(
        self, algorithm: str, key_id: str, signature: str, payload_digest: str
    ) -> bool: ...


@dataclass(frozen=True)
class PublicationReceipt:
    receipt_id: str
    wop_id: str
    payload_digest: str
    published_at: datetime
    publisher_id: str

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "PublicationReceipt":
        receipt_id = _string(value.get("receipt_id"), "receipt.receipt_id")
        wop_id = _string(value.get("wop_id"), "receipt.wop_id")
        digest = _string(value.get("payload_digest"), "receipt.payload_digest")
        publisher = _string(value.get("publisher_id"), "receipt.publisher_id")
        errors = []
        if not OBJECT_ID.fullmatch(receipt_id):
            errors.append("receipt.receipt_id must be a globally unique RECEIPT UUID")
        if not WOP_ID.fullmatch(wop_id):
            errors.append("receipt.wop_id must be a globally unique WOP UUID")
        if not SHA256.fullmatch(digest):
            errors.append("receipt.payload_digest must be lowercase SHA-256")
        if errors:
            raise WorkPackageError(errors)
        return cls(
            receipt_id,
            wop_id,
            digest,
            _parse_time(value.get("published_at"), "receipt.published_at"),
            publisher,
        )


@dataclass(frozen=True)
class ExecutionLease:
    lease_id: str
    wop_id: str
    payload_digest: str
    holder_id: str
    issued_at: datetime
    expires_at: datetime

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "ExecutionLease":
        lease_id = _string(value.get("lease_id"), "lease.lease_id")
        wop_id = _string(value.get("wop_id"), "lease.wop_id")
        digest = _string(value.get("payload_digest"), "lease.payload_digest")
        holder = _string(value.get("holder_id"), "lease.holder_id")
        issued = _parse_time(value.get("issued_at"), "lease.issued_at")
        expires = _parse_time(value.get("expires_at"), "lease.expires_at")
        errors = []
        if not OBJECT_ID.fullmatch(lease_id):
            errors.append("lease.lease_id must be a globally unique LEASE UUID")
        if not WOP_ID.fullmatch(wop_id):
            errors.append("lease.wop_id must be a globally unique WOP UUID")
        if not SHA256.fullmatch(digest):
            errors.append("lease.payload_digest must be lowercase SHA-256")
        if expires <= issued:
            errors.append("lease expiration must be after issuance")
        if errors:
            raise WorkPackageError(errors)
        return cls(lease_id, wop_id, digest, holder, issued, expires)


@dataclass(frozen=True)
class RevocationRecord:
    revocation_id: str
    wop_id: str
    payload_digest: str
    authority_node_id: str
    revoked_at: datetime
    reason: str

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "RevocationRecord":
        revocation_id = _string(value.get("revocation_id"), "revocation.revocation_id")
        wop_id = _string(value.get("wop_id"), "revocation.wop_id")
        digest = _string(value.get("payload_digest"), "revocation.payload_digest")
        authority = _string(
            value.get("authority_node_id"), "revocation.authority_node_id"
        )
        reason = _string(value.get("reason"), "revocation.reason")
        errors = []
        if not OBJECT_ID.fullmatch(revocation_id):
            errors.append(
                "revocation.revocation_id must be a globally unique REVOCATION UUID"
            )
        if not WOP_ID.fullmatch(wop_id):
            errors.append("revocation.wop_id must be a globally unique WOP UUID")
        if not SHA256.fullmatch(digest):
            errors.append("revocation.payload_digest must be lowercase SHA-256")
        if errors:
            raise WorkPackageError(errors)
        return cls(
            revocation_id,
            wop_id,
            digest,
            authority,
            _parse_time(value.get("revoked_at"), "revocation.revoked_at"),
            reason,
        )


@dataclass(frozen=True)
class EvaluationState:
    """Offline observations supplied to WOP evaluation."""

    prerequisite_evidence: frozenset[str]
    satisfied_dependencies: frozenset[str]
    requested_effects: frozenset[str]
    principal_id: str
    repository: str
    baseline_commit: str
    branch: str

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "EvaluationState":
        baseline_commit = _string(
            value.get("baseline_commit"), "evaluation.baseline_commit"
        )
        if not COMMIT.fullmatch(baseline_commit):
            raise WorkPackageError(
                ["evaluation.baseline_commit must be a full Git SHA"]
            )
        return cls(
            frozenset(
                _string_tuple(
                    value.get("prerequisite_evidence"),
                    "evaluation.prerequisite_evidence",
                )
            ),
            frozenset(
                _string_tuple(
                    value.get("satisfied_dependencies"),
                    "evaluation.satisfied_dependencies",
                )
            ),
            frozenset(
                _string_tuple(
                    value.get("requested_effects"),
                    "evaluation.requested_effects",
                    nonempty=True,
                )
            ),
            _string(value.get("principal_id"), "evaluation.principal_id"),
            _string(value.get("repository"), "evaluation.repository"),
            baseline_commit,
            _string(value.get("branch"), "evaluation.branch"),
        )


@dataclass(frozen=True)
class AuthorizationDecision:
    wop_id: str
    payload_digest: str
    allowed: bool
    reasons: tuple[str, ...]
    authority_node_id: str
    requested_effects: tuple[str, ...]

    def to_mapping(self) -> dict[str, Any]:
        return {
            "allowed": self.allowed,
            "authority_node_id": self.authority_node_id,
            "payload_digest": self.payload_digest,
            "reasons": list(self.reasons),
            "requested_effects": list(self.requested_effects),
            "wop_id": self.wop_id,
        }


@dataclass(frozen=True)
class WorkPackage:
    """Immutable machine-readable execution authorization contract."""

    _canonical_data: str

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "WorkPackage":
        if not isinstance(value, Mapping):
            raise WorkPackageError(["WOP root must be a mapping"])
        normalized = json.loads(json.dumps(value))
        return cls(_canonical_json(normalized))

    @property
    def data(self) -> dict[str, Any]:
        """Return a detached copy; the canonical contract cannot be mutated."""
        return json.loads(self._canonical_data)

    @classmethod
    def load(cls, path: Path | str) -> "WorkPackage":
        wop_path = Path(path)
        if not wop_path.is_file():
            raise WorkPackageError([f"WOP not found: {wop_path}"])
        try:
            value = yaml.load(
                wop_path.read_text(encoding="utf-8"), Loader=UniqueKeyLoader
            )
        except (OSError, yaml.YAMLError) as error:
            raise WorkPackageError([f"invalid WOP: {error}"]) from error
        return cls.from_mapping(value)

    @property
    def wop_id(self) -> str:
        return str(self.data.get("wop_id", ""))

    @property
    def payload_digest(self) -> str:
        return str(self.data.get("payload_digest", ""))

    @property
    def payload(self) -> dict[str, Any]:
        return {
            key: value
            for key, value in self.data.items()
            if key not in {"payload_digest", "signature"}
        }

    def calculated_digest(self) -> str:
        return hashlib.sha256(_canonical_json(self.payload).encode("utf-8")).hexdigest()

    def validation_errors(
        self, signature_verifier: SignatureVerifier | None = None
    ) -> tuple[str, ...]:
        value = self.data
        errors: list[str] = []
        required = {
            "schema_version",
            "wop_id",
            "authority_binding",
            "execution_context",
            "authorized_effects",
            "prohibited_effects",
            "prerequisites",
            "dependencies",
            "valid_from",
            "expires_at",
            "lease_policy",
            "revocation_policy",
            "payload_digest",
            "signature",
        }
        for field in sorted(required - set(value)):
            errors.append(f"WOP missing required field: {field}")
        if value.get("schema_version") != 1:
            errors.append("schema_version must be 1")
        if not WOP_ID.fullmatch(self.wop_id):
            errors.append("wop_id must be a globally unique WOP UUID")

        binding = value.get("authority_binding")
        if not isinstance(binding, Mapping):
            errors.append("authority_binding must be a mapping")
            binding = {}
        for field in ("authority_node_id", "mission_id", "phase_id", "work_item_id"):
            field_value = binding.get(field)
            if not isinstance(field_value, str) or not field_value:
                errors.append(f"authority_binding.{field} must bind exactly one identifier")

        context = value.get("execution_context")
        if not isinstance(context, Mapping):
            errors.append("execution_context must be a mapping")
            context = {}
        for field in ("principal_id", "repository", "branch"):
            if not isinstance(context.get(field), str) or not context.get(field):
                errors.append(f"execution_context.{field} must be a non-empty string")
        if not isinstance(context.get("baseline_commit"), str) or not COMMIT.fullmatch(
            context.get("baseline_commit", "")
        ):
            errors.append("execution_context.baseline_commit must be a full Git SHA")
        try:
            _string_tuple(
                context.get("assumptions"),
                "execution_context.assumptions",
                nonempty=True,
            )
        except WorkPackageError as error:
            errors.extend(error.errors)

        effects: dict[str, Mapping[str, Any]] = {}
        try:
            raw_effects = _mapping_tuple(
                value.get("authorized_effects"), "authorized_effects", nonempty=True
            )
            for effect in raw_effects:
                effect_id = effect.get("effect_id")
                if not isinstance(effect_id, str) or not effect_id:
                    errors.append("authorized effect_id must be a non-empty string")
                    continue
                if effect_id in effects:
                    errors.append(f"duplicate authorized effect: {effect_id}")
                effects[effect_id] = effect
                for field in ("kind", "target"):
                    if not isinstance(effect.get(field), str) or not effect.get(field):
                        errors.append(
                            f"authorized effect {effect_id} {field} must be non-empty"
                        )
                try:
                    _string_tuple(
                        effect.get("constraints"),
                        f"authorized effect {effect_id} constraints",
                        nonempty=True,
                    )
                except WorkPackageError as error:
                    errors.extend(error.errors)
        except WorkPackageError as error:
            errors.extend(error.errors)

        prohibited: tuple[str, ...] = ()
        try:
            prohibited = _string_tuple(
                value.get("prohibited_effects"),
                "prohibited_effects",
                nonempty=True,
            )
        except WorkPackageError as error:
            errors.extend(error.errors)
        overlap = sorted(set(effects) & set(prohibited))
        if overlap:
            errors.append(
                "effects cannot be both authorized and prohibited: " + ",".join(overlap)
            )

        for field in ("prerequisites", "dependencies"):
            try:
                entries = _mapping_tuple(value.get(field), field)
                seen: set[str] = set()
                identity = "prerequisite_id" if field == "prerequisites" else "wop_id"
                for entry in entries:
                    entry_id = entry.get(identity)
                    if not isinstance(entry_id, str) or not entry_id:
                        errors.append(f"{field}.{identity} must be a non-empty string")
                    elif entry_id in seen:
                        errors.append(f"duplicate {field} entry: {entry_id}")
                    else:
                        seen.add(entry_id)
                    if entry.get("required") is not True:
                        errors.append(f"{field} entries must declare required: true")
            except WorkPackageError as error:
                errors.extend(error.errors)

        try:
            valid_from = _parse_time(value.get("valid_from"), "valid_from")
            expires_at = _parse_time(value.get("expires_at"), "expires_at")
            if expires_at <= valid_from:
                errors.append("expires_at must be after valid_from")
        except WorkPackageError as error:
            errors.extend(error.errors)

        for policy_name in ("lease_policy", "revocation_policy"):
            policy = value.get(policy_name)
            if not isinstance(policy, Mapping):
                errors.append(f"{policy_name} must be a mapping")
                continue
            if policy_name == "lease_policy":
                if not isinstance(policy.get("required"), bool):
                    errors.append("lease_policy.required must be boolean")
                duration = policy.get("maximum_duration_seconds")
                if not isinstance(duration, int) or isinstance(duration, bool) or duration <= 0:
                    errors.append(
                        "lease_policy.maximum_duration_seconds must be positive"
                    )
            else:
                if policy.get("revocable") is not True:
                    errors.append("revocation_policy.revocable must be true")
                try:
                    _string_tuple(
                        policy.get("authority_node_ids"),
                        "revocation_policy.authority_node_ids",
                        nonempty=True,
                    )
                except WorkPackageError as error:
                    errors.extend(error.errors)

        if not SHA256.fullmatch(self.payload_digest):
            errors.append("payload_digest must be lowercase SHA-256")
        elif self.payload_digest != self.calculated_digest():
            errors.append("payload_digest does not match immutable WOP payload")

        signature = value.get("signature")
        if not isinstance(signature, Mapping):
            errors.append("signature must be a mapping")
        else:
            algorithm = signature.get("algorithm")
            key_id = signature.get("key_id")
            signature_value = signature.get("value")
            if not all(
                isinstance(item, str) and item
                for item in (algorithm, key_id, signature_value)
            ):
                errors.append("signature algorithm, key_id and value are required")
            elif signature_verifier is not None and not signature_verifier.verify(
                algorithm, key_id, signature_value, self.payload_digest
            ):
                errors.append("signature verification failed")
        return tuple(sorted(set(errors)))

    def validate(self, signature_verifier: SignatureVerifier | None = None) -> None:
        errors = self.validation_errors(signature_verifier)
        if errors:
            raise WorkPackageError(errors)

    def evaluate(
        self,
        state: EvaluationState,
        reference_time: datetime,
        receipt: PublicationReceipt,
        lease: ExecutionLease | None = None,
        revocation: RevocationRecord | None = None,
        signature_verifier: SignatureVerifier | None = None,
    ) -> AuthorizationDecision:
        reasons = list(self.validation_errors(signature_verifier))
        now = reference_time.astimezone(timezone.utc)
        binding = self.data.get("authority_binding", {})
        context = self.data.get("execution_context", {})
        try:
            valid_from = _parse_time(self.data.get("valid_from"), "valid_from")
            expires_at = _parse_time(self.data.get("expires_at"), "expires_at")
            if now < valid_from:
                reasons.append("WOP is not yet valid")
            if now >= expires_at:
                reasons.append("WOP is expired")
        except WorkPackageError as error:
            reasons.extend(error.errors)

        if receipt.wop_id != self.wop_id or receipt.payload_digest != self.payload_digest:
            reasons.append("publication receipt does not bind to immutable WOP")
        if receipt.published_at > now:
            reasons.append("publication receipt is later than evaluation time")

        if revocation is not None:
            allowed_revokers = set(
                self.data.get("revocation_policy", {}).get("authority_node_ids", [])
            )
            if (
                revocation.wop_id != self.wop_id
                or revocation.payload_digest != self.payload_digest
            ):
                reasons.append("revocation record does not bind to immutable WOP")
            elif revocation.authority_node_id not in allowed_revokers:
                reasons.append("revocation authority is not permitted by WOP")
            elif revocation.revoked_at <= now:
                reasons.append("WOP is revoked")

        lease_required = self.data.get("lease_policy", {}).get("required") is True
        if lease_required and lease is None:
            reasons.append("required execution lease is absent")
        if lease is not None:
            if lease.wop_id != self.wop_id or lease.payload_digest != self.payload_digest:
                reasons.append("execution lease does not bind to immutable WOP")
            if lease.holder_id != state.principal_id:
                reasons.append("execution lease holder does not match principal")
            if not (lease.issued_at <= now < lease.expires_at):
                reasons.append("execution lease is not active")
            maximum = self.data.get("lease_policy", {}).get(
                "maximum_duration_seconds", 0
            )
            if (lease.expires_at - lease.issued_at).total_seconds() > maximum:
                reasons.append("execution lease exceeds maximum duration")

        for field in ("principal_id", "repository", "baseline_commit", "branch"):
            if context.get(field) != getattr(state, field):
                reasons.append(f"execution context mismatch: {field}")

        required_prerequisites = {
            item.get("evidence_ref")
            for item in self.data.get("prerequisites", [])
            if isinstance(item, Mapping) and item.get("required") is True
        }
        missing_prerequisites = sorted(
            required_prerequisites - state.prerequisite_evidence
        )
        if missing_prerequisites:
            reasons.append(
                "unsatisfied prerequisites: " + ",".join(missing_prerequisites)
            )

        required_dependencies = {
            item.get("wop_id")
            for item in self.data.get("dependencies", [])
            if isinstance(item, Mapping) and item.get("required") is True
        }
        missing_dependencies = sorted(
            required_dependencies - state.satisfied_dependencies
        )
        if missing_dependencies:
            reasons.append(
                "unsatisfied dependencies: " + ",".join(missing_dependencies)
            )

        authorized_effects = {
            item.get("effect_id")
            for item in self.data.get("authorized_effects", [])
            if isinstance(item, Mapping)
        }
        prohibited_effects = set(self.data.get("prohibited_effects", []))
        unauthorized = sorted(state.requested_effects - authorized_effects)
        prohibited = sorted(state.requested_effects & prohibited_effects)
        if unauthorized:
            reasons.append("unauthorized effects requested: " + ",".join(unauthorized))
        if prohibited:
            reasons.append("prohibited effects requested: " + ",".join(prohibited))

        return AuthorizationDecision(
            wop_id=self.wop_id,
            payload_digest=self.payload_digest,
            allowed=not reasons,
            reasons=tuple(sorted(set(reasons))),
            authority_node_id=str(binding.get("authority_node_id", "")),
            requested_effects=tuple(sorted(state.requested_effects)),
        )

    def to_mapping(self) -> dict[str, Any]:
        return self.data

    def to_json(self) -> str:
        return json.dumps(
            self.to_mapping(), indent=2, sort_keys=True, separators=(",", ": ")
        ) + "\n"

    def to_yaml(self) -> str:
        return yaml.safe_dump(self.to_mapping(), sort_keys=True, allow_unicode=True)


def load_mapping(path: Path | str, label: str) -> Mapping[str, Any]:
    object_path = Path(path)
    try:
        value = yaml.load(
            object_path.read_text(encoding="utf-8"), Loader=UniqueKeyLoader
        )
    except (OSError, yaml.YAMLError) as error:
        raise WorkPackageError([f"invalid {label}: {error}"]) from error
    if not isinstance(value, Mapping):
        raise WorkPackageError([f"{label} root must be a mapping"])
    return value


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    validate = sub.add_parser("validate")
    validate.add_argument("wop", type=Path)
    serialize = sub.add_parser("serialize")
    serialize.add_argument("wop", type=Path)
    serialize.add_argument("--format", choices=("json", "yaml"), default="json")
    evaluate = sub.add_parser("evaluate")
    evaluate.add_argument("wop", type=Path)
    evaluate.add_argument("state", type=Path)
    evaluate.add_argument("receipt", type=Path)
    evaluate.add_argument("--lease", type=Path)
    evaluate.add_argument("--revocation", type=Path)
    evaluate.add_argument("--at", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        wop = WorkPackage.load(args.wop)
        if args.command == "validate":
            wop.validate()
            print(f"PASS: immutable WOP {wop.wop_id}")
        elif args.command == "serialize":
            wop.validate()
            sys.stdout.write(wop.to_json() if args.format == "json" else wop.to_yaml())
        else:
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
            decision = wop.evaluate(
                state,
                _parse_time(args.at, "evaluation time"),
                receipt,
                lease,
                revocation,
            )
            print(json.dumps(decision.to_mapping(), sort_keys=True))
            return 0 if decision.allowed else 1
    except WorkPackageError as error:
        for item in error.errors:
            print(f"FAIL: {item}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
