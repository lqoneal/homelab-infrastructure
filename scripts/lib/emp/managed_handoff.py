"""Fail-closed managed Codex handoff resolution.

The handoff is an intent and scope document.  This module only projects
authoritative Zeus state into a delivery plan; it never creates mission,
authority, admission, execution, or session state.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Mapping

import yaml

from scripts.lib.emp import codex_adapter
from scripts.lib.emp.repository_identity import RepositoryIdentityError, resolve as resolve_repository, resolve_declared
from scripts.lib.emp.runtime_paths import resolve_runtime
from scripts.lib.wop.canonical_package import canonical_identity_records


BLOCKERS = {
    "HANDOFF_RESOLUTION_AMBIGUOUS",
    "HANDOFF_BINDING_CONTRADICTION",
    "HANDOFF_AUTHORITY_UNRESOLVED",
    "HANDOFF_EXECUTION_UNAVAILABLE",
}

HANDOFF_CONTRACT_TYPE = "ZEUS_CODEX_HANDOFF"
HANDOFF_SCHEMA_VERSION = 1
HANDOFF_SCHEMA = "engineering/oversight/codex-handoff-contract.schema.yaml"
GATE_CROSSWALK = "engineering/evidence/operation-beta/OPERATION-BETA-CANONICAL-GATE-CATALOG.yaml"

_LABELS = {
    "mission_id": ("mission_id", "mission"),
    "wop_id": ("wop_id", "wop", "work_order", "work-order"),
    "gate_id": ("gate_id", "gate", "gate_id_or_work_unit_id"),
    "execution_id": ("execution_id", "execution"),
    "session_id": ("session_id", "session", "codex_session_id"),
    "provider_id": ("provider_id", "provider"),
    "operation_id": ("operation_id", "operation"),
    "repository": ("repository", "repository_id", "repository_path", "repository_identity"),
    "baseline": ("baseline", "baseline_commit", "published_baseline"),
}


class ManagedHandoffError(ValueError):
    """A malformed handoff source, not an authority decision."""

    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(message)


def _clean(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, (list, tuple, set)):
        return None
    text = str(value).strip().strip("`\"'")
    return text or None


def _flatten_metadata(value: Any, prefix: str = "") -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    if not isinstance(value, Mapping):
        return result
    for key, item in value.items():
        name = str(key).lower().replace("-", "_")
        full = f"{prefix}.{name}" if prefix else name
        if isinstance(item, Mapping):
            for child, values in _flatten_metadata(item, full).items():
                result.setdefault(child, []).extend(values)
        elif isinstance(item, list):
            for member in item:
                cleaned = _clean(member)
                if cleaned:
                    result.setdefault(full, []).append(cleaned)
        else:
            cleaned = _clean(item)
            if cleaned:
                result.setdefault(full, []).append(cleaned)
    return result


def _frontmatter(text: str) -> Mapping[str, Any]:
    if not text.startswith("---"):
        return {}
    parts = text.split("---", 2)
    if len(parts) != 3:
        return {}
    try:
        value = yaml.safe_load(parts[1])
    except yaml.YAMLError:
        return {}
    return value if isinstance(value, Mapping) else {}


def _structured_contract(text: str) -> dict[str, Any] | None:
    """Validate the canonical structured handoff shape when one is supplied."""
    try:
        value = yaml.safe_load(text)
    except yaml.YAMLError as error:
        raise ManagedHandoffError("HANDOFF_CONTRACT_SYNTAX_INVALID", str(error)) from error
    if not isinstance(value, Mapping) or value.get("contract_type") != HANDOFF_CONTRACT_TYPE:
        return None
    required = {
        "schema_version", "contract_type", "request_id", "request_type",
        "instruction_contract", "mission_id", "wop_id", "gate_id", "operation",
        "mode", "mutation_policy", "objective", "authoritative_inputs",
        "preconditions", "allowed_actions", "prohibited_actions", "required_checks",
        "acceptance_criteria", "evidence_requirements", "stop_boundary",
        "next_action_policy",
    }
    optional = {"provider_metadata", "natural_language_context"}
    missing = sorted(required - set(value))
    unknown = sorted(set(value) - required - optional)
    if missing or unknown:
        raise ManagedHandoffError(
            "HANDOFF_CONTRACT_SCHEMA_INVALID",
            f"missing={missing}; unsupported={unknown}",
        )
    if value.get("schema_version") != HANDOFF_SCHEMA_VERSION:
        raise ManagedHandoffError("HANDOFF_CONTRACT_SCHEMA_INVALID", "unsupported schema_version")
    if value.get("operation") != "OPERATION-BETA":
        raise ManagedHandoffError("HANDOFF_CONTRACT_SCHEMA_INVALID", "operation must be OPERATION-BETA")
    if value.get("request_type") not in {
        "ENGINEERING_HANDOFF", "GATE_CORRECTIVE", "GATE_SPECIFICATION",
        "READ_ONLY_AUDIT", "QUALIFICATION",
    }:
        raise ManagedHandoffError("HANDOFF_CONTRACT_SCHEMA_INVALID", "unsupported request_type")
    if value.get("mode") not in {"READ_ONLY", "DEVELOPMENT", "QUALIFICATION"}:
        raise ManagedHandoffError("HANDOFF_CONTRACT_SCHEMA_INVALID", "unsupported mode")
    if value.get("mutation_policy") not in {
        "READ_ONLY", "WORKSPACE_BOUNDED", "CONTROLLED_RUNTIME_TRANSITION",
    }:
        raise ManagedHandoffError("HANDOFF_CONTRACT_SCHEMA_INVALID", "unsupported mutation_policy")
    for field in ("preconditions", "allowed_actions", "prohibited_actions", "required_checks",
                  "acceptance_criteria", "evidence_requirements"):
        items = value.get(field)
        if not isinstance(items, list) or not items or any(not isinstance(item, str) or not item.strip() for item in items):
            raise ManagedHandoffError("HANDOFF_CONTRACT_SCHEMA_INVALID", f"{field} must be a non-empty string list")
    inputs = value.get("authoritative_inputs")
    if not isinstance(inputs, list) or not inputs or any(
        not isinstance(item, Mapping) or not item.get("locator") or not item.get("role")
        or set(item) - {"locator", "role", "required"} for item in inputs
    ):
        raise ManagedHandoffError("HANDOFF_CONTRACT_SCHEMA_INVALID", "authoritative_inputs are invalid")
    policy = value.get("next_action_policy")
    if not isinstance(policy, Mapping) or set(policy) != {"on_success", "on_blocked"} or not all(policy.values()):
        raise ManagedHandoffError("HANDOFF_CONTRACT_SCHEMA_INVALID", "next_action_policy is invalid")
    for field in ("request_id", "instruction_contract", "mission_id", "wop_id", "gate_id",
                  "objective", "stop_boundary"):
        if not isinstance(value.get(field), str) or not value[field].strip():
            raise ManagedHandoffError("HANDOFF_CONTRACT_SCHEMA_INVALID", f"{field} must be non-empty")
    return dict(value)


def extract_semantic_references(text: str) -> dict[str, list[str]]:
    """Extract assertions without treating prose as authority."""
    metadata = _flatten_metadata(_frontmatter(text))
    result = {key: [] for key in _LABELS}
    for field, labels in _LABELS.items():
        label_pattern = "|".join(re.escape(label) for label in labels)
        pattern = re.compile(
            rf"(?im)^\s*(?:[-*]\s*)?(?:{label_pattern})\s*[:=]\s*([^\n#]+)"
        )
        values = list(metadata.get(field, []))
        for label in labels:
            values.extend(metadata.get(label, []))
        values.extend(match.group(1).strip() for match in pattern.finditer(text))
        for value in values:
            cleaned = _clean(value)
            if cleaned and cleaned not in result[field]:
                result[field].append(cleaned)
    return result


def _load_json(path: Path) -> dict[str, Any] | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return value if isinstance(value, dict) else None


def _load_yaml(path: Path) -> dict[str, Any] | None:
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError):
        return None
    return value if isinstance(value, dict) else None


def _records(runtime: Path, root: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    runtime_dirs = (
        "execution-start-transactions", "execution-sessions", "admissions",
        "stage1", "codex-sessions", "execution-active-transitions",
    )
    for directory in runtime_dirs:
        location = runtime / directory
        if location.is_dir():
            for path in sorted(location.glob("*.json")):
                value = _load_json(path)
                if value:
                    records.append({"source": str(path), "authority_class": "RUNTIME", **value})
    canonical = canonical_identity_records(root)
    current_canonical = {str(item["wop_id"]).upper(): item for item in canonical["records"]}
    for item in canonical["records"]:
        records.append({"authority_class": "CANONICAL_PACKAGE", **item})
    work_orders = root / "engineering" / "work-orders"
    if work_orders.is_dir():
        names = {"mission.yaml", "immutable-wop.yaml", "source-wop.yaml", "submission.yaml", "WOP.yaml", "canonical-wop-package.yaml"}
        for path in sorted(work_orders.rglob("*")):
            if path.is_file() and path.name in names:
                value = _load_yaml(path)
                if value:
                    package_identity = value.get("package_identity") if isinstance(value.get("package_identity"), Mapping) else {}
                    package_wop = str(package_identity.get("wop_id") or value.get("wop_id") or "").upper()
                    # The canonical package is the identity owner.  Its
                    # digest-addressed Stage-1 adapter is provenance, not a
                    # second mission/WOP/gate registration.
                    if path.name == "canonical-wop-package.yaml":
                        continue
                    if package_wop in current_canonical:
                        continue
                    records.append({"source": str(path), "authority_class": "REPOSITORY_ARTIFACT", **value})
    crosswalk = _load_yaml(root / GATE_CROSSWALK)
    for row in (crosswalk or {}).get("wop_gate_crosswalk", []):
        if isinstance(row, Mapping):
            records.append({
                "source": str(root / GATE_CROSSWALK),
                "authority_class": "CONTROLLED_CROSSWALK",
                "mission_id": row.get("mission_id"), "wop_id": row.get("wop_id"),
                "gate_id": row.get("wop_gate_id"),
                "operation_id": "OPERATION-BETA",
                "authority_effect": "NONE",
            })
    return records


def _distinct(records: list[dict[str, Any]], field: str) -> list[str]:
    return sorted({str(record[field]).upper() for record in records if record.get(field)})


def _matching(records: list[dict[str, Any]], field: str, value: str | None) -> list[dict[str, Any]]:
    if not value:
        return records
    wanted = value.upper()
    return [record for record in records if str(record.get(field, "")).upper() == wanted]


def _blocked(code: str, message: str, *, candidates: list[str] | None = None,
             hints: Mapping[str, list[str]] | None = None) -> dict[str, Any]:
    return {
        "result": "BLOCKED", "blocker": code,
        "blockers": [{"code": code, "message": message}],
        "candidates": candidates or [], "semantic_references": dict(hints or {}),
        "handoff_authority_source": "NO", "read_only": True,
        "mutation_applied": False, "next_authorized_action": "OPERATOR_REVIEW_HANDOFF_RESOLUTION",
    }


def _one_or_block(field: str, hints: dict[str, list[str]], records: list[dict[str, Any]]) -> tuple[str | None, dict[str, Any] | None]:
    values = hints.get(field, [])
    if len(values) > 1:
        return None, _blocked("HANDOFF_RESOLUTION_AMBIGUOUS", f"handoff contains multiple {field} assertions", candidates=values, hints=hints)
    if values:
        value = values[0].upper()
        matching = _matching(records, field, value)
        if not matching:
            return None, _blocked("HANDOFF_BINDING_CONTRADICTION", f"handoff {field} does not resolve in authoritative state", candidates=[value], hints=hints)
        return value, None
    return None, None


def _resolve_session(runtime: Path, execution: Mapping[str, Any], mission_id: str) -> dict[str, Any]:
    sessions = codex_adapter._all_sessions(runtime)
    historical = [session for session in sessions if session.get("mission_id") == "MISSION-BETA-562F443E16C69401"]
    incompatible = [session for session in sessions
                    if session.get("mission_id") == mission_id and any(
                        session.get(field) != execution.get(field)
                        for field in ("execution_id", "execution_session_id", "provider_session_id", "provider_id")
                    )]
    compatible = [session for session in sessions if all(
        session.get(field) == execution.get(field)
        for field in ("mission_id", "execution_id", "execution_session_id", "provider_session_id", "provider_id")
    )]
    if len(compatible) > 1:
        current = [item for item in compatible if item.get("session_disposition") != "SUPERSEDED" and item.get("state") != "SUPERSEDED"]
        if len(current) != 1:
            return {"action": "BLOCK", "blocker": "HANDOFF_RESOLUTION_AMBIGUOUS", "candidates": [item.get("session_id") for item in compatible]}
        compatible = current
    historical_reused = any(item in compatible for item in historical)
    base = {
        "historical_session_preserved": bool(historical),
        "historical_session_reused": historical_reused,
        "historical_session_reused_for_new_handoff": historical_reused,
    }
    if historical and not historical_reused:
        base["historical_session_preserved"] = True
    if not compatible:
        base.update({"action": "CREATE", "session": None,
                     "session_reuse": "DO_NOT_REUSE" if historical or incompatible else "CREATE"})
        return base
    session = compatible[0]
    live = codex_adapter.runtime_liveness(session).get("session_live")
    base.update({"action": "REUSE" if live else "RESUME", "session": session,
                 "session_reuse": "REUSE" if live else "RESUME"})
    return base


def _resolve_authority(root: Path) -> dict[str, Any]:
    """Read repository authority without adopting an isolated test runtime.

    A handoff resolver may inspect an explicitly supplied isolated runtime.
    That runtime is a fixture for resolution records, not an alternate
    repository authority.  Keep the authority lookup on the repository's
    configured published chain while preserving the caller's environment.
    """
    runtime_override = os.environ.pop("ZEUS_RUNTIME_ROOT", None)
    try:
        return codex_adapter._authority(root)
    finally:
        if runtime_override is not None:
            os.environ["ZEUS_RUNTIME_ROOT"] = runtime_override


def resolve_handoff(repository: Path | str, text: str, *, runtime_root: Path | str | None = None,
                    source: str = "-") -> dict[str, Any]:
    """Resolve a handoff against repository and runtime state, read-only."""
    root = Path(repository).resolve()
    try:
        structured = _structured_contract(text)
    except ManagedHandoffError as error:
        return _blocked(error.code, error.message)
    hints = extract_semantic_references(text)
    try:
        identity = resolve_repository(root)
    except Exception as error:
        return _blocked("HANDOFF_AUTHORITY_UNRESOLVED", f"repository identity cannot be resolved: {error}", hints=hints)
    for assertion in hints["repository"]:
        try:
            resolve_declared(assertion, root)
        except RepositoryIdentityError:
            return _blocked("HANDOFF_BINDING_CONTRADICTION", "handoff repository assertion differs from the registered repository", candidates=[assertion], hints=hints)

    runtime = Path(runtime_root).resolve() if runtime_root else Path(resolve_runtime(root, require_writable=False)["root"]).resolve()
    records = _records(runtime, root)
    operation_values = hints["operation_id"]
    if len(operation_values) > 1:
        return _blocked("HANDOFF_RESOLUTION_AMBIGUOUS", "handoff contains multiple operation assertions", candidates=operation_values, hints=hints)
    operation_id = (operation_values[0] if operation_values else "OPERATION-BETA").upper()
    if operation_id not in {"BETA", "OPERATION-BETA"}:
        return _blocked("HANDOFF_BINDING_CONTRADICTION", "handoff operation is not the registered Operation Beta context", candidates=[operation_id], hints=hints)
    operation_id = "OPERATION-BETA"

    mission_id, blocked = _one_or_block("mission_id", hints, records)
    if blocked:
        return blocked
    wop_id, blocked = _one_or_block("wop_id", hints, records)
    if blocked:
        return blocked
    if mission_id:
        mission_records = _matching(records, "mission_id", mission_id)
    elif wop_id:
        mission_records = _matching(records, "wop_id", wop_id)
    else:
        execution_records = [record for record in records if record.get("execution_id") and record.get("execution_start_state")]
        mission_candidates = _distinct(execution_records, "mission_id")
        if len(mission_candidates) != 1:
            return _blocked("HANDOFF_RESOLUTION_AMBIGUOUS" if mission_candidates else "HANDOFF_AUTHORITY_UNRESOLVED",
                            "mission cannot be uniquely derived from authoritative execution state",
                            candidates=mission_candidates, hints=hints)
        mission_id = mission_candidates[0]
        mission_records = _matching(records, "mission_id", mission_id)
    if not mission_id:
        mission_candidates = _distinct(mission_records, "mission_id")
        if len(mission_candidates) != 1:
            return _blocked("HANDOFF_RESOLUTION_AMBIGUOUS" if mission_candidates else "HANDOFF_AUTHORITY_UNRESOLVED",
                            "mission cannot be uniquely resolved", candidates=mission_candidates, hints=hints)
        mission_id = mission_candidates[0]
    if not wop_id:
        wop_candidates = _distinct(_matching(mission_records, "mission_id", mission_id), "wop_id")
        if len(wop_candidates) != 1:
            return _blocked("HANDOFF_RESOLUTION_AMBIGUOUS" if wop_candidates else "HANDOFF_AUTHORITY_UNRESOLVED",
                            "WOP cannot be uniquely resolved", candidates=wop_candidates, hints=hints)
        wop_id = wop_candidates[0]

    gate_id, blocked = _one_or_block("gate_id", hints, records)
    if blocked:
        return blocked
    bound_records = [record for record in records if str(record.get("mission_id", "")).upper() == mission_id and str(record.get("wop_id", "")).upper() == wop_id]
    if gate_id:
        if not any(str(record.get("gate_id", record.get("canonical_gate_id", ""))).upper() == gate_id for record in bound_records):
            return _blocked("HANDOFF_BINDING_CONTRADICTION", "handoff gate assertion differs from the mission/WOP binding", candidates=[gate_id], hints=hints)
    else:
        gate_candidates = sorted({str(record.get("gate_id") or record.get("canonical_gate_id")).upper() for record in bound_records if record.get("gate_id") or record.get("canonical_gate_id")})
        gate_id = gate_candidates[0] if len(gate_candidates) == 1 else None
        if len(gate_candidates) > 1:
            return _blocked("HANDOFF_RESOLUTION_AMBIGUOUS", "gate cannot be uniquely resolved", candidates=gate_candidates, hints=hints)

    execution_candidates = [record for record in bound_records if record.get("execution_id") and record.get("execution_start_state")]
    execution_values = hints["execution_id"]
    if len(execution_values) > 1:
        return _blocked("HANDOFF_RESOLUTION_AMBIGUOUS", "handoff contains multiple execution assertions", candidates=execution_values, hints=hints)
    if execution_values:
        execution_candidates = _matching(execution_candidates, "execution_id", execution_values[0])
        if not execution_candidates:
            return _blocked("HANDOFF_BINDING_CONTRADICTION", "handoff execution assertion is not bound to the mission/WOP", candidates=execution_values, hints=hints)
    if len(execution_candidates) != 1:
        blocker = "HANDOFF_EXECUTION_UNAVAILABLE" if not execution_candidates else "HANDOFF_RESOLUTION_AMBIGUOUS"
        message = (
            "WOP identity binding is resolved, but no submitted/admitted execution exists"
            if not execution_candidates else "execution is not uniquely available for handoff delivery"
        )
        result = _blocked(
            blocker, message,
            candidates=[str(record.get("execution_id")) for record in execution_candidates], hints=hints,
        )
        identity_record = bound_records[0] if len(bound_records) == 1 else {}
        next_action = identity_record.get("next_authorized_action") or "SUBMIT_EXISTING_WOP_THROUGH_ZEUS"
        result.update({
            "operation_id": operation_id,
            "mission_id": mission_id,
            "wop_id": wop_id,
            "gate_id": gate_id,
            "binding": {"mission": "PASS", "wop": "PASS", "gate": "PASS"},
            "wop_published": identity_record.get("wop_published", "NO"),
            "wop_submitted": identity_record.get("wop_submitted", "NO"),
            "separate_wop_authorization_required": identity_record.get("separate_wop_authorization_required", "NO"),
            "canonical_revision": identity_record.get("canonical_revision", identity_record.get("revision")),
            "canonical_revision_state": identity_record.get("revision_state", "CURRENT"),
            "historical_revision_1_preserved": identity_record.get("historical_revision_1_preserved", "NO"),
            "lifecycle": {"submission": "NOT_SUBMITTED", "admission": "NOT_ADMITTED", "execution": "NOT_EXECUTING"},
            "next_authorized_action": next_action,
        })
        return result
    execution = execution_candidates[0]
    provider_values = hints["provider_id"]
    if len(provider_values) > 1:
        return _blocked("HANDOFF_RESOLUTION_AMBIGUOUS", "handoff contains multiple provider assertions", candidates=provider_values, hints=hints)
    if provider_values and str(execution.get("provider_id", "")).upper() != provider_values[0].upper():
        return _blocked("HANDOFF_BINDING_CONTRADICTION", "handoff provider assertion differs from execution binding", candidates=provider_values, hints=hints)
    baseline = hints["baseline"][0] if len(hints["baseline"]) == 1 else None
    if len(hints["baseline"]) > 1:
        return _blocked("HANDOFF_RESOLUTION_AMBIGUOUS", "handoff contains multiple baseline assertions", candidates=hints["baseline"], hints=hints)
    authoritative_baseline = execution.get("current_published_baseline") or execution.get("execution_start_provenance_baseline")
    if baseline and authoritative_baseline and baseline != authoritative_baseline and baseline != str(execution.get("execution_start_provenance_baseline")):
        return _blocked("HANDOFF_BINDING_CONTRADICTION", "handoff baseline differs from authoritative execution state", candidates=[baseline, str(authoritative_baseline)], hints=hints)
    if not authoritative_baseline:
        authoritative_baseline = str(__import__("subprocess").run(["git", "-C", str(root), "rev-parse", "HEAD"], capture_output=True, text=True, check=False).stdout.strip())

    admission = execution.get("admission_id") or execution.get("admission")
    if not admission:
        admission_candidates = [record.get("admission_id") for record in records if record.get("mission_id") == mission_id and record.get("admission_id")]
        admission = admission_candidates[0] if len(set(admission_candidates)) == 1 else None
    if not admission:
        return _blocked("HANDOFF_EXECUTION_UNAVAILABLE", "admission binding is not available", hints=hints)
    try:
        authority = _resolve_authority(root)
    except Exception as error:
        return _blocked("HANDOFF_AUTHORITY_UNRESOLVED", f"authoritative Operation Beta authority cannot be resolved: {error}", hints=hints)
    session = _resolve_session(runtime, execution, mission_id)
    if session.get("action") == "BLOCK":
        return _blocked(session["blocker"], "multiple compatible managed sessions remain", candidates=session.get("candidates", []), hints=hints)
    session_values = hints["session_id"]
    if len(session_values) > 1:
        return _blocked("HANDOFF_RESOLUTION_AMBIGUOUS", "handoff contains multiple session assertions", candidates=session_values, hints=hints)
    if session_values:
        asserted_session = session_values[0].upper()
        asserted_records = [item for item in codex_adapter._all_sessions(runtime)
                            if str(item.get("session_id", "")).upper() == asserted_session]
        if len(asserted_records) != 1:
            return _blocked("HANDOFF_BINDING_CONTRADICTION", "handoff session assertion is not an authoritative managed session", candidates=[asserted_session], hints=hints)
        session_record = session.get("session") or {}
        if str(session_record.get("session_id", "")).upper() != asserted_session:
            return _blocked("HANDOFF_BINDING_CONTRADICTION", "handoff session assertion is incompatible with the resolved execution", candidates=[asserted_session], hints=hints)
    return {
        "result": "PASS", "handoff_resolution": "PASS", "source": source,
        "handoff_contract": ({"schema": HANDOFF_SCHEMA, "validation": "PASS",
                              "request_id": structured.get("request_id"),
                              "request_type": structured.get("request_type"),
                              "instruction_contract": structured.get("instruction_contract"),
                              "mutation_policy": structured.get("mutation_policy"),
                              "stop_boundary": structured.get("stop_boundary"),
                              "execution_authority": "NONE"} if structured else None),
        "semantic_references": hints, "repository": identity,
        "operation_id": operation_id, "mission_id": mission_id, "wop_id": wop_id,
        "gate_id": gate_id, "baseline": baseline or authoritative_baseline,
        "authority": authority, "admission_id": admission,
        "execution": {"execution_id": execution.get("execution_id"), "record": execution,
                       "execution_authority": "PRESERVED", "execution_available": True},
        "managed_session": session,
        "handoff_authority_source": "NO",
        "handoff_invocation_requires_redundant_approval": "NO",
        "downstream_protected_approvals_preserved": "YES",
        "delivery": {"result": "READY", "mutation_applied": False,
                      "provider_contacted": False, "execution_started": False,
                      "next_authorized_action": "DELIVER_TO_RESOLVED_MANAGED_SESSION"},
        "read_only": True, "mutation_applied": False,
        "next_authorized_action": "DELIVER_TO_RESOLVED_MANAGED_SESSION",
    }


def resolve_source(repository: Path | str, source: str, *, runtime_root: Path | str | None = None,
                   stdin: Any = None) -> dict[str, Any]:
    if source == "-":
        text = (stdin or sys.stdin).read()
    else:
        path = Path(source)
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as error:
            return _blocked("HANDOFF_BINDING_CONTRADICTION", f"handoff source cannot be read: {error}")
    if not text.strip():
        return _blocked("HANDOFF_BINDING_CONTRADICTION", "handoff source is empty")
    return resolve_handoff(repository, text, runtime_root=runtime_root, source=source)


def render(value: Mapping[str, Any]) -> str:
    blockers = value.get("blockers") or []
    session = value.get("managed_session") or {}
    return "\n".join((
        "Zeus Managed Codex Handoff",
        "--------------------------",
        f"Result                    : {value.get('result')}",
        f"Handoff resolution        : {value.get('handoff_resolution', 'BLOCKED')}",
        f"Mission / WOP / Gate      : {value.get('mission_id', 'NONE')} / {value.get('wop_id', 'NONE')} / {value.get('gate_id', 'NONE')}",
        f"Execution                 : {(value.get('execution') or {}).get('execution_id', 'NONE')}",
        f"Session action            : {session.get('action', 'NONE')}",
        f"Historical session reused : {session.get('historical_session_reused_for_new_handoff', 'NO')}",
        f"Blockers                  : {'NONE' if not blockers else ', '.join(item.get('code', 'UNKNOWN') for item in blockers)}",
        f"Next action               : {value.get('next_authorized_action')}",
        "Read-only                 : YES",
    ))
