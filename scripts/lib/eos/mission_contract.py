#!/usr/bin/env python3
"""Repository-independent, fail-closed Mission Contract capability."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

import yaml

STATUSES = {
    "AUTHORIZED", "NO_AUTHORIZED_WORK", "AMBIGUOUS_AUTHORITY",
    "INVALID_CONTRACT", "EXPIRED_AUTHORITY", "SUSPENDED_AUTHORITY",
    "REVOKED_AUTHORITY", "REPOSITORY_MISMATCH", "BRANCH_MISMATCH",
    "BASELINE_MISMATCH", "WOP_UNRESOLVED", "WOP_DIGEST_MISMATCH",
    "APPROVAL_REQUIRED", "ROLE_ASSIGNMENT_REQUIRED",
    "DIRTY_TREE_NOT_AUTHORIZED", "SCOPE_VIOLATION",
}
PERMISSIONS = (
    "inspect", "modify", "generate_evidence", "reconcile_metadata", "stage",
    "commit", "create_branch", "push", "publish", "rollback",
    "reconcile_state", "close_mission",
)
ROLES = (
    "human_authorizer", "repository_operator", "orchestration_agent",
    "execution_agent", "implementation_owner", "document_owner",
    "review_owner", "qualification_owner", "publication_owner",
    "evidence_reviewer",
)
POLICIES = {
    "CLEAN_REQUIRED", "CLASSIFIED_DIRTY_ALLOWED", "PATH_SCOPED_DIRTY_ALLOWED",
    "ISOLATED_WORKTREE_REQUIRED", "PATCH_ONLY", "READ_ONLY",
}
TRANSITIONS = {
    "candidate": {"active", "invalid"},
    "active": {"suspended", "completed", "revoked", "expired", "superseded"},
    "suspended": {"active", "revoked", "expired"},
    "expired": set(), "completed": set(), "revoked": set(),
    "superseded": set(), "invalid": set(),
}


class MissionContractError(ValueError):
    pass


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def digest(value: Any) -> str:
    clean = dict(value)
    clean.pop("contract_digest", None)
    return hashlib.sha256(canonical(clean)).hexdigest()


def load(path: Path) -> dict[str, Any]:
    try:
        value = yaml.safe_load(path.read_text())
    except (OSError, yaml.YAMLError) as exc:
        raise MissionContractError(f"{path}: {exc}") from exc
    if not isinstance(value, Mapping):
        raise MissionContractError(f"{path}: root must be a mapping")
    return dict(value)


def validate(value: Mapping[str, Any], root: Path) -> list[str]:
    errors: list[str] = []
    required = {
        "schema_version", "document_type", "contract_id", "mission_id",
        "registry_id", "wop", "repository", "scope", "permissions", "roles",
        "approvals", "dirty_tree", "lifecycle", "activation", "interruption",
        "closeout",
    }
    for field in sorted(required - set(value)):
        errors.append(f"{field}: required")
    if errors:
        return errors
    if value["document_type"] != "MissionContract":
        errors.append("document_type: must equal MissionContract")
    if value["lifecycle"] not in TRANSITIONS:
        errors.append("lifecycle: invalid")
    if value.get("contract_digest") and value["contract_digest"] != digest(value):
        errors.append("contract_digest: mismatch")
    permissions = value["permissions"]
    if not isinstance(permissions, Mapping):
        errors.append("permissions: must be a mapping")
    else:
        for name in PERMISSIONS:
            if permissions.get(name) not in {True, False}:
                errors.append(f"permissions.{name}: explicit boolean required")
    roles = value["roles"]
    if not isinstance(roles, Mapping):
        errors.append("roles: must be a mapping")
    else:
        for name in ROLES:
            if not roles.get(name):
                errors.append(f"roles.{name}: required")
        if roles.get("execution_agent") == roles.get("human_authorizer"):
            errors.append("roles.execution_agent: cannot self-authorize")
    policy = value["dirty_tree"].get("policy")
    if policy not in POLICIES:
        errors.append("dirty_tree.policy: invalid")
    repository = value["repository"]
    if not isinstance(repository, Mapping):
        errors.append("repository: must be a mapping")
    for field in ("identity", "root", "branch", "baseline"):
        if not repository.get(field):
            errors.append(f"repository.{field}: required")
    wop = value["wop"]
    locator = root / str(wop.get("locator", ""))
    if not wop.get("id") or not locator.is_file():
        errors.append("wop.locator: unresolved")
    elif wop.get("digest") != hashlib.sha256(locator.read_bytes()).hexdigest():
        errors.append("wop.digest: mismatch")
    if value["lifecycle"] == "active":
        if not value["activation"].get("record") or not value["activation"].get("actor"):
            errors.append("activation: attributable record required")
        if value["approvals"].get("activation") != "approved":
            errors.append("approvals.activation: approved required")
    return sorted(errors)


class Resolver:
    def __init__(self, root: Path):
        self.root = root.resolve()
        self.store = self.root / "engineering/mission-contracts/contracts"

    def contracts(self, mission: str | None = None) -> list[tuple[Path, dict[str, Any]]]:
        result = []
        for path in sorted(self.store.glob("*.yaml")):
            value = load(path)
            if mission is None or value.get("mission_id") == mission:
                result.append((path, value))
        return result

    def resolve(self, mission: str | None = None) -> dict[str, Any]:
        candidates = self.contracts(mission)
        invalid = [(p, v, validate(v, self.root)) for p, v in candidates]
        invalid = [item for item in invalid if item[2]]
        active = [(p, v) for p, v in candidates if v.get("lifecycle") == "active"]
        status = "NO_AUTHORIZED_WORK"
        selected = None
        conditions: list[str] = []
        if len(active) > 1:
            status = "AMBIGUOUS_AUTHORITY"
        elif len(active) == 1:
            selected = active[0]
            errors = validate(selected[1], self.root)
            if errors:
                status, conditions = "INVALID_CONTRACT", errors
            else:
                status = self._context_status(selected[1])
        elif invalid:
            status, conditions = "INVALID_CONTRACT", invalid[0][2]
        elif len(candidates) == 1:
            state = candidates[0][1].get("lifecycle")
            status = {
                "suspended": "SUSPENDED_AUTHORITY", "expired": "EXPIRED_AUTHORITY",
                "revoked": "REVOKED_AUTHORITY",
            }.get(state, "NO_AUTHORIZED_WORK")
        value = {
            "resolution": status,
            "transactional_authority": status == "AUTHORIZED",
            "candidate_count": len(candidates),
            "active_count": len(active),
            "unresolved_conditions": conditions,
            "authority_boundary": "Only one valid active attributable contract grants its explicit permissions.",
        }
        if selected:
            value["contract"] = selected[1]
            value["contract_path"] = str(selected[0].relative_to(self.root))
        value["evidence_digest"] = digest(value)
        return value

    def _context_status(self, value: Mapping[str, Any]) -> str:
        import subprocess
        def git(*args: str) -> str:
            return subprocess.check_output(["git", "-C", str(self.root), *args], text=True).strip()
        repo = value["repository"]
        if Path(repo["root"]).resolve() != self.root or repo["identity"] != self.root.name:
            return "REPOSITORY_MISMATCH"
        if git("branch", "--show-current") != repo["branch"]:
            return "BRANCH_MISMATCH"
        if git("rev-parse", "HEAD") != repo["baseline"]:
            return "BASELINE_MISMATCH"
        dirty = bool(git("status", "--porcelain=v1"))
        if dirty and value["dirty_tree"]["policy"] == "CLEAN_REQUIRED":
            return "DIRTY_TREE_NOT_AUTHORIZED"
        return "AUTHORIZED"


def transition(path: Path, root: Path, target: str, actor: str, evidence: str,
               expected: str) -> dict[str, Any]:
    value = load(path)
    current = value.get("lifecycle")
    if current != expected:
        raise MissionContractError(f"expected lifecycle {expected}, observed {current}")
    if target not in TRANSITIONS.get(str(current), set()):
        raise MissionContractError(f"transition {current}->{target} is prohibited")
    value["lifecycle"] = target
    value["activation"] = {
        "actor": actor, "record": evidence,
        "timestamp": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
    }
    value["contract_digest"] = digest(value)
    path.write_text(yaml.safe_dump(value, sort_keys=True))
    return value
