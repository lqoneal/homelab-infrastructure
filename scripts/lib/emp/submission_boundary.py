"""Canonical P2-G1 submission boundary.

This boundary consumes an already-authored, ``ADMISSION_READY`` WOP.  It
validates the immutable authoring trace, records one deterministic submission
receipt, and invokes the admission *request* boundary exactly once.  It does
not run Mission Admission or execution stages.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import uuid
from pathlib import Path
from typing import Any, Mapping

from scripts.lib.emp.repository_identity import resolve, resolve_declared
from scripts.lib.emp.wop_verification import canonical_replay_content, verify_artifact


class SubmissionError(ValueError):
    """Submission cannot safely cross the admission-request boundary."""

    def __init__(self, message: str, *, evidence: Mapping[str, Any] | None = None):
        self.evidence = dict(evidence or {})
        super().__init__(message)


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _write_immutable(path: Path, value: Mapping[str, Any]) -> None:
    serialized = json.dumps(value, indent=2, sort_keys=True) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("x", encoding="utf-8") as stream:
            stream.write(serialized)
            stream.flush()
            os.fsync(stream.fileno())
    except FileExistsError:
        if path.read_text(encoding="utf-8") != serialized:
            raise SubmissionError("immutable submission identity collision")


def _load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise SubmissionError(f"submission receipt is unreadable: {error}") from error
    if not isinstance(value, dict):
        raise SubmissionError("submission receipt must be an object")
    return value


class AdmissionRequestBoundary:
    """The P2 boundary projection; it never executes Mission Admission."""

    def __init__(self, directory: Path | str):
        self.directory = Path(directory)

    def invoke(self, request: Mapping[str, Any]) -> dict[str, Any]:
        request = dict(request)
        request_id = request["admission_request_id"]
        path = self.directory / f"{request_id}.json"
        _write_immutable(path, request)
        return {"result": "PASS", "invocations": 1, "request_id": request_id, "path": str(path)}


def _identity_from_trace(trace: Mapping[str, Any], repository: Path) -> dict[str, Any]:
    declared = (trace.get("repository") or {}).get("canonical_repository_identity")
    if not declared:
        declared = (trace.get("repository") or {}).get("repository_path")
    if not declared:
        raise SubmissionError("canonical repository identity is missing", evidence={"reason_code": "REPOSITORY_IDENTITY_MISSING"})
    try:
        resolved = resolve_declared(declared, repository)
    except ValueError as error:
        raise SubmissionError(str(error), evidence={"reason_code": "REPOSITORY_IDENTITY_MISMATCH"}) from error
    actual = resolve(repository)
    if resolved["canonical_repository_identity"] != actual["canonical_repository_identity"]:
        raise SubmissionError("canonical repository identity mismatch", evidence={"reason_code": "REPOSITORY_IDENTITY_MISMATCH"})
    return resolved


def _validate(wop: Path, repository: Path) -> dict[str, Any]:
    trace_path = wop.with_suffix(wop.suffix + ".traceability.json")
    if not trace_path.is_file():
        raise SubmissionError("immutable authoring provenance is unavailable", evidence={"reason_code": "PROVENANCE_MISSING"})
    verified = verify_artifact(wop)
    if verified.get("result") != "PASS":
        raise SubmissionError("WOP readiness or immutable authoring verification failed", evidence=verified)
    trace = verified["traceability"]
    if trace.get("operation") != "BETA":
        raise SubmissionError("Operation Beta verification failed", evidence={"reason_code": "OPERATION_BETA_REQUIRED", "operation": trace.get("operation")})
    if trace.get("readiness") != "ADMISSION_READY":
        raise SubmissionError("WOP is not ADMISSION_READY", evidence={"reason_code": "READINESS_NOT_ADMISSION_READY"})
    wop_id = str(trace.get("wop_id") or "")
    mission_id = str(trace.get("mission_id") or "")
    if not re.fullmatch(r"WOP-[A-Z0-9][A-Z0-9-]+", wop_id):
        raise SubmissionError("WOP identity is invalid", evidence={"reason_code": "INVALID_WOP_ID", "wop_id": wop_id})
    if not re.fullmatch(r"[A-Z][A-Z0-9]*(?:-[A-Z0-9.]+)+", mission_id):
        raise SubmissionError("Mission identity is invalid", evidence={"reason_code": "INVALID_MISSION_ID", "mission_id": mission_id})
    identity = _identity_from_trace(trace, repository)
    source = (trace.get("source") or {})
    source_path = Path(str(source.get("path", "")))
    if not source_path.is_file() or source.get("digest") != hashlib.sha256(source_path.read_bytes()).hexdigest():
        raise SubmissionError("immutable source provenance does not match", evidence={"reason_code": "SOURCE_PROVENANCE_MISMATCH", "source": str(source_path)})
    output_digest = str(trace.get("output_digest") or "")
    if output_digest != hashlib.sha256(wop.read_bytes()).hexdigest():
        raise SubmissionError("WOP output digest does not match immutable provenance", evidence={"reason_code": "OUTPUT_PROVENANCE_MISMATCH"})
    return {"trace": trace, "trace_path": str(trace_path.resolve()), "wop": str(wop.resolve()),
            "wop_id": wop_id, "mission_id": mission_id, "repository": identity,
            "output_digest": output_digest, "source_digest": str(source["digest"]),
            "template_digest": (trace.get("template") or {}).get("digest"),
            "context_digest": (trace.get("context") or {}).get("digest")}


def submit(wop: Path | str, *, repository: Path | str, store_directory: Path | str,
           admission_boundary: AdmissionRequestBoundary | None = None) -> dict[str, Any]:
    repository_path = Path(repository).resolve()
    facts = _validate(Path(wop).resolve(), repository_path)
    identity = {
        "operation": "BETA", "repository": facts["repository"]["canonical_repository_identity"],
        "wop_id": facts["wop_id"], "mission_id": facts["mission_id"],
        "output_digest": facts["output_digest"], "source_digest": facts["source_digest"],
    }
    submission_id = "SUBMISSION-" + str(uuid.uuid5(uuid.NAMESPACE_URL, _canonical(identity)))
    request_id = "ADMISSION-REQUEST-" + str(uuid.uuid5(uuid.NAMESPACE_URL, submission_id))
    directory = Path(store_directory)
    receipt_path = directory / "receipts" / f"{submission_id}.json"
    if receipt_path.exists():
        receipt = _load(receipt_path)
        if receipt.get("submission_digest") != _digest(identity):
            raise SubmissionError("duplicate submission identity has a different digest", evidence={"reason_code": "DUPLICATE_IDENTITY_DIGEST_MISMATCH"})
        return {**receipt, "receipt_path": str(receipt_path), "duplicate_submission": "IDEMPOTENT", "idempotent_replay": True}
    submission_digest = _digest(identity)
    receipt = {
        "schema_version": 1, "receipt_type": "submission", "submission_id": submission_id,
        "submission_digest": submission_digest, "operation": "BETA", "repository_identity": facts["repository"],
        "wop_id": facts["wop_id"], "mission_id": facts["mission_id"],
        "wop_output_digest": facts["output_digest"], "source_digest": facts["source_digest"],
        "immutable_provenance": {"traceability_digest": _digest(canonical_replay_content(facts["trace"])), "template_digest": facts["template_digest"], "context_digest": facts["context_digest"]},
        "submission_state": "ADMISSION_REQUESTED", "submission_result": "PASS",
        "duplicate_submission": "NEW", "admission_request_id": request_id,
        "next_action": "EVALUATE_MISSION_ADMISSION",
    }
    receipt["receipt_digest"] = _digest(receipt)
    request = {"schema_version": 1, "request_type": "mission-admission-request", "admission_request_id": request_id,
               "submission_id": submission_id, "submission_digest": submission_digest, "mission_id": facts["mission_id"],
               "wop_id": facts["wop_id"], "repository_identity": facts["repository"], "invocation_count": 1,
               "mission_admission_executed": False, "next_action": "EVALUATE_MISSION_ADMISSION"}
    boundary = admission_boundary or AdmissionRequestBoundary(directory / "requests")
    boundary_result = boundary.invoke(request)
    if boundary_result.get("result") != "PASS" or boundary_result.get("invocations") != 1:
        raise SubmissionError("admission request boundary did not produce exactly one invocation", evidence=boundary_result)
    # The receipt remains deterministic; the boundary invocation is recorded
    # in the separate immutable request projection.
    _write_immutable(receipt_path, receipt)
    return {**receipt, "receipt_path": str(receipt_path), "duplicate_submission": "NEW", "idempotent_replay": False}
