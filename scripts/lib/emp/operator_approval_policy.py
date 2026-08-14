"""Canonical, policy-driven resolution of Zeus operator decision boundaries."""
from __future__ import annotations
from pathlib import Path
from typing import Any, Mapping
import yaml

class OperatorApprovalPolicyError(ValueError):
    """The controlled approval-requirements policy is invalid or ambiguous."""

DEFAULT_POLICY = Path(__file__).resolve().parents[3] / "engineering/authority/operator-approval-requirements.yaml"
REQUIRED = {"requirement_id", "lifecycle_situation", "applicability", "required_operator_action", "authority_source", "active", "rationale", "resulting_transition"}

def resolve_operator_approval(context: Mapping[str, Any], policy_path: Path | str | None = None) -> dict[str, Any]:
    path = Path(policy_path or DEFAULT_POLICY)
    try:
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as error:
        raise OperatorApprovalPolicyError(f"operator approval policy cannot be read: {error}") from error
    if not isinstance(document, Mapping) or document.get("schema_version") != 1 or not isinstance(document.get("policy_id"), str):
        raise OperatorApprovalPolicyError("operator approval policy schema is invalid")
    requirements = document.get("requirements")
    if not isinstance(requirements, list):
        raise OperatorApprovalPolicyError("operator approval requirements must be a list")
    seen: set[str] = set(); active = []
    for item in requirements:
        if not isinstance(item, Mapping) or not REQUIRED.issubset(item):
            raise OperatorApprovalPolicyError("operator approval requirement is incomplete")
        identifier = item["requirement_id"]
        if not isinstance(identifier, str) or not identifier.strip() or identifier in seen:
            raise OperatorApprovalPolicyError("operator approval requirement IDs must be unique and non-empty")
        seen.add(identifier)
        clauses = item["applicability"].get("all") if isinstance(item["applicability"], Mapping) else None
        if not isinstance(item["active"], bool) or not isinstance(clauses, list) or not clauses or any(not isinstance(c, Mapping) or not isinstance(c.get("field"), str) or ("equals" not in c and "in" not in c) for c in clauses):
            raise OperatorApprovalPolicyError(f"requirement {identifier} predicates are malformed")
        if item["active"]: active.append(item)
    matches = []
    for item in active:
        if all((clause["field"] in context and ("equals" not in clause or context[clause["field"]] == clause["equals"]) and ("in" not in clause or context[clause["field"]] in clause["in"])) for clause in item["applicability"]["all"]):
            matches.append(item)
    if len(matches) > 1:
        raise OperatorApprovalPolicyError("multiple active operator approval requirements apply")
    if not matches:
        return {"approval_required": False, "policy_id": document["policy_id"], "requirement_id": None, "reason": None}
    item = matches[0]
    return {"approval_required": True, "policy_id": document["policy_id"], "requirement_id": item["requirement_id"], "reason": item["rationale"], "authority_source": item["authority_source"], "required_operator_action": item["required_operator_action"], "resulting_transition": item["resulting_transition"]}
