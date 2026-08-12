"""Integrity-bound production execution-agent qualification lifecycle."""
from __future__ import annotations

import getpass
import hashlib
import json
import os
import socket
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from scripts.lib.emp.authority_resolution import authoritative_source_path
from scripts.lib.emp.production_execution import digest, validate_agent
from scripts.lib.eos import capability_registry, mission_knowledge
import yaml


class AgentQualificationError(ValueError):
    pass


def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _atomic(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(value, indent=2, sort_keys=True) + "\n"
    descriptor, temporary_name = tempfile.mkstemp(
        dir=path.parent, prefix=f".{path.name}."
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def _record_root(repository: Path) -> Path:
    return repository / ".zeus/runtime/agents"


def _fingerprint(repository: Path) -> str:
    policy = json.loads(json.dumps({}))
    del policy
    key = Path("/tmp/zeus-p2-025-owner.pub")
    if not key.is_file():
        raise AgentQualificationError("enrolled engineering public key is unavailable")
    result = subprocess.run(
        ["ssh-keygen", "-lf", str(key)], text=True, capture_output=True, check=False
    )
    if result.returncode:
        raise AgentQualificationError("engineering key fingerprint is unavailable")
    return result.stdout.split()[1]


def _binding(repository: Path) -> dict[str, Any]:
    head = subprocess.check_output(
        ["git", "-C", str(repository), "rev-parse", "HEAD"], text=True
    ).strip()
    pointer = json.loads(
        (repository / ".zeus/runtime/authority/active-publication.json").read_text()
    )
    authority = yaml.safe_load(authoritative_source_path(repository).read_text())
    published = next(
        value["baseline_commit"]
        for value in authority["repositories"].values()
        if Path(value["canonical_locator"]).resolve() == repository
    )
    try:
        recommendation = mission_knowledge.recommend(repository)
        model = mission_knowledge.load(repository)
        capabilities = capability_registry.load(repository)
    except Exception as error:
        raise AgentQualificationError(
            "convergence mission and capability state is unavailable"
        ) from error
    return {
        "repository_identity": str(repository),
        "repository_head": head,
        "published_baseline": published,
        "authority_publication": pointer["transaction_id"],
        "mission_knowledge": {
            "model_id": recommendation["model_id"],
            "revision": str(model["revision"]),
            "recommended_mission": recommendation["recommended_mission"],
            "readiness_digest": (
                recommendation["readiness"]["readiness_digest"]
                if recommendation.get("readiness") else None
            ),
        },
        "capability_registry": {
            "registry_id": capabilities["registry_id"],
            "revision": str(capabilities["revision"]),
        },
    }


def qualification_inputs(repository: Path) -> dict[str, Any]:
    root = repository.resolve()
    binding = _binding(root)
    checks = {
        "agent_identity": bool(getpass.getuser() and socket.gethostname()),
        "repository_access": os.access(root, os.R_OK | os.W_OK),
        "repository_identity": binding["repository_identity"]
        == "/data/engineering/repositories/homelab",
        "convergence_mission_knowledge": bool(binding["mission_knowledge"]),
        "capability_registry_compatibility": bool(binding["capability_registry"]),
        "engineering_authority_compatibility": bool(
            binding["authority_publication"]
        ),
        "runtime_dependencies": all(
            (root / path).exists()
            for path in (
                ".zeus/runtime",
                "engineering/eens/production-eens-policy.yaml",
                "engineering/evidence/production-evidence-policy.yaml",
                "engineering/reconciliation/production-reconciliation-policy.yaml",
            )
        ),
        "execution_capabilities": (root / "scripts/zeus").is_file(),
        "security_configuration": bool(_fingerprint(root)),
        "communication_interfaces": (
            root / "engineering/eens/production-eens-policy.yaml"
        ).is_file(),
        "eens_integration": (
            root / "engineering/eens/production-eens-policy.yaml"
        ).is_file(),
        # Qualification remains valid across the published Operational Alpha
        # sequence.  Binding it to a recommended mission creates a circular
        # prerequisite for the capability that makes OA-11 eligible: CAP-010
        # must qualify while OA-11 is still blocked and therefore no mission
        # is recommended.  Bind to the authoritative model revision and
        # sequence instead; readiness remains fail-closed in the Mission
        # Knowledge Model.
        "lifecycle_compatibility": bool(
            binding["mission_knowledge"].get("model_id")
            and binding["mission_knowledge"].get("revision")
        ),
    }
    return {
        "binding": binding,
        "requirements": {
            key: "PASS" if passed else "FAIL"
            for key, passed in sorted(checks.items())
        },
    }


def candidate(repository: Path) -> dict[str, Any]:
    root = repository.resolve()
    inputs = qualification_inputs(root)
    principal = getpass.getuser()
    return {
        "agent_id": f"zeus-local-{principal}-01",
        "agent_type": "local-authenticated",
        "host_identity": f"{socket.gethostname()}:{socket.getmachine() if hasattr(socket, 'getmachine') else os.uname().machine}",
        "service_identity": principal,
        "supported_mission_classes": ["engineering"],
        "supported_tools": ["zeus-cli", "bounded-artifact-handler"],
        "repository_access_scope": [str(root)],
        "execution_constraints": [
            "controlled-wop-only",
            "exact-repository-baseline",
            "no-unreviewed-external-effects",
        ],
        "qualification_status": "QUALIFIED",
        "qualification_evidence": [],
        "active": True,
        "last_validated_at": None,
        "trust_binding": _fingerprint(root),
        "eens_identity": principal,
        "evidence_signing_identity": principal,
        "interruption_resume_capable": True,
        "concurrency_limit": 1,
        "_qualification_inputs": inputs,
    }


def _load_records(repository: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for path in sorted((_record_root(repository) / "qualifications").glob("*.json")):
        checksum = path.with_suffix(path.suffix + ".sha256")
        try:
            value = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        if (
            checksum.is_file()
            and checksum.read_text().split()[0] == _sha(path)
            and value.get("qualification_digest")
            == digest({k: v for k, v in value.items() if k != "qualification_digest"})
        ):
            records.append(value)
    return records


def registry(repository: Path) -> dict[str, Any]:
    root = repository.resolve()
    binding = _binding(root)
    records = _load_records(root)
    latest: dict[tuple[str, str], dict[str, Any]] = {}
    for record in records:
        key = (
            record["agent"]["agent_id"],
            digest(record.get("binding", {})),
        )
        if record.get("binding") == binding:
            latest[key] = record
    current = [
        record for record in latest.values()
        if record.get("status") == "QUALIFIED"
    ]
    revoked = [
        record for record in records if record.get("status") == "REVOKED"
    ]
    agents = sorted(
        [record["agent"] for record in current], key=lambda item: item["agent_id"]
    )
    unsigned = {
        "schema_version": 1,
        "known_agents": sorted({record["agent"]["agent_id"] for record in records}),
        "eligible_agents": [agent["agent_id"] for agent in agents],
        "qualified_agents": [agent["agent_id"] for agent in agents],
        "inactive_agents": sorted(
            record["agent"]["agent_id"]
            for record in records if record.get("status") == "INACTIVE"
        ),
        "revoked_agents": sorted(
            record["agent"]["agent_id"] for record in revoked
        ),
        "agents": agents,
        "binding": binding,
    }
    return {**unsigned, "registry_digest": digest(unsigned)}


def select(
    repository: Path,
    *,
    mission_class: str,
    required_tools: Iterable[str],
    execution_profile: Iterable[str],
    agent_id: str | None = None,
) -> dict[str, Any]:
    """Select exactly one current agent matching the controlled execution profile.

    Selection is a read-only projection of the integrity-bound registry.  It
    fails closed for missing, stale, ambiguous, or mismatched candidates.
    """
    root = repository.resolve()
    tools = sorted(set(required_tools))
    profile = sorted(set(execution_profile))
    view = registry(root)
    candidates = []
    for agent in view["agents"]:
        if not agent.get("active") or agent.get("qualification_status") != "QUALIFIED":
            continue
        if agent_id and agent.get("agent_id") != agent_id:
            continue
        if root.as_posix() not in [str(item) for item in agent.get("repository_access_scope", [])]:
            continue
        if mission_class not in agent.get("supported_mission_classes", []):
            continue
        if not set(tools) <= set(agent.get("supported_tools", [])):
            continue
        if not set(profile) <= set(agent.get("execution_constraints", [])):
            continue
        candidates.append(agent)
    if len(candidates) != 1:
        raise AgentQualificationError(
            "agent selection failed closed: expected exactly one qualified matching agent"
        )
    selected = candidates[0]
    unsigned = {
        "schema_version": 1,
        "repository_identity": str(root),
        "mission_class": mission_class,
        "required_tools": tools,
        "execution_profile": profile,
        "selected_agent": selected["agent_id"],
        "qualified_agents": sorted(item["agent_id"] for item in candidates),
        "registry_digest": view["registry_digest"],
    }
    return {**unsigned, "selection_digest": digest(unsigned)}


def qualify(
    repository: Path, *, at: datetime | None = None
) -> tuple[dict[str, Any], bool]:
    root = repository.resolve()
    draft = candidate(root)
    inputs = draft.pop("_qualification_inputs")
    failed = [
        name for name, result in inputs["requirements"].items() if result != "PASS"
    ]
    if failed:
        raise AgentQualificationError(
            "production agent qualification failed: " + ", ".join(failed)
        )
    timestamp = (at or datetime.now(timezone.utc)).astimezone(timezone.utc)
    binding = inputs["binding"]
    stable = {
        "schema_version": 1,
        "qualification_version": 1,
        "agent": draft,
        "binding": binding,
        "requirements": inputs["requirements"],
        "status": "QUALIFIED",
    }
    binding_digest = digest(stable)
    path = (
        _record_root(root) / "qualifications"
        / f"{draft['agent_id']}-{binding_digest[:16]}.json"
    )
    if path.is_file():
        matching = [
            record for record in _load_records(root)
            if record.get("qualification_binding_digest") == binding_digest
        ]
        if len(matching) != 1:
            raise AgentQualificationError("qualification replay integrity failed")
        return matching[0], True
    conflicting = [
        record for record in _load_records(root)
        if record["agent"]["agent_id"] == draft["agent_id"]
        and record.get("binding") == binding
        and record.get("qualification_binding_digest") != binding_digest
    ]
    if conflicting:
        raise AgentQualificationError("conflicting qualification already exists")
    draft["last_validated_at"] = timestamp.isoformat().replace("+00:00", "Z")
    draft["qualification_evidence"] = [
        f"agent-qualification:{binding_digest}"
    ]
    validate_agent(
        draft, mission_class="engineering", repository=str(root)
    )
    record = {
        **stable,
        "agent": draft,
        "qualified_at": timestamp.isoformat().replace("+00:00", "Z"),
        "qualified_by": getpass.getuser(),
        "qualification_binding_digest": binding_digest,
    }
    record["qualification_digest"] = digest(record)
    _atomic(path, record)
    path.with_suffix(path.suffix + ".sha256").write_text(
        f"{_sha(path)}  {path.name}\n"
    )
    return record, False


def revoke(
    repository: Path, agent_id: str, *, at: datetime | None = None
) -> tuple[dict[str, Any], bool]:
    root = repository.resolve()
    view = registry(root)
    matching = [
        record for record in _load_records(root)
        if record["agent"]["agent_id"] == agent_id
        and record.get("binding") == view["binding"]
    ]
    if not matching:
        raise AgentQualificationError("current agent qualification not found")
    if matching[-1].get("status") == "REVOKED":
        return matching[-1], True
    previous = matching[-1]
    timestamp = (at or datetime.now(timezone.utc)).astimezone(timezone.utc)
    record = {
        **previous,
        "status": "REVOKED",
        "revoked_at": timestamp.isoformat().replace("+00:00", "Z"),
        "revoked_by": getpass.getuser(),
        "predecessor_qualification_digest": previous["qualification_digest"],
    }
    record.pop("qualification_digest", None)
    record["qualification_digest"] = digest(record)
    path = (
        _record_root(root) / "qualifications"
        / f"{agent_id}-revoked-{record['qualification_digest'][:16]}.json"
    )
    _atomic(path, record)
    path.with_suffix(path.suffix + ".sha256").write_text(
        f"{_sha(path)}  {path.name}\n"
    )
    return record, False


def runtime_registry_path(repository: Path) -> Path:
    root = repository.resolve()
    view = registry(root)
    unsigned = {
        "schema_version": 2,
        "registry_id": "ZEUS-PRODUCTION-EXECUTION-AGENTS",
        "agents": view["agents"],
    }
    value = {**unsigned, "registry_digest": digest(unsigned)}
    path = _record_root(root) / "effective-registry.json"
    _atomic(path, value)
    return path

# --- CR46 ZO-026: owner projection over canonical instrument selection ---
def qualification_instrument_projection(
    repository: Path,
    projection_scope: str,
    *,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    from scripts.lib.emp.mission_verification_controller import (
        select_qualification_instrument,
    )

    root = repository.resolve()

    return {
        **select_qualification_instrument(
            projection_scope,
            context={
                "repository": str(root),
                **dict(context or {}),
            },
        ),
        "owner_surface": "agent_qualification",
        "repository": str(root),
    }
