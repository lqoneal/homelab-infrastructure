"""Canonical, receipt-backed bootstrap identities for direct WOP submission.

This module is intentionally pure.  It does not write runtime state, resolve
publication authority, or launch a provider.  Stage1Runtime owns persistence
and uses these values as the single transaction envelope for an unpublished
Development WOP.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from typing import Any, Mapping


SCHEMA_VERSION = 1
BOOTSTRAP_CLASSIFICATION = "UNPUBLISHED_WOP_SUBMISSION_BOOTSTRAP"


def canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def identity(prefix: str, material: Mapping[str, Any]) -> str:
    return f"{prefix}-" + str(uuid.uuid5(uuid.NAMESPACE_URL, canonical(material)))


def _receipt(receipt_type: str, payload: Mapping[str, Any], timestamp: str) -> dict[str, Any]:
    value = {"schema_version": SCHEMA_VERSION, "receipt_type": receipt_type,
             **dict(payload), "timestamp": timestamp}
    value["receipt_id"] = identity("ZEUS-RECEIPT-" + receipt_type.upper(), value)
    value["receipt_digest"] = digest(value)
    return value


def build(*, metadata: Mapping[str, Any], source: str, source_digest: str,
          repository: str, branch: str, baseline: str, operator: str,
          execution_mode: str, effect_profile: str, timestamp: str,
          package_digest: str, package_id: str, registration_id: str,
          authority_snapshot_id: str, authority_snapshot_digest: str,
          admission_id: str, execution_id: str) -> dict[str, Any]:
    """Return the immutable bootstrap envelope and its receipt chain."""
    binding = {"wop_id": str(metadata["wop_id"]), "mission_id": str(metadata["mission_id"]),
               "source_digest": source_digest, "repository": repository,
               "branch": branch, "baseline": baseline, "execution_mode": execution_mode,
               "effect_profile": effect_profile}
    transaction_id = identity("ZEUS-SUBMISSION-TRANSACTION", binding)
    authority_source = "Engineering Governance / MANUAL-GOVERNANCE-WOP-AUTHORITY-POLICY@1.0"
    submission = _receipt("submission", {
        "transaction_id": transaction_id, "wop_id": binding["wop_id"],
        "mission_id": binding["mission_id"], "source_locator": source,
        "source_digest": source_digest, "repository_identity": repository,
        "canonical_branch": branch, "published_baseline": baseline,
        "operator_identity": operator, "execution_mode": execution_mode,
        "effect_profile": effect_profile, "bootstrap_classification": BOOTSTRAP_CLASSIFICATION,
        "authority_source": authority_source,
    }, timestamp)
    provenance_material = {**binding, "transaction_id": transaction_id,
                           "submission_receipt_digest": submission["receipt_digest"],
                           "authority_source": authority_source}
    provenance_id = identity("ZEUS-PROVENANCE", provenance_material)
    provenance = {"schema_version": SCHEMA_VERSION, "provenance_id": provenance_id,
                  "record_type": "submission-provenance", **provenance_material,
                  "package_digest": package_digest, "authority_snapshot_id": authority_snapshot_id,
                  "admission_id": admission_id, "execution_id": execution_id,
                  "submitted_at": timestamp}
    provenance["provenance_digest"] = digest(provenance)
    execution_transaction_id = identity("ZEUS-EXECUTION-TRANSACTION", {
        "transaction_id": transaction_id, "provenance_id": provenance_id,
        "package_digest": package_digest, "authority_snapshot_digest": authority_snapshot_digest,
    })
    chain = {
        "schema_version": SCHEMA_VERSION, "classification": BOOTSTRAP_CLASSIFICATION,
        "transaction_id": transaction_id, "source_digest": source_digest,
        "submission_receipt": submission, "provenance": provenance,
        "execution_transaction_id": execution_transaction_id,
        "registration_id": registration_id, "package_id": package_id,
        "package_digest": package_digest, "authority_snapshot_id": authority_snapshot_id,
        "authority_snapshot_digest": authority_snapshot_digest, "admission_id": admission_id,
        "execution_id": execution_id, "bootstrap_authority": authority_source,
        "execution_authority": "Engineering Governance",
        "publication_authority": None,
        "publication_authority_required": True,
        "replay_key": digest(binding),
    }
    chain["chain_digest"] = digest(chain)
    return chain


def verify(chain: Mapping[str, Any]) -> None:
    """Fail closed when an immutable bootstrap envelope was altered."""
    submission = chain.get("submission_receipt")
    provenance = chain.get("provenance")
    if not isinstance(submission, Mapping) or not isinstance(provenance, Mapping):
        raise ValueError("bootstrap chain is incomplete")
    supplied = submission.get("receipt_digest")
    unsigned = dict(submission)
    unsigned.pop("receipt_digest", None)
    if not supplied or supplied != digest(unsigned):
        raise ValueError("submission receipt digest mismatch")
    supplied = provenance.get("provenance_digest")
    unsigned = dict(provenance)
    unsigned.pop("provenance_digest", None)
    if not supplied or supplied != digest(unsigned):
        raise ValueError("provenance digest mismatch")
    supplied = chain.get("chain_digest")
    unsigned = dict(chain)
    unsigned.pop("chain_digest", None)
    if not supplied or supplied != digest(unsigned):
        raise ValueError("bootstrap chain digest mismatch")
    if submission.get("transaction_id") != chain.get("transaction_id"):
        raise ValueError("submission transaction binding mismatch")
    if provenance.get("transaction_id") != chain.get("transaction_id"):
        raise ValueError("provenance transaction binding mismatch")
    if submission.get("source_digest") != chain.get("source_digest"):
        raise ValueError("source digest binding mismatch")
