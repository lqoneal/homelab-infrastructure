"""Fail-closed consolidation qualification for Progressive Runtime governance."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from scripts.lib.authority_pipeline import (
    progressive_runtime_capabilities,
    progressive_runtime_dependencies,
    progressive_runtime_execution_contracts,
    progressive_runtime_outcomes,
    progressive_runtime_policies,
    progressive_runtime_registration,
    progressive_runtime_states,
    progressive_runtime_transitions,
)


class RuntimeConsolidationError(ValueError):
    """The consolidated Progressive Runtime baseline is inconsistent."""


SPEC_PATH = "docs/specifications/SPEC-0012-PRODUCTION-EXECUTION-FOUNDATION.md"
INDEX_PATH = "docs/DOC-0001-REPOSITORY_DOCUMENT_INDEX.md"
EXPECTED_SPEC_VERSION = "1.12"
EXPECTED_INDEX_VERSION = "2.71"
REGISTRIES = (
    progressive_runtime_dependencies.CLASSIFICATION_PATH,
    progressive_runtime_registration.REGISTRY_PATH,
    progressive_runtime_capabilities.REGISTRY_PATH,
    progressive_runtime_policies.REGISTRY_PATH,
    progressive_runtime_states.REGISTRY_PATH,
    progressive_runtime_transitions.REGISTRY_PATH,
    progressive_runtime_execution_contracts.REGISTRY_PATH,
    progressive_runtime_outcomes.REGISTRY_PATH,
)
CHAIN = (
    "Runtime Outcome",
    "Runtime Execution Contract",
    "Runtime Transition",
    "Runtime State",
    "Runtime Policy",
    "Runtime Capability",
    "Runtime Layer",
    "Runtime Interface",
    "Registered Runtime Consumer",
)


def _read(root: Path, relative: str) -> str:
    path = root / relative
    if not path.is_file():
        raise RuntimeConsolidationError(
            f"runtime consolidation input is incomplete: {relative}"
        )
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        raise RuntimeConsolidationError(
            f"runtime consolidation input is invalid: {relative}"
        ) from error


def _document_version(text: str, document_id: str) -> str:
    identifier = re.search(r"(?m)^document_id: (\S+)$", text)
    version = re.search(r"(?m)^version: (\S+)$", text)
    if (
        identifier is None
        or identifier.group(1) != document_id
        or version is None
    ):
        raise RuntimeConsolidationError(
            f"missing documentation reference: {document_id}"
        )
    return version.group(1)


def validate(repository: Path | str) -> dict[str, object]:
    """Qualify the accepted registries, full traceability, and documents."""
    root = Path(repository).resolve()
    try:
        dependency = progressive_runtime_dependencies.validate(root)
        registration = progressive_runtime_registration.validate(root)
        capability = progressive_runtime_capabilities.validate(root)
        policy = progressive_runtime_policies.validate(root)
        state = progressive_runtime_states.validate(root)
        transition = progressive_runtime_transitions.validate(root)
        contract = progressive_runtime_execution_contracts.validate(root)
        outcome = progressive_runtime_outcomes.validate(root)
    except ValueError as error:
        raise RuntimeConsolidationError(str(error)) from error

    registry_digests: dict[str, str] = {}
    for relative in REGISTRIES:
        data = _read(root, relative).encode()
        registry_digests[relative] = hashlib.sha256(data).hexdigest()

    spec = _read(root, SPEC_PATH)
    index = _read(root, INDEX_PATH)
    if _document_version(spec, "SPEC-0012") != EXPECTED_SPEC_VERSION:
        raise RuntimeConsolidationError("stale SPEC-0012 runtime baseline metadata")
    if _document_version(index, "DOC-0001") != EXPECTED_INDEX_VERSION:
        raise RuntimeConsolidationError("stale DOC-0001 runtime baseline metadata")
    required_spec_terms = (
        "Progressive Runtime Governance Baseline v1.0",
        "Runtime Outcomes are architecture metadata only",
        "production behavior is changed\nby this baseline.",
    )
    if any(term not in spec for term in required_spec_terms):
        raise RuntimeConsolidationError("inconsistent documentation: SPEC-0012")
    if (
        "SPEC-0012 Version 1.12" not in index
        or "Progressive Runtime Governance Baseline v1.0" not in index
    ):
        raise RuntimeConsolidationError("missing documentation reference: DOC-0001")

    analyses = {
        "dependency": dependency,
        "registration": registration,
        "capability": capability,
        "policy": policy,
        "state": state,
        "transition": transition,
        "execution_contract": contract,
        "outcome": outcome,
    }
    counts = {
        "runtime_layers": len(dependency["runtime_layers"]),
        "registered_consumers": registration["consumer_count"],
        "runtime_capabilities": capability["capability_count"],
        "runtime_policies": policy["policy_count"],
        "runtime_states": state["state_count"],
        "runtime_transitions": transition["transition_count"],
        "runtime_execution_contracts": contract["execution_contract_count"],
        "runtime_outcomes": outcome["outcome_count"],
    }
    payload: dict[str, object] = {
        "status": "PASS",
        "baseline": "Progressive Runtime Governance Baseline v1.0",
        "chain": list(CHAIN),
        "counts": counts,
        "registry_sha256": registry_digests,
        "controlled_documents": {
            "SPEC-0012": EXPECTED_SPEC_VERSION,
            "DOC-0001": EXPECTED_INDEX_VERSION,
        },
        "analyses": analyses,
    }
    canonical = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode()
    payload["qualification_sha256"] = hashlib.sha256(canonical).hexdigest()
    return payload
