"""Publication-gated reconciliation from a Development WOP to a Beta mission.

Stage 1 remains authoritative for the submitted transaction.  This module only
derives a target-mission linkage and prepares canonical projections after an
explicit publication boundary has been satisfied.  It never submits a WOP or
executes the target mission.
"""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
import shutil
import tempfile
from copy import deepcopy
from pathlib import Path
from typing import Any, Mapping

import yaml

from scripts.lib.emp.runtime_paths import runtime_root

TARGET_WOP = "WOP-ZEUS-STOPQ01-CANONICAL-MISSION-PUBLICATION-001"
TARGET_MISSION = "STOPQ-01"
REGISTRY_ID = "EMP-WORK-BETA-STOPQ-01"
CONTRACT_ID = "MC-STOPQ-01"


class CanonicalMissionLifecycleError(ValueError):
    pass


def _digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _atomic(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(name)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def derive_linkage(metadata: Mapping[str, Any], package_path: Path | str, *, package_digest: str | None = None) -> dict[str, Any] | None:
    """Resolve explicit target metadata, with one sealed legacy migration."""
    wop_id = str(metadata.get("wop_id", ""))
    target = metadata.get("target_mission")
    if not isinstance(target, Mapping) and metadata.get("target_mission_id"):
        target = {
            key: metadata.get(key) for key in (
                "target_operation", "target_mission_id", "target_mission_class",
                "target_mission_contract_locator", "target_registry_locator",
                "target_package_locator", "activation_policy",
                "publication_approval_policy",
            ) if metadata.get(key) not in (None, "")
        }
    if not isinstance(target, Mapping) and wop_id != TARGET_WOP:
        return None
    if wop_id == TARGET_WOP and not isinstance(target, Mapping):
        target = {"target_operation": "BETA", "target_mission_id": TARGET_MISSION,
                  "target_mission_class": "disposable-operational-qualification"}
    target = dict(target or {})
    mission = str(target.get("target_mission_id", "")).strip().upper()
    operation = str(target.get("target_operation", "")).strip().upper()
    if operation != "BETA" or not mission:
        raise CanonicalMissionLifecycleError("TARGET_MISSION_METADATA_INVALID")
    locator = str(package_path)
    return {
        "schema_version": 1,
        "target_operation": operation,
        "target_mission_id": mission,
        "target_mission_class": target.get("target_mission_class", "canonical-operational-mission"),
        "target_mission_contract_locator": target.get("target_mission_contract_locator", f"engineering/mission-contracts/candidates/{CONTRACT_ID}.yaml"),
        "target_registry_locator": target.get("target_registry_locator", f"engineering/registry/work-registry.yaml#{REGISTRY_ID}"),
        "target_package_locator": target.get("target_package_locator", "engineering/operational-packages/STOPQ-01/mission.yaml"),
        "development_package_locator": locator,
        "development_package_digest": package_digest,
        "activation_policy": target.get("activation_policy", "publication-triggered"),
        "publication_approval_policy": target.get("publication_approval_policy", "operator-required"),
        "linkage_state": "DERIVED_PREPUBLICATION",
    }


def _stage1_candidates(root: Path, transaction_id: str | None = None) -> list[dict[str, Any]]:
    result = []
    try:
        runtime = runtime_root(root)
    except Exception:
        return result
    for path in sorted((runtime / "stage1" / "missions").glob("*.json")):
        try:
            value = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        if transaction_id and value.get("instance_id") != transaction_id:
            continue
        if value.get("wop_id") == TARGET_WOP or value.get("canonical_mission_linkage"):
            result.append(value)
    return result


def discover(root: Path | str, mission: str = TARGET_MISSION) -> dict[str, Any]:
    """Read-only exact-cardinality discovery; prepublication is not active."""
    repository = Path(root).resolve()
    mission = mission.upper()
    from scripts.lib.emp.mission_contract_discovery import discover as discover_contracts
    contracts = discover_contracts(repository, mission)
    package = repository / "engineering/operational-packages" / mission / "mission.yaml"
    registry = yaml.safe_load((repository / "engineering/registry/work-registry.yaml").read_text())
    matches = [item for item in (registry.get("entities", {}).get("work_items", []) or []) if item.get("registry_id") == REGISTRY_ID]
    active = contracts.get("discovered") and contracts.get("applicable_candidate_count") == 1
    if not active:
        return {"result": "BLOCKED", "resolution": contracts.get("resolution", "MISSING"),
                "mission_id": mission, "mission_contract_count": contracts.get("applicable_candidate_count", 0),
                "registry_count": len(matches), "package_exists": package.is_file(),
                "next_authorized_action": "Publish the qualified candidate, synchronize EOS, then activate the canonical Mission Contract.",
                "discovery_digest": _digest({"mission": mission, "contracts": contracts, "registry": len(matches)})}
    if len(matches) != 1 or not package.is_file():
        return {"result": "BLOCKED", "resolution": "CANONICAL_BINDING_INCOMPLETE", "mission_id": mission,
                "mission_contract_count": contracts.get("applicable_candidate_count", 0), "registry_count": len(matches),
                "package_exists": package.is_file(), "next_authorized_action": "Reconcile exactly one registry entry and authoritative package binding."}
    return {"result": "PASS", "resolution": "DISCOVERED", "mission_id": mission,
            "mission_contract_count": 1, "registry_count": 1, "package_locator": str(package.relative_to(repository)),
            "contract_id": contracts.get("contract_id"), "contract_locator": contracts.get("contract_path"),
            "next_authorized_action": "Continue through the canonical mission workflow.",
            "discovery_digest": _digest({"mission": mission, "contract": contracts.get("contract_id"), "package": _sha(package)})}


def view(root: Path | str, action: str, mission: str = TARGET_MISSION) -> dict[str, Any]:
    repository = Path(root).resolve()
    candidates = _stage1_candidates(repository)
    target = [item for item in candidates if item.get("wop_id") == TARGET_WOP]
    linkage = None
    transaction = None
    if len(target) == 1:
        transaction = target[0]
        linkage = transaction.get("canonical_mission_linkage") or derive_linkage(transaction, transaction.get("package", ""), package_digest=transaction.get("package_digest"))
    elif len(target) > 1:
        return {"result": "BLOCKED", "resolution": "AMBIGUOUS_DEVELOPMENT_TRANSACTION", "mission_id": mission}
    discovery = discover(repository, mission)
    return {"result": "PASS" if discovery.get("result") == "PASS" else "BLOCKED", "action": action,
            "mission_id": mission, "development_transaction": transaction.get("instance_id") if transaction else None,
            "development_admission": ((transaction or {}).get("receipts") or {}).get("admission", {}).get("admission_id"),
            "development_state": (transaction or {}).get("state"), "target_linkage": linkage,
            "canonical_discovery": discovery, "next_authorized_action": discovery.get("next_authorized_action")}


def activate(root: Path | str, transaction: Mapping[str, Any], *, publication_approved: bool, eos_synchronized: bool, platform_validated: bool, fault_after: str | None = None) -> dict[str, Any]:
    """Atomically activate candidate projections; all gates are mandatory."""
    repository = Path(root).resolve()
    if not (publication_approved and eos_synchronized and platform_validated):
        raise CanonicalMissionLifecycleError("PUBLICATION_BOUNDARY_NOT_SATISFIED")
    linkage = transaction.get("canonical_mission_linkage") or derive_linkage(transaction, transaction.get("package", ""), package_digest=transaction.get("package_digest"))
    if not linkage or linkage.get("target_mission_id") != TARGET_MISSION:
        raise CanonicalMissionLifecycleError("TARGET_MISSION_LINKAGE_UNRESOLVED")
    package = repository / "engineering/operational-packages/STOPQ-01/mission.yaml"
    if not package.is_file():
        raise CanonicalMissionLifecycleError("AUTHORITATIVE_OPERATIONAL_PACKAGE_MISSING")
    contract_path = repository / "engineering/mission-contracts/contracts" / f"{CONTRACT_ID}.yaml"
    candidate_path = repository / linkage["target_mission_contract_locator"]
    if not candidate_path.is_file():
        raise CanonicalMissionLifecycleError("MISSION_CONTRACT_CANDIDATE_MISSING")
    registry_path = repository / "engineering/registry/work-registry.yaml"
    registry = yaml.safe_load(registry_path.read_text())
    work = registry.setdefault("entities", {}).setdefault("work_items", [])
    existing = [item for item in work if item.get("registry_id") == REGISTRY_ID]
    if len(existing) > 1:
        raise CanonicalMissionLifecycleError("DUPLICATE_TARGET_REGISTRY_ENTRY")
    if contract_path.exists() and yaml.safe_load(contract_path.read_text()).get("lifecycle") == "active":
        if len(existing) == 1 and existing[0].get("management_state") == "active":
            return {"result": "PASS", "resolution": "IDEMPOTENT_REPLAY", "contract_id": CONTRACT_ID, "registry_id": REGISTRY_ID}
        raise CanonicalMissionLifecycleError("PARTIAL_CANONICAL_ACTIVATION")
    contract = yaml.safe_load(candidate_path.read_text())
    contract["lifecycle"] = "active"
    contract["approvals"]["activation"] = "approved"
    contract["activation"] = {"actor": "Zeus publication reconciler", "record": "publication-approval", "transaction": f"TX-ACTIVATE-{TARGET_MISSION}"}
    contract["contract_digest"] = _digest({k: v for k, v in contract.items() if k != "contract_digest"})
    item = {"registry_id": REGISTRY_ID, "object_type": "WorkItem", "title": "STOPQ-01 Disposable Operational Qualification", "management_state": "active", "owner": "Engineering Governance", "scope": TARGET_MISSION, "authority_reference": "Engineering Governance", "source_records": [transaction.get("wop_id", TARGET_WOP)], "relationships": [{"type": "represented_by", "target": CONTRACT_ID}], "created_at": "publication", "updated_at": "publication", "revision": 1, "transition_history": [{"from": None, "to": "active", "at": "publication", "actor": "Zeus publication reconciler", "reason": "Canonical mission publication activation", "authority_reference": "publication-approval"}], "project_id": "EMP-PROJECT-HOMELAB", "order": 1000, "mission_id": "EMP-MISSION-OPERATION-BETA-BETA-04", "phase_id": None, "sprint_id": None, "work_type": "disposable-operational-qualification", "priority": 0, "completion_criteria": "STOPQ-01 qualification evidence complete", "queue_ids": []}
    registry["revision"] = int(registry.get("revision", 0)) + 1
    registry.setdefault("mutation_history", []).append({"revision": registry["revision"], "previous_revision": registry["revision"] - 1, "at": "publication", "actor": "Zeus publication reconciler", "action": "activate STOPQ-01", "reason": "Publication-triggered canonical mission reconciliation"})
    if not existing:
        work.append(item)
    transaction_dir = repository / "engineering/mission-contracts/transactions"
    lock_path = transaction_dir / ".canonical-mission.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    journal_path = transaction_dir / f"TX-ACTIVATE-{TARGET_MISSION}.json"
    writes = {contract_path: yaml.safe_dump(contract, sort_keys=True).encode(), registry_path: yaml.safe_dump(registry, sort_keys=False).encode(), journal_path: b""}
    before = {str(path): path.read_bytes() if path.exists() else None for path in writes}
    with lock_path.open("a+b") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        try:
            journal = {"schema_version": 1, "transaction_id": "TX-ACTIVATE-STOPQ-01", "state": "PREPARED", "before": {str(path): bool(data) for path, data in before.items()}}
            writes[journal_path] = (json.dumps(journal, indent=2, sort_keys=True) + "\n").encode()
            for path, data in writes.items(): _atomic(path, data)
            if fault_after == "repository": raise CanonicalMissionLifecycleError("INJECTED_ACTIVATION_FAILURE")
            journal["state"] = "COMMITTED"; journal["contract_id"] = CONTRACT_ID; journal["registry_id"] = REGISTRY_ID
            _atomic(journal_path, (json.dumps(journal, indent=2, sort_keys=True) + "\n").encode())
            return {"result": "PASS", "resolution": "ACTIVATED", "contract_id": CONTRACT_ID, "registry_id": REGISTRY_ID, "transaction_id": journal["transaction_id"]}
        except Exception:
            for path, data in before.items():
                target = Path(path)
                if data is None: target.unlink(missing_ok=True)
                else: _atomic(target, data)
            raise


def mission_list(root: Path | str) -> dict[str, Any]:
    from scripts.lib.eos import operational_beta
    from scripts.lib.emp.canonical_lifecycle_resolver import submitted_missions
    base = operational_beta.active_missions(Path(root))
    discovery = discover(root)
    if discovery.get("result") == "PASS":
        base.setdefault("missions", []).append({"mission_id": TARGET_MISSION, "lifecycle": "ACTIVE", "classification": "disposable-operational-qualification", "package": discovery.get("package_locator"), "contract_id": discovery.get("contract_id")})
    canonical = submitted_missions(root)
    existing = {str(item.get("mission_id", "")).upper() for item in base.get("missions", [])}
    for mission in canonical.get("missions", []):
        if str(mission.get("mission_id", "")).upper() not in existing:
            base.setdefault("missions", []).append(mission)
    base["active_mission_count"] = len(base.get("missions", []))
    base["canonical_submission_discovery"] = canonical
    base["canonical_mission_reconciliation"] = discovery
    return base

# --- CR46 ZO-026: lifecycle owner projection over canonical instrument selection ---
def qualification_instrument_projection(
    root: Path | str,
    projection_scope: str,
    *,
    context: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    from scripts.lib.emp.mission_verification_controller import (
        select_qualification_instrument,
    )

    repository = Path(root).resolve()

    return {
        **select_qualification_instrument(
            projection_scope,
            context={
                "repository": str(repository),
                **dict(context or {}),
            },
        ),
        "owner_surface": "canonical_mission_lifecycle",
    }
