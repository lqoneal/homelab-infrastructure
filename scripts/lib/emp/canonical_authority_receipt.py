"""Canonical, read-only authority-receipt interpretation for Zeus lifecycle views.

The repository contains three receipt shapes because Stage 1 and autonomous
dispatch predate the canonical P2/P3/P4 chain.  This module is the explicit
compatibility boundary between those shapes.  It never grants authority and
never writes or rewrites historical receipts.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Sequence


class AuthorityReceiptError(ValueError):
    """An authority receipt is missing, ambiguous, or contradictory."""

    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(message)


CONTRACT = "ZEUS-CANONICAL-AUTHORITY-RECEIPT"
VERSION = "1"
REQUIRED_CANONICAL = (
    "governance_authority",
    "wop_authority",
    "generic_second_approval_required",
    "approval_state",
)


def _digest(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _text(value: Any) -> str | None:
    return str(value) if value is not None and str(value) else None


def _identity_check(value: Mapping[str, Any], expected: Mapping[str, Any] | None) -> None:
    if not expected:
        return
    fields = ("mission_id", "wop_id", "submission_id", "repository_identity")
    mismatches = [field for field in fields if expected.get(field) is not None and value.get(field) is not None
                  and value.get(field) != expected.get(field)]
    if mismatches:
        raise AuthorityReceiptError(
            "AUTHORITY_RECEIPT_IDENTITY_MISMATCH",
            "authority receipt identity differs for: " + ", ".join(mismatches),
        )


def _verify_digest(value: Mapping[str, Any], digest_key: str, *, label: str) -> str:
    supplied = value.get(digest_key)
    if not supplied:
        raise AuthorityReceiptError("AUTHORITY_RECEIPT_DIGEST_MISSING", f"{label} has no {digest_key}")
    unsigned = {key: item for key, item in value.items() if key != digest_key}
    if supplied != _digest(unsigned):
        raise AuthorityReceiptError("AUTHORITY_RECEIPT_DIGEST_MISMATCH", f"{label} digest is invalid")
    return str(supplied)


def _canonical(value: Mapping[str, Any], source: str, expected: Mapping[str, Any] | None) -> dict[str, Any]:
    authority = value.get("authority")
    if not isinstance(authority, Mapping):
        raise AuthorityReceiptError("AUTHORITY_RECEIPT_MISSING", f"{source} has no canonical authority envelope")
    missing = [key for key in REQUIRED_CANONICAL if key not in authority]
    if missing:
        raise AuthorityReceiptError("AUTHORITY_RECEIPT_INCOMPLETE", f"canonical authority is missing: {', '.join(missing)}")
    _identity_check(value, expected)
    if authority.get("generic_second_approval_required") is not False:
        raise AuthorityReceiptError("GENERIC_SECOND_APPROVAL_CONTRADICTION", "canonical authority requires a generic second approval")
    receipt_digest = _verify_digest(value, "receipt_digest", label=source) if value.get("receipt_digest") else None
    return {
        "contract": {"id": CONTRACT, "version": VERSION},
        "classification": "CANONICAL",
        "source": source,
        "mission_id": value.get("mission_id"),
        "wop_id": value.get("wop_id"),
        "submission_id": value.get("submission_id"),
        "repository_identity": value.get("repository_identity"),
        "receipt_digest": receipt_digest,
        "authority_snapshot_digest": authority.get("authority_snapshot_digest"),
        "governance_authority": authority["governance_authority"],
        "wop_authority": authority["wop_authority"],
        "approval_state": authority["approval_state"],
        "generic_second_approval_required": False,
        "explicit_wop_approvals": list(authority.get("explicit_wop_approvals") or []),
        "resolution": "AUTHORIZED_BY_SUBMITTED_WOP",
        "read_only": True,
    }


def _snapshot(value: Mapping[str, Any], snapshot: Mapping[str, Any], source: str,
              expected: Mapping[str, Any] | None, classification: str) -> dict[str, Any]:
    _identity_check({**value, **snapshot}, expected)
    digest_key = "authority_snapshot_digest"
    # Some historical autonomous fixtures retain only the opaque snapshot
    # digest.  Preserve that evidence as an explicit compatibility class; it
    # is not promoted to canonical authority and cannot satisfy a new
    # canonical lifecycle boundary by itself.
    if set(snapshot) <= {digest_key} and snapshot.get(digest_key):
        return {
            "contract": {"id": CONTRACT, "version": VERSION},
            "classification": "AUTONOMOUS_LEGACY_UNVERIFIED",
            "source": source,
            "mission_id": value.get("mission_id"), "wop_id": value.get("wop_id"),
            "submission_id": value.get("submission_id"), "repository_identity": value.get("repository_identity"),
            "receipt_digest": value.get("receipt_digest"),
            "authority_snapshot_digest": snapshot[digest_key],
            "governance_authority": "UNVERIFIED_LEGACY",
            "wop_authority": "UNVERIFIED_LEGACY",
            "approval_state": "UNVERIFIED_LEGACY",
            "generic_second_approval_required": None,
            "explicit_wop_approvals": [], "resolution": "LEGACY_COMPATIBILITY_ONLY", "read_only": True,
        }
    snapshot_digest = _verify_digest(snapshot, digest_key, label=source)
    governance = snapshot.get("governance_authority") or snapshot.get("authority_source")
    wop_authority = snapshot.get("wop_authority") or governance
    approval = snapshot.get("approval_state") or snapshot.get("decision")
    if not governance or not wop_authority or not approval:
        raise AuthorityReceiptError("AUTHORITY_RECEIPT_INCOMPLETE", f"{source} authority snapshot is incomplete")
    if snapshot.get("resolution") not in (None, "AUTHORIZED") and classification != "STAGE1_LEGACY":
        raise AuthorityReceiptError("AUTHORITY_RECEIPT_NOT_AUTHORIZED", f"{source} is not an authorized snapshot")
    return {
        "contract": {"id": CONTRACT, "version": VERSION},
        "classification": classification,
        "source": source,
        "mission_id": value.get("mission_id") or snapshot.get("mission_id"),
        "wop_id": value.get("wop_id") or snapshot.get("wop_id"),
        "submission_id": value.get("submission_id") or snapshot.get("submission_id"),
        "repository_identity": value.get("repository_identity") or snapshot.get("repository"),
        "receipt_digest": value.get("receipt_digest"),
        "authority_snapshot_digest": snapshot_digest,
        "governance_authority": governance,
        "wop_authority": wop_authority,
        "approval_state": approval,
        "generic_second_approval_required": False,
        "explicit_wop_approvals": list(snapshot.get("explicit_wop_approvals") or []),
        "resolution": "COMPATIBILITY_ADAPTER",
        "read_only": True,
    }


def normalize(value: Mapping[str, Any], *, source: str = "UNSPECIFIED",
              expected: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Normalize one canonical, Stage 1, or autonomous authority receipt."""
    if not isinstance(value, Mapping):
        raise AuthorityReceiptError("AUTHORITY_RECEIPT_INVALID", f"{source} is not an object")
    if isinstance(value.get("authority"), Mapping):
        return _canonical(value, source, expected)
    snapshot = value.get("authority_snapshot")
    if isinstance(snapshot, Mapping):
        return _snapshot(value, snapshot, source, expected, "STAGE1_LEGACY" if value.get("receipts") else "AUTONOMOUS_LEGACY")
    receipts = value.get("receipts")
    authorization = receipts.get("authorization") if isinstance(receipts, Mapping) else None
    if isinstance(authorization, Mapping):
        snapshot = value.get("authority_snapshot")
        if not isinstance(snapshot, Mapping):
            return {
                "contract": {"id": CONTRACT, "version": VERSION},
                "classification": "STAGE1_LEGACY_UNVERIFIED",
                "source": source,
                "mission_id": value.get("mission_id"), "wop_id": value.get("wop_id"),
                "submission_id": value.get("submission_id"), "repository_identity": value.get("repository_identity"),
                "receipt_digest": authorization.get("receipt_digest"), "authority_snapshot_digest": None,
                "governance_authority": (value.get("authorization") or {}).get("authority_source", "UNVERIFIED_LEGACY"),
                "wop_authority": "UNVERIFIED_LEGACY", "approval_state": (value.get("authorization") or {}).get("decision", "UNVERIFIED_LEGACY"),
                "generic_second_approval_required": None, "explicit_wop_approvals": [],
                "resolution": "LEGACY_COMPATIBILITY_ONLY", "read_only": True,
            }
        return _snapshot(value, snapshot, source, expected, "STAGE1_LEGACY")
    raise AuthorityReceiptError("AUTHORITY_RECEIPT_MISSING", f"{source} contains no recognized authority receipt")


def resolve(candidates: Sequence[tuple[str, Mapping[str, Any]]], *, expected: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Resolve compatible authority candidates without selecting a new authority.

    Canonical evidence is preferred only as a classification.  A legacy
    candidate may coexist when its normalized authority semantics agree; a
    semantic disagreement or duplicate canonical current receipt fails closed.
    """
    if not candidates:
        raise AuthorityReceiptError("AUTHORITY_RECEIPT_MISSING", "no authority receipt candidates were supplied")
    normalized = [normalize(value, source=source, expected=expected) for source, value in candidates]
    canonical = [item for item in normalized if item["classification"] == "CANONICAL"]
    if len(canonical) > 1:
        raise AuthorityReceiptError("AUTHORITY_RECEIPT_AMBIGUOUS", "multiple canonical authority receipts are current")
    comparable = ("governance_authority", "wop_authority", "approval_state", "generic_second_approval_required")
    anchor = canonical[0] if canonical else normalized[0]
    for item in normalized[1:]:
        if any(item.get(field) != anchor.get(field) for field in comparable):
            raise AuthorityReceiptError("AUTHORITY_RECEIPT_CONTRADICTION", "authority receipt semantics disagree")
    return {
        **anchor,
        "candidates": normalized,
        "legacy_candidates": [item for item in normalized if item is not anchor],
        "canonical_candidate_count": len(canonical),
        "compatibility": "VERIFIED" if len(normalized) > 1 else "NOT_REQUIRED",
    }


def from_path(path: Path | str, *, source: str | None = None,
              expected: Mapping[str, Any] | None = None) -> dict[str, Any]:
    path = Path(path)
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise AuthorityReceiptError("AUTHORITY_RECEIPT_INVALID", f"{path}: {error}") from error
    if not isinstance(value, Mapping):
        raise AuthorityReceiptError("AUTHORITY_RECEIPT_INVALID", f"{path} is not an object")
    return normalize(value, source=source or str(path), expected=expected)
