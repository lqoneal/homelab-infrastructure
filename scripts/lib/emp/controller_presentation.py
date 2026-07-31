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
