"""Read-only authoritative Operational Alpha status resolution.

The superseded Progressive package remains an immutable evidence source.  It
is intentionally not an input to this resolver: current Operational Alpha
state is resolved from the current WOP and its controlled projections.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Mapping

import yaml


class OperationalAlphaStatusError(ValueError):
    """Current Operational Alpha status cannot be resolved safely."""


PROGRESS_PATH = Path("engineering/operations/zeus-operational-alpha-progress.md")
PROJECT_STATE_PATH = Path("docs/project/PROJ-0001-PROJECT_STATE.md")
EMM_PATH = Path("engineering/metadata/operational-alpha-emm.yaml")


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError as error:
        raise OperationalAlphaStatusError(
            f"STATUS_SOURCE_UNAVAILABLE: {path}; "
            "resolution options: restore the controlled source, select a separately "
            "authorized corrective action, or close without changes"
        ) from error


def _progress_values(text: str) -> dict[str, str]:
    values = dict(re.findall(r"^([A-Z0-9_-]+)=([^\n]+)$", text, re.MULTILINE))
    required = (
        "CURRENT_IMPLEMENTATION_WOP",
        "CURRENT_GATE",
        "CURRENT_GATE_STATE",
        "CURRENT_EXECUTION_STATE",
        "SUCCESSOR_ELIGIBILITY",
        "HISTORICAL_PROGRESSIVE_RUNTIME",
    )
    missing = [field for field in required if not values.get(field)]
    if missing:
        raise OperationalAlphaStatusError(
            "STATUS_PROJECTION_INCOMPLETE: " + ", ".join(missing) + "; "
            "resolution options: repair the current controlled projection under a "
            "separately authorized corrective action, or close without changes"
        )
    return values


def _wop(path: Path) -> Mapping[str, object]:
    try:
        value = yaml.safe_load(_read(path))
    except yaml.YAMLError as error:
        raise OperationalAlphaStatusError(
            "STATUS_WOP_INVALID: " + str(error) + "; resolution options: restore "
            "the published WOP, select a separately authorized corrective action, "
            "or close without changes"
        ) from error
    if not isinstance(value, Mapping):
        raise OperationalAlphaStatusError("STATUS_WOP_INVALID: WOP must be a mapping")
    return value


def _artifact_state(root: Path, entity_type: str, wop_id: str) -> str:
    """Read one published artifact state without treating it as authority."""
    if not (root / EMM_PATH).is_file():
        return "ABSENT"
    try:
        emm = yaml.safe_load(_read(root / EMM_PATH))
    except yaml.YAMLError as error:
        raise OperationalAlphaStatusError(f"STATUS_EMM_INVALID: {error}") from error
    entities = emm.get("entities") if isinstance(emm, Mapping) else None
    matches = []
    for item in entities or []:
        if not isinstance(item, Mapping) or item.get("entity_type") != entity_type:
            continue
        source = item.get("source")
        if not isinstance(source, str):
            continue
        value = _wop(root / source)
        binding = value.get("implementation_wop")
        if isinstance(binding, Mapping) and binding.get("wop_id") == wop_id:
            matches.append(item)
    if not matches:
        return "ABSENT"
    if len(matches) != 1:
        raise OperationalAlphaStatusError(f"STATUS_{entity_type.upper()}_AMBIGUOUS")
    source = matches[0].get("source")
    if not isinstance(source, str):
        raise OperationalAlphaStatusError(f"STATUS_{entity_type.upper()}_INVALID")
    value = _wop(root / source)
    return str(value.get("lifecycle_state", "INVALID")).upper()


def _project_lifecycle(text: str) -> tuple[str, str]:
    match = re.search(
        r"Its lifecycle is `(?P<lifecycle>[A-Z_]+)`; execution is "
        r"`(?P<execution>[A-Z_]+)`\.",
        text,
    )
    if not match:
        raise OperationalAlphaStatusError(
            "STATUS_PROJECT_STATE_INCOMPLETE: OA-01 lifecycle statement is missing; "
            "resolution options: repair the current controlled project state under a "
            "separately authorized corrective action, or close without changes"
        )
    return match.group("lifecycle"), match.group("execution")


def resolve(root: Path | str) -> dict[str, object]:
    """Resolve exactly one current OA lifecycle or fail with actionable options."""
    repository = Path(root).resolve()
    progress = _progress_values(_read(repository / PROGRESS_PATH))
    current = progress["CURRENT_IMPLEMENTATION_WOP"]
    if "@" not in current:
        raise OperationalAlphaStatusError("STATUS_WOP_PROJECTION_INVALID")
    current_wop, revision = current.rsplit("@", 1)
    if (repository / EMM_PATH).is_file():
        try:
            from scripts.lib.eos.convergence_runtime import ConvergenceRuntime

            _, wop, _ = ConvergenceRuntime(repository)._wop(current_wop, revision)
        except Exception as error:
            raise OperationalAlphaStatusError(
                "STATUS_LIFECYCLE_TRANSITION_INVALID: " + str(error) + "; "
                "resolution options: restore the exact EMM transition, apply a separately "
                "authorized reconciliation, or close without changes"
            ) from error
    project_lifecycle, project_execution = _project_lifecycle(
        _read(repository / PROJECT_STATE_PATH)
    )

    wop_id = str(wop.get("wop_id", ""))
    revision = str(wop.get("revision", ""))
    lifecycle = str(wop.get("status", "")).upper()
    execution = str((wop.get("lifecycle") or {}).get("execution_state", "")).upper()
    expected_wop = f"{current_wop}@{revision}"
    conflicts: list[str] = []
    if wop_id != current_wop:
        conflicts.append("WOP_IDENTITY")
    if progress["CURRENT_IMPLEMENTATION_WOP"] != expected_wop:
        conflicts.append("WOP_PROJECTION")
    if progress["CURRENT_GATE_STATE"] != lifecycle or project_lifecycle != lifecycle:
        conflicts.append("LIFECYCLE")
    if progress["CURRENT_EXECUTION_STATE"] != execution or project_execution != execution:
        conflicts.append("EXECUTION")
    if progress["HISTORICAL_PROGRESSIVE_RUNTIME"] != "EVIDENCE_ONLY":
        conflicts.append("HISTORICAL_BOUNDARY")
    if conflicts:
        raise OperationalAlphaStatusError(
            "STATUS_RESOLUTION_CONFLICT: " + ", ".join(conflicts) + "; "
            "resolution options: apply a separately authorized reconciliation, "
            "select an alternate corrective action, or close without changes"
        )

    return {
        "schema_version": 1,
        "resolver": "operational-alpha-current-state/1",
        "outcome": "RESOLVED",
        "status": lifecycle,
        "active_gate": progress["CURRENT_GATE"],
        "active_gate_state": lifecycle,
        "execution_state": execution,
        "implementation_wop": {"id": wop_id, "revision": revision},
        "successor_eligibility": progress["SUCCESSOR_ELIGIBILITY"],
        "authority_record": _artifact_state(repository, "AuthorityRecord", wop_id),
        "operational_gate_plan": _artifact_state(repository, "OperationalGatePlan", wop_id),
        "activation": _artifact_state(repository, "ActivationRecord", wop_id),
        "authority_record_creation_eligibility": "ELIGIBLE",
        "historical_progressive_runtime": "EXCLUDED_EVIDENCE_ONLY",
        "authoritative_sources": [
            "EMM-resolved current Implementation WOP", str(PROJECT_STATE_PATH), str(PROGRESS_PATH),
        ] + (["EMM-resolved ImplementationWOPLifecycleTransition"]
             if wop.get("effective_lifecycle_transition") else []),
        "status_resolution_precedence": [
            "current Implementation WOP",
            "controlled Project State",
            "controlled Operational Alpha progress projection",
            "EOS derived projection",
        ],
        "operator_resolution_protocol": {
            "on_block": [
                "preserve system integrity and historical evidence",
                "record diagnosis and blocker classification",
                "present corrective, alternate, or close-without-changes options",
                "resume only after operator direction",
            ]
        },
    }
