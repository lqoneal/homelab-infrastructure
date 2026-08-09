"""Identity-preserving canonicalization for Development WOP sources.

The structured Phase-1 authoring service intentionally derives new identities
from a mission-source document.  This service is the complementary boundary
for an already-authoritative Development WOP source: it preserves the source
bytes and declared identities while materializing the provenance envelope
required by the canonical P2 submission boundary.

It is deliberately deterministic and idempotent.  A pre-existing sidecar is
verified; it is never regenerated over a conflicting artifact.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from pathlib import Path
from typing import Any, Mapping

from scripts.lib.emp.repository_identity import resolve, resolve_declared
from scripts.lib.emp.wop_packaging import extract, lint_source, source_digest
from scripts.lib.emp.wop_validation import require_valid_source
from scripts.lib.emp.wop_verification import verify_artifact


class CanonicalizationError(ValueError):
    """A Development source cannot safely become a canonical authored WOP."""

    def __init__(self, message: str, *, reason_code: str = "CANONICALIZATION_FAILED", evidence: Mapping[str, Any] | None = None):
        self.reason_code = reason_code
        self.evidence = {"reason_code": reason_code, **dict(evidence or {})}
        super().__init__(message)


TEMPLATE = "docs/templates/TPL-0001-ENGINEERING_WORK_ORDER_TEMPLATE.md"
CONTEXT = "engineering/docs/architecture/OPERATION-BETA-AUTHORITY-MODEL.md"
TEMPLATE_IDENTITY = "TPL-0001@1.7"
PROVENANCE_SCHEMA = "phase1-authored-wop/1"


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _compact(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _compact(value[key]) for key in sorted(value, key=str)}
    if isinstance(value, list):
        return [_compact(item) for item in value]
    if isinstance(value, str):
        return " ".join(value.split())
    return value


def _write_immutable(path: Path, value: Mapping[str, Any]) -> bool:
    serialized = json.dumps(value, indent=2, sort_keys=True) + "\n"
    path = path.resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_text(encoding="utf-8") != serialized:
            raise CanonicalizationError(
                f"existing provenance conflicts with deterministic canonicalization: {path}",
                reason_code="PROVENANCE_CONFLICT",
            )
        return True
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent), text=True)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(serialized)
            stream.flush()
            os.fsync(stream.fileno())
        try:
            os.link(temporary, path)
            os.unlink(temporary)
        except FileExistsError:
            os.unlink(temporary)
            if path.read_text(encoding="utf-8") != serialized:
                raise CanonicalizationError("concurrent provenance differs", reason_code="PROVENANCE_CONFLICT")
            return True
    except Exception:
        try:
            os.unlink(temporary)
        except OSError:
            pass
        raise
    return False


def _operation(source: Path, text: str, metadata: Mapping[str, Any]) -> str:
    explicit = str(metadata.get("operation", metadata.get("target_operation", ""))).strip().upper()
    if explicit:
        return explicit
    if re.search(r"\bOperation\s+Beta\b", text, re.IGNORECASE) and not re.search(r"\bOperational\s+Alpha\b", text, re.IGNORECASE):
        return "BETA"
    raise CanonicalizationError(
        f"{source} does not declare Operation Beta", reason_code="OPERATION_BETA_NOT_DECLARED"
    )


def _expected_trace(source: Path, repository_root: Path, metadata: Mapping[str, Any], text: str) -> dict[str, Any]:
    identity = resolve(repository_root)
    declared = metadata.get("repository_identity")
    if declared not in (None, ""):
        try:
            resolve_declared(declared, repository_root)
        except ValueError as error:
            raise CanonicalizationError(str(error), reason_code="REPOSITORY_IDENTITY_MISMATCH") from error
    operation = _operation(source, text, metadata)
    if operation != "BETA":
        raise CanonicalizationError("Operation Beta is required", reason_code="OPERATION_BETA_REQUIRED")
    digest = source_digest(source)
    template_path = repository_root / TEMPLATE
    context_path = repository_root / CONTEXT
    if not template_path.is_file() or not context_path.is_file():
        raise CanonicalizationError("authoritative template or Operation Beta context is unavailable", reason_code="AUTHORITATIVE_CONTEXT_MISSING")
    validation = require_valid_source(source, repository_root=repository_root).as_dict()
    lint_issues = lint_source(source, metadata)
    normalized = _compact({"metadata": dict(validation["metadata"]), "operation": operation})
    context_digest = _digest({"operation": operation, "repository": identity, "context_digest": source_digest(context_path)})
    trace: dict[str, Any] = {
        "schema_version": PROVENANCE_SCHEMA,
        "authoring_mode": "IDENTITY_PRESERVING_AUTOMATIC_CANONICALIZATION",
        "result": "PASS",
        "readiness": "ADMISSION_READY",
        "wop_id": str(metadata["wop_id"]),
        "mission_id": str(metadata["mission_id"]),
        "operation": operation,
        "repository": identity,
        "source": {
            "path": str(source.resolve()),
            "digest": digest,
            "normalized_digest": _digest(normalized),
        },
        "template": {
            "path": str(template_path.resolve()),
            "digest": source_digest(template_path),
            "identity": TEMPLATE_IDENTITY,
        },
        "context": {
            "path": str(context_path.resolve()),
            "digest": context_digest,
            "identity": "Operation Beta",
            "source_digest": source_digest(context_path),
        },
        "output_digest": digest,
        "source_to_output": {
            "source_bytes": "canonical_authored_wop_output",
            "Wop Id": "wop_id",
            "Mission Id": "mission_id",
            "all_declared_metadata": "source_preserved_without_rewrite",
        },
        "lint": {"result": "PASS" if not lint_issues else "WARN", "issues": lint_issues},
        "validation": validation,
        "blockers": [],
        "authority": {
            "governance_authority": "operator-submitted WOP",
            "wop_authority": "operator-submitted WOP",
            "generic_second_approval_required": False,
            "approval_state": "NOT_REQUIRED_UNLESS_DECLARED_IN_WOP",
        },
        "canonicalization": {
            "mode": "IDENTITY_PRESERVING",
            "source_bytes_preserved": True,
            "source_digest": digest,
            "wop_identity_preserved": True,
            "mission_identity_preserved": True,
        },
        "next_action": "zeus submit <SOURCE>",
    }
    return trace


def _verify_existing(source: Path, repository_root: Path, metadata: Mapping[str, Any], text: str, sidecar: Path) -> dict[str, Any]:
    verified = verify_artifact(source)
    if verified.get("result") != "PASS":
        raise CanonicalizationError(
            "existing authored provenance is not verifiable",
            reason_code="PROVENANCE_INVALID",
            evidence=verified,
        )
    trace = verified["traceability"]
    expected_digest = source_digest(source)
    if trace.get("operation") != "BETA":
        raise CanonicalizationError("existing provenance is not Operation Beta", reason_code="OPERATION_BETA_REQUIRED")
    for field in ("wop_id", "mission_id"):
        if metadata.get(field) not in (None, "") and str(trace.get(field, "")) != str(metadata.get(field, "")):
            raise CanonicalizationError(
                f"existing provenance {field} conflicts with source identity",
                reason_code="PROVENANCE_IDENTITY_CONFLICT",
                evidence={"field": field, "source": metadata.get(field), "provenance": trace.get(field)},
            )
    source_record = trace.get("source") or {}
    provenance_source = Path(str(source_record.get("path", "")))
    if not provenance_source.is_file() or source_record.get("digest") != source_digest(provenance_source):
        raise CanonicalizationError("source digest differs from existing provenance", reason_code="SOURCE_DIGEST_MISMATCH")
    if trace.get("output_digest") != expected_digest:
        raise CanonicalizationError("authored output digest differs from source", reason_code="OUTPUT_DIGEST_MISMATCH")
    declared = (trace.get("repository") or {}).get("canonical_repository_identity")
    try:
        resolve_declared(declared, repository_root)
    except ValueError as error:
        raise CanonicalizationError(str(error), reason_code="REPOSITORY_IDENTITY_MISMATCH") from error
    return {"classification": "CURRENT_AUTHORED", "traceability": trace, "traceability_path": str(sidecar.resolve()), "replayed": True}


def canonicalize(source: Path | str, repository_root: Path | str) -> dict[str, Any]:
    source = Path(source).resolve()
    repository = Path(repository_root).resolve()
    if not source.is_file() or source.suffix.lower() not in {".md", ".markdown", ".txt", ".docx"}:
        raise CanonicalizationError("input is not a promotable Development source", reason_code="NOT_PROMOTABLE_SOURCE")
    try:
        metadata, text = extract(source, validate=False)
    except Exception as error:
        raise CanonicalizationError(str(error), reason_code="SOURCE_PARSE_FAILED") from error
    sidecar = source.with_suffix(source.suffix + ".traceability.json")
    if sidecar.is_file():
        return _verify_existing(source, repository, metadata, text, sidecar)
    try:
        require_valid_source(source, repository_root=repository)
    except Exception as error:
        raise CanonicalizationError(str(error), reason_code="SOURCE_CONTRACT_INVALID") from error
    trace = _expected_trace(source, repository, metadata, text)
    replayed = _write_immutable(sidecar, trace)
    return {"classification": "DEVELOPMENT_SOURCE_PROMOTABLE", "traceability": trace,
            "traceability_path": str(sidecar.resolve()), "replayed": replayed}


def classify(source: Path | str, repository_root: Path | str) -> dict[str, Any]:
    """Classify a source without creating a provenance sidecar."""
    source = Path(source).resolve()
    if source.is_dir():
        return {"classification": "LEGACY_SUPPORTED", "source": str(source)}
    sidecar = source.with_suffix(source.suffix + ".traceability.json")
    if sidecar.is_file():
        result = canonicalize(source, repository_root)
        return {key: result[key] for key in ("classification", "traceability_path", "traceability")}
    if source.suffix.lower() in {".md", ".markdown", ".txt", ".docx"}:
        # Contract validation is intentionally performed here so malformed or
        # ambiguous inputs fail closed before any legacy option is considered.
        canonicalize_result = _classification_probe(source, repository_root)
        return canonicalize_result
    return {"classification": "LEGACY_SUPPORTED", "source": str(source)}


def _classification_probe(source: Path, repository_root: Path) -> dict[str, Any]:
    try:
        metadata, text = extract(source, validate=False)
        require_valid_source(source, repository_root=repository_root)
        trace = _expected_trace(source, Path(repository_root), metadata, text)
    except CanonicalizationError:
        raise
    except Exception as error:
        raise CanonicalizationError(str(error), reason_code="SOURCE_CONTRACT_INVALID") from error
    return {"classification": "DEVELOPMENT_SOURCE_PROMOTABLE", "wop_id": trace["wop_id"], "mission_id": trace["mission_id"]}
