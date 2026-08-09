"""Machine-readable Zeus managed-work continuation contracts.

The contract is deliberately a small, structured transaction.  It is not a
prompt transport and it cannot introduce a new mission, execution, provider,
or session binding.  Zeus validates and records it before the managed adapter
is allowed to continue an existing execution.
"""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from pathlib import Path
from typing import Any, Mapping

import yaml

from scripts.lib.emp.production_execution import atomic_write, canonical_bytes, digest, load_json


CONTRACT_TYPE = "ZEUS_MANAGED_WORK_CONTRACT"
SCHEMA_VERSION = 1
STAGE_DIR = "work-contracts"
EVENT_DIR = "work-contract-events"
REQUIRED_BINDINGS = (
    "mission_id", "execution_id", "execution_session_id", "provider_id",
    "provider_session_id",
)
ALLOWED_ACTIONS = {"CONTINUE_CONTROLLED_MISSION_WORK", "RECONCILE_EXECUTION_STATE"}


class WorkContractError(ValueError):
    def __init__(self, code: str, message: str, *, details: Mapping[str, Any] | None = None):
        self.code = code
        self.message = message
        self.details = dict(details or {})
        super().__init__(message)


def _source_digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _load_source(path: Path) -> tuple[dict[str, Any], str]:
    try:
        raw = path.read_bytes()
    except OSError as error:
        raise WorkContractError("WORK_CONTRACT_SOURCE_UNAVAILABLE", str(error)) from error
    try:
        value = json.loads(raw.decode("utf-8")) if path.suffix.lower() == ".json" else yaml.safe_load(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError, yaml.YAMLError) as error:
        raise WorkContractError("WORK_CONTRACT_SYNTAX_INVALID", f"work-contract is not valid structured data: {error}") from error
    if not isinstance(value, dict):
        raise WorkContractError("WORK_CONTRACT_SHAPE_INVALID", "work-contract root must be an object")
    return value, _source_digest(raw)


def _validate_shape(value: Mapping[str, Any]) -> dict[str, Any]:
    required = {"schema_version", "contract_type", "contract_id", "mission_id", "execution_id",
                "execution_session_id", "provider_id", "provider_session_id", "requested_action",
                "actions"}
    missing = sorted(required - set(value))
    if missing:
        raise WorkContractError("WORK_CONTRACT_SCHEMA_INVALID", "missing required fields: " + ", ".join(missing))
    unknown = sorted(set(value) - required)
    if unknown:
        raise WorkContractError("WORK_CONTRACT_SCHEMA_INVALID", "unsupported fields: " + ", ".join(unknown))
    if value.get("schema_version") != SCHEMA_VERSION or value.get("contract_type") != CONTRACT_TYPE:
        raise WorkContractError("WORK_CONTRACT_SCHEMA_INVALID", "unsupported work-contract schema or type")
    if not isinstance(value.get("contract_id"), str) or not value["contract_id"]:
        raise WorkContractError("WORK_CONTRACT_SCHEMA_INVALID", "contract_id must be a non-empty string")
    if value.get("requested_action") not in ALLOWED_ACTIONS:
        raise WorkContractError("WORK_CONTRACT_ACTION_INVALID", "requested_action is not a Zeus-managed action")
    actions = value.get("actions")
    if not isinstance(actions, list) or not actions:
        raise WorkContractError("WORK_CONTRACT_SCHEMA_INVALID", "actions must be a non-empty list")
    for index, action in enumerate(actions):
        if not isinstance(action, dict) or action.get("action") not in ALLOWED_ACTIONS:
            raise WorkContractError("WORK_CONTRACT_ACTION_INVALID", f"actions[{index}] is not structured Zeus work")
        if set(action) != {"action"}:
            raise WorkContractError("WORK_CONTRACT_PROSE_FORBIDDEN", f"actions[{index}] contains unsupported execution fields")
    return deepcopy(dict(value))


def validate(path: Path | str, *, mission_id: str, binding: Mapping[str, Any]) -> dict[str, Any]:
    """Validate source syntax, immutable identity, and current runtime binding."""
    source = Path(path).resolve()
    value, source_digest = _load_source(source)
    contract = _validate_shape(value)
    requested_mission = str(mission_id).upper()
    if str(contract.get("mission_id", "")).upper() != requested_mission:
        raise WorkContractError("MISSION_BINDING_MISMATCH", "work-contract mission differs from requested mission")
    for field in REQUIRED_BINDINGS:
        expected = binding.get(field)
        observed = contract.get(field)
        if not expected or observed != expected:
            raise WorkContractError(f"{field.upper()}_BINDING_MISMATCH", f"work-contract {field} differs from the authoritative runtime")
    if binding.get("session_disposition") == "SUPERSEDED" or binding.get("state") == "SUPERSEDED":
        raise WorkContractError("STALE_RUNTIME_BINDING", "work-contract targets a superseded runtime")
    # A stopped transport is not a stale Zeus/thread binding.  Native thread
    # recovery validates persistence and ownership before the contract can be
    # consumed; only durable supersession invalidates this binding here.
    return {"contract": contract, "source": str(source), "source_digest": source_digest,
            "contract_payload_digest": digest(contract)}


def _record_path(runtime: Path, contract_id: str) -> Path:
    directory = (runtime / STAGE_DIR).resolve()
    path = (directory / f"{contract_id}.json").resolve()
    try:
        path.relative_to(directory)
    except ValueError as error:
        raise WorkContractError("WORK_CONTRACT_PATH_INVALID", "contract identity escapes runtime") from error
    return path


def _event(runtime: Path, contract_id: str, event: str, payload: Mapping[str, Any]) -> dict[str, Any]:
    directory = runtime / EVENT_DIR / contract_id
    directory.mkdir(parents=True, exist_ok=True)
    existing = sorted(directory.glob("*.json"))
    material: dict[str, Any] = {"schema_version": 1, "sequence": len(existing) + 1,
                                "contract_id": contract_id, "event": event,
                                "payload": deepcopy(dict(payload)),
                                "previous_event_digest": None}
    if existing:
        material["previous_event_digest"] = load_json(existing[-1]).get("event_digest")
    material["event_digest"] = digest(material)
    path = directory / f"{material['sequence']:04d}.json"
    if path.exists() and load_json(path) != material:
        raise WorkContractError("WORK_CONTRACT_EVENT_CONFLICT", "immutable work-contract event conflicts")
    if not path.exists():
        atomic_write(path, material)
    return material


def ingest(path: Path | str, *, runtime: Path | str, mission_id: str,
           binding: Mapping[str, Any]) -> dict[str, Any]:
    """Persist one validated contract in the managed execution provenance chain."""
    validated = validate(path, mission_id=mission_id, binding=binding)
    runtime_path = Path(runtime).resolve()
    contract = validated["contract"]
    contract_id = contract["contract_id"]
    record_path = _record_path(runtime_path, contract_id)
    unsigned = {
        "schema_version": SCHEMA_VERSION, "record_type": CONTRACT_TYPE,
        "contract_id": contract_id, "contract": contract,
        "source": validated["source"], "source_digest": validated["source_digest"],
        "contract_payload_digest": validated["contract_payload_digest"],
        "binding": {field: binding.get(field) for field in REQUIRED_BINDINGS},
        "runtime_session_id": binding.get("session_id"),
        "zeus_managed_execution_owner": "Zeus",
        "provenance": {"source_kind": "operator_supplied_machine_contract",
                        "validation": "PASS", "execution_authority": "EXISTING_MANAGED_EXECUTION"},
    }
    if record_path.is_file():
        existing = load_json(record_path)
        if existing.get("record_digest") != digest({k: v for k, v in existing.items() if k != "record_digest"}):
            raise WorkContractError("WORK_CONTRACT_RECORD_CORRUPT", "persisted work-contract digest mismatch")
        if existing.get("contract_payload_digest") != unsigned["contract_payload_digest"]:
            raise WorkContractError("WORK_CONTRACT_REPLAY_CONFLICT", "contract ID was reused with different content")
        if existing.get("binding") != unsigned["binding"]:
            raise WorkContractError("WORK_CONTRACT_REPLAY_CONFLICT", "contract replay has a different runtime binding")
        return {**existing, "result": "PASS", "replay": "IDEMPOTENT", "mutation_applied": False,
                "read_only": True}
    unsigned["record_digest"] = digest(unsigned)
    atomic_write(record_path, unsigned)
    event = _event(runtime_path, contract_id, "WORK_CONTRACT_ACCEPTED", {
        "source_digest": unsigned["source_digest"], "contract_payload_digest": unsigned["contract_payload_digest"],
        "mission_id": binding.get("mission_id"), "execution_id": binding.get("execution_id"),
        "execution_session_id": binding.get("execution_session_id"), "provider_id": binding.get("provider_id"),
        "provider_session_id": binding.get("provider_session_id"), "runtime_session_id": binding.get("session_id"),
    })
    return {**unsigned, "result": "PASS", "replay": "APPLIED", "mutation_applied": True,
            "event_digest": event["event_digest"], "read_only": False}
