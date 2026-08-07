"""Canonical, non-executing WOP package contract.

This module validates the portable package description used by future WOP
authoring.  It deliberately does not submit, admit, dispatch, or execute a
package.  Authority remains external to the package and technical edges are
the only permitted dependency edges.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

import yaml


SCHEMA_VERSION = "canonical-wop-package/1"
REQUIRED_TOP_LEVEL = (
    "package_identity", "authority_binding", "bootstrap", "requirements",
    "execution_graph", "evidence_contract", "recovery_contract",
    "failure_model", "publication_boundary", "reconciliation_contract",
    "closeout_contract", "extensions",
)
DEPENDENCY_KINDS = {
    "TECHNICAL_CAPABILITY", "INTERFACE", "DATA", "ARTIFACT", "QUALIFICATION",
    "ENVIRONMENT", "RESOURCE", "INTEGRATION", "PUBLICATION_BASELINE", "SAFETY",
}
EXTENSION_TYPES = {"CAGF_SOURCE_PROJECTION"}


class CanonicalPackageError(ValueError):
    """Raised when a canonical package candidate fails closed."""


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def package_digest(package: Mapping[str, Any]) -> str:
    payload = {key: value for key, value in package.items() if key != "integrity"}
    return hashlib.sha256(_canonical(payload).encode("utf-8")).hexdigest()


def _require_mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise CanonicalPackageError(f"{label} must be a mapping")
    return value


def _require_nonempty_string(value: Any, label: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise CanonicalPackageError(f"{label} must be a non-empty string")


def _require_string_list(value: Any, label: str, *, nonempty: bool = False) -> None:
    if not isinstance(value, list) or any(not isinstance(item, str) or not item for item in value):
        raise CanonicalPackageError(f"{label} must be a list of non-empty strings")
    if nonempty and not value:
        raise CanonicalPackageError(f"{label} must not be empty")
    if len(value) != len(set(value)):
        raise CanonicalPackageError(f"{label} must not contain duplicates")


def _walk_graph(requirements: list[Mapping[str, Any]]) -> None:
    ids = [item.get("requirement_id") for item in requirements]
    if any(not isinstance(item, str) or not item for item in ids):
        raise CanonicalPackageError("requirements.requirement_id must be non-empty")
    if len(ids) != len(set(ids)):
        raise CanonicalPackageError("requirement IDs must be unique")
    known = set(ids)
    edges: dict[str, set[str]] = {item: set() for item in ids}
    for item in requirements:
        for dependency in item.get("technical_dependencies", []):
            dep = _require_mapping(dependency, "technical_dependencies item")
            kind = dep.get("kind")
            if kind not in DEPENDENCY_KINDS:
                raise CanonicalPackageError(f"unsupported or authority dependency kind: {kind}")
            if "authority" in str(dep.get("kind", "")).upper() or "authority" in str(dep.get("requirement_id", "")).lower():
                raise CanonicalPackageError("mission-to-mission authority dependencies are prohibited")
            target = dep.get("requirement_id")
            if target is not None:
                if target not in known:
                    raise CanonicalPackageError(f"unknown technical dependency: {target}")
                edges[item["requirement_id"]].add(target)
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node: str) -> None:
        if node in visiting:
            raise CanonicalPackageError("technical dependency cycle detected")
        if node in visited:
            return
        visiting.add(node)
        for target in edges[node]:
            visit(target)
        visiting.remove(node)
        visited.add(node)

    for node in edges:
        visit(node)


def _validate_cagf_extension(extension: Mapping[str, Any]) -> None:
    payload = _require_mapping(extension.get("payload"), "CAGF extension payload")
    required = {
        "projection_family", "source_owners", "normalized_inputs", "source_digests",
        "freshness_rules", "identity_rules", "generator", "projection",
        "provenance_manifest", "publication_policy", "qualification",
    }
    missing = sorted(required - set(payload))
    if missing:
        raise CanonicalPackageError("CAGF extension missing: " + ", ".join(missing))
    _require_nonempty_string(payload["projection_family"], "CAGF projection_family")
    _require_string_list(payload["source_owners"], "CAGF source_owners", nonempty=True)
    _require_string_list(payload["normalized_inputs"], "CAGF normalized_inputs", nonempty=True)
    _require_string_list(payload["source_digests"], "CAGF source_digests", nonempty=True)
    generator = _require_mapping(payload["generator"], "CAGF generator")
    for key in ("identity", "digest", "deterministic"):
        if key not in generator:
            raise CanonicalPackageError(f"CAGF generator missing: {key}")
    projection = _require_mapping(payload["projection"], "CAGF projection")
    if projection.get("authority") is not False:
        raise CanonicalPackageError("CAGF generated projection must be non-authoritative")


def validate(package: Mapping[str, Any]) -> dict[str, Any]:
    """Validate a package candidate and return derived immutable facts."""
    if not isinstance(package, Mapping):
        raise CanonicalPackageError("package root must be a mapping")
    if package.get("schema_version") != SCHEMA_VERSION:
        raise CanonicalPackageError(f"schema_version must be {SCHEMA_VERSION}")
    missing = [field for field in REQUIRED_TOP_LEVEL if field not in package]
    if missing:
        raise CanonicalPackageError("package missing: " + ", ".join(missing))
    identity = _require_mapping(package["package_identity"], "package_identity")
    for key in ("package_id", "wop_id", "mission_id", "gate_id", "revision", "baseline_commit"):
        if key not in identity:
            raise CanonicalPackageError(f"package_identity missing: {key}")
    _require_nonempty_string(identity["package_id"], "package_id")
    _require_nonempty_string(identity["wop_id"], "wop_id")
    _require_nonempty_string(identity["mission_id"], "mission_id")
    _require_nonempty_string(identity["gate_id"], "gate_id")
    if not isinstance(identity["revision"], int) or identity["revision"] < 1:
        raise CanonicalPackageError("package revision must be a positive integer")
    if not isinstance(identity["baseline_commit"], str) or len(identity["baseline_commit"]) != 40:
        raise CanonicalPackageError("baseline_commit must be a full Git SHA")
    authority = _require_mapping(package["authority_binding"], "authority_binding")
    if authority.get("authority_source") in (None, ""):
        raise CanonicalPackageError("authority_binding.authority_source is required")
    if authority.get("mission_to_mission") is True:
        raise CanonicalPackageError("mission-to-mission authority is prohibited")
    bootstrap = _require_mapping(package["bootstrap"], "bootstrap")
    _require_string_list(bootstrap.get("steps"), "bootstrap.steps", nonempty=True)
    requirements = package["requirements"]
    if not isinstance(requirements, list) or not requirements:
        raise CanonicalPackageError("requirements must be a non-empty list")
    normalized_requirements: list[Mapping[str, Any]] = []
    for item in requirements:
        req = _require_mapping(item, "requirement")
        for key in ("requirement_id", "objective", "verification", "evidence", "acceptance", "failure_behavior", "replay_behavior"):
            if key not in req:
                raise CanonicalPackageError(f"requirement missing: {key}")
        normalized_requirements.append(req)
    _walk_graph(normalized_requirements)
    graph = _require_mapping(package["execution_graph"], "execution_graph")
    if graph.get("model") not in ("DAG", "HYBRID"):
        raise CanonicalPackageError("execution_graph.model must be DAG or HYBRID")
    for field in ("implementation_complete", "qualification_complete", "publication_authorized", "published", "repository_reconciled", "eos_synchronized", "closed"):
        if field not in package["publication_boundary"]:
            raise CanonicalPackageError(f"publication_boundary missing: {field}")
    for extension in package["extensions"]:
        ext = _require_mapping(extension, "extension")
        if ext.get("type") not in EXTENSION_TYPES:
            raise CanonicalPackageError(f"unsupported extension type: {ext.get('type')}")
        if ext.get("type") == "CAGF_SOURCE_PROJECTION":
            _validate_cagf_extension(ext)
    supplied = _require_mapping(package.get("integrity", {}), "integrity")
    digest = package_digest(package)
    if supplied and supplied.get("package_digest") != digest:
        raise CanonicalPackageError("package_digest does not match canonical package payload")
    return {
        "result": "PASS",
        "schema_version": SCHEMA_VERSION,
        "package_id": identity["package_id"],
        "package_digest": digest,
        "requirement_count": len(requirements),
        "extension_types": [item.get("type") for item in package["extensions"]],
        "executable": False,
    }


def load(path: Path | str) -> dict[str, Any]:
    path = Path(path)
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as error:
        raise CanonicalPackageError(f"invalid canonical package: {error}") from error
    if not isinstance(value, Mapping):
        raise CanonicalPackageError("canonical package root must be a mapping")
    validate(value)
    return dict(value)
