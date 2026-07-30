"""Deterministic, observational resolution of one executable mission."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any, Mapping

import yaml

from scripts.lib.emp import progressive_oa
from scripts.lib.emp.controlled_mission_authority import ControlledMissionAuthority
from scripts.lib.emp.mission_contract_discovery import require as require_discovery


class MissionResolutionError(ValueError):
    """Mission resolution failed before any protected effect."""

    def __init__(self, result: dict[str, Any]):
        self.result = result
        super().__init__(f"{result['resolution']}: {result['reason']}")


def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _yaml(path: Path) -> dict[str, Any]:
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as error:
        raise ValueError(f"{path}: {error}") from error
    if not isinstance(value, dict):
        raise ValueError(f"{path}: mapping required")
    return value


def _denied(state: str, reason: str, checks: list[dict[str, str]]) -> dict[str, Any]:
    value = {
        "schema_version": 1,
        "resolution": state,
        "resolved": False,
        "reason": reason,
        "checks": checks,
        "protected_effects_allowed": False,
        "execution_agent_dispatched": False,
        "mission_executed": False,
        "next_authorized_action": "STOP_FAIL_CLOSED",
    }
    value["resolution_digest"] = _digest(value)
    return value


def resolve(
    root: Path | str,
    *,
    candidates: list[Mapping[str, Any]] | None = None,
    sources: Mapping[str, Path | str | None] | None = None,
    observed: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    repository = Path(root).resolve()
    checks: list[dict[str, str]] = []

    def passed(name: str, detail: str) -> None:
        checks.append({"check": name, "result": "PASS", "detail": detail})

    def fail(state: str, reason: str) -> dict[str, Any]:
        checks.append({"check": "mission_resolution", "result": "FAIL", "detail": reason})
        return _denied(state, reason, checks)

    try:
        authority = ControlledMissionAuthority(
            repository, expected_gate="OA-04", observed=observed
        ).require(boundary="oa04_mission_resolution")
        discovery = require_discovery(repository)
    except ValueError as error:
        return fail("STALE_AUTHORITY", str(error))
    if discovery["contract_id"] != authority["contract_id"]:
        return fail("CONTRACT_CHANGED", "discovery and authority contract identities differ")
    passed("mission_contract", discovery["contract_id"])

    configured = dict(sources or {})
    registry_path = Path(configured.get(
        "registry", repository / "engineering/registry/work-registry.yaml"
    ))
    try:
        registry = _yaml(registry_path)
    except ValueError as error:
        return fail("RECONCILIATION_FAILED", str(error))
    eligible = list(candidates) if candidates is not None else [
        item for item in registry.get("entities", {}).get("work_items", [])
        if item.get("registry_id") == discovery["contract"].get("registry_id")
        and str(item.get("management_state", "")).lower() == "active"
    ]
    if not eligible:
        return fail("ZERO_ELIGIBLE_MISSIONS", "no executable mission is eligible")
    if len(eligible) != 1:
        return fail("MULTIPLE_ELIGIBLE_MISSIONS", "multiple executable missions are eligible")
    mission = dict(eligible[0])
    required_mission = ("registry_id", "mission_id", "phase_id", "management_state")
    if any(not mission.get(key) for key in required_mission):
        return fail("INCOMPLETE_MISSION", "executable mission identity is incomplete")
    passed("executable_mission", str(mission["registry_id"]))

    wop_binding = discovery["contract"].get("wop", {})
    wop_path = Path(configured.get("wop", repository / str(wop_binding.get("locator", ""))))
    try:
        wop = _yaml(wop_path)
    except ValueError as error:
        return fail("WOP_BINDING_CHANGED", str(error))
    if (
        wop_binding.get("id") != progressive_oa.PACKAGE
        or wop_binding.get("digest") != _sha256(wop_path)
        or wop.get("wop_id") != authority["wop_id"]
        or wop.get("work_item_id") != mission["registry_id"]
        or wop.get("status") != "Active"
    ):
        return fail("WOP_BINDING_CHANGED", "executable WOP binding mismatch")
    passed("executable_wop", str(wop["wop_id"]))

    interface_path = Path(configured.get(
        "execution_interface",
        repository / "engineering/execution/execution-interface.yaml",
    ))
    try:
        interface = _yaml(interface_path)
    except ValueError as error:
        return fail("EXECUTION_INTERFACE_CHANGED", str(error))
    if (
        interface.get("interface_id") != "ENGINEERING-EXECUTION-INTERFACE"
        or interface.get("schema_version") != 2
        or not interface.get("routes", {}).get("controller")
        or not interface.get("semantic_bindings")
    ):
        return fail("EXECUTION_INTERFACE_CHANGED", "execution definition is incomplete")
    passed("execution_definition", str(interface["interface_id"]))

    admission_path = repository / authority["package_admission_receipt"]
    chain = [
        {"type": "mission_contract", "identity": discovery["contract_id"],
         "locator": discovery["contract_path"], "digest": discovery["contract_sha256"]},
        {"type": "wop", "identity": wop["wop_id"],
         "locator": str(wop_path.relative_to(repository)), "digest": _sha256(wop_path)},
        {"type": "admission", "identity": progressive_oa.PACKAGE,
         "locator": str(admission_path.relative_to(repository)), "digest": _sha256(admission_path)},
        {"type": "acceptance_chain", "identity": "OA-01..OA-03",
         "digest": _digest(authority["prior_acceptance_receipts"])},
    ]
    if len(chain) != 4 or any(not item.get("identity") or not item.get("digest") for item in chain):
        return fail("AUTHORITY_CHAIN_CHANGED", "authority chain is incomplete")
    passed("authority_chain", "Mission Contract -> WOP -> admission -> OA-01..OA-03")

    reconciliation = subprocess.run(
        [str(repository / "scripts/engctl"), "eos", "sync-validate"],
        cwd=repository, text=True, capture_output=True, check=False,
    )
    if reconciliation.returncode:
        return fail("RECONCILIATION_FAILED", reconciliation.stderr or reconciliation.stdout)
    passed("reconciliation", "repository and EOS synchronized")

    value = {
        "schema_version": 1,
        "resolution": "RESOLVED",
        "resolved": True,
        "reason": "exactly one executable mission resolution is complete",
        "mission": {
            "registry_id": mission["registry_id"],
            "mission_id": mission["mission_id"],
            "phase_id": mission["phase_id"],
            "management_state": mission["management_state"],
        },
        "wop": {
            "wop_id": wop["wop_id"],
            "locator": str(wop_path.relative_to(repository)),
            "digest": _sha256(wop_path),
        },
        "execution_definition": {
            "interface_id": interface["interface_id"],
            "schema_version": interface["schema_version"],
            "locator": str(interface_path.relative_to(repository)),
            "digest": _sha256(interface_path),
            "controller": interface["routes"]["controller"],
        },
        "authority_chain": chain,
        "authority_digest": authority["authority_digest"],
        "discovery_digest": discovery["discovery_digest"],
        "contract_id": discovery["contract_id"],
        "repository_identity": authority["repository_identity"],
        "branch": authority["branch"],
        "head": authority["head"],
        "qualified_baseline": authority["qualified_baseline"],
        "checks": checks,
        "protected_effects_allowed": True,
        "execution_agent_dispatched": False,
        "mission_executed": False,
        "next_authorized_action": "CONTINUE_OBSERVATIONAL_QUALIFICATION",
    }
    value["resolution_digest"] = _digest(value)
    return value


def require(root: Path | str, **kwargs: Any) -> dict[str, Any]:
    result = resolve(root, **kwargs)
    if not result["resolved"]:
        raise MissionResolutionError(result)
    return result
