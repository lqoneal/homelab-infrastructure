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


BLOCKERS = {
    "HANDOFF_RESOLUTION_AMBIGUOUS",
    "HANDOFF_BINDING_CONTRADICTION",
    "HANDOFF_AUTHORITY_UNRESOLVED",
    "HANDOFF_EXECUTION_UNAVAILABLE",
    "HANDOFF_TRANSACTION_AUTHORITY_MISSING",
    "HANDOFF_TRANSACTION_UNKNOWN",
    "HANDOFF_TRANSACTION_SCOPE_MISSING",
}

_LABELS = {
    "mission_id": ("mission_id", "mission"),
    "wop_id": ("wop_id", "wop", "work_order", "work-order"),
    "gate_id": ("gate_id", "gate", "gate_id_or_work_unit_id"),
    "execution_id": ("execution_id", "execution"),
    "session_id": ("session_id", "session", "codex_session_id"),
    "provider_id": ("provider_id", "provider"),
    "operation_id": ("operation_id", "operation"),
    "emm_id": ("emm_id", "emm", "execution_management_model"),
    "transaction_id": ("transaction_id", "transaction", "transaction_identity"),
    "transaction_type": ("transaction_type", "transaction_class", "transaction_kind"),
    "repository": ("repository", "repository_id", "repository_path", "repository_identity"),
    "baseline": ("baseline", "baseline_commit", "published_baseline"),
}


class ManagedHandoffError(ValueError):
    """A malformed handoff source, not an authority decision."""

    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(message)


def build_administrative_execution_contract(
    resolved: Mapping[str, Any], *, supplemental_prompt: str | None = None,
) -> dict[str, Any]:
    """Build the provider contract from the resolved transaction authority."""
    if (resolved.get("result") != "PASS" or
            resolved.get("handoff_input_classification") != "AUTHORIZED_ADMINISTRATIVE_TRANSACTION"):
        raise ManagedHandoffError("HANDOFF_NOT_EXECUTABLE", "transaction authority is not executable")
    required = ("transaction_id", "transaction_type", "objective", "authorized_scope",
                "prohibited_scope", "acceptance_criteria", "qualification_authority")
    missing = [field for field in required if not resolved.get(field)]
    if missing:
        raise ManagedHandoffError(
            "HANDOFF_EXECUTION_CONTRACT_INCOMPLETE",
            "authoritative transaction execution semantics are incomplete: " + ", ".join(missing),
        )
    if str(resolved.get("qualification_authority", "")).upper() != "ZEUS":
        raise ManagedHandoffError("HANDOFF_QUALIFICATION_AUTHORITY_UNRESOLVED", "qualification authority is not ZEUS")
    criteria = list(resolved["acceptance_criteria"])
    prohibited = list(resolved["prohibited_scope"])
    required_evidence = list(resolved.get("required_evidence") or
                             criteria + ["provider terminal record", "actor-aware mutation attribution"])
    verification = [
        "TRANSACTION_ID_MATCH",
        "OBJECTIVE_EXECUTED",
        "ACCEPTANCE_CRITERIA_EVALUATED",
        "REQUIRED_EVIDENCE_RETAINED",
        "PROVIDER_SCOPE_COMPLIANCE",
        "PROTECTED_ACTIONS_ABSENT",
    ]
    stop_conditions = [
        "STOP_ON_MISSING_TRANSACTION_SEMANTICS",
        "STOP_ON_ACCEPTANCE_CRITERIA_FAILURE",
        "STOP_ON_PROVIDER_SCOPE_FAILURE",
        "STOP_BEFORE_PROTECTED_OPERATIONS",
    ]
    contract = {
        "transaction_id": resolved["transaction_id"],
        "transaction_type": resolved["transaction_type"],
        "objective": resolved["objective"],
        "authorized_scope": list(resolved["authorized_scope"]),
        "prohibited_scope": prohibited,
        "lifecycle_boundary": {
            "current_gate": resolved.get("current_gate", "C03"),
            "last_completed_gate": resolved.get("last_completed_gate", "C02"),
            "c03_executed": "NO",
            "protected_lifecycle_actions": prohibited,
        },
        "protected_operations": ["GIT", "PUBLICATION", "EOS", "ROADMAP_ADVANCEMENT"],
        "acceptance_criteria": criteria,
        "required_verification": verification,
        "required_evidence": required_evidence,
        "stop_conditions": stop_conditions,
        "qualification_authority": "ZEUS",
        "provider_self_qualification": "PROHIBITED",
        "operator_prompt": supplemental_prompt,
    }
    contract["provider_prompt"] = (
        "Execute the following authoritative administrative transaction exactly.\n\n"
        + yaml.safe_dump(contract, sort_keys=False)
        + ("\nSupplemental operator instruction ( subordinate to the contract ):\n" + supplemental_prompt
           if supplemental_prompt else "")
    )
    return contract


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
    # Transaction identity is an identity assertion, not authority.  Accept a
    # bare T-AUTH/transaction token so the resolver can report missing or
    # contradictory authority precisely instead of treating it as prose.
    for value in re.findall(r"\bT-AUTH-[0-9A-Z-]+\b", text, re.IGNORECASE):
        cleaned = value.upper()
        if cleaned not in result["transaction_id"]:
            result["transaction_id"].append(cleaned)
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
    work_orders = root / "engineering" / "work-orders"
    if work_orders.is_dir():
        names = {"mission.yaml", "immutable-wop.yaml", "source-wop.yaml", "submission.yaml", "WOP.yaml", "canonical-wop-package.yaml"}
        for path in sorted(work_orders.rglob("*")):
            if path.is_file() and path.name in names:
                value = _load_yaml(path)
                if value:
                    records.append({"source": str(path), "authority_class": "REPOSITORY_ARTIFACT", **value})
    return records


def _transaction_records(root: Path) -> list[dict[str, Any]]:
    """Load explicit administrative authority records only.

    This is deliberately a repository source, never handoff prose or runtime
    state.  The directory is initially empty on installations without a
    persisted administrative transaction, which is a meaningful fail-closed
    result rather than permission to synthesize authority.
    """
    records: list[dict[str, Any]] = []
    for relative in ("engineering/authority/transactions",
                     "engineering/authority/records",
                     "engineering/execution/transactions"):
        directory = root / relative
        if not directory.is_dir():
            continue
        for path in sorted(directory.glob("*")):
            if path.suffix.lower() not in {".yaml", ".yml", ".json"}:
                continue
            value = _load_json(path) if path.suffix.lower() == ".json" else _load_yaml(path)
            if isinstance(value, dict) and value.get("transaction_id"):
                records.append({"source": str(path), "authority_class": "TRANSACTION_AUTHORITY", **value})
    return records


_CANONICAL_ADMINISTRATIVE_AUTHORITY = {
    "authority_source_class": "CANONICAL_OPERATOR_AUTHORIZATION",
    "authority_model": "MODEL_B",
    "write_authority": "BOUNDED",
    "provider_mode": "ZEUS_MANAGED_NON_INTERACTIVE",
    "protected_git_authority": "ZEUS_ONLY",
    "qualification_authority": "ZEUS",
    "publication_authority": "ZEUS_ONLY",
    "eos_authority": "ZEUS_ONLY",
}

_T_AUTH_05_SUPPLEMENTAL_FIELDS = {
    "authorization_boundary": "OPERATION_BETA_GOVERNANCE_AUTHORITY_RECONCILIATION_ONLY",
    "t_auth_05_objective": "DEFINED",
    "t_auth_05_acceptance_criteria": "DEFINED",
    "t_auth_05_required_scope": "DEFINED",
    "t_auth_05_prohibited_scope": "DEFINED",
}

_T_AUTH_05_SUPPLEMENTAL_CRITERIA = {
    "T_AUTH_05_CANONICAL_AUTHORITY=PRESENT",
    "T_AUTH_05_OBJECTIVE=DEFINED",
    "T_AUTH_05_ACCEPTANCE_CRITERIA=DEFINED",
    "T_AUTH_05_REQUIRED_SCOPE=DEFINED",
    "T_AUTH_05_AUTHORITY_SOURCE=CANONICAL",
    "CURRENT_OPERATION=OPERATION-BETA",
    "CURRENT_EMM=OPERATION-BETA-EMM",
    "AUTHORITY_MODEL=MODEL_B",
    "HISTORICAL_OPERATIONAL_ALPHA_AUTHORITY=NOT_USED_AS_CURRENT_AUTHORITY",
    "TEMPORARY_CR48_CR55_EXECUTION_MECHANICS=NOT_REQUIRED_AS_AUTHORITY",
    "HANDOFF_PROSE=NOT_AUTHORITY",
    "IMPLICIT_OPERATOR_AUTHORITY=NOT_USED",
    "HANDOFF_TRANSACTION_AUTHORITY_MISSING=NO",
    "T_AUTH_05_EXECUTED=NO",
    "T_AUTH_06_EXECUTED=NO",
    "C02_EXECUTED=NO",
    "CR48_CR55_RETIRED=NO",
}


def _validate_canonical_administrative_authority(
        record: Mapping[str, Any], transaction_id: str, hints: dict[str, list[str]]) -> dict[str, Any] | None:
    """Validate common canonical authority, then transaction supplements."""
    state = str(record.get("state", "")).upper()
    if state not in {"CURRENT", "AUTHORIZED", "AUTHORIZED_FOR_IMPLEMENTATION", "ACTIVE"}:
        return _blocked("HANDOFF_BINDING_CONTRADICTION",
                        "canonical transaction authority has invalid state",
                        candidates=[state], hints=hints)
    for field, wanted in _CANONICAL_ADMINISTRATIVE_AUTHORITY.items():
        if str(record.get(field, "")).upper() != wanted:
            return _blocked("HANDOFF_BINDING_CONTRADICTION",
                            f"canonical transaction authority has invalid {field}",
                            candidates=[str(record.get(field, ""))], hints=hints)
    criteria = record.get("acceptance_criteria")
    if not isinstance(criteria, list) or not any(isinstance(item, str) and item.strip() for item in criteria):
        return _blocked("HANDOFF_BINDING_CONTRADICTION",
                        "canonical transaction authority acceptance criteria are incomplete",
                        candidates=[transaction_id], hints=hints)

    # Supplemental requirements are selected by transaction identity.  A
    # generic canonical transaction must never be made to impersonate T-AUTH-05.
    if transaction_id == "T-AUTH-05":
        for field, wanted in _T_AUTH_05_SUPPLEMENTAL_FIELDS.items():
            if str(record.get(field, "")).upper() != wanted.upper():
                return _blocked("HANDOFF_BINDING_CONTRADICTION",
                                f"T-AUTH-05 authority has invalid {field}",
                                candidates=[str(record.get(field, ""))], hints=hints)
        actual_criteria = {str(item).upper() for item in criteria if isinstance(item, str)}
        if not _T_AUTH_05_SUPPLEMENTAL_CRITERIA.issubset(actual_criteria):
            return _blocked("HANDOFF_BINDING_CONTRADICTION",
                            "T-AUTH-05 authority acceptance criteria are incomplete",
                            candidates=sorted(_T_AUTH_05_SUPPLEMENTAL_CRITERIA - actual_criteria), hints=hints)
    return None


def _resolve_administrative_transaction(root: Path, hints: dict[str, list[str]]) -> dict[str, Any] | None:
    """Resolve an explicit bounded administrative transaction.

    Returning ``None`` means this is a normal WOP/gate handoff.  Once a
    transaction identity is present, no mission or gate is inferred.
    """
    transaction_values = hints.get("transaction_id", [])
    if not transaction_values:
        return None
    if len(transaction_values) > 1:
        return _blocked("HANDOFF_RESOLUTION_AMBIGUOUS", "handoff contains multiple transaction assertions",
                        candidates=transaction_values, hints=hints)
    transaction_id = transaction_values[0].upper()
    records = _transaction_records(root)
    matches = _matching(records, "transaction_id", transaction_id)
    if not matches:
        return _blocked("HANDOFF_TRANSACTION_AUTHORITY_MISSING" if transaction_id.startswith("T-AUTH-")
                        else "HANDOFF_TRANSACTION_UNKNOWN",
                        "transaction identity is not backed by a current canonical authority record",
                        candidates=[transaction_id], hints=hints)
    current = [item for item in matches if str(item.get("state", "CURRENT")).upper()
               in {"CURRENT", "AUTHORIZED", "AUTHORIZED_FOR_IMPLEMENTATION", "ACTIVE"}]
    if len(current) != 1:
        return _blocked("HANDOFF_RESOLUTION_AMBIGUOUS", "transaction identity has no unique current authority record",
                        candidates=[str(item.get("source")) for item in matches], hints=hints)
    record = current[0]
    expected = {
        "operation_id": "OPERATION-BETA", "emm_id": "OPERATION-BETA-EMM",
    }
    for field, wanted in expected.items():
        asserted = hints.get(field, [])
        if len(asserted) > 1:
            return _blocked("HANDOFF_RESOLUTION_AMBIGUOUS", f"handoff contains multiple {field} assertions",
                            candidates=asserted, hints=hints)
        actual = str(record.get(field, "")).upper()
        if asserted and asserted[0].upper() != actual:
            return _blocked("HANDOFF_BINDING_CONTRADICTION", f"handoff {field} differs from transaction authority",
                            candidates=[asserted[0], actual], hints=hints)
        if actual != wanted:
            return _blocked("HANDOFF_BINDING_CONTRADICTION", f"transaction authority has invalid {field}",
                            candidates=[actual], hints=hints)
    if str(record.get("transaction_type", "")).upper() not in {
            "BOUNDED_ADMINISTRATIVE_CORRECTIVE", "BOUNDED_QUALIFICATION_TRANSACTION"}:
        return _blocked("HANDOFF_BINDING_CONTRADICTION",
                        "transaction authority has unsupported administrative transaction type",
                        candidates=[str(record.get("transaction_type", ""))], hints=hints)
    authorized_scope = record.get("authorized_scope")
    if (not isinstance(authorized_scope, list) or
            not authorized_scope or
            any(not isinstance(item, str) or not item.strip() for item in authorized_scope)):
        return _blocked("HANDOFF_TRANSACTION_SCOPE_MISSING", "transaction authority has no authorized scope",
                        candidates=[transaction_id], hints=hints)
    if "canonical_authority" in record and not isinstance(record.get("canonical_authority"), bool):
        return _blocked("HANDOFF_BINDING_CONTRADICTION",
                        "transaction authority has invalid canonical_authority flag",
                        candidates=[str(record.get("canonical_authority"))], hints=hints)
    if record.get("canonical_authority") is True:
        blocked = _validate_canonical_administrative_authority(record, transaction_id, hints)
        if blocked:
            return blocked
    if record.get("authority_source") in {"OPERATIONAL_ALPHA", "OA_MISSION_CONTRACT"} or \
            str(record.get("mission_contract", "")).upper().startswith("OA"):
        return _blocked("HANDOFF_BINDING_CONTRADICTION", "Operational Alpha mission authority cannot authorize Beta transaction",
                        candidates=[transaction_id], hints=hints)
    return record


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

    administrative = _resolve_administrative_transaction(root, hints)
    if isinstance(administrative, dict) and administrative.get("result") == "BLOCKED":
        return administrative
    if administrative is not None:
        # Administrative work has explicit transaction authority and therefore
        # deliberately has no mission/WOP/gate/admission projection.  The
        # resulting request is still the same Zeus-managed provider contract;
        # this function only constructs it and never starts a provider.
        try:
            authority = _resolve_authority(root)
            from scripts.lib.eos.operational_beta import authority as resolve_beta_authority
            beta_authority = resolve_beta_authority(root)
        except Exception as error:
            return _blocked("HANDOFF_AUTHORITY_UNRESOLVED", f"authoritative Operation Beta authority cannot be resolved: {error}", hints=hints)
        authority_validity = {
            "model_b_authority": beta_authority.get("authority_model") == "MODEL_B"
            and beta_authority.get("current_emm") == "OPERATION-BETA-EMM"
            and bool(beta_authority.get("current_wop")),
            "operation_beta_authority": beta_authority.get("authority_framework") == "OPERATION_BETA"
            and beta_authority.get("active_operation") == "BETA"
            and beta_authority.get("authority_integrity") == "PASS"
            and beta_authority.get("authority_resolution") == "PASS"
            and beta_authority.get("authority_digest_validation") == "PASS",
        }
        if not all(authority_validity.values()):
            return _blocked("HANDOFF_AUTHORITY_UNRESOLVED",
                            "canonical Operation Beta MODEL_B authority qualification failed", hints=hints)
        transaction_id = str(administrative["transaction_id"]).upper()
        execution_id = str(administrative.get("execution_id") or f"ZEUS-EXECUTION-REQUEST-{transaction_id}").upper()
        from scripts.lib.emp.qualification_contract import resolve_qualification_context
        qualification_context = resolve_qualification_context(administrative)
        if qualification_context["result"] != "PASS":
            return _blocked("HANDOFF_QUALIFICATION_AUTHORITY_UNRESOLVED",
                            "transaction qualification authority cannot be routed through Zeus",
                            candidates=[transaction_id], hints=hints)
        return {
            "result": "PASS", "handoff_resolution": "PASS", "handoff_input_classification": "AUTHORIZED_ADMINISTRATIVE_TRANSACTION",
            "source": source, "semantic_references": hints, "repository": identity,
            "operation_id": "OPERATION-BETA", "emm_id": "OPERATION-BETA-EMM",
            "transaction_id": transaction_id, "transaction_type": administrative["transaction_type"],
            "authority_source": administrative["authority_source"],
            "authorized_scope": list(administrative["authorized_scope"]),
            "cleanup_paths": list(administrative.get("cleanup_paths", [])),
            "write_authority": administrative.get("write_authority", "BOUNDED"),
            "provider_mode": administrative.get("provider_mode", "ZEUS_MANAGED_NON_INTERACTIVE"),
            "protected_git_authority": administrative.get("protected_git_authority", "ZEUS_ONLY"),
            "qualification_authority": administrative.get("qualification_authority", "ZEUS"),
            "objective": administrative.get("objective"),
            "prohibited_scope": list(administrative.get("prohibited_scope", [])),
            "acceptance_criteria": list(administrative.get("acceptance_criteria", [])),
            "required_evidence": list(administrative.get("required_evidence") or
                                       list(administrative.get("acceptance_criteria", [])) +
                                       ["provider terminal record", "actor-aware mutation attribution"]),
            "current_gate": administrative.get("current_gate", "C03"),
            "last_completed_gate": administrative.get("last_completed_gate", "C02"),
            "authority_context": {
                "transaction_authority": "RESOLVED",
                "provider_authority": "CODEX_BOUNDED_IMPLEMENTATION_PROVIDER",
                "zeus_controller_authority": "PRESERVED",
                "qualification_authority": administrative.get("qualification_authority", "ZEUS"),
            },
            "qualification_context": qualification_context,
            "authority": authority,
            "model_b_authority_validity": "PASS",
            "operation_beta_authority_validity": "PASS",
            "execution": {"execution_id": execution_id, "execution_authority": "PRESERVED",
                           "execution_available": True, "transaction_id": transaction_id},
            "zeus_execution_request": {"execution_id": execution_id, "transaction_id": transaction_id,
                                        "provider_mode": administrative.get("provider_mode", "ZEUS_MANAGED_NON_INTERACTIVE"),
                                        "provider": "CODEX_BOUNDED_IMPLEMENTATION_PROVIDER",
                                        "managed_lifecycle": "ZEUS_MANAGED", "constructed": True,
                                        "provider_contacted": False},
            "authorized_scope_resolved": "YES", "execution_request_constructed": "YES",
            "handoff_authority_source": "YES", "read_only": True, "mutation_applied": False,
            "delivery": {"result": "READY", "provider_contacted": False, "execution_started": False,
                          "next_authorized_action": "DELIVER_TO_ZEUS_MANAGED_PROVIDER"},
            "next_authorized_action": "DELIVER_TO_ZEUS_MANAGED_PROVIDER",
        }

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
        return _blocked("HANDOFF_EXECUTION_UNAVAILABLE" if not execution_candidates else "HANDOFF_RESOLUTION_AMBIGUOUS",
                        "execution is not uniquely available for handoff delivery",
                        candidates=[str(record.get("execution_id")) for record in execution_candidates], hints=hints)
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


def execute_administrative_handoff(repository: Path | str, resolved: Mapping[str, Any], *,
                                   prompt: str | None, output_path: Path | str,
                                   codex_bin: str = "codex", timeout_seconds: float = 300.0,
                                   retained_evidence: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Execute one already-resolved administrative handoff through Zeus."""
    if resolved.get("result") != "PASS" or resolved.get("handoff_input_classification") != "AUTHORIZED_ADMINISTRATIVE_TRANSACTION":
        raise ManagedHandoffError("HANDOFF_NOT_EXECUTABLE", "only an authorized administrative handoff may execute")
    contract = build_administrative_execution_contract(resolved, supplemental_prompt=prompt)
    from scripts.lib.emp.managed_provider import execute
    result = execute(repository=repository, prompt=contract["provider_prompt"],
                     authorized_paths=resolved["authorized_scope"],
                     execution_id=resolved["execution"]["execution_id"],
                     codex_bin=codex_bin, timeout_seconds=timeout_seconds,
                     output_path=output_path,
                     timing_root="/data/engineering/logs/codex-session-timed")
    result["execution_contract"] = contract
    result["authority_context"] = {
        "provider_authority": "CODEX_BOUNDED_IMPLEMENTATION_PROVIDER",
        "provider_self_qualification": "PROHIBITED",
        "zeus_controller_authority": "PRESERVED",
        "qualification_authority": resolved.get("qualification_authority", "ZEUS"),
    }
    cleanup = resolved.get("cleanup_paths", [])
    root = Path(repository).resolve()
    removed = []
    for relative in cleanup:
        candidate = (root / str(relative)).resolve()
        try:
            candidate.relative_to(root)
        except ValueError as error:
            raise ManagedHandoffError("CLEANUP_SCOPE_ESCAPE", str(relative)) from error
        if candidate.is_file():
            candidate.unlink()
            removed.append(str(relative))
    result["cleanup_paths"] = cleanup
    result["cleanup_removed"] = removed
    # Completion is evidence only.  This explicit Zeus-controller route is the
    # only post-provider qualification path; it never dispatches a second
    # provider task and provider output cannot approve or qualify itself.
    qualification = route_post_provider_qualification(resolved, result, None, retained_evidence=retained_evidence)
    result["qualification"] = qualification
    result["qualification_state"] = qualification.get("qualification", "REQUIRED")
    result["transaction_state"] = qualification.get("transaction_state", "REQUIRED")
    result["operator_acceptance"] = qualification.get("operator_acceptance", "NOT_APPLICABLE")
    result["next_authorized_action"] = qualification["next_authorized_action"]
    output = Path(output_path).resolve()
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if qualification.get("qualification_receipt") is not None:
        receipt_path = output.with_name(output.stem + ".qualification-receipt.json")
        receipt_path.write_text(json.dumps(qualification["qualification_receipt"], indent=2, sort_keys=True) + "\n", encoding="utf-8")
        result["qualification_receipt_path"] = str(receipt_path)
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def route_post_provider_qualification(
        resolved: Mapping[str, Any], managed_session: Mapping[str, Any],
        operator_acceptance: Mapping[str, Any] | None,
        *, retained_evidence: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Route completed provider work to Zeus qualification authority.

    Qualification is a controller action, not a provider handoff.  Keeping
    this boundary explicit prevents a caller from satisfying
    ``qualification_authority=ZEUS`` by launching Codex again.
    """
    if str(resolved.get("qualification_authority", "")).upper() != "ZEUS":
        return {
            "result": "BLOCKED", "qualification": "REQUIRED",
            "transaction_state": "REQUIRED",
            "blocker": "QUALIFICATION_AUTHORITY_NOT_ZEUS",
            "qualification_actor": "ZEUS_CONTROLLER",
            "qualification_provider_dispatch": "NO",
            "next_authorized_action": "STOP_FAIL_CLOSED",
            "provider_launched": False,
        }
    return qualify_administrative_handoff(
        resolved, managed_session, operator_acceptance,
        retained_evidence=retained_evidence,
    )


def qualify_administrative_handoff(
        resolved: Mapping[str, Any], managed_session: Mapping[str, Any],
        operator_acceptance: Mapping[str, Any] | None,
        *, retained_evidence: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Apply Zeus administrative qualification after provider completion.

    This is intentionally separate from ``execute_administrative_handoff``:
    invoking it never launches a provider and never interprets provider prose.
    """
    if (resolved.get("result") != "PASS" or
            resolved.get("handoff_input_classification") != "AUTHORIZED_ADMINISTRATIVE_TRANSACTION"):
        raise ManagedHandoffError("HANDOFF_NOT_QUALIFIABLE", "only an authorized administrative handoff may qualify")
    from scripts.lib.emp.qualification_contract import (
        finalize_administrative_transaction_evidence,
        qualify_administrative_transaction,
    )
    session = dict(managed_session)
    required_fields = (
        "executed_transaction_id", "transaction_objective_executed",
        "acceptance_criteria_evaluated", "acceptance_criteria_results",
        "required_evidence_retained",
    )
    transaction = {
        "transaction_id": resolved.get("transaction_id"),
        "transaction_type": resolved.get("transaction_type"),
        "transaction_state": resolved.get("transaction_state", "REQUIRED"),
        "objective": resolved.get("objective"),
        "authorized_scope": resolved.get("authorized_scope", []),
        "prohibited_scope": resolved.get("prohibited_scope", []),
        "acceptance_criteria": resolved.get("acceptance_criteria", []),
        "qualification_authority": resolved.get("qualification_authority", "ZEUS"),
    }
    finalization = None
    if not all(field in session for field in required_fields) or session.get("evidence_finalization_actor") != "ZEUS_CONTROLLER" or session.get("evidence_finalization") != "PASS":
        contract = session.get("execution_contract")
        evidence = retained_evidence or session.get("retained_evidence")
        if not isinstance(contract, Mapping) or not isinstance(evidence, Mapping):
            return {
                "result": "BLOCKED", "qualification": "REQUIRED",
                "transaction_id": transaction["transaction_id"],
                "blocker": "ZEUS_EVIDENCE_FINALIZATION_INPUT_MISSING",
                "qualification_actor": "ZEUS_CONTROLLER",
                "qualification_provider_dispatch": "NO", "provider_launched": False,
                "next_authorized_action": "RECONCILE_ADMINISTRATIVE_EVIDENCE",
            }
        finalization = finalize_administrative_transaction_evidence(
            transaction, contract, session, evidence,
        )
        session.update(finalization)
    result = qualify_administrative_transaction(transaction, session, operator_acceptance)
    if finalization is not None:
        result["evidence_finalization"] = finalization
    return result


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
        f"Execution completion      : {session.get('result', value.get('result', 'NOT_RECORDED'))}",
        f"Operator approval         : {(value.get('qualification') or {}).get('approval_requirement_id', 'NOT_REQUIRED')}",
        f"Qualification             : {(value.get('qualification') or {}).get('qualification', 'NOT_RUN')}",
        f"Historical session reused : {session.get('historical_session_reused_for_new_handoff', 'NO')}",
        f"Blockers                  : {'NONE' if not blockers else ', '.join(item.get('code', 'UNKNOWN') for item in blockers)}",
        f"Next action               : {value.get('next_authorized_action')}",
        "Read-only                 : YES",
    ))
