"""Read-only mission-centric verification projection for Operational Alpha 01."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

import yaml

from scripts.lib.emp import progressive_oa
from scripts.lib.eos.mission_contract import Resolver


class OA01VerificationError(ValueError):
    """The current OA-01 mission projection cannot be resolved safely."""


def _yaml(path: Path) -> dict[str, Any]:
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as error:
        raise OA01VerificationError(f"cannot load {path}: {error}") from error
    if not isinstance(value, dict):
        raise OA01VerificationError(f"{path} must contain a mapping")
    return value


def _git(root: Path, *arguments: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), *arguments],
        text=True, capture_output=True, check=False,
    )
    if result.returncode:
        raise OA01VerificationError(
            result.stderr.strip() or f"git {' '.join(arguments)} failed"
        )
    return result.stdout.strip()


class OA01MissionVerification:
    """Compose existing authoritative sources without owning their state."""

    def __init__(self, root: Path | str):
        self.root = Path(root).resolve()

    def _registry_item(self, registry_id: str) -> dict[str, Any]:
        registry = _yaml(self.root / "engineering/registry/work-registry.yaml")
        items = registry.get("entities", {}).get("work_items", [])
        matches = [item for item in items if item.get("registry_id") == registry_id]
        if len(matches) != 1:
            raise OA01VerificationError(
                f"Mission Contract registry_id resolved {len(matches)} work items"
            )
        return matches[0]

    def _contract(self) -> tuple[dict[str, Any], dict[str, Any]]:
        resolution = Resolver(self.root).resolve()
        contract = resolution.get("contract")
        if not isinstance(contract, dict):
            raise OA01VerificationError(
                f"active Mission Contract is unavailable: {resolution['resolution']}"
            )
        return resolution, contract

    def _identity(
        self, contract: dict[str, Any], work_item: dict[str, Any]
    ) -> dict[str, Any]:
        wop = _yaml(
            self.root
            / "engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/immutable-wop.yaml"
        )
        return {
            "mission_id": contract["mission_id"],
            "contract_id": contract["contract_id"],
            "work_item_id": work_item["registry_id"],
            "operational_mission_id": work_item.get("mission_id"),
            "progressive_wop_id": wop["wop_id"],
            "progressive_package_id": progressive_oa.PACKAGE,
        }

    @staticmethod
    def _assert_selector(selector: str | None, identity: dict[str, Any]) -> None:
        if selector in (None, "current"):
            return
        if selector not in set(identity.values()):
            raise OA01VerificationError(
                f"mission selector does not identify OA-01: {selector}"
            )

    @staticmethod
    def _blockers(
        resolution: dict[str, Any],
        contract: dict[str, Any],
        state: dict[str, Any],
    ) -> list[str]:
        blockers: list[str] = []
        if resolution["resolution"] != "AUTHORIZED":
            blockers.append(f"GOVERNANCE_{resolution['resolution']}")
        if contract.get("lifecycle") != "active":
            blockers.append(f"MISSION_CONTRACT_{str(contract.get('lifecycle')).upper()}")
        for approval, value in sorted(contract.get("approvals", {}).items()):
            if value != "approved":
                blockers.append(f"APPROVAL_{approval.upper()}_{str(value).upper()}")
        gate_state = state.get("active_gate_state")
        if gate_state in ("IMPLEMENTATION_REQUIRED", "PENDING"):
            blockers.append(f"{state['active_gate']}_{gate_state}")
        elif gate_state == "AWAITING_OPERATOR_VERIFICATION":
            marker = (
                Path(contract["repository"]["root"])
                / progressive_oa.PACKAGE_PATH
                / f"runtime/evidence/{state['active_gate']}/VERIFIED"
            )
            blockers.append(
                f"{state['active_gate']}_OPERATOR_ACCEPTANCE_REQUIRED"
                if marker.is_file()
                else f"{state['active_gate']}_OPERATOR_VERIFICATION_REQUIRED"
            )
        elif gate_state in ("FAILED", "REJECTED", "INTERRUPTED"):
            blockers.append(f"{state['active_gate']}_{gate_state}")
        return sorted(set(blockers))

    def show(self, selector: str | None = None) -> dict[str, Any]:
        resolution, contract = self._contract()
        work_item = self._registry_item(contract["registry_id"])
        identity = self._identity(contract, work_item)
        self._assert_selector(selector, identity)
        state = progressive_oa.next_action(self.root)
        approvals = {
            key: value
            for key, value in sorted(contract.get("approvals", {}).items())
            if value != "approved"
        }
        if state["active_gate"]:
            approvals["active_gate"] = {
                "gate_id": state["active_gate"],
                "requirement": (
                    "operator verification followed by integrity-valid "
                    "explicit operator acceptance"
                ),
                "state": state["active_gate_state"],
            }
        blockers = self._blockers(resolution, contract, state)
        eligible = (
            resolution["resolution"] == "AUTHORIZED"
            and contract.get("lifecycle") == "active"
            and state.get("status") != "STOPPED_FAIL_CLOSED"
            and state.get("active_gate_state")
            not in ("FAILED", "REJECTED", "INTERRUPTED")
        )
        value = {
            "schema_version": 1,
            "current_mission": identity,
            "mission_status": str(work_item["management_state"]).upper(),
            "governance_state": resolution["resolution"],
            "execution_state": state["status"],
            "eligibility": "ELIGIBLE" if eligible else "INELIGIBLE",
            "readiness": "READY" if not blockers else "BLOCKED",
            "blockers": blockers,
            "next_authorized_action": state["next_action"],
            "authority_source": resolution["contract_path"],
            "required_approvals": approvals,
            "mission_contract": {
                "contract_id": contract["contract_id"],
                "lifecycle": contract["lifecycle"],
                "resolution": resolution["resolution"],
                "wop_id": contract["wop"]["id"],
                "wop_locator": contract["wop"]["locator"],
            },
            "progressive_wop": {
                "package_id": state["package_id"],
                "status": state["status"],
                "active_gate": state["active_gate"],
                "active_gate_state": state["active_gate_state"],
                "accepted_gates": state["accepted_gates"],
            },
            "repository": {
                "identity": self.root.name,
                "root": str(Path(_git(self.root, "rev-parse", "--show-toplevel")).resolve()),
                "branch": _git(self.root, "branch", "--show-current"),
                "head": _git(self.root, "rev-parse", "HEAD"),
                "working_tree": (
                    "CLEAN"
                    if not _git(self.root, "status", "--porcelain=v1")
                    else "MODIFIED"
                ),
                "qualified_baseline": contract["repository"]["baseline"],
            },
            "sources": {
                "governance": resolution["contract_path"],
                "project_state": "docs/project/PROJ-0001-PROJECT_STATE.md",
                "work_registry": "engineering/registry/work-registry.yaml",
                "eos_matrix": "engineering/eos/repository-eos-authority.yaml",
                "progressive_state": str(
                    progressive_oa.state_path(self.root).relative_to(self.root)
                ),
            },
        }
        value["projection_digest"] = hashlib.sha256(
            json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        return value

    def command(self, action: str, selector: str | None = None) -> Any:
        value = self.show(selector)
        mission_id = value["current_mission"]["mission_id"]
        if action == "list":
            return [{
                **value["current_mission"],
                "governance_state": value["governance_state"],
                "execution_state": value["execution_state"],
                "eligibility": value["eligibility"],
            }]
        if action == "show":
            return value
        if action == "state":
            return {
                "mission_id": mission_id,
                "governance_state": value["governance_state"],
                "execution_state": value["execution_state"],
                "mission_status": value["mission_status"],
            }
        if action == "readiness":
            return {
                "mission_id": mission_id,
                "readiness": value["readiness"],
                "blockers": value["blockers"],
                "required_approvals": value["required_approvals"],
            }
        if action == "eligibility":
            return {
                "mission_id": mission_id,
                "eligibility": value["eligibility"],
                "blockers": value["blockers"],
            }
        if action == "blockers":
            return {"mission_id": mission_id, "blockers": value["blockers"]}
        if action == "contract":
            return value["mission_contract"]
        if action == "authority":
            return {
                "mission_id": mission_id,
                "governance_state": value["governance_state"],
                "authority_source": value["authority_source"],
                "required_approvals": value["required_approvals"],
            }
        if action == "next":
            return {
                "mission_id": mission_id,
                "next_authorized_action": value["next_authorized_action"],
                "blockers": value["blockers"],
            }
        raise OA01VerificationError(
            f"unsupported mission verification action: {action}"
        )
