"""Read-only authority verification for repository publication transitions.

This module is deliberately independent of repository projection and the
publication workflow.  It validates durable transaction/receipt authority
against already-resolved Git and EOS facts, so every consumer can share one
fail-closed baseline classification without creating an import cycle.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping


PUBLICATION_SCHEMA = 1
TRANSACTION_DIR = "publication-transactions"
MILESTONES = (
    "PUBLICATION_DISCOVERED",
    "WORKTREE_CLASSIFIED",
    "CANDIDATE_RESOLVED",
    "CANDIDATE_ISOLATED",
    "PREPUBLICATION_VERIFIED",
    "CANDIDATE_STAGED",
    "STAGED_SET_VERIFIED",
    "COMMIT_CREATED",
    "REMOTE_PUBLISHED",
    "EOS_SYNCHRONIZED",
    "POSTPUBLICATION_VERIFIED",
    "PUBLICATION_QUALIFIED",
)
NEXT_BY_STATE = {
    "PUBLICATION_DISCOVERED": "CLASSIFY_PUBLICATION_WORKTREE",
    "WORKTREE_CLASSIFIED": "PREPARE_PUBLICATION_CANDIDATE",
    "CANDIDATE_RESOLVED": "VERIFY_PREPUBLICATION",
    "CANDIDATE_ISOLATED": "VERIFY_PREPUBLICATION",
    "PREPUBLICATION_VERIFIED": "STAGE_PUBLICATION_CANDIDATE",
    "CANDIDATE_STAGED": "VERIFY_STAGED_SET",
    "STAGED_SET_VERIFIED": "COMMIT_PUBLICATION",
    "COMMIT_CREATED": "PUSH_PUBLICATION",
    "REMOTE_PUBLISHED": "SYNCHRONIZE_EOS",
    "EOS_SYNCHRONIZED": "VERIFY_POSTPUBLICATION_STATE",
    "POSTPUBLICATION_VERIFIED": "QUALIFY_PUBLICATION",
    "PUBLICATION_QUALIFIED": "PUBLICATION_COMPLETE",
}


def _digest(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def safe_load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def receipt_path(runtime: Path, publication_id: str, milestone: str) -> Path:
    return runtime / "publication-receipts" / publication_id / f"{milestone}.json"


def receipt_errors(
    runtime: Path,
    record: Mapping[str, Any],
    milestone: str,
    entry: Mapping[str, Any] | None = None,
) -> list[str]:
    """Validate an immutable milestone receipt and transaction-side binding."""
    expected_path = receipt_path(runtime, str(record.get("publication_id") or ""), milestone)
    reference = dict(entry or (record.get("milestones") or {}).get(milestone) or {})
    errors: list[str] = []
    if not reference:
        return [f"{milestone} is not referenced by the transaction"]
    if Path(str(reference.get("receipt_path") or "")) != expected_path:
        errors.append(f"{milestone} receipt path is not repository-runtime canonical")
    receipt = safe_load(expected_path)
    if not receipt:
        return [*errors, f"{milestone} receipt is missing or invalid"]
    recorded_digest = receipt.get("receipt_digest")
    payload = dict(receipt)
    payload.pop("receipt_digest", None)
    if not recorded_digest or _digest(payload) != recorded_digest:
        errors.append(f"{milestone} receipt digest is invalid")
    if reference.get("receipt_digest") != recorded_digest:
        errors.append(f"{milestone} transaction receipt digest does not match")
    expected = {
        "schema_version": PUBLICATION_SCHEMA,
        "receipt_type": "zeus-publication-milestone",
        "milestone": milestone,
        "result": reference.get("result"),
        "publication_id": record.get("publication_id"),
        "mission_id": record.get("mission_id"),
        "wop_id": record.get("wop_id"),
        "publication_cohort_id": record.get("publication_cohort_id"),
        "supersedes_publication_id": record.get("supersedes_publication_id"),
        "repository_id": record.get("repository_id"),
        "input_digest": record.get("candidate_digest"),
    }
    for key, value in expected.items():
        if receipt.get(key) != value:
            errors.append(f"{milestone} receipt {key} binding does not match the transaction")
    if reference.get("result") != "PASS" or receipt.get("result") != "PASS":
        errors.append(f"{milestone} receipt is not a passing authority receipt")
    return errors


def transaction_integrity(runtime: Path, record: Mapping[str, Any]) -> dict[str, Any]:
    """Validate the durable state/receipt projection used for authorization."""
    milestones = dict(record.get("milestones") or {})
    completed = list(record.get("completed_milestones") or [])
    pending = list(record.get("pending_milestones") or [])
    expected_completed = [
        name for name in MILESTONES
        if name in milestones and milestones[name].get("result") == "PASS"
    ]
    errors: list[str] = []
    if record.get("schema_version") != PUBLICATION_SCHEMA:
        errors.append("publication transaction schema is invalid")
    if completed != expected_completed:
        errors.append("completed_milestones does not match passing receipt references")
    if pending != [name for name in MILESTONES if name not in expected_completed]:
        errors.append("pending_milestones does not complement completed_milestones")
    for milestone in expected_completed:
        errors.extend(receipt_errors(runtime, record, milestone, milestones.get(milestone)))
    state = record.get("current_state")
    if state in MILESTONES:
        if state not in expected_completed:
            errors.append("current_state is not backed by a completed milestone receipt")
        elif expected_completed != list(MILESTONES[: MILESTONES.index(str(state)) + 1]):
            errors.append("completed milestone ordering does not match current_state")
    elif state not in {"FAILED", "ABORTED"}:
        errors.append("current_state is not a canonical publication state")
    if state == "PREPUBLICATION_VERIFIED" and record.get("prepublication_result") != "PASS":
        errors.append("PREPUBLICATION_VERIFIED requires prepublication_result=PASS")
    expected_next = (
        "RESOLVE_PUBLICATION_BLOCKER" if state == "FAILED"
        else "PUBLICATION_ABORTED" if state == "ABORTED"
        else NEXT_BY_STATE.get(str(state), "STOP_FAIL_CLOSED")
    )
    if record.get("next_authorized_action") != expected_next:
        errors.append("persisted next_authorized_action does not match current_state")
    return {"result": "PASS" if not errors else "FAIL", "errors": errors}


def resolve_transaction_lineage(
    values: list[dict[str, Any]],
    *,
    mission_id: str | None = None,
    wop_id: str | None = None,
    repository_id: str | None = None,
    include_qualified_fallback: bool = True,
) -> dict[str, Any]:
    """Resolve canonical current publication authority without mutation.

    Supersession is derived from immutable successor links.  A qualified
    transaction is terminal historical provenance while a nonterminal
    transaction exists, but remains the mission lookup fallback after a
    completed publication.  No timestamp participates in selection.
    """
    records = [value for value in values if isinstance(value, dict)]
    errors: list[dict[str, str]] = []
    by_id: dict[str, dict[str, Any]] = {}
    duplicate_ids: set[str] = set()
    for value in records:
        publication_id = str(value.get("publication_id") or "")
        if not publication_id:
            errors.append({"code": "PUBLICATION_TRANSACTION_INTEGRITY_FAILURE", "reason": "publication transaction identity is missing"})
            continue
        if publication_id in by_id:
            duplicate_ids.add(publication_id)
        else:
            by_id[publication_id] = value
    for publication_id in sorted(duplicate_ids):
        errors.append({"code": "PUBLICATION_ID_AMBIGUOUS", "reason": f"publication identity is duplicated: {publication_id}"})

    mission = str(mission_id or "").upper()
    wop = str(wop_id or "").upper()
    scoped = [
        value for value in records
        if (not mission or str(value.get("mission_id") or "").upper() == mission)
        and (not wop or str(value.get("wop_id") or "").upper() == wop)
        and (not repository_id or value.get("repository_id") == repository_id)
    ]
    authoritative = [value for value in scoped if value.get("current_state") not in {"FAILED", "ABORTED"}]

    successors: dict[str, list[dict[str, Any]]] = {}
    for value in authoritative:
        successor_id = str(value.get("publication_id") or "")
        target_id = str(value.get("supersedes_publication_id") or "")
        if not target_id:
            continue
        target = by_id.get(target_id)
        if target is None:
            errors.append({"code": "SUPERSEDED_PUBLICATION_MISSING", "reason": f"{successor_id} supersedes missing publication {target_id}"})
            continue
        if target_id == successor_id:
            errors.append({"code": "SUPERSESSION_CYCLE", "reason": f"publication {successor_id} supersedes itself"})
            continue
        if str(target.get("mission_id") or "").upper() != str(value.get("mission_id") or "").upper():
            errors.append({"code": "SUPERSESSION_MISSION_MISMATCH", "reason": f"{successor_id} supersedes a publication from another mission"})
        if str(target.get("wop_id") or "").upper() != str(value.get("wop_id") or "").upper():
            errors.append({"code": "SUPERSESSION_WOP_MISMATCH", "reason": f"{successor_id} supersedes a publication from another WOP"})
        if target.get("repository_id") != value.get("repository_id"):
            errors.append({"code": "SUPERSESSION_REPOSITORY_MISMATCH", "reason": f"{successor_id} supersedes a publication from another repository"})
        successors.setdefault(target_id, []).append(value)

    # Follow immutable predecessor pointers.  A repeated node proves a cycle;
    # creation/update timestamps are intentionally irrelevant.
    for value in authoritative:
        seen: set[str] = set()
        cursor = value
        while cursor.get("supersedes_publication_id"):
            cursor_id = str(cursor.get("publication_id") or "")
            if cursor_id in seen:
                errors.append({"code": "SUPERSESSION_CYCLE", "reason": f"supersession cycle contains {cursor_id}"})
                break
            seen.add(cursor_id)
            target = by_id.get(str(cursor.get("supersedes_publication_id")))
            if target is None:
                break
            cursor = target

    operational = [value for value in authoritative if value.get("current_state") != "PUBLICATION_QUALIFIED"]
    authoritative_targets = {
        str(value.get("supersedes_publication_id"))
        for value in authoritative if value.get("supersedes_publication_id")
    }
    current = [value for value in operational if value.get("publication_id") not in authoritative_targets]
    if not current and include_qualified_fallback:
        current = [
            value for value in authoritative
            if value.get("current_state") == "PUBLICATION_QUALIFIED"
            and value.get("publication_id") not in authoritative_targets
        ]

    if len(current) > 1:
        current_ids = ", ".join(sorted(str(value.get("publication_id")) for value in current))
        errors.append({"code": "PUBLICATION_CARDINALITY_CONFLICT", "reason": f"more than one authoritative current publication transaction resolves the scope: {current_ids}"})

    current_ids = {str(value.get("publication_id")) for value in current}
    dispositions: dict[str, str] = {}
    for value in scoped:
        publication_id = str(value.get("publication_id") or "")
        state = value.get("current_state")
        if publication_id in current_ids:
            dispositions[publication_id] = "CURRENT_QUALIFIED" if state == "PUBLICATION_QUALIFIED" else "CURRENT"
        elif state in {"FAILED", "ABORTED"}:
            dispositions[publication_id] = str(state)
        elif state == "PUBLICATION_QUALIFIED":
            dispositions[publication_id] = "HISTORICAL_QUALIFIED"
        elif publication_id in authoritative_targets:
            dispositions[publication_id] = "SUPERSEDED"
        else:
            dispositions[publication_id] = "HISTORICAL"

    # Sibling nonterminal successors are competing current claims.  Qualified
    # siblings are terminal history and cannot compete with a recovery/reprepare.
    for target_id, claimed in successors.items():
        competing = [value for value in claimed if value.get("current_state") != "PUBLICATION_QUALIFIED"]
        if len(competing) > 1:
            errors.append({"code": "INCOMPATIBLE_SUPERSESSION_LINEAGE", "reason": f"multiple nonterminal publications supersede {target_id}"})

    # De-duplicate identical diagnostics produced while walking a cycle.
    unique_errors: list[dict[str, str]] = []
    seen_errors: set[tuple[str, str]] = set()
    for error in errors:
        key = (error["code"], error["reason"])
        if key not in seen_errors:
            seen_errors.add(key)
            unique_errors.append(error)
    return {
        "result": "PASS" if not unique_errors and len(current) <= 1 else "FAIL",
        "current": current if not unique_errors else [],
        "current_ids": sorted(current_ids) if not unique_errors else [],
        "historical": [value for value in scoped if str(value.get("publication_id") or "") not in current_ids],
        "dispositions": dispositions,
        "errors": unique_errors,
        "selection_authority": "IMMUTABLE_SUPERSESSION_LINEAGE_AND_TERMINAL_STATE",
        "timestamp_ordering_used": False,
        "read_only": True,
    }


def active_transactions(
    values: list[dict[str, Any]], *, include_qualified: bool = True
) -> list[dict[str, Any]]:
    """Compatibility projection of the validated canonical current set."""
    resolved = resolve_transaction_lineage(
        values, include_qualified_fallback=include_qualified
    )
    return list(resolved["current"]) if resolved["result"] == "PASS" else []


def _runtime_identity_errors(runtime: Path, facts: Mapping[str, Any]) -> list[str]:
    identity = safe_load(runtime / "runtime-identity.json")
    expected = {
        "repository": facts.get("repository_root"),
        "repository_id": facts.get("repository_id"),
        "repository_identity": facts.get("repository_identity"),
    }
    if not identity:
        return ["repository-bound runtime identity is missing or invalid"]
    return [
        f"runtime {field} binding does not match the repository"
        for field, value in expected.items()
        if identity.get(field) != value
    ]


def _active_for_repository(runtime: Path, repository_id: str) -> tuple[list[dict[str, Any]], list[str]]:
    directory = runtime / TRANSACTION_DIR
    if not directory.is_dir():
        return [], []
    values: list[dict[str, Any]] = []
    errors: list[str] = []
    for path in sorted(directory.glob("PUBLICATION-*.json")):
        value = safe_load(path)
        if not value:
            errors.append(f"publication transaction is malformed: {path}")
            continue
        if value.get("repository_id") == repository_id:
            values.append(value)
    lineage = resolve_transaction_lineage(
        values, repository_id=repository_id, include_qualified_fallback=False
    )
    errors.extend(item["reason"] for item in lineage["errors"])
    return list(lineage["current"]), errors


def _receipt(runtime: Path, record: Mapping[str, Any], milestone: str) -> dict[str, Any]:
    return safe_load(receipt_path(runtime, str(record.get("publication_id") or ""), milestone))


def resolve_repository_baseline(
    facts: Mapping[str, Any],
    *,
    runtime_root: Path | str | None = None,
    mission_id: str | None = None,
    wop_id: str | None = None,
    publication_id: str | None = None,
) -> dict[str, Any]:
    """Classify converged or receipt-authorized repository/EOS state.

    Git ancestry alone never authorizes divergence.  Transitional validity is
    granted only by one repository-bound, integral transaction whose current
    milestone receipt proves the exact live topology.
    """
    head = facts.get("head")
    origin = facts.get("origin_main")
    eos = facts.get("eos_baseline")
    eos_available = facts.get("eos_available") is True
    eos_identity_match = facts.get("eos_identity_match") is True
    eos_current_valid = facts.get("eos_manifest_consistent") is True
    eos_baseline_valid = facts.get("eos_baseline_manifest_consistent") is True
    converged = bool(head and head == origin and (not eos_available or eos == head))
    steady_valid = converged and (
        not eos_available or (eos_identity_match and eos_current_valid)
    )

    base = {
        "result": "PASS" if steady_valid else "FAIL",
        "repository_valid": steady_valid,
        "classification": "STEADY_STATE_CONVERGED" if steady_valid else "UNAUTHORIZED_DIVERGENCE",
        "steady_state_converged": steady_valid,
        "authorized_transition": False,
        "transition_state": None,
        "publication_id": None,
        "mission_id": mission_id,
        "wop_id": wop_id,
        "transaction_integrity": None,
        "next_authorized_action": None,
        "errors": [],
    }
    if steady_valid:
        if runtime_root is None:
            return base
        converged_active, _ = _active_for_repository(
            Path(runtime_root).resolve(), str(facts.get("repository_id") or "")
        )
        if publication_id:
            converged_active = [value for value in converged_active
                                if value.get("publication_id") == publication_id]
        if mission_id:
            converged_active = [value for value in converged_active
                                if value.get("mission_id") == str(mission_id).upper()]
        if wop_id:
            converged_active = [value for value in converged_active
                                if value.get("wop_id") == str(wop_id).upper()]
        if len(converged_active) != 1:
            return base
        converged_record = converged_active[0]
        state_requires_validation = converged_record.get("current_state") in {
            "EOS_SYNCHRONIZED", "POSTPUBLICATION_VERIFIED"
        } or (
            converged_record.get("current_state") in {"COMMIT_CREATED", "REMOTE_PUBLISHED"}
            and converged_record.get("commit_id") == head
        )
        if not state_requires_validation:
            return base

    errors: list[str] = []
    if runtime_root is None:
        errors.append("repository divergence has no repository-bound Zeus runtime authority")
        return {**base, "errors": errors}
    runtime = Path(runtime_root).resolve()
    errors.extend(_runtime_identity_errors(runtime, facts))
    active, transaction_errors = _active_for_repository(runtime, str(facts.get("repository_id") or ""))
    errors.extend(transaction_errors)
    if publication_id:
        active = [value for value in active if value.get("publication_id") == publication_id]
    if mission_id:
        active = [value for value in active if value.get("mission_id") == str(mission_id).upper()]
    if wop_id:
        active = [value for value in active if value.get("wop_id") == str(wop_id).upper()]
    if len(active) != 1:
        errors.append(f"authorized publication transaction cardinality is {len(active)}, expected 1")
        return {**base, "errors": errors}

    record = active[0]
    integrity = transaction_integrity(runtime, record)
    if integrity.get("result") != "PASS":
        errors.extend(f"transaction integrity: {item}" for item in integrity.get("errors", []))
    if record.get("repository_root") != facts.get("repository_root"):
        errors.append("publication repository root binding does not match")
    if record.get("repository_id") != facts.get("repository_id"):
        errors.append("publication repository identity does not match")
    if mission_id and record.get("mission_id") != str(mission_id).upper():
        errors.append("publication mission binding does not match")
    if wop_id and record.get("wop_id") != str(wop_id).upper():
        errors.append("publication WOP binding does not match")
    if facts.get("branch") != "main" or facts.get("detached_head") is True:
        errors.append("publication transition is not bound to branch main")
    if facts.get("index_clean") is not True:
        errors.append("publication transition index is not clean")
    if not eos_available or not eos_identity_match or not eos_baseline_valid:
        errors.append("authorized prior EOS baseline is unavailable or internally inconsistent")

    state = str(record.get("current_state") or "")
    commit_id = record.get("commit_id")
    starting_head = record.get("starting_head")
    starting_origin = record.get("starting_origin")
    starting_eos = record.get("starting_eos_baseline")
    if not (starting_head and starting_head == starting_origin == starting_eos):
        errors.append("publication starting HEAD/origin/EOS baseline is contradictory")

    classification = "UNAUTHORIZED_DIVERGENCE"
    if state == "COMMIT_CREATED":
        receipt = _receipt(runtime, record, state)
        expected = {
            "commit_id": commit_id,
            "parent_id": starting_head,
        }
        for field, value in expected.items():
            if receipt.get(field) != value:
                errors.append(f"COMMIT_CREATED receipt {field} does not match")
        if head != commit_id:
            errors.append("HEAD does not equal the authorized publication commit")
        if origin != starting_origin or eos != starting_eos:
            errors.append("origin/main or EOS moved from the authorized starting baseline")
        if facts.get("origin_main_ancestor_of_head") is not True or facts.get("behind_count") != 0:
            errors.append("origin/main is not a clean ancestor of the publication commit")
        classification = "AUTHORIZED_COMMIT_CREATED_PRE_PUSH"
    elif state == "REMOTE_PUBLISHED":
        receipt = _receipt(runtime, record, state)
        expected = {
            "commit_id": commit_id,
            "published_head": commit_id,
            "remote_ref": "refs/heads/main",
        }
        for field, value in expected.items():
            if receipt.get(field) != value:
                errors.append(f"REMOTE_PUBLISHED receipt {field} does not match")
        if not (head and head == origin == commit_id == record.get("published_head")):
            errors.append("HEAD/origin do not equal the remotely published transaction commit")
        if eos != starting_eos:
            errors.append("EOS moved before its authorized synchronization milestone")
        if facts.get("origin_main_ancestor_of_head") is not True:
            errors.append("published commit ancestry is invalid")
        classification = "AUTHORIZED_REMOTE_PUBLISHED_PRE_EOS_SYNC"
    elif state in {"EOS_SYNCHRONIZED", "POSTPUBLICATION_VERIFIED"}:
        receipt = _receipt(runtime, record, "EOS_SYNCHRONIZED")
        if receipt.get("eos_baseline") != commit_id:
            errors.append("EOS_SYNCHRONIZED receipt baseline does not match the publication commit")
        if not (head and head == origin == eos == commit_id):
            errors.append("EOS-synchronized publication is not fully converged")
        if not eos_current_valid:
            errors.append("converged EOS projection is inconsistent")
        classification = "EOS_SYNCHRONIZED_CONVERGED"
    else:
        errors.append(f"publication state {state or 'MISSING'} does not authorize repository divergence")

    valid = not errors
    return {
        **base,
        "result": "PASS" if valid else "FAIL",
        "repository_valid": valid,
        "classification": classification if valid else "UNAUTHORIZED_DIVERGENCE",
        "steady_state_converged": False,
        "authorized_transition": valid,
        "transition_state": state,
        "publication_id": record.get("publication_id"),
        "mission_id": record.get("mission_id"),
        "wop_id": record.get("wop_id"),
        "transaction_integrity": integrity,
        "next_authorized_action": NEXT_BY_STATE.get(state),
        "errors": errors,
    }
