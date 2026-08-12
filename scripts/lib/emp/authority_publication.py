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
    ACTIVE_PUBLICATION_POINTER,
    AUTHORITY_RUNTIME_RELATIVE_PATH,
    AuthorityResolutionError,
    AuthorityResolutionRuntime,
    authoritative_source_path,
    canonical_json,
    digest,
    utc_text,
)
from scripts.lib.emp.runtime_paths import runtime_path


class AuthorityPublicationError(ValueError):
    """A publication or activation transaction failed closed."""


SIGNATURE_NAMESPACE = "zeus-authority-publication"
TRUST_POLICY_RELATIVE_PATH = Path("engineering/authority/owner-trust-policy.yaml")
TRANSACTION_SCHEMA_VERSION = 1
DIGEST_PATTERN = re.compile(r"^[0-9a-f]{64}$")
PRODUCTION_AUTHORITY_OWNER = "Lawrence O'Neal"
PRODUCTION_AUTHORITY_PRINCIPAL = "loneal"

RECORD_RULES = {
    "mission_authority": ("missions", PRODUCTION_AUTHORITY_OWNER),
    "phase_authority": ("phases", PRODUCTION_AUTHORITY_OWNER),
    "work_item_authority": ("work_items", PRODUCTION_AUTHORITY_OWNER),
    "repository_identity": ("repositories", PRODUCTION_AUTHORITY_OWNER),
    "repository_baseline": ("repositories", PRODUCTION_AUTHORITY_OWNER),
    "authority_node": ("authority_bindings", PRODUCTION_AUTHORITY_OWNER),
    "approval_authority": ("approvals", PRODUCTION_AUTHORITY_OWNER),
    "authorization_decision": (
        "authorization_decisions", PRODUCTION_AUTHORITY_OWNER
    ),
    "identity_record": ("principals", PRODUCTION_AUTHORITY_OWNER),
    "governing_baseline": ("governing_baselines", PRODUCTION_AUTHORITY_OWNER),
    "operational_configuration": (
        "operational_configurations", PRODUCTION_AUTHORITY_OWNER
    ),
    "operational_revocation": (
        "operational_revocations", PRODUCTION_AUTHORITY_OWNER
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
                "operator approval decision must be supplied as GRANTED or DENIED"
            )
        if payload.get("authorized_lifecycle_state") != "Active":
            raise AuthorityPublicationError(
                "operator approval must explicitly bind Active lifecycle"
            )
        if not DIGEST_PATTERN.fullmatch(str(payload.get("scope_digest", ""))):
            raise AuthorityPublicationError("operator approval scope digest invalid")


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
            authoritative_source_path(root),
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
                "code": "OPERATOR_APPROVAL_PUBLICATION_MISSING",
                "detail": "no authenticated-operator approval envelope",
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
        runtime = runtime_path(self.root, "authority").resolve()
        if runtime in target_path.parents and os.environ.get("ZEUS_TESTING") != "1":
            publication = (
                runtime / "publications" / f"REVOCATION-{envelope['envelope_id']}"
            )
            publication.mkdir(parents=True, exist_ok=False)
            state_path = publication / "authority-state.yaml"
            self._create_only(
                state_path, yaml.safe_dump(revoked, sort_keys=True).encode("utf-8")
            )
            envelope_path_copy = publication / "revocation-envelope.json"
            signature_path_copy = publication / "revocation-envelope.sig"
            self._create_only(
                envelope_path_copy,
                (json.dumps(envelope, indent=2, sort_keys=True) + "\n").encode("utf-8"),
            )
            self._create_only(signature_path_copy, Path(signature_path).read_bytes())
            artifacts = publication / "artifacts.sha256"
            self._create_only(
                artifacts,
                "".join(
                    f"{hashlib_sha256(path.read_bytes())}  {path.name}\n"
                    for path in (state_path, envelope_path_copy, signature_path_copy)
                ).encode("utf-8"),
            )
            pointer = runtime / ACTIVE_PUBLICATION_POINTER
            pointer_value = {
                "schema_version": 1,
                "transaction_id": f"REVOCATION-{envelope['envelope_id']}",
                "authority_state": str(state_path.relative_to(runtime)),
                "authority_state_digest": hashlib_sha256(state_path.read_bytes()),
                "artifact_manifest": str(artifacts.relative_to(runtime)),
                "artifact_manifest_digest": hashlib_sha256(artifacts.read_bytes()),
                "activated_at": utc_text(at),
            }
            self._atomic_bytes(
                pointer,
                (json.dumps(pointer_value, indent=2, sort_keys=True) + "\n").encode(),
            )
            revoked_state_digest = hashlib_sha256(state_path.read_bytes())
        else:
            self._atomic_yaml(target_path, revoked)
            revoked_state_digest = hashlib_sha256(target_path.read_bytes())
        receipt = {
            "schema_version": 1,
            "revocation_id": envelope["record_id"],
            "activation_transaction_id": activation["transaction_id"],
            "revoked_at": utc_text(at),
            "previous_state_digest": previous_digest,
            "revoked_state_digest": revoked_state_digest,
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
        directory = self._transaction(transaction)
        metadata = self._metadata(directory)
        if metadata.get("state") == "ACTIVATED":
            return self._verify_idempotent_activation(directory, Path(target))
        if metadata.get("state") != "STAGING":
            raise AuthorityPublicationError(
                f"transaction must be STAGING, found {metadata.get('state')}"
            )
        readiness = self.verify_readiness(directory, at=at)
        candidate = self.build_candidate(directory)
        if candidate["candidate_digest"] != readiness["candidate_digest"]:
            raise AuthorityPublicationError("candidate changed after readiness validation")
        target_path = Path(target).resolve()
        expected = (
            runtime_path(self.root, "authority", ACTIVE_PUBLICATION_POINTER)
        ).resolve()
        if target_path != expected and os.environ.get("ZEUS_TESTING") != "1":
            raise AuthorityPublicationError(
                "production activation target must be the repository-fixed runtime pointer"
            )
        runtime_activation = target_path == expected
        starting_snapshot = (
            self._repository_snapshot() if runtime_activation else None
        )
        if starting_snapshot and (
            starting_snapshot["tracked"] or starting_snapshot["staged"]
        ) and not self._qualified_pmct_reconciliation(starting_snapshot):
            raise AuthorityPublicationError(
                "repository tracked or staged state must be clean or an exact "
                "authenticated PMCT capability-state reconciliation before activation"
            )
        if starting_snapshot:
            published_head = self._candidate_repository_baseline(candidate)
            if published_head != starting_snapshot["head"]:
                raise AuthorityPublicationError(
                    "publication baseline does not match repository HEAD"
                )
        previous = target_path.read_bytes() if target_path.exists() else b""
        backup = directory / "previous-authority-state.yaml"
        if backup.exists():
            if backup.read_bytes() != previous:
                raise AuthorityPublicationError(
                    "activation retry previous-pointer binding mismatch"
                )
        else:
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
        if not runtime_activation:
            self._atomic_yaml(target_path, activated)
            activated_state_digest = hashlib_sha256(target_path.read_bytes())
        else:
            store = expected.parent
            publication, state_path, artifact_manifest = (
                self._create_runtime_publication(
                    store=store,
                    transaction=directory,
                    transaction_id=readiness["transaction_id"],
                    activated=activated,
                )
            )
            activated_state_digest = hashlib_sha256(state_path.read_bytes())
            pointer = {
                "schema_version": 1,
                "transaction_id": readiness["transaction_id"],
                "authority_state": str(state_path.relative_to(store)),
                "authority_state_digest": activated_state_digest,
                "artifact_manifest": str(artifact_manifest.relative_to(store)),
                "artifact_manifest_digest": hashlib_sha256(
                    artifact_manifest.read_bytes()
                ),
                "activated_at": utc_text(at),
            }
            ending_snapshot = self._repository_snapshot()
            if ending_snapshot != starting_snapshot:
                raise AuthorityPublicationError(
                    "repository HEAD or tracked state changed during activation"
                )
            self._atomic_bytes(
                target_path,
                (json.dumps(pointer, indent=2, sort_keys=True) + "\n").encode("utf-8"),
            )
            if authoritative_source_path(self.root) != state_path:
                raise AuthorityPublicationError(
                    "active publication pointer did not resolve to the new artifact"
                )
        receipt = {
            "schema_version": 1,
            "transaction_id": readiness["transaction_id"],
            "target": str(target_path),
            "activated_at": utc_text(at),
            "previous_state_digest": hashlib_sha256(previous),
            "activated_state_digest": activated_state_digest,
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

    def _repository_snapshot(self) -> dict[str, str]:
        def git(*arguments: str) -> str:
            result = subprocess.run(
                ["git", "-C", str(self.root), *arguments],
                text=True,
                capture_output=True,
                check=False,
            )
            if result.returncode:
                raise AuthorityPublicationError(
                    result.stderr.strip() or "repository inspection failed"
                )
            return result.stdout.strip()

        return {
            "head": git("rev-parse", "HEAD"),
            "tracked": git("status", "--porcelain=v1", "--untracked-files=no"),
            "staged": git("diff", "--cached", "--name-only"),
        }

    def _qualified_pmct_reconciliation(self, snapshot: Mapping[str, str]) -> bool:
        """Accept only the exact sealed PMCT ledger delta produced before publication."""
        if snapshot.get("staged"):
            return False
        relative = Path("engineering/runtime/pmct/capability-state.yaml")
        if snapshot.get("tracked", "").splitlines() != [f"M {relative.as_posix()}"]:
            return False
        state_path = self.root / relative
        try:
            committed = yaml.safe_load(
                subprocess.run(
                    ["git", "-C", str(self.root), "show", f"HEAD:{relative.as_posix()}"],
                    text=True, capture_output=True, check=True,
                ).stdout
            )
            current = yaml.safe_load(state_path.read_text(encoding="utf-8"))
        except (OSError, subprocess.CalledProcessError, yaml.YAMLError):
            return False
        if not isinstance(committed, dict) or not isinstance(current, dict):
            return False
        run_id = current.get("last_run_id")
        if not isinstance(run_id, str) or not re.fullmatch(
            r"PMCT-\d{8}T\d{6}Z-[0-9a-f]{12}", run_id
        ):
            return False
        run = self.root / "engineering/runtime/pmct/runs" / run_id
        try:
            marker = (run / "COMPLETE").read_text(encoding="utf-8").strip()
            manifest = json.loads((run / "run-manifest.json").read_text())
            result = json.loads((run / "capability-result.json").read_text())
            artifact_lines = (run / "artifacts.sha256").read_text().splitlines()
        except (OSError, json.JSONDecodeError):
            return False
        if marker != "PMCT_COMPLETION_MARKER=COMPLETE":
            return False
        for line in artifact_lines:
            expected, separator, name = line.partition("  ")
            artifact = run / name.removeprefix("./")
            if (
                not separator
                or not DIGEST_PATTERN.fullmatch(expected)
                or not artifact.is_file()
                or hashlib_sha256(artifact.read_bytes()) != expected
            ):
                return False
        head = snapshot.get("head")
        if (
            manifest.get("run_id") != run_id
            or result.get("run_id") != run_id
            or manifest.get("repository") != str(self.root)
            or manifest.get("head") != head
            or manifest.get("implementation_baseline") != head
            or manifest.get("gate") != result.get("gate")
            or manifest.get("result") != result.get("result")
        ):
            return False
        pointer_path = (
            runtime_path(self.root, "authority", ACTIVE_PUBLICATION_POINTER)
        )
        if pointer_path.is_file():
            try:
                pointer = json.loads(pointer_path.read_text(encoding="utf-8"))
                active = yaml.safe_load(
                    authoritative_source_path(self.root).read_text(encoding="utf-8")
                )
                baselines = [
                    value.get("baseline_commit")
                    for value in active.get("repositories", {}).values()
                    if Path(str(value.get("canonical_locator", ""))).resolve()
                    == self.root
                ]
            except (OSError, json.JSONDecodeError, yaml.YAMLError, AuthorityResolutionError):
                return False
            if (
                len(baselines) != 1
                or manifest.get("published_baseline") != baselines[0]
                or manifest.get("active_authority_publication")
                != pointer.get("transaction_id")
            ):
                return False
        gate = str(result.get("gate", ""))
        reasons = result.get("reasons")
        completed_at = manifest.get("completed_at")
        if (
            gate not in committed.get("gates", {})
            or not isinstance(reasons, list)
            or not all(isinstance(reason, str) for reason in reasons)
            or not completed_at
        ):
            return False
        expected = json.loads(json.dumps(committed))
        gate_state = expected["gates"][gate]
        run_result = str(result.get("result", ""))
        gate_state["status"] = run_result
        gate_state["reason"] = "; ".join(reasons)
        if run_result == "PASS":
            gate_state["codex_validation"] = "PASS"
            if gate_state.get("operator_acceptance") != "RECORDED":
                gate_state["gate_status"] = "AWAITING_OPERATOR_VERIFICATION"
        expected["last_run_id"] = run_id
        expected["last_evaluated_gate"] = gate
        expected["updated_at"] = completed_at
        expected["overall_result"] = (
            "PASS"
            if all(value.get("status") == "PASS" for value in expected["gates"].values())
            else "NOT_READY"
        )
        return current == expected

    def _candidate_repository_baseline(self, candidate: Mapping[str, Any]) -> str:
        matches = [
            str(record.get("baseline_commit", ""))
            for record in candidate.get("repositories", {}).values()
            if isinstance(record, Mapping)
            and Path(str(record.get("canonical_locator", ""))).resolve() == self.root
        ]
        if len(matches) != 1 or not re.fullmatch(r"[0-9a-f]{40}", matches[0]):
            raise AuthorityPublicationError(
                "candidate must contain exactly one repository baseline"
            )
        return matches[0]

    def _create_runtime_publication(
        self,
        *,
        store: Path,
        transaction: Path,
        transaction_id: str,
        activated: Mapping[str, Any],
    ) -> tuple[Path, Path, Path]:
        publications = store / "publications"
        publications.mkdir(parents=True, exist_ok=True, mode=0o700)
        publication = publications / transaction_id
        if publication.exists():
            return self._verify_existing_runtime_publication(
                publication=publication,
                transaction=transaction,
                activated=activated,
            )
        staging = publications / f".staging-{transaction_id}-{uuid.uuid4().hex}"
        quarantine = store / "quarantine"
        try:
            staging.mkdir(mode=0o700)
            state_path = staging / "authority-state.yaml"
            self._create_only(
                state_path,
                yaml.safe_dump(dict(activated), sort_keys=True).encode("utf-8"),
            )
            artifact_lines = [
                f"{hashlib_sha256(state_path.read_bytes())}  authority-state.yaml\n"
            ]
            for source_directory in ("envelopes", "signatures"):
                destination = staging / source_directory
                destination.mkdir(mode=0o700)
                for source in sorted((transaction / source_directory).iterdir()):
                    copied = destination / source.name
                    self._create_only(copied, source.read_bytes())
                    artifact_lines.append(
                        f"{hashlib_sha256(copied.read_bytes())}  "
                        f"{source_directory}/{source.name}\n"
                    )
            artifact_manifest = staging / "artifacts.sha256"
            self._create_only(
                artifact_manifest, "".join(artifact_lines).encode("utf-8")
            )
            self._seal_publication(staging)
            os.replace(staging, publication)
            return (
                publication,
                publication / "authority-state.yaml",
                publication / "artifacts.sha256",
            )
        except Exception:
            if staging.exists():
                quarantine.mkdir(parents=True, exist_ok=True, mode=0o700)
                diagnostic = quarantine / (
                    f"{transaction_id}-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
                    f"-{uuid.uuid4().hex}"
                )
                os.replace(staging, diagnostic)
            raise

    def _verify_existing_runtime_publication(
        self,
        *,
        publication: Path,
        transaction: Path,
        activated: Mapping[str, Any],
    ) -> tuple[Path, Path, Path]:
        state_path = publication / "authority-state.yaml"
        artifact_manifest = publication / "artifacts.sha256"
        expected_state = yaml.safe_dump(dict(activated), sort_keys=True).encode("utf-8")
        expected_artifacts: dict[str, str] = {
            "authority-state.yaml": hashlib_sha256(expected_state)
        }
        for source_directory in ("envelopes", "signatures"):
            for source in sorted((transaction / source_directory).iterdir()):
                expected_artifacts[f"{source_directory}/{source.name}"] = (
                    hashlib_sha256(source.read_bytes())
                )
        try:
            actual_artifacts = {}
            for line in artifact_manifest.read_text(encoding="utf-8").splitlines():
                artifact_digest, separator, artifact_name = line.partition("  ")
                if not separator:
                    raise ValueError("malformed artifact manifest")
                actual_artifacts[artifact_name] = artifact_digest
            protected = [state_path, artifact_manifest]
            protected.extend(
                path for path in publication.rglob("*") if path.is_file()
            )
            protection_valid = (
                publication.stat().st_mode & 0o222 == 0
                and all(path.stat().st_mode & 0o222 == 0 for path in protected)
            )
        except (OSError, ValueError):
            protection_valid = False
            actual_artifacts = {}
        if (
            not state_path.is_file()
            or not artifact_manifest.is_file()
            or hashlib_sha256(state_path.read_bytes()) != expected_artifacts[
                "authority-state.yaml"
            ]
            or actual_artifacts != expected_artifacts
            or any(
                hashlib_sha256((publication / name).read_bytes()) != expected_digest
                for name, expected_digest in expected_artifacts.items()
            )
            or not protection_valid
        ):
            raise AuthorityPublicationError(
                "conflicting runtime publication already exists"
            )
        return publication, state_path, artifact_manifest

    @staticmethod
    def _seal_publication(publication: Path) -> None:
        for path in sorted(publication.rglob("*"), reverse=True):
            if path.is_file():
                path.chmod(0o444)
            elif path.is_dir():
                path.chmod(0o555)
        publication.chmod(0o555)

    def _verify_idempotent_activation(
        self, directory: Path, target: Path
    ) -> dict[str, Any]:
        receipt = load_mapping(
            directory / "activation-receipt.yaml", "activation receipt"
        )
        receipt_digest = receipt.pop("receipt_digest", None)
        if receipt_digest != digest(receipt):
            raise AuthorityPublicationError("activation receipt digest mismatch")
        receipt["receipt_digest"] = receipt_digest
        if str(Path(target).resolve()) != receipt.get("target"):
            raise AuthorityPublicationError("idempotent activation target mismatch")
        active = authoritative_source_path(self.root)
        if hashlib_sha256(active.read_bytes()) != receipt["activated_state_digest"]:
            raise AuthorityPublicationError(
                "idempotent activation artifact digest mismatch"
            )
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
        expected_pointer = (
            runtime_path(self.root, "authority", ACTIVE_PUBLICATION_POINTER)
        ).resolve()
        if target_path == expected_pointer:
            active = authoritative_source_path(self.root)
            if hashlib_sha256(active.read_bytes()) != receipt["activated_state_digest"]:
                raise AuthorityPublicationError(
                    "active authority state changed after activation"
                )
        elif hashlib_sha256(target_path.read_bytes()) != receipt["activated_state_digest"]:
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

# --- CR46 ZO-024 / ZO-059 / ZO-061: authority owner projections ---
def result_freshness_projection(
    result_record: Mapping[str, Any],
    *,
    active_gate_id: str,
    authority_digest: str | None = None,
    authority_revision: Any = None,
    lifecycle_revision: Any = None,
) -> dict[str, Any]:
    from scripts.lib.emp.stage1_runtime import result_freshness_provenance

    return {
        **result_freshness_provenance(
            result_record,
            active_gate_id=active_gate_id,
            authority_digest=authority_digest,
            authority_revision=authority_revision,
            lifecycle_revision=lifecycle_revision,
        ),
        "owner_surface": "authority_publication",
    }


def gate_execution_provenance_projection(
    gate_id: str,
    **context: Any,
) -> dict[str, Any]:
    from scripts.lib.emp.stage1_runtime import (
        classify_gate_execution_provenance,
    )

    return {
        **classify_gate_execution_provenance(
            gate_id,
            **context,
        ),
        "owner_surface": "authority_publication",
    }


def validation_applicability_projection(
    validator_class: str,
    **context: Any,
) -> dict[str, Any]:
    from scripts.lib.emp.codex_reconciliation import (
        classify_validation_applicability,
    )

    return {
        **classify_validation_applicability(
            validator_class,
            **context,
        ),
        "owner_surface": "authority_publication",
    }
