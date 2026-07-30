"""Deterministic, fail-closed discovery of one applicable Mission Contract."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from scripts.lib.eos.mission_contract import MissionContractError, Resolver, load, validate


class MissionContractDiscoveryError(ValueError):
    """No unique, complete, current, authorized contract was discovered."""

    def __init__(self, result: dict[str, Any]):
        self.result = result
        super().__init__(f"{result['resolution']}: {result['reason']}")


def _digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def discover(root: Path | str, mission: str | None = None) -> dict[str, Any]:
    repository = Path(root).resolve()
    resolver = Resolver(repository)
    paths = sorted(resolver.store.glob("*.yaml"), key=lambda item: item.as_posix())
    candidates: list[dict[str, Any]] = []
    malformed: list[str] = []
    for path in paths:
        locator = str(path.relative_to(repository))
        try:
            contract = load(path)
            errors = validate(contract, repository)
        except (OSError, MissionContractError, ValueError) as error:
            malformed.append(f"{locator}: {error}")
            continue
        if mission is not None and contract.get("mission_id") != mission:
            continue
        candidates.append({
            "locator": locator,
            "contract_id": contract.get("contract_id"),
            "mission_id": contract.get("mission_id"),
            "lifecycle": contract.get("lifecycle"),
            "errors": errors,
        })

    resolution = resolver.resolve(mission)
    status = resolution.get("resolution")
    invalid = [item for item in candidates if item["errors"]]
    reason = "exactly one applicable Mission Contract discovered"
    failure = None
    if malformed:
        failure, reason = "MALFORMED", "; ".join(malformed)
    elif invalid:
        joined = "; ".join(
            f"{item['locator']}: {', '.join(item['errors'])}" for item in invalid
        )
        failure = (
            "UNAUTHORIZED" if "approval" in joined.lower()
            else "INCOMPLETE" if "required" in joined.lower()
            else "MALFORMED"
        )
        reason = joined
    elif status == "NO_AUTHORIZED_WORK":
        failure, reason = "MISSING", "no applicable active Mission Contract"
    elif status == "AMBIGUOUS_AUTHORITY":
        failure, reason = "AMBIGUOUS", "multiple applicable active Mission Contracts"
    elif status == "REVOKED_AUTHORITY":
        failure, reason = "REVOKED", "applicable Mission Contract is revoked"
    elif status in ("SUSPENDED_AUTHORITY", "EXPIRED_AUTHORITY"):
        failure, reason = "INACTIVE", f"applicable Mission Contract is {status.lower()}"
    elif status in ("REPOSITORY_MISMATCH", "BRANCH_MISMATCH", "WOP_DIGEST_MISMATCH"):
        failure, reason = "MISMATCHED", status.lower()
    elif status == "BASELINE_MISMATCH":
        failure, reason = "STALE", "Mission Contract baseline is not current"
    elif status in ("INVALID_CONTRACT", "APPROVAL_REQUIRED", "ROLE_ASSIGNMENT_REQUIRED"):
        failure, reason = "UNAUTHORIZED", status.lower()
    elif status != "AUTHORIZED":
        failure, reason = "CONFLICTED", str(status)

    selected = resolution.get("contract")
    value = {
        "schema_version": 1,
        "resolution": failure or "DISCOVERED",
        "discovered": failure is None,
        "applicable_candidate_count": resolution.get("active_count", 0),
        "candidate_count": len(candidates),
        "candidates": candidates,
        "reason": reason,
        "protected_effects_allowed": failure is None,
        "next_authorized_action": "CONTINUE" if failure is None else "STOP_FAIL_CLOSED",
    }
    if failure is None and selected:
        value.update({
            "contract": selected,
            "contract_id": selected["contract_id"],
            "mission_id": selected["mission_id"],
            "contract_path": resolution["contract_path"],
            "contract_sha256": hashlib.sha256(
                (repository / resolution["contract_path"]).read_bytes()
            ).hexdigest(),
        })
    value["discovery_digest"] = _digest(value)
    return value


def require(root: Path | str, mission: str | None = None) -> dict[str, Any]:
    result = discover(root, mission)
    if not result["discovered"]:
        raise MissionContractDiscoveryError(result)
    return result
