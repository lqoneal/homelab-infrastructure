"""Read-only verification for authored Development WOP artifacts.

This module deliberately verifies artifacts produced by the authoring service;
it does not author, submit, admit, or mutate WOP state.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Mapping


# These are the only fields whose values are expected to vary when an
# equivalent artifact is replayed in another filesystem location.
_LOCATION_FIELDS = frozenset({"path", "output", "traceability", "next_action"})

# Marker-shaped syntax only.  In particular, prose containing the word
# "placeholder" is not a marker and must not be rejected.
_TOKEN_PATTERNS = (
    re.compile(r"\{\{[^{}\r\n]+\}\}"),
    re.compile(r"<[A-Z][A-Z0-9 _.-]*(?:/[A-Z][A-Z0-9 _.-]*)?>"),
    re.compile(r"@@[A-Z][A-Z0-9_.-]*@@"),
)


def unresolved_tokens(text: str) -> list[str]:
    """Return unique unresolved template tokens in source order."""
    matches: list[tuple[int, str]] = []
    for pattern in _TOKEN_PATTERNS:
        matches.extend((match.start(), match.group(0)) for match in pattern.finditer(text))
    result: list[str] = []
    for _, token in sorted(matches):
        if token not in result:
            result.append(token)
    return result


def _canonical(value: Any, *, field: str | None = None) -> Any:
    if isinstance(value, Mapping):
        return {
            str(key): _canonical(item, field=str(key))
            for key, item in sorted(value.items(), key=lambda item: str(item[0]))
            if str(key) not in _LOCATION_FIELDS
            and not (field == "validation" and str(key) == "source")
        }
    if isinstance(value, list):
        return [_canonical(item, field=field) for item in value]
    if field in _LOCATION_FIELDS:
        return "<RUNTIME_PATH>"
    return value


def canonical_replay_content(value: Mapping[str, Any]) -> dict[str, Any]:
    """Return replay-comparable content with runtime locators removed."""
    return _canonical(value)


def compare_replay(first: Mapping[str, Any], second: Mapping[str, Any]) -> dict[str, Any]:
    """Compare equivalent replay content while preserving identity checks."""
    left = canonical_replay_content(first)
    right = canonical_replay_content(second)
    required = (
        "repository", "wop_id", "mission_id", "source", "template", "context",
        "output_digest", "readiness", "blockers",
    )
    preserved = {field: left.get(field) == right.get(field) for field in required}
    return {
        "result": "PASS" if left == right and all(preserved.values()) else "FAIL",
        "canonical_equal": left == right,
        "preserved_fields": preserved,
    }


def verify_artifact(path: Path) -> dict[str, Any]:
    """Verify output digest, traceability, readiness, and unresolved tokens."""
    output = path.read_text(encoding="utf-8")
    tokens = unresolved_tokens(output)
    trace_path = path.with_suffix(path.suffix + ".traceability.json")
    if not trace_path.is_file():
        return {"result": "FAIL", "path": str(path.resolve()), "errors": ["traceability record not found"]}
    try:
        trace = json.loads(trace_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        return {"result": "FAIL", "path": str(path.resolve()), "errors": [f"invalid traceability record: {error}"]}
    errors = []
    if trace.get("output_digest") != hashlib.sha256(output.encode()).hexdigest():
        errors.append("traceability output digest mismatch")
    if tokens:
        errors.append("unresolved template tokens: " + ", ".join(tokens))
    if trace.get("readiness") != "ADMISSION_READY":
        errors.append("readiness is not ADMISSION_READY")
    return {
        "result": "PASS" if not errors else "FAIL",
        "path": str(path.resolve()),
        "traceability": trace,
        "tokens": tokens,
        "errors": errors,
    }


def verify_replay(first: Path, second: Path) -> dict[str, Any]:
    """Verify two authored artifacts, ignoring only runtime filesystem paths."""
    first_result = verify_artifact(first)
    second_result = verify_artifact(second)
    if first_result["result"] != "PASS" or second_result["result"] != "PASS":
        return {"result": "FAIL", "first": first_result, "second": second_result, "replay": "FAIL"}
    comparison = compare_replay(first_result["traceability"], second_result["traceability"])
    return {
        "result": comparison["result"], "replay": comparison["result"],
        "first": first_result, "second": second_result, "comparison": comparison,
    }
