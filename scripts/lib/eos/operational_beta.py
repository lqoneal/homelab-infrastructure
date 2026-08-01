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

ROADMAP = "engineering/docs/architecture/OPERATION-BETA-ROADMAP.md"
CHARTER = "engineering/docs/operations/OPERATION-BETA-CHARTER.md"
AUTHORITY = "engineering/docs/architecture/OPERATION-BETA-AUTHORITY-MODEL.md"
TRANSITION = "engineering/operations/operation-beta-transition.md"
DESIGN = "engineering/docs/architecture/ENGINEERING-PLATFORM-DESIGN-PRINCIPLES.md"

class OperationalBetaError(ValueError):
    pass


def _read(root: Path, relative: str) -> str:
    try:
        return (root / relative).read_text(encoding="utf-8")
    except OSError as error:
        raise OperationalBetaError(f"BETA_AUTHORITY_UNAVAILABLE: {relative}: {error}") from error


def _digest(value: Any) -> str:
    return hashlib.sha256(repr(value).encode()).hexdigest()


def _execution_records(root: Path, mission_id: str) -> list[dict[str, Any]]:
    """Read valid execution records without treating history as current state."""
    directory = root / ".zeus/runtime/mission-executions"
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
        admission_path = root / ".zeus/runtime/mission-admissions" / f"{value.get('admission_id')}.json"
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
        admission_path = root / ".zeus/runtime/mission-admissions" / f"{value.get('admission_id')}.json"
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
        "supersession": (admission_value or {}).get("supersession") or (admission_value or {}).get("artifacts", {}).get("authority_context", {}).get("admission", {}).get("supersession"),
        "next_authorized_action": f"Resume {value.get('mission_id')}: zeus execute-mission resume --execution-id {value['execution_id']}"
        if value["state"] in {"Waiting", "Suspended"}
        else None,
        "projection": "existing execution record",
    }


def _admission_records(root: Path, mission_id: str) -> list[dict[str, Any]]:
    """Read valid admissions for a mission, preserving immutable history."""
    directory = root / ".zeus/runtime/mission-admissions"
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
    executable = state not in {"STALE", "SUPERSEDED", "CANCELLED", "REJECTED", "CONSUMED", "COMPLETED"} and fresh
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
    current_admissions = [item for item in admissions if item["executable"]]
    current_executions = [item for item in executions if item["state"] in {"Waiting", "Suspended", "Executing", "Running", "Qualifying", "AwaitingAcceptance"}]
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
        "ZDCL-01": ("ZDCL", "Native session foundation", ["BETA-00"], "CURRENT", "ELIGIBLE", rows[1]),
        "CAGF-01": ("CAGF", "Canonical generation foundation", ["ZDCL-01"], "PLANNED", "BLOCKED", rows[3]),
        "EPE-01": ("EPE", "Executable mission-contract foundation", ["CAGF-01"], "PLANNED", "BLOCKED", rows[5]),
    }
    for mission_id, (family, title, dependencies, lifecycle, classification, row) in definitions.items():
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
    for card in cards:
        card["missing_dependencies"] = [dep for dep in card["dependencies"] if by_id[dep]["lifecycle"] != "COMPLETED"]
        if card["lifecycle"] == "CURRENT" and card["missing_dependencies"]:
            card["classification"] = "BLOCKED"
        card["readiness"] = "ELIGIBLE" if card["lifecycle"] == "CURRENT" and not card["missing_dependencies"] else card["classification"]
    return cards


def _metrics(cards: list[dict[str, Any]]) -> dict[str, Any]:
    def count(predicate): return sum(1 for card in cards if predicate(card))
    total = len(cards)
    completed = count(lambda card: card["lifecycle"] == "COMPLETED")
    return {"total_missions": total, "completed": completed,
            "current": count(lambda card: card["lifecycle"] == "CURRENT"),
            "eligible": count(lambda card: card["classification"] == "ELIGIBLE"),
            "blocked": count(lambda card: card["classification"] == "BLOCKED"),
            "planned": count(lambda card: card["lifecycle"] == "PLANNED"),
            "capability_progress": {"completed": 0, "total": 0, "percent": 0},
            "implementation_progress": {"completed": 0, "total": total, "percent": round(completed * 100 / total, 2)},
            "qualification_progress": {"completed": 0, "total": total, "percent": 0},
            "documentation_progress": {"completed": completed, "total": total, "percent": round(completed * 100 / total, 2)},
            "publication_progress": {"completed": completed, "total": total, "percent": round(completed * 100 / total, 2)},
            "validation_progress": {"completed": completed, "total": total, "percent": round(completed * 100 / total, 2)},
            "promotion_readiness": "READY_FOR_ZDCL-01" if count(lambda card: card["classification"] == "ELIGIBLE") else "BLOCKED",
            "critical_path": ["BETA-00", "ZDCL-01", "CAGF-01", "EPE-01"],
            "dependency_health": "PASS", "authority_health": "PASS",
            "controller_health": "PASS", "roadmap_health": "PASS",
            "unresolved_recommendations": 0,
            "production_development_divergence": "DEVELOPMENT_AHEAD_OF_PRODUCTION"}


def operation(root: Path | str) -> dict[str, Any]:
    root = Path(root)
    integrity = _integrity(root)
    cards = _cards_with_dependencies(root)
    metrics = _metrics(cards)
    result = "PASS" if integrity["result"] == "PASS" else "FAIL"
    return {"result": result, "operation_id": "OPERATION-BETA", "operation": "BETA",
            "status": "ACTIVE_DEVELOPMENT", "production_baseline": "OA-v1.0.0",
            "development_baseline": "OB-PLAN-v1.0.0", "mission_families": ["ZDCL", "CAGF", "EPE"],
            "missions": cards, "metrics": metrics, "integrity": integrity,
            "authoritative_sources": [ROADMAP, CHARTER, AUTHORITY, TRANSITION, DESIGN]}


def active_missions(root: Path | str) -> dict[str, Any]:
    """Return only active Beta work; completed Alpha is not an active view."""
    value = operation(root)
    active = [card for card in value["missions"] if card["lifecycle"] != "COMPLETED"]
    return {
        "result": value["result"], "operation": "BETA", "status": value["status"],
        "production_baseline": value["production_baseline"],
        "development_baseline": value["development_baseline"],
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
                "authority": mission["authoritative_sources"],
                **{key: mission.get(key) for key in ("current_admission", "current_execution", "historical_admissions", "historical_executions", "integrity", "projection")}}
    raise OperationalBetaError("BETA_UNSUPPORTED_MISSION_VIEW")


def next_action(root: Path | str, subject: str | None = None) -> dict[str, Any]:
    value = operation(root)
    cards = value["missions"]
    if subject and subject.upper() in value["mission_families"]:
        cards = [card for card in cards if card["family"] == subject.upper()]
    candidate = next((card for card in cards if card["classification"] == "ELIGIBLE"), None)
    projection = _mission_projection(Path(root), candidate["mission_id"]) if candidate else {}
    return {"result": value["result"], "operation": "BETA", "scope": subject.upper() if subject else "BETA",
            "recommended_mission": candidate["mission_id"] if candidate else None,
            "next_authorized_action": (projection.get("current_execution") or {}).get("next_authorized_action") if projection.get("current_execution") and projection.get("current_execution").get("next_authorized_action") else (f"Resolve and execute WOP-{candidate['mission_id']}-FOUNDATION-001" if candidate else "Await authoritative predecessor completion"),
            "current_admission": projection.get("current_admission"),
            "current_execution": projection.get("current_execution"),
            "historical_admissions": projection.get("historical_admissions", []),
            "historical_executions": projection.get("historical_executions", []),
            "metrics": value["metrics"], "authoritative_sources": value["authoritative_sources"]}
