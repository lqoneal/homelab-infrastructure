"""Read-only operator verification for the P2-G1 submission boundary."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _receipt(response: Mapping[str, Any]) -> tuple[dict[str, Any] | None, list[str]]:
    errors: list[str] = []
    raw_path = response.get("receipt_path")
    if not raw_path:
        return None, ["receipt_path is missing"]
    path = Path(str(raw_path)).resolve()
    if not path.is_file():
        return None, [f"receipt_path does not resolve to an existing receipt: {path}"]
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        return None, [f"receipt is unreadable: {error}"]
    if not isinstance(value, dict):
        return None, ["receipt is not a JSON object"]
    digest = response.get("receipt_digest")
    if not digest:
        errors.append("receipt_digest is missing")
    if value.get("receipt_digest") != digest:
        errors.append("returned receipt_digest does not match receipt contents")
    unsigned = {key: item for key, item in value.items() if key != "receipt_digest"}
    if value.get("receipt_digest") != _digest(unsigned):
        errors.append("receipt_digest fails canonical receipt verification")
    if value.get("receipt_type") != "submission":
        errors.append("receipt_type is not submission")
    if value.get("submission_id") != response.get("submission_id"):
        errors.append("receipt submission_id does not match returned submission_id")
    return value, errors


def verify_submission_pair(first: Mapping[str, Any], replay: Mapping[str, Any], *,
                           runtime_root: Path | str | None = None) -> dict[str, Any]:
    """Verify first submission and deterministic replay without mutation."""
    errors: list[str] = []
    required = {
        "submission_result": "PASS", "submission_state": "ADMISSION_REQUESTED",
    }
    for field, expected in required.items():
        if first.get(field) != expected:
            errors.append(f"first {field} is not {expected}")
    for field in ("submission_id", "receipt_digest", "admission_request_id", "mission_id", "wop_id"):
        if not first.get(field):
            errors.append(f"first {field} is missing")
    if first.get("operation") != "BETA":
        errors.append("first operation is not BETA")
    if not first.get("repository_identity"):
        errors.append("first repository_identity is missing")
    provenance = first.get("immutable_provenance")
    if not isinstance(provenance, Mapping) or not provenance.get("traceability_digest"):
        errors.append("immutable provenance is missing")

    receipt, receipt_errors = _receipt(first)
    errors.extend(f"first receipt: {item}" for item in receipt_errors)
    replay_fields = ("submission_id", "receipt_digest", "admission_request_id", "mission_id", "wop_id")
    if replay.get("duplicate_submission") != "IDEMPOTENT":
        errors.append("replay duplicate_submission is not IDEMPOTENT")
    for field in replay_fields:
        if replay.get(field) != first.get(field):
            errors.append(f"replay {field} differs from first submission")
    replay_receipt, replay_receipt_errors = _receipt(replay)
    errors.extend(f"replay receipt: {item}" for item in replay_receipt_errors)
    if receipt is not None and replay_receipt is not None and receipt != replay_receipt:
        errors.append("replay receipt contents differ from first receipt")

    if first.get("admission_id") or first.get("execution_id"):
        errors.append("downstream admission or execution identity was returned")
    if runtime_root is not None:
        root = Path(runtime_root).resolve()
        request = root / "requests" / f"{first.get('admission_request_id')}.json"
        if not request.is_file():
            errors.append("admission request projection is missing")
        else:
            try:
                request_value = json.loads(request.read_text(encoding="utf-8"))
            except (OSError, UnicodeError, json.JSONDecodeError) as error:
                errors.append(f"admission request projection is unreadable: {error}")
            else:
                if request_value.get("invocation_count") != 1:
                    errors.append("admission request invocation count is not one")
                if request_value.get("mission_admission_executed") is not False:
                    errors.append("Mission Admission execution is not explicitly false")
                for field in ("submission_id", "mission_id", "wop_id"):
                    if request_value.get(field) != first.get(field):
                        errors.append(f"admission request {field} differs from submission")
        for directory_name in ("mission-admissions", "mission-executions", "native-sessions"):
            directory = root / directory_name
            if directory.is_dir() and any(directory.glob("*.json")):
                errors.append(f"downstream artifacts exist in {directory_name}")

    return {
        "result": "PASS" if not errors else "FAIL",
        "checks": {
            "receipt_path": not any("receipt_path" in item for item in receipt_errors),
            "receipt_digest": bool(first.get("receipt_digest")),
            "receipt_type": receipt is not None and receipt.get("receipt_type") == "submission",
            "immutable_provenance": isinstance(provenance, Mapping) and bool(provenance.get("traceability_digest")),
            "replay": replay.get("duplicate_submission") == "IDEMPOTENT" and all(replay.get(field) == first.get(field) for field in replay_fields),
            "no_downstream_execution": not (first.get("admission_id") or first.get("execution_id")),
        },
        "errors": errors,
    }
