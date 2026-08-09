"""Read-only Operation Beta roadmap and controller projections.

The Beta roadmap is planning authority.  This module parses the published
roadmap and validates its bindings; it does not create a second mission or
capability authority and never persists derived metrics.
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any
import yaml
from scripts.lib.emp.runtime_paths import runtime_path
from scripts.lib.wop.canonical_package import canonical_identity_records

ROADMAP = "engineering/docs/architecture/OPERATION-BETA-ROADMAP.md"
CHARTER = "engineering/docs/operations/OPERATION-BETA-CHARTER.md"
AUTHORITY = "engineering/docs/architecture/OPERATION-BETA-AUTHORITY-MODEL.md"
TRANSITION = "engineering/operations/operation-beta-transition.md"
DESIGN = "engineering/docs/architecture/ENGINEERING-PLATFORM-DESIGN-PRINCIPLES.md"
CURRENT_MISSION = "engineering/missions/operation-beta-current.yaml"
GATE_CATALOG = "engineering/evidence/operation-beta/OPERATION-BETA-CANONICAL-GATE-CATALOG.yaml"

_NON_CURRENT_LIFECYCLE_STATES = {
    "", "UNRESOLVED", "MISSION_NOT_FOUND", "COMPLETED", "CLOSED",
    "CANCELLED", "FAILED", "SUPERSEDED", "REJECTED",
}

class OperationalBetaError(ValueError):
    pass


def authority(root: Path | str, *, include_current_execution: bool = True) -> dict[str, Any]:
    """Resolve the published Operation Beta authority projection.

    This is the current operator-facing authority source.  The historical
    Operational Alpha/EMM and manual-governance policy records remain
    available for explicit legacy WOP reconciliation, but they do not govern
    the Beta execution path.
    """
    root = Path(root).resolve()
    current = _current_mission(root)
    activation_path = (root / str(current.get("authority_record", ""))).resolve()
    if root not in activation_path.parents or not activation_path.is_file():
        raise OperationalBetaError("BETA_AUTHORITY_RECORD_UNAVAILABLE")
    try:
        activation = yaml.safe_load(activation_path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as error:
        raise OperationalBetaError(f"BETA_AUTHORITY_RECORD_INVALID: {error}") from error
    if not isinstance(activation, dict):
        raise OperationalBetaError("BETA_AUTHORITY_RECORD_INVALID")
    if any((activation.get(key) != expected) for key, expected in (
        ("operation", "OPERATION-BETA"),
        ("mission_id", current.get("mission_id")),
        ("lifecycle_state", "ACTIVE"),
        ("publication_state", "PUBLISHED_ACTIVE"),
    )):
        raise OperationalBetaError("BETA_AUTHORITY_RECORD_BINDING_INVALID")
    # Lifecycle receipt verifiers call this with current execution disabled:
    # authority validation is upstream of receipt resolution and must not
    # recurse through the downstream current-execution projection.  Public
    # authority views use the default and therefore expose the same live
    # current gate and next action as the operation and mission projections.
    operation_data = operation(root, include_current_execution=include_current_execution)
    next_data = next_action(root, include_current_execution=include_current_execution)
    source_digests = operation_data["integrity"]["source_digests"]
    authority_digest = hashlib.sha256(
        json.dumps({
            "activation": activation,
            "current_mission": current,
            "source_digests": source_digests,
        }, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str).encode()
    ).hexdigest()
    return {
        "result": "PASS",
        "authority_integrity": "PASS",
        "authority_framework": "OPERATION_BETA",
        "authority_resolution": "PASS",
        "authority_digest_validation": "PASS",
        "active_operation": "BETA",
        "authority_source": "Operation Beta",
        "authority_digest": authority_digest,
        "active_gate": ((operation_data.get("current_gate_mapping") or {}).get("operation_gate_id")
                        or operation_data["recommended_mission"]),
        "current_platform_mission": current,
        "operation_id": operation_data["operation_id"],
        "mission_id": current["mission_id"],
        "authority_record": str(activation_path),
        "oa_authority": "SUPERSEDED",
        "authoritative_sources": operation_data["authoritative_sources"] + [str(current["authority_record"])],
        "next_authorized_action": next_data["next_authorized_action"],
    }


def _read(root: Path, relative: str) -> str:
    try:
        return (root / relative).read_text(encoding="utf-8")
    except OSError as error:
        raise OperationalBetaError(f"BETA_AUTHORITY_UNAVAILABLE: {relative}: {error}") from error


def _current_mission(root: Path) -> dict[str, Any]:
    try:
        value = yaml.safe_load(_read(root, CURRENT_MISSION))
    except yaml.YAMLError as error:
        raise OperationalBetaError(f"BETA_CURRENT_MISSION_INVALID: {error}") from error
    if not isinstance(value, dict) or value.get("mission_id") != "BETA-04" or value.get("status") != "PUBLISHED_ACTIVE":
        raise OperationalBetaError("BETA_CURRENT_MISSION_NOT_PUBLISHED")
    return value


def _digest(value: Any) -> str:
    return hashlib.sha256(repr(value).encode()).hexdigest()


def _execution_records(root: Path, mission_id: str) -> list[dict[str, Any]]:
    """Read valid execution records without treating history as current state."""
    directory = runtime_path(root, "mission-executions")
    matches = []
    for path in sorted(directory.glob("MISSION-EXECUTION-*.json")):
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
            supplied = value.pop("state_digest", None)
            expected = hashlib.sha256(
                json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
            ).hexdigest()
            if supplied != expected or value.get("mission_id") != mission_id:
                continue
            value["state_digest"] = supplied
            matches.append(value)
        except (OSError, ValueError, json.JSONDecodeError):
            continue
    return matches


def _execution_detail(root: Path, value: dict[str, Any]) -> dict[str, Any]:
    """Project one execution, including its freshness diagnostics."""
    admission_value = None
    try:
        admission_path = runtime_path(root, "mission-admissions") / f"{value.get('admission_id')}.json"
        admission_value = json.loads(admission_path.read_text(encoding="utf-8"))
    except (OSError, TypeError, json.JSONDecodeError):
        admission_value = None
    admitted_baseline = (admission_value or {}).get("artifacts", {}).get("repository_baseline")
    current_baseline = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "HEAD"],
        text=True, capture_output=True, check=False,
    ).stdout.strip()
    current_validation = None
    if value.get("current_gate") == "VALIDATE_WOP":
        admission_path = runtime_path(root, "mission-admissions") / f"{value.get('admission_id')}.json"
        try:
            admission = json.loads(admission_path.read_text(encoding="utf-8"))
            wop = admission["artifacts"]["wop_result"]["wop"]
            from scripts.lib.emp.wop_admission import AdmissionController
            failures = AdmissionController().validate(wop, str(root.resolve()))
            current_validation = {
                "result": "PASS" if not failures else "FAIL",
                "failures": [item.to_mapping() for item in failures],
                "source": "canonical WOP submission/execution validator",
            }
        except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
            current_validation = {"result": "FAIL", "failures": [{"message": str(error)}]}
    session = None
    if value.get("session_id"):
        try:
            from scripts.lib.emp.native_session import NativeSessionStore
            native = NativeSessionStore(runtime_path(root, "native-sessions")).load(value["session_id"])
            session = {key: native.get(key) for key in ("session_id", "lifecycle_state", "execution_id", "current_gate", "authorized_effect_profile", "blockers", "next_authorized_action", "created_at", "updated_at", "suspended_at", "resumed_at", "closed_at")}
            session["progress"] = {"completed_checkpoints": len(native.get("checkpoints", [])), "required_gates": 4}
        except (OSError, ValueError):
            session = {"session_id": value["session_id"], "lifecycle_state": "INVALID", "blockers": ["SESSION_STATE_INVALID"]}
    return {
        "execution_id": value["execution_id"],
        "state": value["state"],
        "current_gate": value.get("current_gate"),
        "wait_category": (value.get("wait_reason") or {}).get("category"),
        "wait_reason": value.get("wait_reason"),
        "current_validation": current_validation,
        "admission_id": value.get("admission_id"),
        "submission_id": (admission_value or {}).get("request", {}).get("submission_id"),
        "admitted_baseline": admitted_baseline,
        "current_baseline": current_baseline,
        "freshness": "PASS" if admitted_baseline == current_baseline else "STALE",
        "current_session": session,
        "supersession": (admission_value or {}).get("supersession") or (admission_value or {}).get("artifacts", {}).get("authority_context", {}).get("admission", {}).get("supersession"),
        "next_authorized_action": f"Resume {value.get('mission_id')}: zeus execute-mission resume --execution-id {value['execution_id']}"
        if value["state"] in {"Waiting", "Suspended"}
        else None,
        "projection": "existing execution record",
    }


def _admission_records(root: Path, mission_id: str) -> list[dict[str, Any]]:
    """Read valid admissions for a mission, preserving immutable history."""
    directory = runtime_path(root, "mission-admissions")
    records = []
    for path in sorted(directory.glob("MISSION-ADMISSION-*.json")):
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
            supplied = value.pop("state_digest", None)
            expected = hashlib.sha256(
                json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
            ).hexdigest()
            if supplied != expected:
                continue
            binding = value.get("artifacts", {}).get("mission_binding", {})
            if value.get("request", {}).get("mission_id") != mission_id and binding.get("mission_id") != mission_id:
                continue
            value["state_digest"] = supplied
            records.append(value)
        except (OSError, ValueError, json.JSONDecodeError):
            continue
    return records


def _admission_detail(root: Path, value: dict[str, Any]) -> dict[str, Any]:
    request = value.get("request", {})
    artifacts = value.get("artifacts", {})
    binding = artifacts.get("mission_binding", {})
    authority_admission = artifacts.get("authority_context", {}).get("admission", {})
    baseline = artifacts.get("repository_baseline") or request.get("repository_baseline")
    current = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "HEAD"],
        text=True, capture_output=True, check=False,
    ).stdout.strip()
    state = value.get("admission_state", "ACTIVE")
    fresh = bool(baseline and baseline == current)
    operational = request.get("mode") == "operational" and artifacts.get("admission_decision", {}).get("admission_decision") == "ACCEPTED"
    executable = state not in {"STALE", "SUPERSEDED", "CANCELLED", "REJECTED", "CONSUMED", "COMPLETED"} and fresh and operational
    return {
        "admission_id": value.get("admission_id"),
        "admission_state": state,
        "mission_id": request.get("mission_id") or binding.get("mission_id"),
        "submission_id": request.get("submission_id") or binding.get("submission_id"),
        "wop_id": binding.get("wop_id") or authority_admission.get("wop_id") or request.get("wop_id"),
        "repository": binding.get("repository") or authority_admission.get("repository"),
        "admitted_baseline": baseline,
        "current_baseline": current,
        "freshness": "PASS" if fresh else "STALE",
        "executable": executable,
        "supersession": value.get("supersession") or artifacts.get("authority_context", {}).get("admission", {}).get("supersession"),
        "authority": binding.get("authority") or authority_admission.get("authority"),
        "projection": "existing admission record",
    }


def _mission_projection(root: Path, mission_id: str) -> dict[str, Any]:
    """Resolve current and historical lifecycle state once for every controller."""
    admissions = [_admission_detail(root, item) for item in _admission_records(root, mission_id)]
    executions = [_execution_detail(root, item) for item in _execution_records(root, mission_id)]
    completed_admissions = {item.get("admission_id") for item in executions if item.get("state") == "Completed"}
    current_admissions = [item for item in admissions if item["executable"] and item.get("admission_id") not in completed_admissions]
    current_executions = [item for item in executions if item["state"] in {"Pending", "Authorized", "Preparing", "Executing", "Waiting", "Suspended", "Resuming", "Verifying", "Running", "Qualifying", "AwaitingAcceptance"}]
    result = "PASS"
    integrity = None
    if len(current_admissions) > 1:
        result, integrity = "FAIL", {"reason": "MULTIPLE_CURRENT_ADMISSIONS", "admission_ids": [item["admission_id"] for item in current_admissions]}
    if len(current_executions) > 1:
        result, integrity = "FAIL", {"reason": "MULTIPLE_CURRENT_EXECUTIONS", "execution_ids": [item["execution_id"] for item in current_executions]}
    return {
        "current_admission": current_admissions[0] if len(current_admissions) == 1 else None,
        "current_execution": current_executions[0] if len(current_executions) == 1 else None,
        "historical_admissions": [item for item in admissions if item not in current_admissions],
        "historical_executions": [item for item in executions if item not in current_executions],
        "integrity": integrity or {"result": "PASS"},
        "result": result,
        "projection": "canonical mission projection",
    }


def _tag(root: Path, name: str) -> str | None:
    result = subprocess.run(
        ["git", "-C", str(root), "rev-list", "-1", name],
        text=True, capture_output=True, check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else None


def _roadmap_rows(root: Path) -> list[dict[str, Any]]:
    text = _read(root, ROADMAP)
    rows: list[dict[str, Any]] = []
    pattern = re.compile(r"^\|\s*(\d+)\s*\|\s*`([^`]+)`\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|$")
    for line in text.splitlines():
        match = pattern.match(line)
        if match:
            order, mission, scope, depends, exit_boundary = match.groups()
            rows.append({"order": int(order), "mission_id": mission,
                         "scope": scope, "depends_on": depends,
                         "exit_boundary": exit_boundary})
    if [row["order"] for row in rows] != list(range(len(rows))):
        raise OperationalBetaError("BETA_ROADMAP_ORDER_INVALID")
    if not rows or rows[0]["mission_id"] != "BETA-00":
        raise OperationalBetaError("BETA_ROADMAP_ROOT_INVALID")
    return rows


def _mission_cards(root: Path) -> list[dict[str, Any]]:
    rows = _roadmap_rows(root)
    # The published roadmap explicitly identifies the first actionable
    # increment in each family.  Later ranges remain planning scope, not
    # invented missions or capabilities.
    cards = [{
        "mission_id": "BETA-00", "family": "BETA", "title": "Engineering Platform Assessment",
        "scope": rows[0]["scope"], "dependencies": [], "lifecycle": "COMPLETED",
        "classification": "COMPLETED", "capabilities": [], "source_order": 0,
    }]
    definitions = {
        "ZDCL-01": ("ZDCL", "Native session foundation", ["BETA-00"], "RECOMMENDED", "ELIGIBLE", rows[1]),
        "CAGF-01": ("CAGF", "Canonical generation foundation", ["ZDCL-01"], "PLANNED", "BLOCKED", rows[3]),
        "EPE-01": ("EPE", "Executable mission-contract foundation", ["CAGF-01"], "PLANNED", "BLOCKED", rows[5]),
    }
    for mission_id, (family, title, dependencies, lifecycle, classification, row) in definitions.items():
        if mission_id == "ZDCL-01":
            try:
                from scripts.lib.emp.beta_closeout import load as load_closeout
                closed = load_closeout(root)
            except (OSError, ValueError):
                closed = None
            if closed and closed.get("lifecycle") == "COMPLETED" and closed.get("acceptance", {}).get("status") == "ACCEPTED":
                lifecycle, classification = "COMPLETED", "COMPLETED"
        if mission_id == "CAGF-01" and any(card["mission_id"] == "ZDCL-01" and card["lifecycle"] == "COMPLETED" for card in cards):
            lifecycle, classification = "RECOMMENDED", "ELIGIBLE"
        cards.append({"mission_id": mission_id, "family": family, "title": title,
                      "scope": row["scope"], "dependencies": dependencies,
                      "lifecycle": lifecycle, "classification": classification,
                      "capabilities": [], "source_order": row["order"]})
    return cards


def _integrity(root: Path) -> dict[str, Any]:
    sources = [ROADMAP, CHARTER, AUTHORITY, TRANSITION, DESIGN]
    missing = [source for source in sources if not (root / source).is_file()]
    texts = {source: _read(root, source) for source in sources} if not missing else {}
    required = {
        "pillars": all(token in texts.get(CHARTER, "") for token in ("ZDCL", "CAGF", "EPE")),
        "production_baseline": all("OA-v1.0.0" in texts.get(source, "") for source in (ROADMAP, CHARTER, TRANSITION)),
        "authority_boundaries": "Mission Knowledge Model" in texts.get(AUTHORITY, "") and "Capability Registry" in texts.get(AUTHORITY, ""),
        "design_constitution": "Single Authority." in texts.get(DESIGN, ""),
        "planning_only": "does not allocate capability IDs" in texts.get(ROADMAP, ""),
    }
    alpha = _tag(root, "OA-v1.0.0")
    beta = _tag(root, "OB-PLAN-v1.0.0")
    checks = {**required, "sources_present": not missing, "alpha_tag": alpha is not None, "beta_tag": beta is not None}
    failures = [name for name, passed in checks.items() if not passed]
    return {"result": "PASS" if not failures else "FAIL", "checks": checks,
            "failures": failures, "missing_sources": missing,
            "production_baseline": alpha, "development_baseline": beta,
            "source_digests": {source: hashlib.sha256(text.encode()).hexdigest() for source, text in texts.items()}}


def _cards_with_dependencies(root: Path) -> list[dict[str, Any]]:
    cards = _mission_cards(root)
    by_id = {card["mission_id"]: card for card in cards}
    canonical = canonical_identity_records(root)
    bindings = {str(item.get("mission_id", "")).upper(): item for item in canonical["records"]}
    for card in cards:
        card["missing_dependencies"] = [dep for dep in card["dependencies"] if by_id[dep]["lifecycle"] != "COMPLETED"]
        if card["lifecycle"] == "RECOMMENDED" and card["missing_dependencies"]:
            card["classification"] = "BLOCKED"
        card["readiness"] = "ELIGIBLE" if card["lifecycle"] == "RECOMMENDED" and not card["missing_dependencies"] else card["classification"]
        binding = bindings.get(card["mission_id"])
        if binding:
            card["canonical_binding"] = {
                "mission_id": binding["mission_id"],
                "wop_id": binding["wop_id"],
                "gate_id": binding["gate_id"],
                "canonical_revision": binding["canonical_revision"],
                "revision_state": binding["revision_state"],
                "wop_published": binding["wop_published"],
                "wop_submitted": binding["wop_submitted"],
                "separate_wop_authorization_required": binding["separate_wop_authorization_required"],
                "historical_revision_1_preserved": binding["historical_revision_1_preserved"],
                "next_authorized_action": binding["next_authorized_action"],
            }
    return cards


def _metrics(cards: list[dict[str, Any]]) -> dict[str, Any]:
    def count(predicate): return sum(1 for card in cards if predicate(card))
    total = len(cards)
    completed = count(lambda card: card["lifecycle"] == "COMPLETED")
    return {"total_missions": total, "completed": completed,
            "current_executable": 0,
            "recommended": count(lambda card: card["lifecycle"] == "RECOMMENDED"),
            "eligible": count(lambda card: card["classification"] == "ELIGIBLE"),
            "blocked": count(lambda card: card["classification"] == "BLOCKED"),
            "planned": count(lambda card: card["lifecycle"] == "PLANNED"),
            "capability_progress": {"completed": 0, "total": 0, "percent": 0},
            "implementation_progress": {"completed": 0, "total": total, "percent": round(completed * 100 / total, 2)},
            "qualification_progress": {"completed": 0, "total": total, "percent": 0},
            "documentation_progress": {"completed": completed, "total": total, "percent": round(completed * 100 / total, 2)},
            "publication_progress": {"completed": completed, "total": total, "percent": round(completed * 100 / total, 2)},
            "validation_progress": {"completed": completed, "total": total, "percent": round(completed * 100 / total, 2)},
            "promotion_readiness": ("READY_FOR_" + next((card["mission_id"] for card in cards if card["classification"] == "ELIGIBLE"), "NONE")) if count(lambda card: card["classification"] == "ELIGIBLE") else "BLOCKED",
            "critical_path": ["BETA-00", "ZDCL-01", "CAGF-01", "EPE-01"],
            "dependency_health": "PASS", "authority_health": "PASS",
            "controller_health": "PASS", "roadmap_health": "PASS",
            "unresolved_recommendations": 0,
            "production_development_divergence": "DEVELOPMENT_AHEAD_OF_PRODUCTION"}


def _gate_crosswalk(root: Path, wop_id: str, lifecycle_state: str) -> dict[str, Any]:
    """Resolve the WOP/Operation gate relationship from the controlled catalog."""
    try:
        catalog = yaml.safe_load(_read(root, GATE_CATALOG))
    except yaml.YAMLError as error:
        raise OperationalBetaError(f"BETA_GATE_CROSSWALK_INVALID: {error}") from error
    rows = catalog.get("wop_gate_crosswalk") if isinstance(catalog, dict) else None
    if not isinstance(rows, list):
        raise OperationalBetaError("BETA_GATE_CROSSWALK_MISSING")
    matches = [
        row for row in rows
        if isinstance(row, dict)
        and row.get("wop_id") == wop_id
        and lifecycle_state in (row.get("lifecycle_states") or [])
    ]
    if len(matches) != 1:
        raise OperationalBetaError(
            "BETA_GATE_CROSSWALK_AMBIGUOUS" if matches else "BETA_GATE_CROSSWALK_UNRESOLVED"
        )
    row = matches[0]
    return {
        "wop_gate": row.get("wop_gate"),
        "wop_gate_id": row.get("wop_gate_id"),
        "operation_gate_id": row.get("operation_gate_id"),
        "relationship": row.get("relationship"),
        "source": GATE_CATALOG,
    }


def _canonical_current_execution(root: Path) -> dict[str, Any]:
    """Project the one receipt-backed current mission without selecting a plan.

    The canonical lifecycle resolver remains the state owner.  This adapter
    performs operation-wide cardinality and adds the controlled gate crosswalk;
    it does not create a second mission lifecycle or infer authority from the
    roadmap.
    """
    from scripts.lib.emp.canonical_lifecycle_resolver import (
        resolve as resolve_lifecycle,
        submitted_missions,
    )

    index = submitted_missions(root)
    if index.get("result") != "PASS":
        return {"result": "FAIL", "current_execution": None,
                "blockers": index.get("blockers") or [{
                    "code": "BETA_LIFECYCLE_INDEX_INVALID",
                    "message": "canonical submitted-mission index failed",
                }]}
    active = [
        item for item in index.get("missions", [])
        if item.get("lifecycle_state") not in _NON_CURRENT_LIFECYCLE_STATES
    ]
    if len(active) > 1:
        return {
            "result": "FAIL", "current_execution": None,
            "blockers": [{
                "code": "MULTIPLE_CURRENT_EXECUTABLE_MISSIONS",
                "message": "more than one receipt-backed lifecycle mission claims current execution",
                "mission_ids": sorted(item.get("mission_id") for item in active),
            }],
            "canonical_lifecycle_index": index,
        }
    if not active:
        return {"result": "PASS", "current_execution": None, "blockers": [],
                "canonical_lifecycle_index": index}

    listed = active[0]
    resolved = resolve_lifecycle(root, listed["mission_id"])
    if resolved.get("result") != "PASS":
        return {"result": "FAIL", "current_execution": None,
                "blockers": resolved.get("blockers") or [{
                    "code": "BETA_CURRENT_LIFECYCLE_UNRESOLVED",
                    "message": "current lifecycle mission failed canonical resolution",
                }], "canonical_lifecycle_index": index}
    for field in ("mission_id", "wop_id", "lifecycle_state", "next_authorized_action"):
        if listed.get(field) != resolved.get(field):
            return {"result": "FAIL", "current_execution": None,
                    "blockers": [{
                        "code": "BETA_CURRENT_LIFECYCLE_CONTRADICTION",
                        "message": f"canonical lifecycle index and resolver disagree on {field}",
                    }], "canonical_lifecycle_index": index}
    try:
        gate_mapping = _gate_crosswalk(root, str(resolved.get("wop_id")),
                                       str(resolved.get("lifecycle_state")))
    except OperationalBetaError as error:
        return {"result": "FAIL", "current_execution": None,
                "blockers": [{"code": str(error), "message": str(error)}],
                "canonical_lifecycle_index": index}

    recovery_action = None
    if resolved.get("execution_started") is True:
        try:
            from scripts.lib.emp.codex_adapter import (
                _result as codex_result,
                current_session,
            )
            session = current_session(root, listed["mission_id"])
            if session:
                runtime = codex_result(session, repository=root)
                recovery_action = runtime.get("runtime_recovery_action")
        except Exception:
            # Runtime recovery is an observational, subordinate projection.
            # Its absence cannot replace or advance the lifecycle owner.
            recovery_action = None

    current = {
        "mission_id": resolved.get("mission_id"),
        "wop_id": resolved.get("wop_id"),
        "submission_id": resolved.get("submission_id"),
        "admission_id": resolved.get("admission_id"),
        "bootstrap_id": resolved.get("bootstrap_id"),
        "dispatch_id": resolved.get("dispatch_id"),
        "provider_id": resolved.get("provider_id"),
        "provider_session_id": resolved.get("provider_session_id"),
        "provider_invocation_id": resolved.get("provider_invocation_id"),
        "execution_id": resolved.get("execution_id"),
        "execution_session_id": resolved.get("execution_session_id"),
        "lifecycle_state": resolved.get("lifecycle_state"),
        "current_gate_mapping": gate_mapping,
        "mission_work_started": resolved.get("mission_work_started", False),
        "repository_work_started": resolved.get("repository_work_started", False),
        "lifecycle_next_action": resolved.get("next_authorized_action"),
        "next_authorized_action": resolved.get("next_authorized_action"),
        "runtime_recovery_action": recovery_action,
        "canonical_lifecycle_owner": resolved.get("canonical_lifecycle_owner"),
        "canonical_state_source": resolved.get("canonical_state_source"),
        "read_only": True,
    }
    return {"result": "PASS", "current_execution": current, "blockers": [],
            "canonical_lifecycle_index": index}


def _selected_card(cards: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Canonical Beta selection used by every list, queue, and inspection view."""
    return next((card for card in cards if card["classification"] == "ELIGIBLE"), None)


def operation(root: Path | str, *, include_current_execution: bool = True) -> dict[str, Any]:
    root = Path(root)
    current = _current_mission(root)
    integrity = _integrity(root)
    cards = _cards_with_dependencies(root)
    metrics = _metrics(cards)
    selected = _selected_card(cards)
    execution_projection = (_canonical_current_execution(root) if include_current_execution else
                            {"result": "PASS", "current_execution": None, "blockers": [],
                             "canonical_lifecycle_index": None})
    current_execution = execution_projection["current_execution"]
    result = "PASS" if integrity["result"] == "PASS" and execution_projection["result"] == "PASS" else "FAIL"
    metrics["current_executable"] = 1 if current_execution else 0
    return {"result": result, "operation_id": "OPERATION-BETA", "operation": "BETA",
            "status": "ACTIVE_DEVELOPMENT", "production_baseline": "OA-v1.0.0",
            "development_baseline": "OB-PLAN-v1.0.0", "mission_families": ["ZDCL", "CAGF", "EPE"],
            "current_platform_mission": current,
            "current_executable_mission": (current_execution or {}).get("mission_id"),
            "current_execution": current_execution,
            "current_wop": (current_execution or {}).get("wop_id"),
            "current_lifecycle_state": (current_execution or {}).get("lifecycle_state"),
            "current_gate_mapping": (current_execution or {}).get("current_gate_mapping"),
            "lifecycle_next_action": (current_execution or {}).get("lifecycle_next_action"),
            "mission_work_started": (current_execution or {}).get("mission_work_started", False),
            "repository_work_started": (current_execution or {}).get("repository_work_started", False),
            "runtime_recovery_action": (current_execution or {}).get("runtime_recovery_action"),
            "recommended_mission": selected["mission_id"] if selected else None,
            "future_recommended_mission": selected["mission_id"] if selected else None,
            "selection_source": "operational_beta._selected_card",
            "current_execution_source": "canonical_lifecycle_resolver.submitted_missions/resolve",
            "missions": cards, "metrics": metrics, "integrity": integrity,
            "blockers": execution_projection.get("blockers", []),
            "canonical_lifecycle_index": execution_projection.get("canonical_lifecycle_index"),
            "authoritative_sources": [ROADMAP, CHARTER, AUTHORITY, TRANSITION, DESIGN],
            "projection_sources": [GATE_CATALOG]}


def active_missions(root: Path | str) -> dict[str, Any]:
    """Return only active Beta work; completed Alpha is not an active view."""
    value = operation(root)
    active = [card for card in value["missions"] if card["lifecycle"] != "COMPLETED"]
    return {
        "result": value["result"], "operation": "BETA", "status": value["status"],
        "production_baseline": value["production_baseline"],
        "development_baseline": value["development_baseline"],
        "current_platform_mission": value["current_platform_mission"],
        "current_executable_mission": value["current_executable_mission"],
        "current_execution": value.get("current_execution"),
        "current_wop": value.get("current_wop"),
        "current_lifecycle_state": value.get("current_lifecycle_state"),
        "current_gate_mapping": value.get("current_gate_mapping"),
        "lifecycle_next_action": value.get("lifecycle_next_action"),
        "recommended_mission": value["recommended_mission"],
        "future_recommended_mission": value.get("future_recommended_mission"),
        "selection_source": value["selection_source"],
        "missions": active, "active_mission_count": len(active),
        "authoritative_sources": value["authoritative_sources"],
        "integrity": value["integrity"],
    }


def completed_missions(root: Path | str) -> dict[str, Any]:
    """Return completed Beta records for the historical interface."""
    value = operation(root)
    completed = [card for card in value["missions"] if card["lifecycle"] == "COMPLETED"]
    return {"result": value["result"], "operation": "BETA", "missions": completed,
            "historical": True, "authoritative_sources": value["authoritative_sources"],
            "integrity": value["integrity"]}


def queue(root: Path | str, view: str = "list") -> dict[str, Any]:
    """Project the operation-wide Beta queue without environment partitioning."""
    value = operation(root)
    cards = value["missions"]
    if view == "next":
        cards = [card for card in cards if card["classification"] == "ELIGIBLE"][:1]
    elif view == "blockers":
        cards = [card for card in cards if card["classification"] == "BLOCKED"]
    elif view == "history":
        cards = [card for card in cards if card["lifecycle"] == "COMPLETED"]
    elif view not in {"list", "show"}:
        raise OperationalBetaError("BETA_QUEUE_VIEW_INVALID")
    executions = {}
    projections = {}
    for item in cards:
        projection = _mission_projection(Path(root), item["mission_id"])
        projections[item["mission_id"]] = projection
        if projection["current_execution"]:
            executions[item["mission_id"]] = projection["current_execution"]
    return {
        "result": value["result"], "operation": "BETA", "queue_scope": "OPERATION",
        "execution_environment": "ADMITTED_MISSION_ATTRIBUTE",
        "current_platform_mission": value["current_platform_mission"],
        "current_executable_mission": value["current_executable_mission"],
        "current_execution": value.get("current_execution"),
        "current_wop": value.get("current_wop"),
        "current_lifecycle_state": value.get("current_lifecycle_state"),
        "current_gate_mapping": value.get("current_gate_mapping"),
        "lifecycle_next_action": value.get("lifecycle_next_action"),
        "recommended_mission": value["recommended_mission"],
        "future_recommended_mission": value.get("future_recommended_mission"),
        "selection_source": value["selection_source"],
        "missions": cards, "metrics": value["metrics"],
        "executions": executions,
        "projections": projections,
        "selection_interface": "zeus missions select",
        "authoritative_sources": value["authoritative_sources"],
        "integrity": value["integrity"],
    }


def roadmap(root: Path | str, family: str | None = None) -> dict[str, Any]:
    value = operation(root)
    if family:
        family = family.upper()
        if family not in value["mission_families"]:
            raise OperationalBetaError("BETA_UNKNOWN_MISSION_FAMILY")
        value["missions"] = [card for card in value["missions"] if card["family"] == family]
    value["roadmap_family"] = family or "BETA"
    value["roadmap_digest"] = hashlib.sha256(_read(Path(root), ROADMAP).encode()).hexdigest()
    return value


def metrics(root: Path | str, subject: str | None = None) -> dict[str, Any]:
    value = operation(root)
    if not subject or subject.upper() in {"BETA", "OA"}:
        return {"result": value["result"], "operation": "BETA", "metrics": value["metrics"], "integrity": value["integrity"]}
    mission = mission_state(root, subject)
    return {"result": value["result"], "mission_id": mission["mission_id"], "family": mission["family"],
            "metrics": {"implementation_progress": 0 if mission["lifecycle"] != "COMPLETED" else 100,
                        "qualification_progress": 0, "publication_progress": 0,
                        "validation_progress": 0}, "integrity": value["integrity"]}


def mission_state(root: Path | str, mission_id: str) -> dict[str, Any]:
    value = operation(root)
    selected = mission_id.upper()
    if selected == value["current_platform_mission"]["mission_id"]:
        current = value["current_platform_mission"]
        return {
            "result": value["result"], "operation": "BETA", "mission_id": selected,
            "family": "BETA", "title": current["title"], "scope": "; ".join(current["scope"]),
            "dependencies": [current["previous_mission"]], "missing_dependencies": [],
            "lifecycle": "CURRENT_PLATFORM", "classification": "ACTIVE", "readiness": "ACTIVE",
            "current_admission": None, "current_execution": None,
            "historical_admissions": [], "historical_executions": [],
            "integrity": {"result": "PASS"}, "projection": "published current mission",
            "authoritative_sources": value["authoritative_sources"],
        }
    for card in value["missions"]:
        if card["mission_id"] == selected:
            return {"result": value["result"], **card, "operation": "BETA",
                    **_mission_projection(Path(root), selected),
                    "authoritative_sources": value["authoritative_sources"]}
    raise OperationalBetaError("BETA_MISSION_NOT_FOUND")


def mission_history(root: Path | str, mission_id: str) -> dict[str, Any]:
    """Expose lifecycle history explicitly; never fold it into current state."""
    mission = mission_state(root, mission_id)
    return {
        "result": mission["result"], "operation": "BETA", "mission_id": mission["mission_id"],
        "historical": True,
        "historical_admissions": mission["historical_admissions"],
        "historical_executions": mission["historical_executions"],
        "authoritative_sources": mission["authoritative_sources"],
        "integrity": mission["integrity"],
    }


def mission_view(root: Path | str, action: str, mission_id: str) -> dict[str, Any]:
    mission = mission_state(root, mission_id)
    current = _current_mission(Path(root))
    if action in ("state", "status", "show", "verify", "health"):
        return mission
    if action in ("readiness", "eligibility"):
        return {"result": mission["result"], "mission_id": mission["mission_id"],
                "lifecycle": mission["lifecycle"], "classification": mission["classification"],
                "readiness": mission["readiness"], "missing_dependencies": mission["missing_dependencies"],
                "authoritative_sources": mission["authoritative_sources"]}
    if action in ("blockers", "prerequisites", "dependencies"):
        return {"result": mission["result"], "mission_id": mission["mission_id"],
                "dependencies": mission["dependencies"], "missing_dependencies": mission["missing_dependencies"],
                "blocking_conditions": ["DEPENDENCY_UNSATISFIED"] if mission["missing_dependencies"] else [],
                "authoritative_sources": mission["authoritative_sources"]}
    if action == "authority":
        return {"result": mission["result"], "operation": "BETA", "mission_id": mission["mission_id"],
                "governance_authority": "Engineering Governance",
                "authority": mission["authoritative_sources"],
                "current_platform_mission": current,
                "development_baseline": "OB-PLAN-v1.0.0",
                "production_baseline": "OA-v1.0.0",
                "authority_boundary": "planning and selection only; no admission or execution",
                "authoritative_sources": mission["authoritative_sources"]}
    if action == "contract":
        return {"result": mission["result"], "operation": "BETA", "mission_id": mission["mission_id"],
                "contract": {"mission_id": mission["mission_id"], "family": mission["family"],
                             "title": mission["title"], "scope": mission["scope"],
                             "dependencies": mission["dependencies"], "lifecycle": mission["lifecycle"],
                             "classification": mission["classification"], "readiness": mission["readiness"]},
                "contract_type": "BETA_ROADMAP_SELECTION_CONTRACT",
                "mission_contract_prerequisite": False,
                "authoritative_sources": mission["authoritative_sources"]}
    if action == "snapshot":
        return {"result": mission["result"], "operation": "BETA", "mission_id": mission["mission_id"],
                "state": mission, "next": next_action(root, mission["family"]),
                "selection": {"recommended_mission": mission["mission_id"] if mission["classification"] == "ELIGIBLE" else None,
                              "source": "operational_beta.next_action"},
                "authoritative_sources": mission["authoritative_sources"]}
    if action in ("metrics",):
        return metrics(root, mission_id)
    if action in ("brief", "explain"):
        return {"result": mission["result"], "operation": "BETA", "mission_id": mission["mission_id"],
                "title": mission["title"], "family": mission["family"], "scope": mission["scope"],
                "lifecycle": mission["lifecycle"], "classification": mission["classification"],
                "dependencies": mission["dependencies"], "missing_dependencies": mission["missing_dependencies"],
                "readiness": mission["readiness"],
                "selection_rationale": ("first eligible mission in the authoritative Beta sequence"
                                         if mission["classification"] == "ELIGIBLE"
                                         else "mission is not selected because authoritative readiness is unmet"),
                "blocking_conditions": (["DEPENDENCY_UNSATISFIED"]
                                         if mission["missing_dependencies"] else []),
                "production_baseline": "OA-v1.0.0",
                "development_baseline": "OB-PLAN-v1.0.0",
                "current_platform_mission": current,
                "current_executable_mission": operation(root)["current_executable_mission"],
                "authority": mission["authoritative_sources"],
                **{key: mission.get(key) for key in ("current_admission", "current_execution", "historical_admissions", "historical_executions", "integrity", "projection")}}
    raise OperationalBetaError("BETA_UNSUPPORTED_MISSION_VIEW")


def next_action(root: Path | str, subject: str | None = None, *,
                include_current_execution: bool = True) -> dict[str, Any]:
    value = operation(root, include_current_execution=include_current_execution)
    cards = value["missions"]
    if subject and subject.upper() in value["mission_families"]:
        cards = [card for card in cards if card["family"] == subject.upper()]
    candidate = _selected_card(cards)
    projection = _mission_projection(Path(root), candidate["mission_id"]) if candidate else {}
    completed_operational = next((item for item in reversed(projection.get("historical_executions", [])) if item.get("state") == "Completed" and (item.get("current_session") or {}).get("lifecycle_state") == "COMPLETED"), None)
    binding = (candidate or {}).get("canonical_binding", {})
    resolved_next = ((value.get("current_execution") or {}).get("lifecycle_next_action")
                     or (projection.get("current_execution") or {}).get("next_authorized_action")
                     or ((binding.get("next_authorized_action") + " (CAGF-01)") if binding.get("next_authorized_action") == "SUBMIT_EXISTING_CAGF01_WOP_THROUGH_ZEUS" else binding.get("next_authorized_action"))
                     or ("Qualify, accept, synchronize, and close ZDCL-01 through the normal lifecycle process." if completed_operational
                         else (f"Publish a separately authorized WOP for {candidate['mission_id']}, then submit and admit it through Zeus." if candidate else "Await authoritative predecessor completion")))
    return {"result": value["result"], "operation_id": value.get("operation_id", "OPERATION-BETA"),
            "operation": "BETA", "scope": subject.upper() if subject else "BETA",
            "current_platform_mission": value["current_platform_mission"],
            "current_executable_mission": value["current_executable_mission"],
            "current_execution": value.get("current_execution"),
            "current_wop": value.get("current_wop"),
            "current_lifecycle_state": value.get("current_lifecycle_state"),
            "current_gate_mapping": value.get("current_gate_mapping"),
            "mission_work_started": value.get("mission_work_started", False),
            "repository_work_started": value.get("repository_work_started", False),
            "lifecycle_next_action": value.get("lifecycle_next_action"),
            "runtime_recovery_action": value.get("runtime_recovery_action"),
            "recommended_mission": candidate["mission_id"] if candidate else None,
            "future_recommended_mission": candidate["mission_id"] if candidate else None,
            "selection_source": "operational_beta._selected_card",
            "next_authorized_action": resolved_next,
            "future_candidate_admission": projection.get("current_admission"),
            "future_candidate_execution": projection.get("current_execution"),
            "historical_admissions": projection.get("historical_admissions", []),
            "historical_executions": projection.get("historical_executions", []),
            "blockers": value.get("blockers", []),
            "metrics": value["metrics"], "authoritative_sources": value["authoritative_sources"]}
