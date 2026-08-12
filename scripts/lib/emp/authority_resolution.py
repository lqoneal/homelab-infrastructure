#!/usr/bin/env python3
"""Fail-closed Authority Resolution Bundle runtime."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import uuid
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Mapping

import yaml

from scripts.lib.authority.engine import AuthorityGraph, AuthorityValidationError
from scripts.lib.emp.runtime_paths import runtime_path


class AuthorityResolutionError(ValueError):
    """Authority state cannot produce a valid operational bundle."""


PRODUCTION_AUTHORITY_OWNER = "Lawrence O'Neal"
PRODUCTION_AUTHORITY_PRINCIPAL = "loneal"
OWNER = {
    "mission": PRODUCTION_AUTHORITY_OWNER,
    "repository": PRODUCTION_AUTHORITY_OWNER,
    "approval": PRODUCTION_AUTHORITY_OWNER,
    "authority": PRODUCTION_AUTHORITY_OWNER,
    "governing_baseline": PRODUCTION_AUTHORITY_OWNER,
    "submitter": PRODUCTION_AUTHORITY_OWNER,
}
AUTHORITY_STATE_RELATIVE_PATH = Path(
    "engineering/authority/operational-authority-state.yaml"
)
AUTHORITY_RUNTIME_RELATIVE_PATH = Path(".zeus/runtime/authority")
ACTIVE_PUBLICATION_POINTER = "active-publication.json"
PLACEHOLDER = re.compile(r"(?:placeholder|example|test|tbd|unknown)", re.IGNORECASE)
COMMIT = re.compile(r"^[0-9a-f]{40}$")
DIGEST = re.compile(r"^[0-9a-f]{64}$")


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def identifier(prefix: str, value: Any) -> str:
    return f"{prefix}-{uuid.uuid5(uuid.NAMESPACE_URL, canonical_json(value))}"


def utc_text(value: datetime) -> str:
    if value.tzinfo is None:
        raise AuthorityResolutionError("resolution timestamp must include a timezone")
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def load_authority_state(path: Path | str) -> Mapping[str, Any]:
    try:
        value = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as error:
        raise AuthorityResolutionError(f"invalid authority source state: {error}") from error
    if not isinstance(value, Mapping):
        raise AuthorityResolutionError("authority source state must be an object")
    return value


def authoritative_source_path(repository_root: Path | str) -> Path:
    """Return the integrity-qualified production authority source path.

    New publications live in an ignored, append-only operational store so
    activation cannot modify the Git baseline it authorizes.  The tracked
    source remains a migration fallback until the first runtime publication.
    """
    root = Path(repository_root).resolve()
    runtime = runtime_path(root, "authority")
    pointer = runtime / ACTIVE_PUBLICATION_POINTER
    if pointer.is_file():
        try:
            value = json.loads(pointer.read_text(encoding="utf-8"))
            relative = Path(str(value["authority_state"]))
            expected = str(value["authority_state_digest"])
            manifest_relative = Path(str(value["artifact_manifest"]))
            manifest_expected = str(value["artifact_manifest_digest"])
        except (OSError, KeyError, TypeError, json.JSONDecodeError) as error:
            raise AuthorityResolutionError(
                f"invalid active authority publication pointer: {error}"
            ) from error
        if relative.is_absolute() or ".." in relative.parts:
            raise AuthorityResolutionError("authority publication path is not bounded")
        path = (runtime / relative).resolve()
        if runtime not in path.parents:
            raise AuthorityResolutionError("authority publication escapes runtime store")
        if path.is_symlink() or not path.is_file():
            raise AuthorityResolutionError("active authority publication is unavailable")
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != expected:
            raise AuthorityResolutionError(
                "active authority publication digest mismatch"
            )
        manifest = (runtime / manifest_relative).resolve()
        if (
            runtime not in manifest.parents
            or manifest.is_symlink()
            or not manifest.is_file()
            or hashlib.sha256(manifest.read_bytes()).hexdigest() != manifest_expected
        ):
            raise AuthorityResolutionError(
                "active authority publication manifest mismatch"
            )
        for line in manifest.read_text(encoding="utf-8").splitlines():
            artifact_digest, separator, artifact_name = line.partition("  ")
            artifact = (manifest.parent / artifact_name).resolve()
            if (
                not separator
                or manifest.parent not in artifact.parents
                or not artifact.is_file()
                or hashlib.sha256(artifact.read_bytes()).hexdigest()
                != artifact_digest
            ):
                raise AuthorityResolutionError(
                    "active authority publication artifact integrity failure"
                )
        return path
    path = root / AUTHORITY_STATE_RELATIVE_PATH
    if path.is_symlink() or (path.parent.exists() and path.parent.resolve() != path.parent):
        raise AuthorityResolutionError("authority source path may not use symbolic links")
    return path


def authority_activation_target(repository_root: Path | str) -> Path:
    """Return the fixed pointer updated by production activation."""
    root = Path(repository_root).resolve()
    return root / AUTHORITY_RUNTIME_RELATIVE_PATH / ACTIVE_PUBLICATION_POINTER


class AuthorityResolutionRuntime:
    """Resolve read-only, owner-labelled repository state into a sealed ARB."""

    VERSION = "zeus-authority-resolution/1"

    def __init__(self, repository_root: Path | str, source_state: Mapping[str, Any]):
        self.root = Path(repository_root).resolve()
        self.state = deepcopy(dict(source_state))

    def resolve(
        self,
        *,
        mission_id: str,
        work_item_id: str,
        principal_id: str,
        issued_at: datetime,
    ) -> dict[str, Any]:
        self._validate_state()
        mission = self._select("missions", mission_id, OWNER["mission"])
        work = self._select("work_items", work_item_id, OWNER["mission"])
        if work.get("mission_id") != mission_id:
            raise AuthorityResolutionError("work item mission binding mismatch")
        phase_id = work.get("phase_id")
        phase = self._select("phases", phase_id, OWNER["mission"])
        if phase.get("mission_id") != mission_id:
            raise AuthorityResolutionError("phase mission binding mismatch")
        for label, value in (("mission", mission), ("phase", phase), ("work item", work)):
            if value.get("lifecycle_state") not in {"active", "qualified", "ready"}:
                raise AuthorityResolutionError(f"{label} lifecycle state is not admissible")
        if work.get("qualification_status") != "QUALIFIED":
            raise AuthorityResolutionError("work item is not qualified")

        repository = self._repository()
        approval = self._approval(work)
        authority = self._authority(work)
        governing = self._governing()
        principal = self._select("principals", principal_id, OWNER["submitter"])
        if principal.get("authentication_status") != "VERIFIED":
            raise AuthorityResolutionError("submitter authentication is not verified")

        material = {
            "mission_id": mission_id,
            "phase_id": phase_id,
            "work_item_id": work_item_id,
            "intent_revision": work["revision"],
            "repository_id": repository["repository_id"],
            "baseline_commit": repository["baseline_commit"],
            "approval_reference": approval["reference"],
            "authority_node_id": authority["authority_node_id"],
            "principal_id": principal_id,
        }
        issued = utc_text(issued_at)
        expires = utc_text(issued_at + timedelta(minutes=15))
        resolution_id = identifier("ARB", material)
        reservations = {
            "wop_reservation_id": identifier("WOP-RESERVATION", material),
            "adr_evaluation_request_id": identifier("ADR-REQUEST", material),
        }
        provenance = [
            self._provenance("mission", OWNER["mission"], mission),
            self._provenance("phase", OWNER["mission"], phase),
            self._provenance("work_item", OWNER["mission"], work),
            self._provenance("repository", OWNER["repository"], repository),
            self._provenance("approval", OWNER["approval"], approval),
            self._provenance("authority", OWNER["authority"], authority),
            self._provenance(
                "governing_baseline", OWNER["governing_baseline"], governing
            ),
            self._provenance("submitter", OWNER["submitter"], principal),
        ]
        bundle = {
            "schema_version": 1,
            "resolution_id": resolution_id,
            "mode": "operational",
            "issued_at": issued,
            "expires_at": expires,
            "mission": {
                "mission_id": mission_id,
                "phase_id": phase_id,
                "work_item_id": work_item_id,
                "intent_revision": work["revision"],
                "qualification_record": work["qualification_record"],
            },
            "repository": {
                key: repository[key]
                for key in (
                    "repository_id", "canonical_locator", "baseline_commit", "assertion_id"
                )
            },
            "approval": {
                key: approval[key]
                for key in (
                    "reference", "authority", "decision", "decision_at",
                    "authorized_lifecycle_state", "scope_digest",
                )
            },
            "authority": {
                key: authority[key]
                for key in (
                    "authority_node_id", "graph_version", "chain", "capabilities",
                    "resolution_digest",
                )
            },
            "governing_baseline": {
                key: governing[key]
                for key in (
                    "manifest_id", "manifest_revision", "references", "manifest_digest"
                )
            },
            "submitter": {
                "principal_id": principal_id,
                "session_id": principal["session_id"],
                "authentication_record": principal["authentication_record"],
            },
            "reservations": reservations,
            "provenance": provenance,
            "resolver_version": self.VERSION,
        }
        bundle["bundle_digest"] = digest(bundle)
        validate_bundle(bundle, expected_repository=self.root, at=issued_at)
        return bundle

    def _validate_state(self) -> None:
        if self.state.get("schema_version") != 1:
            raise AuthorityResolutionError("authority source schema_version must be 1")
        if self.state.get("operationally_configured") is not True:
            raise AuthorityResolutionError(
                "repository authority source is not operationally configured"
            )
        required = {
            "missions", "phases", "work_items", "repositories", "approvals",
            "authority_bindings", "governing_baselines", "principals",
        }
        if not required.issubset(self.state):
            raise AuthorityResolutionError(
                "authority source state is incomplete: "
                + ", ".join(sorted(required - set(self.state)))
            )
        for collection in required:
            if not isinstance(self.state[collection], Mapping):
                raise AuthorityResolutionError(f"{collection} must be an object")

    def _select(self, collection: str, item_id: str, expected_owner: str) -> dict[str, Any]:
        value = self.state[collection].get(item_id)
        if not isinstance(value, Mapping):
            raise AuthorityResolutionError(f"{collection} record does not resolve: {item_id}")
        result = deepcopy(dict(value))
        if result.get("owner") != expected_owner:
            raise AuthorityResolutionError(f"{collection} authoritative owner mismatch")
        self._reject_placeholders(result)
        return result

    def _repository(self) -> dict[str, Any]:
        matches = [
            deepcopy(dict(value))
            for value in self.state["repositories"].values()
            if isinstance(value, Mapping)
            and Path(str(value.get("canonical_locator", ""))).resolve() == self.root
        ]
        if len(matches) != 1:
            raise AuthorityResolutionError("repository identity must resolve exactly once")
        value = matches[0]
        if value.get("owner") != OWNER["repository"]:
            raise AuthorityResolutionError("repository authoritative owner mismatch")
        discovered = self._git("rev-parse", "--show-toplevel")
        head = self._git("rev-parse", "HEAD")
        if Path(discovered).resolve() != self.root:
            raise AuthorityResolutionError("repository identity mismatch")
        if value.get("baseline_commit") != head or not COMMIT.fullmatch(head):
            raise AuthorityResolutionError("repository baseline mismatch")
        self._reject_placeholders(value)
        return value

    def _approval(self, work: Mapping[str, Any]) -> dict[str, Any]:
        value = self._select(
            "approvals", str(work.get("approval_reference", "")), OWNER["approval"]
        )
        if value.get("decision") != "GRANTED":
            raise AuthorityResolutionError("human approval is not granted")
        if value.get("authorized_lifecycle_state") != "Active":
            raise AuthorityResolutionError("approval does not authorize Active lifecycle")
        if value.get("scope_digest") != work.get("scope_digest"):
            raise AuthorityResolutionError("approval scope does not bind the work item")
        return value

    def _authority(self, work: Mapping[str, Any]) -> dict[str, Any]:
        value = self._select(
            "authority_bindings",
            str(work.get("authority_binding_id", "")),
            OWNER["authority"],
        )
        graph_path = (self.root / str(value.get("graph_path", ""))).resolve()
        try:
            graph = AuthorityGraph.load(graph_path)
            graph.validate()
            resolution = graph.resolve(str(value.get("authority_node_id", "")))
        except AuthorityValidationError as error:
            raise AuthorityResolutionError(f"authority graph invalid: {error}") from error
        chain = list(resolution.path)
        capabilities = sorted(resolution.effective_capabilities)
        resolution_digest = digest(
            {"graph_id": graph.graph_id, "chain": chain, "capabilities": capabilities}
        )
        expected = {
            "graph_version": graph.graph_id,
            "chain": chain,
            "capabilities": capabilities,
            "resolution_digest": resolution_digest,
        }
        for field, item in expected.items():
            if value.get(field) != item:
                raise AuthorityResolutionError(f"authority {field} mismatch")
        return value

    def _governing(self) -> dict[str, Any]:
        active = [
            deepcopy(dict(value))
            for value in self.state["governing_baselines"].values()
            if isinstance(value, Mapping) and value.get("lifecycle_state") == "Active"
        ]
        if len(active) != 1:
            raise AuthorityResolutionError(
                "governing baseline must resolve exactly one Active manifest"
            )
        value = active[0]
        if value.get("owner") != OWNER["governing_baseline"]:
            raise AuthorityResolutionError("governing baseline owner mismatch")
        expected = digest(
            {
                "manifest_id": value.get("manifest_id"),
                "manifest_revision": value.get("manifest_revision"),
                "references": value.get("references"),
            }
        )
        if value.get("manifest_digest") != expected:
            raise AuthorityResolutionError("governing baseline digest mismatch")
        return value

    @staticmethod
    def _provenance(field: str, owner: str, value: Mapping[str, Any]) -> dict[str, str]:
        return {
            "field": field,
            "owner": owner,
            "record_id": str(value["record_id"]),
            "record_revision": str(value["record_revision"]),
            "record_digest": digest(value),
        }

    @staticmethod
    def _reject_placeholders(value: Any) -> None:
        if isinstance(value, Mapping):
            for item in value.values():
                AuthorityResolutionRuntime._reject_placeholders(item)
        elif isinstance(value, list):
            for item in value:
                AuthorityResolutionRuntime._reject_placeholders(item)
        elif isinstance(value, str) and (not value.strip() or PLACEHOLDER.search(value)):
            raise AuthorityResolutionError("operational authority contains a placeholder")

    def _git(self, *arguments: str) -> str:
        result = subprocess.run(
            ["git", "-C", str(self.root), *arguments],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode:
            raise AuthorityResolutionError(
                f"repository verification failed: {result.stderr.strip()}"
            )
        return result.stdout.strip()


def validate_bundle(
    bundle: Mapping[str, Any], *, expected_repository: Path | str, at: datetime
) -> None:
    """Validate a sealed operational bundle and its cross-object bindings."""
    if bundle.get("schema_version") != 1 or bundle.get("mode") != "operational":
        raise AuthorityResolutionError("Authority Resolution Bundle mode/schema invalid")
    supplied = bundle.get("bundle_digest")
    material = {key: value for key, value in bundle.items() if key != "bundle_digest"}
    if supplied != digest(material) or not DIGEST.fullmatch(str(supplied or "")):
        raise AuthorityResolutionError("Authority Resolution Bundle seal mismatch")
    repository = bundle.get("repository", {})
    if Path(str(repository.get("canonical_locator", ""))).resolve() != Path(
        expected_repository
    ).resolve():
        raise AuthorityResolutionError("Authority Resolution Bundle repository mismatch")
    if not COMMIT.fullmatch(str(repository.get("baseline_commit", ""))):
        raise AuthorityResolutionError("Authority Resolution Bundle baseline invalid")
    approval = bundle.get("approval", {})
    if (
        approval.get("decision") != "GRANTED"
        or approval.get("authorized_lifecycle_state") != "Active"
    ):
        raise AuthorityResolutionError("Authority Resolution Bundle approval invalid")
    try:
        expiry = datetime.fromisoformat(str(bundle["expires_at"]).replace("Z", "+00:00"))
    except (KeyError, ValueError) as error:
        raise AuthorityResolutionError("Authority Resolution Bundle expiry invalid") from error
    if at.tzinfo is None or expiry <= at.astimezone(timezone.utc):
        raise AuthorityResolutionError("Authority Resolution Bundle is expired")
    provenance = bundle.get("provenance")
    if not isinstance(provenance, list):
        raise AuthorityResolutionError("Authority Resolution Bundle provenance missing")
    expected_fields = {
        "mission", "phase", "work_item", "repository", "approval", "authority",
        "governing_baseline", "submitter",
    }
    if {item.get("field") for item in provenance if isinstance(item, Mapping)} != expected_fields:
        raise AuthorityResolutionError("Authority Resolution Bundle provenance incomplete")
    for item in provenance:
        if (
            not isinstance(item, Mapping)
            or item.get("owner") not in OWNER.values()
            or not DIGEST.fullmatch(str(item.get("record_digest", "")))
        ):
            raise AuthorityResolutionError("Authority Resolution Bundle provenance invalid")
    AuthorityResolutionRuntime._reject_placeholders(bundle)
