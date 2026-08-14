"""Zeus-owned qualification of completed administrative managed sessions.

Provider output is evidence only.  Qualification is decided here from the
authoritative transaction, the independently observed managed-session record,
and a transaction-bound operator acceptance record only when the canonical
approval policy requires one.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from scripts.lib.emp.operator_approval_policy import resolve_operator_approval


class AdministrativeQualificationError(ValueError):
    """Raised when an administrative qualification input is malformed."""


_REQUIRED_SESSION_PREDICATES = {
    "zeus_managed_session_created": "YES",
    "provider_process_owned_by": "ZEUS",
    "provider_process_state": "COMPLETED",
    "provider_exit_status": 0,
    "scope_verification": "PASS",
    "terminal_reconciliation": "PASS",
    "execution_session_integrity": "PASS",
    "authorized_scope_compliance": "PASS",
    "required_evidence_completeness": "PASS",
    "acceptance_criteria_verification": "PASS",
    "provider_terminal_record": "RETAINED",
    "actor_aware_mutation_attribution": "PASS",
}

_ZEUS_RECEIPT_MARKER = "/receipts/qualification/"


def finalize_administrative_transaction_evidence(
    transaction: Mapping[str, Any],
    execution_contract: Mapping[str, Any],
    managed_session: Mapping[str, Any],
    retained_evidence: Mapping[str, Any],
) -> dict[str, Any]:
    """Derive Zeus-owned transaction acceptance evidence from retained facts.

    This is deliberately a separate boundary from provider execution and
    qualification.  Provider output, including fields with names matching
    the finalized fields, is never an input to the derivation.  The caller
    must provide independently retained, Zeus-attributed verification facts.
    """
    txid = str(transaction.get("transaction_id", "")).upper()
    contract_txid = str(execution_contract.get("transaction_id", "")).upper()
    failures: list[str] = []
    if not txid or contract_txid != txid:
        failures.append("transaction identity does not match execution contract")
    execution_id = str(
        managed_session.get("zeus_execution_id")
        or managed_session.get("execution_id")
        or retained_evidence.get("zeus_execution_id", "")
    ).upper()
    if not execution_id or not execution_id.endswith(txid):
        failures.append("Zeus execution identity is not deterministically bound to transaction")
    context_txid = str(
        retained_evidence.get("transaction_id")
        or (retained_evidence.get("transaction_context") or {}).get("transaction_id", "")
    ).upper()
    if context_txid != txid:
        failures.append("retained evidence transaction context is not bound")
    if str(managed_session.get("provider_process_state", "")).upper() != "COMPLETED" or managed_session.get("provider_exit_status") != 0:
        failures.append("provider terminal evidence is not successful")
    if managed_session.get("scope_verification") != "PASS" or managed_session.get("terminal_reconciliation") != "PASS":
        failures.append("provider scope or terminal reconciliation is not PASS")

    attribution = retained_evidence.get("actor_aware_mutation_attribution", {})
    provider_diff = list(managed_session.get("provider_post_execution_diff", managed_session.get("post_execution_diff", [])))
    if not isinstance(attribution, Mapping):
        failures.append("actor-aware mutation attribution is absent")
        attribution = {}
    if provider_diff or attribution.get("provider_mutation") != "NO":
        failures.append("provider mutation is present")
    if attribution.get("evidence_finalization_actor") != "ZEUS_CONTROLLER":
        failures.append("evidence finalization actor is not Zeus")
    if attribution.get("zeus_controller_mutation") != "YES":
        failures.append("Zeus controller mutation is not recorded")

    criteria = execution_contract.get("acceptance_criteria")
    criterion_facts = retained_evidence.get("acceptance_criteria")
    if not isinstance(criteria, list) or not criteria:
        failures.append("execution contract acceptance criteria are absent")
        criteria = []
    if not isinstance(criterion_facts, list):
        criterion_facts = []
    by_criterion = {str(item.get("criterion", "")): item for item in criterion_facts if isinstance(item, Mapping)}
    criterion_results: list[dict[str, Any]] = []
    for criterion in criteria:
        fact = by_criterion.get(str(criterion))
        valid = (
            isinstance(fact, Mapping)
            and str(fact.get("result", "")).upper() == "PASS"
            and bool(fact.get("evidence"))
            and bool(fact.get("evidence_source"))
            and str(fact.get("evaluated_by", "")).upper() == "ZEUS"
            and str(fact.get("authority", "")).upper() != "CODEX"
        )
        criterion_results.append({
            "criterion": str(criterion),
            "result": "PASS" if valid else "BLOCKED",
            "evidence": fact.get("evidence") if isinstance(fact, Mapping) else None,
            "evidence_source": fact.get("evidence_source") if isinstance(fact, Mapping) else None,
            "evaluated_by": "ZEUS",
        })
        if not valid:
            failures.append("acceptance criterion lacks independently retained PASS evidence: " + str(criterion))

    required = execution_contract.get("required_evidence")
    required_facts = retained_evidence.get("required_evidence")
    if not isinstance(required, list) or not required:
        failures.append("execution contract required evidence is absent")
        required = []
    if not isinstance(required_facts, list):
        required_facts = []
    by_requirement = {str(item.get("requirement", "")): item for item in required_facts if isinstance(item, Mapping)}
    required_results: list[dict[str, Any]] = []
    for requirement in required:
        fact = by_requirement.get(str(requirement))
        valid = (
            isinstance(fact, Mapping)
            and fact.get("present") is True
            and bool(fact.get("evidence"))
            and bool(fact.get("evidence_source"))
            and str(fact.get("evaluated_by", "")).upper() == "ZEUS"
            and str(fact.get("authority", "")).upper() != "CODEX"
        )
        required_results.append({
            "requirement": str(requirement),
            "present": valid,
            "evidence": fact.get("evidence") if isinstance(fact, Mapping) else None,
            "evidence_source": fact.get("evidence_source") if isinstance(fact, Mapping) else None,
            "evaluated_by": "ZEUS",
        })
        if not valid:
            failures.append("required evidence is not independently retained: " + str(requirement))

    objective_facts = retained_evidence.get("objective_evidence")
    objective_valid = (
        isinstance(objective_facts, list) and bool(objective_facts)
        and all(isinstance(item, Mapping) and str(item.get("result", "")).upper() == "PASS"
                and item.get("evidence") and item.get("evidence_source")
                and str(item.get("evaluated_by", "")).upper() == "ZEUS"
                and str(item.get("authority", "")).upper() != "CODEX" for item in objective_facts)
        and bool(criterion_results) and all(item["result"] == "PASS" for item in criterion_results)
    )
    if not objective_valid:
        failures.append("transaction objective lacks sufficient independently retained evidence")

    finalized = {
        "executed_transaction_id": txid if not failures or not any("identity" in item or "bound" in item for item in failures) else None,
        "transaction_objective_executed": "YES" if objective_valid and not failures else "NO",
        "acceptance_criteria_evaluated": "YES" if criterion_results and not failures else "NO",
        "acceptance_criteria_results": criterion_results,
        "required_evidence_retained": "YES" if required_results and not failures else "NO",
        "required_evidence_results": required_results,
        "evidence_finalization_actor": "ZEUS_CONTROLLER",
        "provider_assertions_authoritative": "NO",
        "provider_self_qualification": "PROHIBITED",
        "provider_mutation": "NO" if not provider_diff else "YES",
        "zeus_controller_mutation": "YES" if attribution.get("zeus_controller_mutation") == "YES" else "NO",
        "evidence_finalization": "PASS" if not failures else "BLOCKED",
        "evidence_finalization_failures": failures,
    }
    return finalized


def _transaction_acceptance_failures(
    transaction: Mapping[str, Any], managed_session: Mapping[str, Any],
) -> list[str]:
    contract = managed_session.get("execution_contract")
    if not isinstance(contract, Mapping):
        return ["transaction-specific execution contract is absent"]
    failures: list[str] = []
    if str(contract.get("transaction_id", "")).upper() != str(transaction.get("transaction_id", "")).upper():
        failures.append("execution contract transaction identity mismatch")
    if str(contract.get("transaction_type", "")).upper() != str(transaction.get("transaction_type", "")).upper():
        failures.append("execution contract transaction type mismatch")
    for field in ("objective", "authorized_scope", "prohibited_scope", "acceptance_criteria",
                  "lifecycle_boundary", "protected_operations", "required_verification",
                  "required_evidence", "stop_conditions"):
        if not contract.get(field):
            failures.append(f"execution contract field is missing: {field}")
    if managed_session.get("executed_transaction_id", "").upper() != str(transaction.get("transaction_id", "")).upper():
        failures.append("executed transaction identity is missing or incorrect")
    if managed_session.get("transaction_objective_executed") != "YES":
        failures.append("transaction objective was not demonstrated as executed")
    if managed_session.get("acceptance_criteria_evaluated") != "YES":
        failures.append("transaction acceptance criteria were not evaluated")
    results = managed_session.get("acceptance_criteria_results")
    criteria = contract.get("acceptance_criteria", [])
    if not isinstance(results, list) or len(results) != len(criteria):
        failures.append("transaction acceptance evidence is incomplete")
    elif any(not isinstance(item, Mapping) or str(item.get("result", "")).upper() != "PASS" for item in results):
        failures.append("transaction acceptance criteria did not all pass")
    if managed_session.get("required_evidence_retained") != "YES":
        failures.append("required transaction evidence was not retained")
    return failures


def resolve_qualification_context(
    transaction: Mapping[str, Any],
    *,
    provider_authority: Mapping[str, Any] | None = None,
    policy_path: Path | str | None = None,
) -> dict[str, Any]:
    """Resolve Zeus qualification separately from provider authority.

    The provider is intentionally represented as a bounded implementation
    authority.  Its prohibition on self-qualification is an input to this
    context, never a prohibition on the Zeus controller.  This pure resolver
    performs no provider work and persists no receipt.
    """
    qualification_authority = str(transaction.get("qualification_authority", "ZEUS")).upper()
    provider = dict(provider_authority or {})
    if qualification_authority != "ZEUS":
        return {
            "result": "BLOCKED",
            "qualification_transaction_resolution": "FAIL",
            "qualification_execution_available": "NO",
            "blocker": "QUALIFICATION_AUTHORITY_NOT_ZEUS",
            "provider_self_qualification": "PROHIBITED",
            "zeus_qualification_authority": "NOT_PRESERVED",
        }
    approval = resolve_operator_approval(
        {**transaction, **provider,
         "lifecycle_class": transaction.get("lifecycle_class", "ADMINISTRATIVE")},
        policy_path,
    )
    required = bool(approval["approval_required"])
    return {
        "result": "PASS",
        "qualification_transaction_resolution": "PASS",
        "qualification_execution_available": "YES" if not required else "NO",
        "provider_authority_model": "CODEX_BOUNDED_IMPLEMENTATION_PROVIDER",
        "provider_self_qualification": "PROHIBITED",
        "zeus_controller_authority": "PRESERVED",
        "zeus_qualification_authority": "PRESERVED",
        "operator_approval_policy_resolved": "YES",
        "operator_approval_required": required,
        "operator_acceptance": "REQUIRED" if required else "NOT_APPLICABLE",
        "approval_requirement_id": approval.get("requirement_id"),
        "approval_reason": approval.get("reason"),
        "next_authorized_action": approval.get("required_operator_action") if required else "ZEUS_INDEPENDENT_QUALIFICATION",
    }


def qualify_administrative_transaction(
    transaction: Mapping[str, Any],
    managed_session: Mapping[str, Any],
    operator_acceptance: Mapping[str, Any] | None,
    *, policy_path: Path | str | None = None,
) -> dict[str, Any]:
    """Independently qualify one completed administrative managed session.

    This function never launches a provider.  It also deliberately does not
    inspect provider stdout/stderr: final-report prose is not authority.
    """
    transaction_id = str(transaction.get("transaction_id", "")).upper()
    transaction_type = str(transaction.get("transaction_type", "")).upper()
    if not transaction_id or transaction_type not in {
            "BOUNDED_ADMINISTRATIVE_CORRECTIVE", "BOUNDED_QUALIFICATION_TRANSACTION"}:
        return _blocked("ADMINISTRATIVE_TRANSACTION_REQUIRED", transaction_id)

    try:
        routing = resolve_qualification_context(transaction, provider_authority=managed_session, policy_path=policy_path)
    except ValueError as error:
        return _blocked("OPERATOR_APPROVAL_POLICY_INVALID", transaction_id, reason=str(error))
    if routing["result"] != "PASS":
        return {**routing, "transaction_id": transaction_id, "qualification": "REQUIRED", "provider_launched": False}
    current_state = str(transaction.get("transaction_state", transaction.get("state", ""))).upper()
    if current_state in {"QUALIFIED", "ACCEPTED", "QUALIFIED_OR_ACCEPTED_TERMINAL"}:
        return _qualified(transaction_id, operator_acceptance, idempotent=True)

    failures: list[str] = []
    failures.extend(_transaction_acceptance_failures(transaction, managed_session))
    for field, expected in _REQUIRED_SESSION_PREDICATES.items():
        actual = managed_session.get(field)
        if actual != expected:
            failures.append(f"{field}={actual!r}; expected {expected!r}")
    if managed_session.get("out_of_scope_changes", []) != []:
        failures.append("out_of_scope_changes must be empty")
    if managed_session.get("protected_actions_performed", []) != []:
        failures.append("protected_actions_performed must be empty")
    provider_diff = managed_session.get("provider_post_execution_diff", managed_session.get("post_execution_diff", []))
    forged_receipts = [path for path in provider_diff if _ZEUS_RECEIPT_MARKER in f"/{path}"]
    if forged_receipts:
        failures.append("provider attempted to mutate Zeus qualification receipt: " + ", ".join(forged_receipts))
    if managed_session.get("unauthorized_controller_changes", []) != []:
        failures.append("unauthorized controller changes are present")
    if str(managed_session.get("receipt_authority", "ZEUS")).upper() == "CODEX":
        failures.append("provider cannot authoritatively persist Zeus qualification receipts")

    try:
        approval = resolve_operator_approval(
            {**transaction, **managed_session,
             "lifecycle_class": transaction.get("lifecycle_class", "ADMINISTRATIVE" if transaction_type == "BOUNDED_ADMINISTRATIVE_CORRECTIVE" else "MISSION")},
            policy_path,
        )
    except ValueError as error:
        return _blocked("OPERATOR_APPROVAL_POLICY_INVALID", transaction_id, reason=str(error))
    acceptance = operator_acceptance or {}
    if approval["approval_required"]:
        if str(acceptance.get("operator_decision", "")).upper() != "ACCEPT":
            return _approval_required(transaction_id, approval)
        if str(acceptance.get("transaction_id", "")).upper() != transaction_id:
            failures.append("operator acceptance is not transaction-bound")
        if str(acceptance.get("authority_source_class", "")).upper() != "CANONICAL_OPERATOR_AUTHORIZATION":
            failures.append("operator acceptance is not authoritative")
        if not acceptance.get("acceptance_record_id"):
            failures.append("operator acceptance record identity is missing")

    if failures:
        return {
            "result": "BLOCKED",
            "qualification": "REQUIRED",
            "transaction_id": transaction_id,
            "transaction_state": current_state or "REQUIRED",
            "provider_completion_is_qualification": False,
            "operator_acceptance_required": approval["approval_required"],
            "approval_requirement_id": approval.get("requirement_id"),
            "approval_reason": approval.get("reason"),
            "approval_authority_source": approval.get("authority_source"),
            "failures": failures,
            "next_authorized_action": "RECONCILE_ADMINISTRATIVE_QUALIFICATION",
            "provider_launched": False,
            "provider_scope_compliance": "FAIL" if forged_receipts else managed_session.get("provider_scope_compliance", "PASS"),
            "zeus_controller_mutation": managed_session.get("zeus_controller_mutation", "NO"),
        }
    return {**_qualified(transaction_id, acceptance if approval["approval_required"] else None, idempotent=False),
            "provider_self_qualification": "PROHIBITED",
            "zeus_qualification_authority": "PRESERVED",
            "operator_approval_policy_resolved": "YES"}


def _qualified(transaction_id: str, acceptance: Mapping[str, Any] | None, *, idempotent: bool) -> dict[str, Any]:
    successor = (
        "BEGIN_C03_EOS_AND_ENGINEERING_STATE_ASSESSMENT"
        if transaction_id == "C02-POST-ACCEPTANCE-TEST-RECONCILIATION"
        else "C02_POST_ACCEPTANCE_TEST_RECONCILIATION"
    )
    return {
        "result": "PASS",
        "qualification": "PASS",
        "transaction_id": transaction_id,
        "transaction_state": "QUALIFIED_OR_ACCEPTED_TERMINAL",
        "operator_decision": "ACCEPT" if acceptance else "NOT_REQUIRED",
        "operator_acceptance": "AUTHORITATIVE_AND_TRANSACTION_BOUND" if acceptance else "NOT_APPLICABLE",
        "acceptance_record_id": (acceptance or {}).get("acceptance_record_id"),
        "provider_completion_is_qualification": False,
        "operator_acceptance_required": bool(acceptance),
        "qualification_evidence": ["provider_exit_zero", "session_integrity", "scope_compliance", "evidence_complete", "terminal_reconciliation", "no_protected_actions", "no_out_of_scope_changes"],
        "idempotent_replay": idempotent,
        "provider_launched": False,
        "qualification_actor": "ZEUS_CONTROLLER",
        "qualification_provider_dispatch": "NO",
        "next_authorized_action": successor,
        "qualification_receipt": _receipt(transaction_id, acceptance, idempotent),
        "provider_self_qualification": "PROHIBITED",
        "zeus_qualification_authority": "PRESERVED",
        "operator_approval_policy_resolved": "YES",
    }


def _approval_required(transaction_id: str, approval: Mapping[str, Any]) -> dict[str, Any]:
    return {"result": "BLOCKED", "qualification": "REQUIRED", "transaction_id": transaction_id,
            "operator_acceptance_required": True, "approval_requirement_id": approval["requirement_id"],
            "approval_reason": approval["reason"],
            "approval_authority_source": approval["authority_source"],
            "approval_resulting_transition": approval["resulting_transition"],
            "next_authorized_action": approval["required_operator_action"],
            "provider_completion_is_qualification": False, "provider_launched": False,
            "qualification_actor": "ZEUS_CONTROLLER", "qualification_provider_dispatch": "NO",
            "provider_self_qualification": "PROHIBITED",
            "zeus_qualification_authority": "PRESERVED",
            "operator_approval_policy_resolved": "YES"}


def _blocked(code: str, transaction_id: str, *, reason: str | None = None) -> dict[str, Any]:
    return {
        "result": "BLOCKED",
        "qualification": "REQUIRED",
        "transaction_id": transaction_id,
        "blocker": code,
        "provider_completion_is_qualification": False,
        "operator_acceptance_required": False,
        "approval_policy_error": reason,
        "next_authorized_action": "STOP_FAIL_CLOSED",
        "provider_launched": False,
        "qualification_actor": "ZEUS_CONTROLLER",
        "qualification_provider_dispatch": "NO",
        "transaction_state": "REQUIRED",
    }


def _receipt(transaction_id: str, acceptance: Mapping[str, Any] | None, idempotent: bool) -> dict[str, Any]:
    value = {
        "transaction_id": transaction_id,
        "operator_acceptance": bool(acceptance),
        "idempotent_replay": idempotent,
        "authority": "ZEUS",
        "receipt_authority": "ZEUS",
        "provider_mutation": "NO",
        "zeus_controller_mutation": "YES",
        "zeus_receipt_attribution": "ZEUS_CONTROLLER_MUTATION",
        "qualification_actor": "ZEUS_CONTROLLER",
    }
    value["receipt_id"] = "ZEUS-QUALIFICATION-" + hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()[:24]
    return value
