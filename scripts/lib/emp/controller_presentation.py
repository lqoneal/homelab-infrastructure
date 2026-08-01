"""Shared operator, verification, and structured controller presentation."""
from __future__ import annotations

import json
from typing import Any


def operator_text(value: Any, title: str | None = None) -> str:
    """Render a concise operator view without changing the source value."""
    if not isinstance(value, dict):
        return f"{title + ': ' if title else ''}{value}\n"
    lines = []
    if title:
        lines.extend([title, "-" * len(title)])
    if title == "Capability list":
        capabilities = value.get("capabilities", [])
        if value.get("registry_id") and not capabilities:
            raise ValueError("non-empty capability registry produced zero rendered rows")
        lines.extend([
            "",
            "ID                Lifecycle    Availability   Regression   Mission   Name",
        ])
        for item in capabilities:
            lines.append(
                f"{item['capability_id']:<18} {item['lifecycle']:<12} "
                f"{item['runtime_availability']:<14} {item['regression_status']:<12} "
                f"{item['mission_introduced']:<9} {item['name']}"
            )
        operational = sum(item.get("lifecycle") == "Operational" for item in capabilities)
        unavailable = sum(item.get("runtime_availability") != "AVAILABLE" for item in capabilities)
        lines.extend([
            "",
            "Summary",
            "-------",
            f"Registered capabilities : {len(capabilities)}",
            f"Operational             : {operational}",
            f"Unavailable             : {unavailable}",
            f"Registry revision       : {value.get('revision')}",
            "Registry verification   : PASS",
        ])
        return "\n".join(lines) + "\n"
    if "mission_title" in value:
        lines.extend([
            f"Mission title                 : {value['mission_title']}",
            f"Engineering objective        : {value.get('engineering_objective', '')}",
            f"Purpose                      : {value.get('purpose', '')}",
            f"Operational problem solved   : {value.get('operational_problem_solved', '')}",
            f"Engineering value            : {value.get('engineering_value', '')}",
            f"Operational outcome          : {value.get('operational_outcome_after_acceptance', '')}",
            f"Capabilities introduced     : {', '.join(value.get('capabilities_introduced', []))}",
            f"Outcome capabilities        : {', '.join(value.get('outcome_capabilities', []))}",
            f"Operational Alpha progress   : Mission {value.get('operational_alpha_progress', {}).get('mission_number')} of {value.get('operational_alpha_progress', {}).get('total_missions')}",
            f"Zeus capability delta        : {value.get('zeus_capability_delta', {}).get('description', '')}",
            f"Prerequisites                : {json.dumps(value.get('prerequisites', {}), sort_keys=True)}",
            f"Completion criteria          : {', '.join(value.get('completion_criteria', []))}",
            f"Expected evidence            : {', '.join(value.get('expected_qualification_evidence', []))}",
            f"Verification commands        : {', '.join(value.get('verification_commands', []))}",
            f"Risks mitigated              : {', '.join(value.get('risks_mitigated', []))}",
            f"Required operator authorization: {value.get('required_operator_authorization', '')}",
            f"Controlled references        : {', '.join(value.get('references', []))}",
        ])
        return "\n".join(lines) + "\n"
    for key in ("result", "mission_id", "classification", "lifecycle", "recommended_mission",
                "roadmap_id", "roadmap_revision", "mission_knowledge_revision", "status"):
        if key in value and not isinstance(value[key], (dict, list)):
            lines.append(f"{key.replace('_', ' ').title():28}: {value[key]}")
    if "provenance_verification" in value:
        verification = value["provenance_verification"]
        lines.append(f"{'Provenance verification':28}: {verification.get('result', 'UNKNOWN')}")
    if "blocking_conditions" in value:
        blockers = value["blocking_conditions"]
        lines.append(f"{'Blockers':28}: {', '.join(blockers) if blockers else 'none'}")
    if "missing_capabilities" in value:
        missing = value["missing_capabilities"]
        lines.append(f"{'Missing capabilities':28}: {', '.join(missing) if missing else 'none'}")
    if "missing_outcome_capabilities" in value:
        missing_outcomes = value["missing_outcome_capabilities"]
        lines.append(f"{'Missing outcome capabilities':28}: {', '.join(missing_outcomes) if missing_outcomes else 'none'}")
    missions = value.get("missions")
    if isinstance(missions, list):
        lines.extend(["", "Mission roadmap", "---------------"])
        for item in missions:
            marker = "*" if item.get("recommendation") else " "
            lines.append(f"{marker} {item.get('mission_id', '?'):5} {item.get('lifecycle', '?'):11} {item.get('classification', '?')}")
    if not lines:
        lines.append("No operator summary available")
    return "\n".join(lines) + "\n"


def emit(value: Any, *, json_mode: bool = False, verify: bool = False, title: str | None = None) -> None:
    """Use one value for all modes; only explicit modes emit structured data."""
    if json_mode or verify:
        print(json.dumps(value, sort_keys=True))
    else:
        print(operator_text(value, title=title), end="")
