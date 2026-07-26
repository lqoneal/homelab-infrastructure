#!/usr/bin/env python3
"""Authorized public-key enrollment for operational authority owners."""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
import uuid
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping

import yaml

from scripts.lib.emp.authority_publication import (
    REQUIRED_OWNERS,
    SIGNATURE_NAMESPACE,
    AuthorityPublicationError,
    digest,
    load_mapping,
)
from scripts.lib.emp.authority_resolution import canonical_json, utc_text


class OwnerEnrollmentError(ValueError):
    """Owner enrollment input or lifecycle transition is invalid."""


ENROLLMENT_NAMESPACE = "zeus-owner-enrollment"
ROOT_POLICY_RELATIVE_PATH = Path("engineering/authority/enrollment-root-policy.yaml")
REGISTRY_RELATIVE_PATH = Path("engineering/authority/owner-enrollment-registry.yaml")


def enrollment_status(
    root: Path | str, registry_path: Path | str | None = None
) -> dict[str, Any]:
    repository = Path(root).resolve()
    path = (
        Path(registry_path)
        if registry_path is not None
        else fixed_path(repository, REGISTRY_RELATIVE_PATH)
    )
    registry = load_mapping(path, "owner enrollment registry")
    supplied = registry.pop("registry_digest", None)
    valid_digest = supplied == digest(registry)
    active = [
        value
        for value in registry.get("enrollments", {}).values()
        if value.get("lifecycle_state") == "active"
    ]
    owners = {value.get("owner") for value in active}
    return {
        "registry_digest_valid": valid_digest,
        "active_enrollment_count": len(active),
        "enrolled_owners": sorted(owner for owner in owners if owner),
        "missing_owners": sorted(REQUIRED_OWNERS - owners),
        "trust_compilation_ready": valid_digest and owners == REQUIRED_OWNERS,
    }


def fixed_path(root: Path, relative: Path) -> Path:
    path = root.resolve() / relative
    if path.is_symlink() or (path.parent.exists() and path.parent.resolve() != path.parent):
        raise OwnerEnrollmentError("enrollment path may not use symbolic links")
    return path


def public_key_details(path: Path | str) -> dict[str, str]:
    key_path = Path(path)
    try:
        text = key_path.read_text(encoding="utf-8").strip()
    except OSError as error:
        raise OwnerEnrollmentError(f"public key cannot be read: {error}") from error
    if "PRIVATE KEY" in text or not text.startswith(("ssh-", "ecdsa-")):
        raise OwnerEnrollmentError("only OpenSSH public keys may be enrolled")
    result = subprocess.run(
        ["ssh-keygen", "-lf", str(key_path), "-E", "sha256"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode:
        raise OwnerEnrollmentError("public key validation failed")
    parts = result.stdout.strip().split()
    if len(parts) < 4 or not parts[1].startswith("SHA256:"):
        raise OwnerEnrollmentError("public key fingerprint is unavailable")
    return {
        "public_key": " ".join(text.split()[:2]),
        "fingerprint": parts[1],
        "key_type": parts[-1].strip("()"),
    }


def request_identifier(value: Mapping[str, Any]) -> str:
    material = {key: item for key, item in value.items() if key != "request_id"}
    return "OWNER-ENROLLMENT-" + str(
        uuid.uuid5(uuid.NAMESPACE_URL, canonical_json(material))
    )


def prepare_request(
    *,
    action: str,
    owner: str,
    principal: str,
    authorization_reference: str,
    requested_at: datetime,
    public_key_path: Path | str | None = None,
    target_enrollment_id: str | None = None,
) -> dict[str, Any]:
    if action not in {"enroll", "rotate", "suspend", "retire"}:
        raise OwnerEnrollmentError("enrollment action is unsupported")
    if owner not in REQUIRED_OWNERS:
        raise OwnerEnrollmentError("owner is not a designated authority owner")
    if not principal or not authorization_reference:
        raise OwnerEnrollmentError(
            "principal and explicit authorization reference are required"
        )
    key = None
    if action in {"enroll", "rotate"}:
        if public_key_path is None:
            raise OwnerEnrollmentError("enroll/rotate requires a public key")
        key = public_key_details(public_key_path)
    elif public_key_path is not None:
        raise OwnerEnrollmentError("suspend/retire must not supply a new key")
    if action in {"rotate", "suspend", "retire"} and not target_enrollment_id:
        raise OwnerEnrollmentError(f"{action} requires target enrollment identity")
    value = {
        "schema_version": 1,
        "action": action,
        "owner": owner,
        "principal": principal,
        "authorization_reference": authorization_reference,
        "requested_at": utc_text(requested_at),
        "target_enrollment_id": target_enrollment_id,
        "key": key,
    }
    value["request_id"] = request_identifier(value)
    return value


class EnrollmentTrustRoot:
    def __init__(self, root: Path | str, policy_path: Path | str | None = None):
        self.root = Path(root).resolve()
        path = (
            Path(policy_path)
            if policy_path is not None
            else fixed_path(self.root, ROOT_POLICY_RELATIVE_PATH)
        )
        self.policy = load_mapping(path, "enrollment root policy")
        if (
            self.policy.get("schema_version") != 1
            or self.policy.get("operationally_configured") is not True
        ):
            raise OwnerEnrollmentError("enrollment root policy is not configured")
        if self.policy.get("signature_namespace") != ENROLLMENT_NAMESPACE:
            raise OwnerEnrollmentError("enrollment signature namespace mismatch")
        principals = self.policy.get("authorization_principals")
        if not isinstance(principals, list) or not principals:
            raise OwnerEnrollmentError("enrollment authorization principals absent")
        self.principals = set(principals)
        allowed = Path(str(self.policy.get("allowed_signers_file", "")))
        if not allowed.is_absolute():
            allowed = self.root / allowed
        self.allowed = allowed.resolve()
        if not self.allowed.is_file() or not self.allowed.read_text().strip():
            raise OwnerEnrollmentError("enrollment allowed signers absent")

    def verify(self, request: Mapping[str, Any], signature: Path, signer: str) -> None:
        if signer not in self.principals:
            raise OwnerEnrollmentError("enrollment signer is not authorized")
        result = subprocess.run(
            [
                "ssh-keygen", "-Y", "verify",
                "-f", str(self.allowed),
                "-I", signer,
                "-n", ENROLLMENT_NAMESPACE,
                "-s", str(signature),
            ],
            input=canonical_json(request).encode(),
            capture_output=True,
            check=False,
        )
        if result.returncode:
            raise OwnerEnrollmentError("enrollment authorization signature invalid")


class OwnerEnrollmentRegistry:
    def __init__(
        self,
        root: Path | str,
        *,
        policy_path: Path | str | None = None,
        registry_path: Path | str | None = None,
    ):
        self.root = Path(root).resolve()
        self.trust = EnrollmentTrustRoot(self.root, policy_path)
        self.path = (
            Path(registry_path)
            if registry_path is not None
            else fixed_path(self.root, REGISTRY_RELATIVE_PATH)
        )

    def apply(
        self, *, request_path: Path | str, signature: Path | str, signer: str
    ) -> dict[str, Any]:
        request = load_mapping(request_path, "enrollment request")
        if (
            request.get("schema_version") != 1
            or request.get("action") not in {"enroll", "rotate", "suspend", "retire"}
            or request.get("owner") not in REQUIRED_OWNERS
            or not request.get("principal")
            or not request.get("authorization_reference")
        ):
            raise OwnerEnrollmentError("enrollment request is incomplete")
        if request.get("request_id") != request_identifier(request):
            raise OwnerEnrollmentError("enrollment request identity mismatch")
        self.trust.verify(request, Path(signature), signer)
        registry = load_mapping(self.path, "owner enrollment registry")
        if registry.get("schema_version") != 1:
            raise OwnerEnrollmentError("owner enrollment registry schema invalid")
        supplied_digest = registry.get("registry_digest")
        if supplied_digest != digest(
            {key: value for key, value in registry.items() if key != "registry_digest"}
        ):
            raise OwnerEnrollmentError("owner enrollment registry digest mismatch")
        records = registry.get("enrollments")
        if not isinstance(records, Mapping):
            raise OwnerEnrollmentError("owner enrollment registry records invalid")
        records = deepcopy(dict(records))
        action = request["action"]
        target_id = request.get("target_enrollment_id")
        if action in {"suspend", "retire", "rotate"}:
            target = records.get(target_id)
            if not isinstance(target, Mapping) or target.get("lifecycle_state") != "active":
                raise OwnerEnrollmentError("target enrollment is not active")
            target = deepcopy(dict(target))
            target["lifecycle_state"] = {
                "rotate": "rotated",
                "suspend": "suspended",
                "retire": "retired",
            }[action]
            target["successor_enrollment_id"] = None
            records[target_id] = target
        new_id = None
        if action in {"enroll", "rotate"}:
            key = request["key"]
            for existing in records.values():
                if (
                    existing.get("fingerprint") == key["fingerprint"]
                    and existing.get("lifecycle_state") == "active"
                ):
                    raise OwnerEnrollmentError("public key is already actively enrolled")
            new_id = "OWNER-IDENTITY-" + str(
                uuid.uuid5(
                    uuid.NAMESPACE_URL,
                    canonical_json(
                        {
                            "owner": request["owner"],
                            "principal": request["principal"],
                            "fingerprint": key["fingerprint"],
                        }
                    ),
                )
            )
            records[new_id] = {
                "enrollment_id": new_id,
                "owner": request["owner"],
                "principal": request["principal"],
                **key,
                "lifecycle_state": "active",
                "authorization_reference": request["authorization_reference"],
                "authorization_request_id": request["request_id"],
                "authorization_signer": signer,
                "predecessor_enrollment_id": target_id,
                "successor_enrollment_id": None,
            }
            if target_id:
                records[target_id]["successor_enrollment_id"] = new_id
        registry["enrollments"] = records
        registry["revision"] = int(registry.get("revision", 0)) + 1
        registry["registry_digest"] = digest(
            {key: value for key, value in registry.items() if key != "registry_digest"}
        )
        self._atomic_yaml(self.path, registry)
        return {
            "action": action,
            "request_id": request["request_id"],
            "enrollment_id": new_id or target_id,
            "lifecycle_state": (
                "active" if new_id else records[target_id]["lifecycle_state"]
            ),
            "registry_revision": registry["revision"],
        }

    def verify(self) -> dict[str, Any]:
        return enrollment_status(self.root, self.path)

    def compile_trust(self, output: Path | str) -> dict[str, str]:
        status = self.verify()
        if not status["trust_compilation_ready"]:
            raise OwnerEnrollmentError("all designated owners must be actively enrolled")
        registry = load_mapping(self.path, "owner enrollment registry")
        active = sorted(
            (
                value
                for value in registry["enrollments"].values()
                if value["lifecycle_state"] == "active"
            ),
            key=lambda value: (value["owner"], value["principal"]),
        )
        directory = Path(output)
        directory.mkdir(parents=True, exist_ok=False)
        signers = directory / "allowed-signers"
        signers.write_text(
            "".join(
                f"{value['principal']} {value['public_key']}\n" for value in active
            )
        )
        policy = {
            "schema_version": 1,
            "operationally_configured": True,
            "signature_namespace": SIGNATURE_NAMESPACE,
            "allowed_signers_file": "allowed-signers",
            "owners": {},
            "source_registry_digest": registry["registry_digest"],
            "candidate_only": True,
        }
        for value in active:
            policy["owners"].setdefault(value["owner"], {"principals": []})[
                "principals"
            ].append(value["principal"])
        policy_path = directory / "owner-trust-policy.yaml"
        policy_path.write_text(yaml.safe_dump(policy, sort_keys=True))
        return {"policy": str(policy_path), "allowed_signers": str(signers)}

    @staticmethod
    def _atomic_yaml(path: Path, value: Mapping[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporary = tempfile.mkstemp(dir=path.parent, prefix=".enrollment.")
        try:
            with os.fdopen(descriptor, "w") as stream:
                yaml.safe_dump(dict(value), stream, sort_keys=True)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, path)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
