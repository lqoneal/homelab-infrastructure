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


def mission_view(store_directory: Path | str, mission_id: str, action: str = "snapshot") -> dict[str, Any]:
    """Read-only native projection for a mission at the P2 boundary.

    This intentionally requires only the immutable submission receipt and
    admission-request projection.  It does not manufacture an admission or
    bootstrap record merely to satisfy a mission inspection command.
    """
    directory = Path(store_directory).resolve()
    requested_mission = str(mission_id).upper()
    matches: list[tuple[Path, dict[str, Any]]] = []
    for path in sorted((directory / "receipts").glob("*.json")):
        try:
            value = _load(path)
        except SubmissionError:
            continue
        if str(value.get("mission_id", "")).upper() == requested_mission:
            matches.append((path, value))
    if not matches:
        return {"result": "MISSION_NOT_FOUND", "mission_id": requested_mission, "read_only": True}
    if len(matches) != 1:
        return {
            "result": "FAIL", "mission_id": requested_mission, "read_only": True,
            "blockers": [{"code": "MISSION_IDENTITY_AMBIGUOUS", "message": "multiple P2 submission receipts resolve the mission"}],
        }
    receipt_path, receipt = matches[0]
    blockers: list[dict[str, str]] = []

    # P2 is the canonical lifecycle owner while the mission is waiting for
    # admission evaluation.  Verify the immutable receipt and its request
    # projection before exposing any state; do not trust a convenience field
    # or a historical execution record.
    required = ("receipt_type", "submission_id", "submission_digest", "admission_request_id",
                "mission_id", "wop_id", "operation", "repository_identity", "wop_output_digest",
                "source_digest", "immutable_provenance", "submission_state", "submission_result")
    missing = [key for key in required if not receipt.get(key)]
    if missing:
        blockers.append({"code": "CANONICAL_RECEIPT_INCOMPLETE", "message": "submission receipt is missing: " + ", ".join(missing)})
    if receipt.get("receipt_type") != "submission":
        blockers.append({"code": "CANONICAL_RECEIPT_TYPE_INVALID", "message": "mission discovery requires a canonical submission receipt"})
    unsigned = {key: value for key, value in receipt.items() if key != "receipt_digest"}
    if receipt.get("receipt_digest") != _digest(unsigned):
        blockers.append({"code": "CANONICAL_RECEIPT_DIGEST_MISMATCH", "message": "submission receipt digest does not verify"})
    repository_identity = receipt.get("repository_identity")
    canonical_repository = repository_identity.get("canonical_repository_identity") if isinstance(repository_identity, Mapping) else None
    identity = {
        "operation": receipt.get("operation"), "repository": canonical_repository,
        "wop_id": receipt.get("wop_id"), "mission_id": receipt.get("mission_id"),
        "output_digest": receipt.get("wop_output_digest"), "source_digest": receipt.get("source_digest"),
    }
    if receipt.get("submission_digest") != _digest(identity):
        blockers.append({"code": "CANONICAL_IDENTITY_DIGEST_MISMATCH", "message": "submission identity digest does not verify"})
    if str(receipt.get("mission_id", "")).upper() != requested_mission:
        blockers.append({"code": "CANONICAL_MISSION_IDENTITY_MISMATCH", "message": "submission receipt mission identity differs from requested mission"})
    if receipt.get("submission_state") != "ADMISSION_REQUESTED" or receipt.get("submission_result") != "PASS":
        blockers.append({"code": "CANONICAL_STATE_UNSUPPORTED", "message": "read-only P2 resolver supports only ADMISSION_REQUESTED/PASS"})

    request_path = directory / "requests" / f"{receipt.get('admission_request_id')}.json"
    request: dict[str, Any] = {}
    if not request_path.is_file():
        blockers.append({"code": "ADMISSION_REQUEST_PROJECTION_MISSING", "message": "admission request projection is unavailable"})
    else:
        try:
            request = _load(request_path)
        except SubmissionError as error:
            blockers.append({"code": "ADMISSION_REQUEST_PROJECTION_INVALID", "message": str(error)})
    if request:
        request_identity = {
            "admission_request_id": request.get("admission_request_id"),
            "submission_id": request.get("submission_id"), "mission_id": request.get("mission_id"),
            "wop_id": request.get("wop_id"), "submission_digest": request.get("submission_digest"),
        }
        expected_request_id = "ADMISSION-REQUEST-" + str(uuid.uuid5(uuid.NAMESPACE_URL, str(receipt.get("submission_id"))))
        if request.get("admission_request_id") != receipt.get("admission_request_id") or request.get("admission_request_id") != expected_request_id:
            blockers.append({"code": "ADMISSION_REQUEST_IDENTITY_MISMATCH", "message": "admission request identity is not deterministic for the submission"})
        if any(request.get(key) != receipt.get(key) for key in ("submission_id", "mission_id", "wop_id", "submission_digest")):
            blockers.append({"code": "CANONICAL_IDENTITY_CHAIN_MISMATCH", "message": "submission and admission-request identities disagree"})
        if request.get("invocation_count") != 1 or request.get("mission_admission_executed") is not False:
            blockers.append({"code": "ADMISSION_REQUEST_STATE_CONTRADICTION", "message": "admission request is not the single, unexecuted canonical request"})

    authority = receipt.get("authority")
    if not isinstance(authority, Mapping) or authority.get("governance_authority") != "operator-submitted WOP" or authority.get("wop_authority") != "operator-submitted WOP" or authority.get("generic_second_approval_required") is not False:
        blockers.append({"code": "CANONICAL_AUTHORITY_CONTRADICTION", "message": "canonical submission authority projection is invalid"})

    canonical_next = "EVALUATE_MISSION_ADMISSION"
    if receipt.get("next_action") not in (None, canonical_next):
        blockers.append({"code": "CANONICAL_NEXT_ACTION_CONTRADICTION", "message": "submission receipt next action conflicts with ADMISSION_REQUESTED state"})

    value = {
        "result": "PASS" if not blockers else "FAIL",
        "mission": "DISCOVERABLE",
        "mission_id": receipt.get("mission_id"),
        "wop_id": receipt.get("wop_id"),
        "operation": receipt.get("operation"),
        "submission_id": receipt.get("submission_id"),
        "submission_state": receipt.get("submission_state"),
        "lifecycle_state": receipt.get("submission_state"),
        "wop_published": receipt.get("wop_published", "NOT_RESOLVED_BY_P2"),
        "wop_submitted": True,
        "authority": dict(authority) if isinstance(authority, Mapping) else {
            "governance_authority": "operator-submitted WOP",
            "wop_authority": "operator-submitted WOP",
            "generic_second_approval_required": False,
            "approval_state": "NOT_REQUIRED_UNLESS_DECLARED_IN_WOP",
        },
        "blockers": blockers,
        "next_authorized_action": canonical_next,
        "canonical_next_action_source": "P2_SUBMISSION_RECEIPT_STATE",
        "canonical_lifecycle_owner": "RECEIPT_BACKED_CANONICAL_LIFECYCLE_CHAIN",
        "canonical_projection": "P2_SUBMISSION_RECEIPT",
        "readiness": "ADMISSION_REQUESTED",
        "eligibility": "ADMISSION_EVALUATION_PENDING",
        "historical_projections": "PRESERVED_AND_EXCLUDED_FROM_CURRENT_STATE",
        "submission_receipt": {"path": str(receipt_path), "digest": receipt.get("receipt_digest")},
        "admission_request": {"path": str(request_path), "id": receipt.get("admission_request_id"), "invocation_count": request.get("invocation_count")},
        "source_digest": receipt.get("source_digest"),
        "wop_output_digest": receipt.get("wop_output_digest"),
        "immutable_provenance": receipt.get("immutable_provenance"),
        "read_only": True,
    }
    if action == "authority":
        return {key: value[key] for key in ("result", "mission_id", "wop_id", "lifecycle_state", "authority", "blockers", "next_authorized_action", "read_only")}
    if action == "blockers":
        return {key: value[key] for key in ("result", "mission_id", "wop_id", "lifecycle_state", "authority", "blockers", "next_authorized_action", "read_only")}
    if action == "next":
        return {key: value[key] for key in ("result", "mission_id", "wop_id", "lifecycle_state", "authority", "blockers", "next_authorized_action", "read_only")}
    if action == "readiness":
        return {key: value[key] for key in ("result", "mission_id", "wop_id", "readiness", "lifecycle_state", "authority", "blockers", "next_authorized_action", "read_only")}
    if action == "eligibility":
        return {key: value[key] for key in ("result", "mission_id", "wop_id", "eligibility", "lifecycle_state", "authority", "blockers", "next_authorized_action", "read_only")}
    if action in {"show", "state", "status", "lifecycle"}:
        return {key: value[key] for key in ("result", "mission_id", "wop_id", "lifecycle_state", "submission_state", "authority", "blockers", "next_authorized_action", "read_only")}
    return value


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
           admission_boundary: AdmissionRequestBoundary | None = None,
           submission_context: Mapping[str, Any] | None = None) -> dict[str, Any]:
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
        expected_traceability = (receipt.get("immutable_provenance") or {}).get("traceability_digest")
        actual_traceability = _digest(canonical_replay_content(facts["trace"]))
        if expected_traceability != actual_traceability:
            raise SubmissionError(
                "replayed source provenance differs from the submitted identity",
                evidence={"reason_code": "PROVENANCE_REPLAY_MISMATCH", "expected": expected_traceability, "actual": actual_traceability},
            )
        return {**receipt, "receipt_path": str(receipt_path), "duplicate_submission": "IDEMPOTENT", "idempotent_replay": True}
    submission_digest = _digest(identity)
    receipt = {
        "schema_version": 1, "receipt_type": "submission", "submission_id": submission_id,
        "submission_digest": submission_digest, "operation": "BETA", "repository_identity": facts["repository"],
        "wop_id": facts["wop_id"], "mission_id": facts["mission_id"],
        "wop_output_digest": facts["output_digest"], "source_digest": facts["source_digest"],
        "immutable_provenance": {"traceability_digest": _digest(canonical_replay_content(facts["trace"])), "template_digest": facts["template_digest"], "context_digest": facts["context_digest"]},
        "authority": {
            "governance_authority": "operator-submitted WOP",
            "wop_authority": "operator-submitted WOP",
            "generic_second_approval_required": False,
            "approval_state": "NOT_REQUIRED_UNLESS_DECLARED_IN_WOP",
            "explicit_wop_approvals": (facts["trace"].get("approval_gates") or facts["trace"].get("approval") or []),
        },
        "submission_state": "ADMISSION_REQUESTED", "submission_result": "PASS",
        "duplicate_submission": "NEW", "admission_request_id": request_id,
        "next_action": "EVALUATE_MISSION_ADMISSION",
    }
    if submission_context:
        # Submission options are validation context, not a second authority
        # source. They deliberately do not participate in submission identity
        # so redundant repository-resolution inputs cannot fork a mission.
        receipt["submission_context"] = {
            "baseline": submission_context.get("baseline"),
            "impact": submission_context.get("impact"),
            "affected_repositories": submission_context.get("affected_repositories", []),
            "resources_available": bool(submission_context.get("resources_available", False)),
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
