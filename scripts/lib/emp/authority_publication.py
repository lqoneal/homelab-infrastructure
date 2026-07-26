#!/usr/bin/env python3
"""Signed, staged publication and explicit activation of authority source state."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
import uuid
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

import yaml

from scripts.lib.emp.authority_resolution import (
    AuthorityResolutionError,
    AuthorityResolutionRuntime,
    canonical_json,
    digest,
    utc_text,
)


class AuthorityPublicationError(ValueError):
    """A publication or activation transaction failed closed."""


SIGNATURE_NAMESPACE = "zeus-authority-publication"
TRUST_POLICY_RELATIVE_PATH = Path("engineering/authority/owner-trust-policy.yaml")
TRANSACTION_SCHEMA_VERSION = 1
DIGEST_PATTERN = re.compile(r"^[0-9a-f]{64}$")

RECORD_RULES = {
    "mission_authority": ("missions", "Mission Registry"),
    "phase_authority": ("phases", "Mission Registry"),
    "work_item_authority": ("work_items", "Mission Registry"),
    "repository_identity": ("repositories", "Repository Identity Management"),
    "repository_baseline": ("repositories", "Repository Identity Management"),
    "authority_node": (
        "authority_bindings", "Governance Authority Graph Registrar"
    ),
    "approval_authority": (
        "approvals", "Engineering Governance decision registry"
    ),
    "authorization_decision": (
        "authorization_decisions", "Authorization Decision Service"
    ),
    "identity_record": ("principals", "Identity Provider"),
    "governing_baseline": (
        "governing_baselines", "Engineering Governance Baseline Registrar"
    ),
    "operational_configuration": (
        "operational_configurations", "Mission Admission Controller"
    ),
    "operational_revocation": (
        "operational_revocations", "Mission Admission Controller"
    ),
}
REQUIRED_RECORD_TYPES = {
    "mission_authority",
    "phase_authority",
    "work_item_authority",
    "repository_identity",
    "repository_baseline",
    "authority_node",
    "approval_authority",
    "identity_record",
    "governing_baseline",
    "operational_configuration",
}
REQUIRED_OWNERS = {owner for _, owner in RECORD_RULES.values()}
PAYLOAD_REQUIRED = {
    "mission_authority": {"lifecycle_state"},
    "phase_authority": {"mission_id", "lifecycle_state"},
    "work_item_authority": {
        "mission_id", "phase_id", "lifecycle_state", "qualification_status",
        "qualification_record", "revision", "approval_reference",
        "authority_binding_id", "scope_digest",
    },
    "repository_identity": {
        "repository_id", "canonical_locator", "assertion_id",
    },
    "repository_baseline": {"baseline_commit"},
    "authority_node": {
        "graph_path", "authority_node_id", "graph_version", "chain",
        "capabilities", "resolution_digest",
    },
    "approval_authority": {
        "reference", "authority", "decision", "decision_at",
        "authorized_lifecycle_state", "scope_digest",
    },
    "authorization_decision": {
        "decision", "lifecycle_state", "decision_digest",
    },
    "identity_record": {
        "authentication_status", "session_id", "authentication_record",
    },
    "governing_baseline": {
        "lifecycle_state", "manifest_id", "manifest_revision", "references",
        "manifest_digest",
    },
    "operational_configuration": {
        "lifecycle_state", "mission_id", "work_item_id", "principal_id",
        "activation_policy",
    },
    "operational_revocation": {
        "activation_transaction_id", "decision", "reason",
    },
}


def publication_template(record_type: str) -> dict[str, Any]:
    if record_type not in RECORD_RULES:
        raise AuthorityPublicationError("publication record type is not supported")
    return {
        "record_type": record_type,
        "designated_owner": RECORD_RULES[record_type][1],
        "required_payload_fields": sorted(PAYLOAD_REQUIRED[record_type]),
        "payload": {field: None for field in sorted(PAYLOAD_REQUIRED[record_type])},
        "unsigned_template": True,
        "signing_namespace": SIGNATURE_NAMESPACE,
    }


def validate_publication_payload(record_type: str, payload: Mapping[str, Any]) -> None:
    if record_type not in RECORD_RULES:
        raise AuthorityPublicationError("publication record type is not supported")
    if not isinstance(payload, Mapping):
        raise AuthorityPublicationError("publication payload must be an object")
    missing = sorted(
        field
        for field in PAYLOAD_REQUIRED[record_type]
        if payload.get(field) in (None, "", [], {})
    )
    if missing:
        raise AuthorityPublicationError(
            "publication payload missing: " + ", ".join(missing)
        )
    if record_type == "approval_authority":
        if payload.get("decision") not in {"GRANTED", "DENIED"}:
            raise AuthorityPublicationError(
                "Governance approval decision must be supplied as GRANTED or DENIED"
            )
        if payload.get("authorized_lifecycle_state") != "Active":
            raise AuthorityPublicationError(
                "Governance approval must explicitly bind Active lifecycle"
            )
        if not DIGEST_PATTERN.fullmatch(str(payload.get("scope_digest", ""))):
            raise AuthorityPublicationError("Governance approval scope digest invalid")


def prepare_publication_envelope(
    *,
    record_type: str,
    record_id: str,
    record_revision: int,
    signer_principal: str,
    published_at: datetime,
    payload: Mapping[str, Any],
) -> dict[str, Any]:
    validate_publication_payload(record_type, payload)
    if not record_id or not signer_principal or record_revision < 1:
        raise AuthorityPublicationError(
            "record identity, revision, and signer principal are required"
        )
    envelope = {
        "schema_version": 1,
        "record_type": record_type,
        "record_id": record_id,
        "record_revision": record_revision,
        "owner": RECORD_RULES[record_type][1],
        "signer_principal": signer_principal,
        "published_at": utc_text(published_at),
        "payload": deepcopy(dict(payload)),
        "payload_digest": digest(payload),
    }
    envelope["envelope_id"] = envelope_identifier(envelope)
    return envelope


def commissioning_status(repository_root: Path | str) -> dict[str, Any]:
    """Return a read-only, non-activating production commissioning assessment."""
    root = Path(repository_root).resolve()
    blockers: list[dict[str, str]] = []
    try:
        policy = load_mapping(trust_policy_path(root), "owner trust policy")
    except AuthorityPublicationError as error:
        policy = {}
        blockers.append({"code": "TRUST_POLICY_INVALID", "detail": str(error)})
    policy_enabled = policy.get("operationally_configured") is True
    if not policy_enabled:
        blockers.append(
            {
                "code": "TRUST_POLICY_NOT_CONFIGURED",
                "detail": "owner trust policy remains fail-closed",
            }
        )
    owners = policy.get("owners") if isinstance(policy.get("owners"), Mapping) else {}
    missing_owners = sorted(REQUIRED_OWNERS - set(owners))
    for owner in missing_owners:
        blockers.append(
            {
                "code": "OWNER_TRUST_NOT_ENROLLED",
                "detail": owner,
            }
        )
    signer_path = Path(str(policy.get("allowed_signers_file", "")))
    if not signer_path.is_absolute():
        signer_path = root / signer_path
    signer_count = 0
    if signer_path.is_file() and not signer_path.is_symlink():
        signer_count = sum(
            1
            for line in signer_path.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        )
    if signer_count == 0:
        blockers.append(
            {
                "code": "NO_PRODUCTION_SIGNERS",
                "detail": "allowed signers contains no enrolled public keys",
            }
        )
    enrollment_policy_path = root / "engineering/authority/enrollment-root-policy.yaml"
    enrollment_registry_path = (
        root / "engineering/authority/owner-enrollment-registry.yaml"
    )
    try:
        enrollment_policy = load_mapping(
            enrollment_policy_path, "enrollment root policy"
        )
    except AuthorityPublicationError as error:
        enrollment_policy = {}
        blockers.append(
            {"code": "ENROLLMENT_ROOT_INVALID", "detail": str(error)}
        )
    if enrollment_policy.get("operationally_configured") is not True:
        blockers.append(
            {
                "code": "ENROLLMENT_ROOT_NOT_CONFIGURED",
                "detail": "enrollment authorization trust root is absent",
            }
        )
    try:
        enrollment_registry = load_mapping(
            enrollment_registry_path, "owner enrollment registry"
        )
    except AuthorityPublicationError as error:
        enrollment_registry = {}
        blockers.append(
            {"code": "OWNER_ENROLLMENT_REGISTRY_INVALID", "detail": str(error)}
        )
    enrollment_records = (
        enrollment_registry.get("enrollments")
        if isinstance(enrollment_registry.get("enrollments"), Mapping)
        else {}
    )
    actively_enrolled = {
        value.get("owner")
        for value in enrollment_records.values()
        if isinstance(value, Mapping) and value.get("lifecycle_state") == "active"
    }
    for owner in sorted(REQUIRED_OWNERS - actively_enrolled):
        blockers.append({"code": "OWNER_ENROLLMENT_MISSING", "detail": owner})
    try:
        source = load_mapping(
            root / "engineering/authority/operational-authority-state.yaml",
            "operational authority source",
        )
    except AuthorityPublicationError as error:
        source = {}
        blockers.append({"code": "AUTHORITY_SOURCE_INVALID", "detail": str(error)})
    source_enabled = source.get("operationally_configured") is True
    if not source_enabled:
        blockers.append(
            {
                "code": "AUTHORITY_SOURCE_NOT_ACTIVATED",
                "detail": "operational authority source remains fail-closed",
            }
        )
    required_collections = {
        RECORD_RULES[record_type][0] for record_type in REQUIRED_RECORD_TYPES
    }
    for collection in sorted(required_collections):
        if not isinstance(source.get(collection), Mapping) or not source[collection]:
            blockers.append(
                {
                    "code": "REQUIRED_RECORD_COLLECTION_EMPTY",
                    "detail": collection,
                }
            )
    publication_directory = root / "engineering/authority/publications"
    envelopes = (
        list(publication_directory.glob("*.json"))
        if publication_directory.is_dir()
        else []
    )
    signatures = (
        list(publication_directory.glob("*.sig"))
        if publication_directory.is_dir()
        else []
    )
    published_types: set[str] = set()
    for path in envelopes:
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(value, Mapping) and value.get("record_type") in RECORD_RULES:
            published_types.add(str(value["record_type"]))
    for record_type in sorted(REQUIRED_RECORD_TYPES - published_types):
        blockers.append(
            {"code": "UNSIGNED_PUBLICATION_MISSING", "detail": record_type}
        )
    if "approval_authority" not in published_types:
        blockers.append(
            {
                "code": "GOVERNANCE_APPROVAL_PUBLICATION_MISSING",
                "detail": "no owner-prepared Governance approval envelope",
            }
        )
    if source_enabled and not isinstance(source.get("activation"), Mapping):
        blockers.append(
            {
                "code": "ACTIVATION_RECEIPT_BINDING_MISSING",
                "detail": "active source has no activation transaction binding",
            }
        )
    result = {
        "schema_version": 1,
        "repository": str(root),
        "trust_policy_configured": policy_enabled,
        "enrolled_owner_count": len(owners),
        "required_owner_count": len(REQUIRED_OWNERS),
        "allowed_signer_count": signer_count,
        "active_owner_enrollment_count": len(actively_enrolled),
        "prepared_envelope_count": len(envelopes),
        "detached_signature_count": len(signatures),
        "authority_source_configured": source_enabled,
        "blockers": sorted(blockers, key=lambda item: (item["code"], item["detail"])),
    }
    result["commissioning_state"] = "READY" if not blockers else "BLOCKED"
    result["assessment_digest"] = digest(result)
    return result


def trust_policy_path(repository_root: Path | str) -> Path:
    root = Path(repository_root).resolve()
    path = root / TRUST_POLICY_RELATIVE_PATH
    if path.is_symlink() or (path.parent.exists() and path.parent.resolve() != path.parent):
        raise AuthorityPublicationError("owner trust policy may not use symbolic links")
    return path


def load_mapping(path: Path | str, label: str) -> dict[str, Any]:
    try:
        value = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as error:
        raise AuthorityPublicationError(f"invalid {label}: {error}") from error
    if not isinstance(value, Mapping):
        raise AuthorityPublicationError(f"{label} must be an object")
    return deepcopy(dict(value))


def envelope_material(envelope: Mapping[str, Any]) -> dict[str, Any]:
    return {key: deepcopy(value) for key, value in envelope.items()}


def envelope_identifier(envelope: Mapping[str, Any]) -> str:
    material = {
        key: value for key, value in envelope.items() if key != "envelope_id"
    }
    return "PUBLICATION-" + str(
        uuid.uuid5(uuid.NAMESPACE_URL, canonical_json(material))
    )


class OwnerTrustPolicy:
    def __init__(self, repository_root: Path | str, value: Mapping[str, Any]):
        self.root = Path(repository_root).resolve()
        self.value = deepcopy(dict(value))
        if self.value.get("schema_version") != 1:
            raise AuthorityPublicationError("trust policy schema_version must be 1")
        if self.value.get("operationally_configured") is not True:
            raise AuthorityPublicationError("owner trust policy is not configured")
        if self.value.get("signature_namespace") != SIGNATURE_NAMESPACE:
            raise AuthorityPublicationError("trust policy signature namespace mismatch")
        owners = self.value.get("owners")
        if not isinstance(owners, Mapping):
            raise AuthorityPublicationError("trust policy owners must be an object")
        allowed = Path(str(self.value.get("allowed_signers_file", "")))
        if not allowed.is_absolute():
            allowed = self.root / allowed
        self.allowed_signers = allowed.resolve()
        if (
            not self.allowed_signers.is_file()
            or self.allowed_signers.is_symlink()
            or not self.allowed_signers.read_text(encoding="utf-8").strip()
        ):
            raise AuthorityPublicationError("allowed signers file is absent or empty")

    @classmethod
    def load(
        cls, repository_root: Path | str, path: Path | str | None = None
    ) -> "OwnerTrustPolicy":
        source = Path(path) if path is not None else trust_policy_path(repository_root)
        return cls(repository_root, load_mapping(source, "owner trust policy"))

    def verify(
        self, *, owner: str, signer_principal: str, message: bytes, signature: Path
    ) -> None:
        owner_policy = self.value["owners"].get(owner)
        if not isinstance(owner_policy, Mapping):
            raise AuthorityPublicationError(f"owner is not trusted: {owner}")
        principals = owner_policy.get("principals")
        if not isinstance(principals, list) or signer_principal not in principals:
            raise AuthorityPublicationError("signer principal is not authorized for owner")
        result = subprocess.run(
            [
                "ssh-keygen", "-Y", "verify",
                "-f", str(self.allowed_signers),
                "-I", signer_principal,
                "-n", SIGNATURE_NAMESPACE,
                "-s", str(signature),
            ],
            input=message,
            capture_output=True,
            check=False,
        )
        if result.returncode:
            raise AuthorityPublicationError("publication signature verification failed")


class AuthorityPublicationFramework:
    """Build create-only signed transactions and explicitly activate them."""

    def __init__(
        self,
        repository_root: Path | str,
        *,
        policy_path: Path | str | None = None,
    ):
        self.root = Path(repository_root).resolve()
        self.policy = OwnerTrustPolicy.load(self.root, policy_path)

    def initialize(self, transaction: Path | str) -> Path:
        directory = Path(transaction)
        directory.mkdir(parents=True, exist_ok=False)
        (directory / "envelopes").mkdir()
        (directory / "signatures").mkdir()
        metadata = {
            "schema_version": TRANSACTION_SCHEMA_VERSION,
            "transaction_id": "AUTHORITY-PUBLICATION-" + str(uuid.uuid4()),
            "state": "STAGING",
            "created_at": utc_text(datetime.now(timezone.utc)),
        }
        self._atomic_yaml(directory / "transaction.yaml", metadata)
        return directory

    def stage(
        self,
        *,
        transaction: Path | str,
        envelope_path: Path | str,
        signature_path: Path | str,
    ) -> dict[str, Any]:
        directory = self._transaction(transaction, required_state="STAGING")
        envelope = load_mapping(envelope_path, "publication envelope")
        self._verify_envelope(envelope, Path(signature_path))
        envelope_id = envelope["envelope_id"]
        target = directory / "envelopes" / f"{envelope_id}.json"
        signature_target = directory / "signatures" / f"{envelope_id}.sig"
        serialized = json.dumps(envelope, indent=2, sort_keys=True) + "\n"
        self._create_only(target, serialized.encode("utf-8"))
        try:
            self._create_only(signature_target, Path(signature_path).read_bytes())
        except Exception:
            if target.exists():
                target.unlink()
            raise
        candidate = self.build_candidate(directory)
        self._atomic_yaml(directory / "candidate.yaml", candidate)
        return {
            "transaction": str(directory),
            "envelope_id": envelope_id,
            "record_type": envelope["record_type"],
            "record_id": envelope["record_id"],
            "state": "STAGED",
        }

    def build_candidate(self, transaction: Path | str) -> dict[str, Any]:
        directory = self._transaction(transaction)
        candidate: dict[str, Any] = {
            "schema_version": 1,
            "operationally_configured": False,
            "status": "staged-authority-publication",
            "missions": {},
            "phases": {},
            "work_items": {},
            "repositories": {},
            "approvals": {},
            "authority_bindings": {},
            "governing_baselines": {},
            "principals": {},
            "authorization_decisions": {},
            "operational_configurations": {},
            "operational_revocations": {},
        }
        seen_types: set[str] = set()
        for path in sorted((directory / "envelopes").glob("*.json")):
            envelope = json.loads(path.read_text(encoding="utf-8"))
            signature = directory / "signatures" / f"{envelope['envelope_id']}.sig"
            self._verify_envelope(envelope, signature)
            record_type = envelope["record_type"]
            collection, owner = RECORD_RULES[record_type]
            record_id = envelope["record_id"]
            payload = deepcopy(envelope["payload"])
            payload.update(
                {
                    "record_id": record_id,
                    "record_revision": envelope["record_revision"],
                    "owner": owner,
                }
            )
            evidence = {
                "envelope_id": envelope["envelope_id"],
                "publication_digest": digest(envelope),
                "record_type": record_type,
                "signer_principal": envelope["signer_principal"],
            }
            existing = candidate[collection].get(record_id, {})
            overlap = set(existing) & set(payload)
            for key in overlap:
                if existing[key] != payload[key]:
                    raise AuthorityPublicationError(
                        f"conflicting publication for {collection}.{record_id}.{key}"
                    )
            provenance = list(existing.get("publication_provenance", []))
            provenance.append(evidence)
            candidate[collection][record_id] = {
                **existing,
                **payload,
                "publication_provenance": sorted(
                    provenance, key=lambda item: item["record_type"]
                ),
            }
            seen_types.add(record_type)
        candidate["publication_record_types"] = sorted(seen_types)
        candidate["candidate_digest"] = digest(candidate)
        return candidate

    def verify_readiness(
        self, transaction: Path | str, *, at: datetime
    ) -> dict[str, Any]:
        directory = self._transaction(transaction, required_state="STAGING")
        candidate = self.build_candidate(directory)
        missing_types = sorted(
            REQUIRED_RECORD_TYPES - set(candidate["publication_record_types"])
        )
        if missing_types:
            raise AuthorityPublicationError(
                "required publication record types missing: " + ", ".join(missing_types)
            )
        configurations = candidate["operational_configurations"]
        if len(configurations) != 1:
            raise AuthorityPublicationError(
                "exactly one operational configuration is required"
            )
        configuration = next(iter(configurations.values()))
        if configuration.get("lifecycle_state") != "Active":
            raise AuthorityPublicationError("operational configuration is not Active")
        required = ("mission_id", "work_item_id", "principal_id")
        if any(not configuration.get(field) for field in required):
            raise AuthorityPublicationError("operational configuration is incomplete")
        provisional = deepcopy(candidate)
        provisional["operationally_configured"] = True
        provisional["status"] = "provisional-readiness-validation"
        provisional.pop("candidate_digest", None)
        try:
            bundle = AuthorityResolutionRuntime(self.root, provisional).resolve(
                mission_id=configuration["mission_id"],
                work_item_id=configuration["work_item_id"],
                principal_id=configuration["principal_id"],
                issued_at=at,
            )
        except AuthorityResolutionError as error:
            raise AuthorityPublicationError(
                f"Authority Resolution Runtime readiness failed: {error}"
            ) from error
        result = {
            "schema_version": 1,
            "transaction_id": self._metadata(directory)["transaction_id"],
            "candidate_digest": candidate["candidate_digest"],
            "verified_at": utc_text(at),
            "record_type_count": len(candidate["publication_record_types"]),
            "required_record_types": sorted(REQUIRED_RECORD_TYPES),
            "resolution_id": bundle["resolution_id"],
            "bundle_digest": bundle["bundle_digest"],
            "readiness": "READY",
        }
        result["readiness_digest"] = digest(result)
        self._atomic_yaml(directory / "readiness.yaml", result)
        return result

    def revoke(
        self,
        *,
        envelope_path: Path | str,
        signature_path: Path | str,
        target: Path | str,
        receipt_path: Path | str,
        at: datetime,
    ) -> dict[str, Any]:
        envelope = load_mapping(envelope_path, "revocation envelope")
        self._verify_envelope(envelope, Path(signature_path))
        if envelope.get("record_type") != "operational_revocation":
            raise AuthorityPublicationError(
                "revocation requires an operational_revocation envelope"
            )
        target_path = Path(target).resolve()
        current = load_mapping(target_path, "operational authority state")
        if current.get("operationally_configured") is not True:
            raise AuthorityPublicationError("operational authority source is not active")
        activation = current.get("activation")
        if not isinstance(activation, Mapping):
            raise AuthorityPublicationError("active source has no activation binding")
        if (
            envelope["payload"].get("activation_transaction_id")
            != activation.get("transaction_id")
        ):
            raise AuthorityPublicationError("revocation activation binding mismatch")
        if envelope["payload"].get("decision") != "REVOKED":
            raise AuthorityPublicationError("revocation decision must be REVOKED")
        revoked = deepcopy(current)
        revoked["operationally_configured"] = False
        revoked["status"] = "revoked"
        revoked["revocation"] = {
            "envelope_id": envelope["envelope_id"],
            "record_id": envelope["record_id"],
            "revoked_at": utc_text(at),
            "reason": envelope["payload"].get("reason"),
            "publication_digest": digest(envelope),
        }
        revoked.pop("source_digest", None)
        revoked["source_digest"] = digest(revoked)
        previous_digest = hashlib_sha256(target_path.read_bytes())
        self._atomic_yaml(target_path, revoked)
        receipt = {
            "schema_version": 1,
            "revocation_id": envelope["record_id"],
            "activation_transaction_id": activation["transaction_id"],
            "revoked_at": utc_text(at),
            "previous_state_digest": previous_digest,
            "revoked_state_digest": hashlib_sha256(target_path.read_bytes()),
            "state": "REVOKED",
        }
        receipt["receipt_digest"] = digest(receipt)
        self._create_only(
            Path(receipt_path),
            yaml.safe_dump(receipt, sort_keys=True).encode("utf-8"),
        )
        return receipt

    def activate(
        self,
        transaction: Path | str,
        *,
        target: Path | str,
        at: datetime,
    ) -> dict[str, Any]:
        directory = self._transaction(transaction, required_state="STAGING")
        readiness = self.verify_readiness(directory, at=at)
        candidate = self.build_candidate(directory)
        if candidate["candidate_digest"] != readiness["candidate_digest"]:
            raise AuthorityPublicationError("candidate changed after readiness validation")
        target_path = Path(target).resolve()
        expected = (
            self.root / "engineering/authority/operational-authority-state.yaml"
        ).resolve()
        if target_path != expected and os.environ.get("ZEUS_TESTING") != "1":
            raise AuthorityPublicationError(
                "production activation target must be the repository-fixed authority source"
            )
        previous = target_path.read_bytes() if target_path.exists() else b""
        backup = directory / "previous-authority-state.yaml"
        self._create_only(backup, previous)
        activated = deepcopy(candidate)
        activated.pop("candidate_digest", None)
        activated["operationally_configured"] = True
        activated["status"] = "operational"
        activated["activation"] = {
            "transaction_id": readiness["transaction_id"],
            "activated_at": utc_text(at),
            "readiness_digest": readiness["readiness_digest"],
            "previous_state_digest": hashlib_sha256(previous),
        }
        activated["source_digest"] = digest(activated)
        self._atomic_yaml(target_path, activated)
        receipt = {
            "schema_version": 1,
            "transaction_id": readiness["transaction_id"],
            "target": str(target_path),
            "activated_at": utc_text(at),
            "previous_state_digest": hashlib_sha256(previous),
            "activated_state_digest": hashlib_sha256(target_path.read_bytes()),
            "readiness_digest": readiness["readiness_digest"],
            "state": "ACTIVATED",
        }
        receipt["receipt_digest"] = digest(receipt)
        self._atomic_yaml(directory / "activation-receipt.yaml", receipt)
        metadata = self._metadata(directory)
        metadata["state"] = "ACTIVATED"
        metadata["activated_at"] = utc_text(at)
        self._atomic_yaml(directory / "transaction.yaml", metadata)
        return receipt

    def rollback(
        self, transaction: Path | str, *, target: Path | str, at: datetime
    ) -> dict[str, Any]:
        directory = self._transaction(transaction, required_state="ACTIVATED")
        receipt = load_mapping(directory / "activation-receipt.yaml", "activation receipt")
        receipt_digest = receipt.pop("receipt_digest", None)
        if receipt_digest != digest(receipt):
            raise AuthorityPublicationError("activation receipt digest mismatch")
        target_path = Path(target).resolve()
        if str(target_path) != receipt.get("target"):
            raise AuthorityPublicationError("rollback target mismatch")
        if hashlib_sha256(target_path.read_bytes()) != receipt["activated_state_digest"]:
            raise AuthorityPublicationError("active authority state changed after activation")
        previous = (directory / "previous-authority-state.yaml").read_bytes()
        if hashlib_sha256(previous) != receipt["previous_state_digest"]:
            raise AuthorityPublicationError("rollback snapshot digest mismatch")
        self._atomic_bytes(target_path, previous)
        result = {
            "schema_version": 1,
            "transaction_id": receipt["transaction_id"],
            "rolled_back_at": utc_text(at),
            "restored_state_digest": hashlib_sha256(previous),
            "state": "ROLLED_BACK",
        }
        result["rollback_digest"] = digest(result)
        self._atomic_yaml(directory / "rollback-receipt.yaml", result)
        metadata = self._metadata(directory)
        metadata["state"] = "ROLLED_BACK"
        self._atomic_yaml(directory / "transaction.yaml", metadata)
        return result

    def _verify_envelope(
        self, envelope: Mapping[str, Any], signature: Path
    ) -> None:
        required = {
            "schema_version", "envelope_id", "record_type", "record_id",
            "record_revision", "owner", "signer_principal", "published_at",
            "payload", "payload_digest",
        }
        if envelope.get("schema_version") != 1 or not required.issubset(envelope):
            raise AuthorityPublicationError("publication envelope is incomplete")
        record_type = str(envelope["record_type"])
        if record_type not in RECORD_RULES:
            raise AuthorityPublicationError("publication record type is not supported")
        expected_owner = RECORD_RULES[record_type][1]
        if envelope.get("owner") != expected_owner:
            raise AuthorityPublicationError("publication owner does not own record type")
        if envelope.get("envelope_id") != envelope_identifier(envelope):
            raise AuthorityPublicationError("publication envelope identity mismatch")
        if envelope.get("payload_digest") != digest(envelope.get("payload")):
            raise AuthorityPublicationError("publication payload digest mismatch")
        if (
            not isinstance(envelope.get("record_revision"), int)
            or envelope["record_revision"] < 1
            or not isinstance(envelope.get("payload"), Mapping)
        ):
            raise AuthorityPublicationError("publication revision or payload invalid")
        validate_publication_payload(record_type, envelope["payload"])
        try:
            published_at = datetime.fromisoformat(
                str(envelope["published_at"]).replace("Z", "+00:00")
            )
        except ValueError as error:
            raise AuthorityPublicationError(
                "publication timestamp must be ISO-8601"
            ) from error
        if published_at.tzinfo is None:
            raise AuthorityPublicationError(
                "publication timestamp must include a timezone"
            )
        self.policy.verify(
            owner=expected_owner,
            signer_principal=str(envelope["signer_principal"]),
            message=canonical_json(envelope_material(envelope)).encode("utf-8"),
            signature=signature,
        )

    def _transaction(
        self, transaction: Path | str, required_state: str | None = None
    ) -> Path:
        directory = Path(transaction).resolve()
        metadata = self._metadata(directory)
        if metadata.get("schema_version") != TRANSACTION_SCHEMA_VERSION:
            raise AuthorityPublicationError("transaction schema invalid")
        if required_state is not None and metadata.get("state") != required_state:
            raise AuthorityPublicationError(
                f"transaction must be {required_state}, found {metadata.get('state')}"
            )
        return directory

    @staticmethod
    def _metadata(directory: Path) -> dict[str, Any]:
        return load_mapping(directory / "transaction.yaml", "transaction metadata")

    @staticmethod
    def _create_only(path: Path, value: bytes) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with path.open("xb") as stream:
                stream.write(value)
                stream.flush()
                os.fsync(stream.fileno())
        except FileExistsError as error:
            raise AuthorityPublicationError(f"create-only collision: {path.name}") from error

    @staticmethod
    def _atomic_yaml(path: Path, value: Mapping[str, Any]) -> None:
        serialized = yaml.safe_dump(dict(value), sort_keys=True).encode("utf-8")
        AuthorityPublicationFramework._atomic_bytes(path, serialized)

    @staticmethod
    def _atomic_bytes(path: Path, value: bytes) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporary = tempfile.mkstemp(dir=path.parent, prefix=".authority.")
        try:
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(value)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, path)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)


def hashlib_sha256(value: bytes) -> str:
    import hashlib

    return hashlib.sha256(value).hexdigest()
