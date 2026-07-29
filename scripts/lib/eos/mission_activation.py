#!/usr/bin/env python3
"""Fail-closed Mission Contract admission and atomic activation services."""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
import subprocess
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping

import yaml

from scripts.lib.eos.mission_contract import (
    MissionContractError,
    Resolver,
    digest as contract_digest,
    load,
    validate,
)

TERMINAL = {"expired", "completed", "revoked", "superseded", "invalid"}
ELIGIBLE_REGISTRY_STATES = {"ready", "active"}


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(root), *args],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _yaml(value: Mapping[str, Any]) -> bytes:
    return yaml.safe_dump(dict(value), sort_keys=True).encode()


@dataclass(frozen=True)
class Check:
    qualification: str
    passed: bool
    code: str
    detail: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "qualification": self.qualification,
            "result": "PASS" if self.passed else "FAIL",
            "code": self.code,
            "detail": self.detail,
        }


class Admission:
    """Deterministically qualify one activation request."""

    def __init__(self, root: Path):
        self.root = root.resolve()

    def decide(
        self, contract_path: Path, request: Mapping[str, Any]
    ) -> dict[str, Any]:
        contract = load(contract_path)
        registry_path = self.root / "engineering/registry/work-registry.yaml"
        registry = yaml.safe_load(registry_path.read_text())
        checks: list[Check] = []

        def add(name: str, condition: bool, code: str, detail: str) -> None:
            checks.append(Check(name, bool(condition), code, detail))

        lifecycle = str(contract.get("lifecycle", ""))
        add(
            "mission_eligibility",
            lifecycle == "candidate",
            "MISSION_LIFECYCLE_INELIGIBLE",
            f"expected candidate, observed {lifecycle or 'missing'}",
        )
        add(
            "mission_eligibility",
            request.get("mission_id") == contract.get("mission_id"),
            "MISSION_ID_MISMATCH",
            "activation request and contract mission identities must match",
        )

        errors = validate(contract, self.root)
        add(
            "mission_eligibility",
            not errors,
            "CONTRACT_INVALID",
            "; ".join(errors) if errors else "contract schema and bindings valid",
        )

        wop = contract.get("wop") or {}
        wop_path = self.root / str(wop.get("locator", ""))
        wop_value: Mapping[str, Any] = {}
        if wop_path.is_file():
            loaded = yaml.safe_load(wop_path.read_text())
            wop_value = loaded if isinstance(loaded, Mapping) else {}
        add("wop_qualification", wop_path.is_file(), "WOP_UNRESOLVED", str(wop_path))
        add(
            "wop_qualification",
            wop_path.is_file() and wop.get("digest") == _sha(wop_path),
            "WOP_DIGEST_MISMATCH",
            "contract digest must bind the resolved WOP",
        )
        add(
            "wop_qualification",
            str(wop_value.get("status", "")).lower() == "active",
            "WOP_LIFECYCLE_INELIGIBLE",
            f"WOP status={wop_value.get('status', 'missing')}",
        )
        add(
            "wop_qualification",
            wop_value.get("work_item_id") == contract.get("registry_id"),
            "WOP_REGISTRY_MISMATCH",
            "WOP work item must match contract registry identity",
        )

        repo = contract.get("repository") or {}
        actual_root = Path(_git(self.root, "rev-parse", "--show-toplevel")).resolve()
        add(
            "repository_qualification",
            actual_root == self.root
            and Path(str(repo.get("root", ""))).resolve() == self.root
            and repo.get("identity") in {self.root.name, "homelab-infrastructure"},
            "REPOSITORY_MISMATCH",
            f"resolved repository root={actual_root}",
        )
        add(
            "repository_qualification",
            repo.get("branch") == _git(self.root, "branch", "--show-current"),
            "BRANCH_MISMATCH",
            "contract branch must equal the checked-out branch",
        )
        remote = _git(self.root, "remote", "get-url", "origin")
        add(
            "repository_qualification",
            not repo.get("remote") or repo.get("remote") == remote,
            "REPOSITORY_REMOTE_MISMATCH",
            f"resolved origin={remote}",
        )
        add(
            "baseline_qualification",
            repo.get("baseline") == _git(self.root, "rev-parse", "HEAD"),
            "BASELINE_MISMATCH",
            "contract baseline must equal HEAD",
        )

        roles = contract.get("roles") or {}
        add(
            "role_qualification",
            all(roles.get(name) for name in (
                "human_authorizer", "repository_operator", "orchestration_agent",
                "execution_agent", "implementation_owner", "document_owner",
                "review_owner", "qualification_owner", "publication_owner",
                "evidence_reviewer",
            )),
            "ROLE_ASSIGNMENT_REQUIRED",
            "all operational roles must be assigned",
        )
        add(
            "role_qualification",
            roles.get("execution_agent") != roles.get("human_authorizer"),
            "SELF_AUTHORIZATION_PROHIBITED",
            "execution agent and human authorizer must differ",
        )

        approval = request.get("approval") or {}
        approval_path = self.root / str(approval.get("locator", ""))
        approval_value: Mapping[str, Any] = {}
        if approval_path.is_file():
            loaded = yaml.safe_load(approval_path.read_text())
            approval_value = loaded if isinstance(loaded, Mapping) else {}
        approval_ok = (
            approval_path.is_file()
            and approval.get("digest") == _sha(approval_path)
            and approval_value.get("decision") == "approved"
            and approval_value.get("mission_id") == contract.get("mission_id")
            and approval_value.get("contract_id") == contract.get("contract_id")
            and bool(approval_value.get("authorizer"))
        )
        add(
            "approval_qualification",
            approval_ok,
            "APPROVAL_INVALID",
            "attributable approval must bind the mission and contract",
        )

        work_items = (registry.get("entities") or {}).get("work_items", [])
        matches = [x for x in work_items if x.get("registry_id") == contract.get("registry_id")]
        add(
            "mission_eligibility",
            len(matches) == 1,
            "REGISTRY_BINDING_UNRESOLVED",
            f"resolved {len(matches)} Work Registry items",
        )
        item = matches[0] if len(matches) == 1 else {}
        add(
            "mission_eligibility",
            item.get("management_state") in ELIGIBLE_REGISTRY_STATES,
            "REGISTRY_LIFECYCLE_INELIGIBLE",
            f"registry state={item.get('management_state', 'missing')}",
        )
        wop_label = Path(str(wop.get("locator", ""))).parent.name
        add(
            "scope_qualification",
            item.get("scope") in {contract.get("mission_id"), wop.get("id"), wop_label},
            "SCOPE_MISMATCH",
            "registry scope must bind the mission or contracted WOP",
        )

        dependencies = (registry.get("entities") or {}).get("dependencies", [])
        blocking = [
            x.get("registry_id")
            for x in dependencies
            if x.get("dependent_id") == contract.get("registry_id")
            and x.get("management_state") not in {"completed", "satisfied", "archived"}
        ]
        add(
            "dependency_qualification",
            not blocking,
            "DEPENDENCY_UNRESOLVED",
            f"blocking dependencies={sorted(str(x) for x in blocking)}",
        )

        scope = contract.get("scope") or {}
        manifest = self.root / str(scope.get("classification_manifest", ""))
        add(
            "scope_qualification",
            not scope.get("classification_manifest")
            or (
                manifest.is_file()
                and scope.get("classification_manifest_digest") == _sha(manifest)
            ),
            "SCOPE_MANIFEST_INVALID",
            "classification manifest locator and digest must resolve",
        )

        failures = [check for check in checks if not check.passed]
        return {
            "schema_version": 1,
            "decision": "DENY" if failures else "ADMIT",
            "mission_id": contract.get("mission_id"),
            "contract_id": contract.get("contract_id"),
            "request_id": request.get("request_id"),
            "checks": [check.as_dict() for check in checks],
            "reason_codes": sorted({check.code for check in failures}),
        }


class ActivationService:
    """Activate and reconcile canonical repository records as one transaction."""

    def __init__(
        self,
        root: Path,
        eos_sync: Callable[[], None] | None = None,
        fault_after: str | None = None,
    ):
        self.root = root.resolve()
        self.eos_sync = eos_sync
        self.fault_after = fault_after
        self.transaction_dir = self.root / "engineering/mission-contracts/transactions"
        self.evidence_dir = self.root / "engineering/evidence/mission-activations"

    def _fault(self, phase: str) -> None:
        if self.fault_after == phase:
            raise MissionContractError(f"injected activation failure after {phase}")

    def _project_state(self, original: bytes, contract: Mapping[str, Any]) -> bytes:
        text = original.decode()
        marker = "\n## Operational Mission Activation\n"
        if marker in text:
            text = text.split(marker, 1)[0].rstrip() + "\n"
        block = (
            f"{marker}\n"
            f"- Mission: `{contract['mission_id']}`\n"
            f"- Mission Contract: `{contract['contract_id']}`\n"
            "- Lifecycle: `ACTIVE`\n"
            "- Publication execution: not started\n"
        )
        return (text.rstrip() + "\n" + block).encode()

    def _registry_state(
        self,
        original: bytes,
        contract: Mapping[str, Any],
        request: Mapping[str, Any],
        transaction_id: str,
        timestamp: str,
    ) -> bytes:
        """Patch the one bound item without reserializing unrelated user content."""
        text = original.decode()
        registry = yaml.safe_load(text)
        previous_registry_revision = int(registry.get("revision", 0))
        next_registry_revision = previous_registry_revision + 1
        text = text.replace(
            f"revision: {previous_registry_revision}\nupdated_at:",
            f"revision: {next_registry_revision}\nupdated_at:",
            1,
        )
        old_updated = str(registry.get("updated_at"))
        text = text.replace(
            f"updated_at: '{old_updated}'\nserialization:",
            f"updated_at: '{timestamp}'\nserialization:",
            1,
        )
        mutation = (
            f"- revision: {next_registry_revision}\n"
            f"  previous_revision: {previous_registry_revision}\n"
            f"  at: '{timestamp}'\n"
            f"  actor: {request['actor']}\n"
            f"  action: activate {contract['registry_id']}\n"
            f"  reason: Reconcile atomic activation of Mission Contract "
            f"{contract['contract_id']} in {transaction_id}.\n"
        )
        boundary = "authority_boundary:\n"
        if boundary not in text:
            raise MissionContractError("registry authority boundary is unresolved")
        text = text.replace(boundary, mutation + boundary, 1)

        marker = f"  - registry_id: {contract['registry_id']}\n"
        start = text.find(marker)
        if start < 0:
            raise MissionContractError("registry reconciliation cardinality failed")
        end = text.find("\n  - registry_id:", start + len(marker))
        if end < 0:
            end = text.find("\n  queues:", start)
        item = text[start:end]
        item_value = next(
            entry for entry in registry["entities"]["work_items"]
            if entry.get("registry_id") == contract["registry_id"]
        )
        item_state = item_value.get("management_state")
        if item_state not in ELIGIBLE_REGISTRY_STATES:
            raise MissionContractError("registry item is not eligible for activation")
        if item_state == "ready":
            item = item.replace(
                "    management_state: ready\n",
                "    management_state: active\n",
                1,
            )
        prior_updated = str(item_value.get("updated_at"))
        prior_item_revision = int(item_value.get("revision", 0))
        if item_state == "ready" and prior_updated != "None":
            item = item.replace(
                f"    updated_at: '{prior_updated}'\n",
                f"    updated_at: '{timestamp}'\n",
                1,
            )
        if item_state == "ready":
            item = item.replace(
                f"    revision: {prior_item_revision}\n",
                f"    revision: {prior_item_revision + 1}\n",
                1,
            )
        activation_history = (
            "    - from: ready\n"
            "      to: active\n"
            f"      at: '{timestamp}'\n"
            f"      actor: {request['actor']}\n"
            "      reason: Mission Contract atomic activation\n"
            f"      authority_reference: {request['approval']['locator']}\n"
            f"      mission_contract: {contract['contract_id']}\n"
            f"      transaction_id: {transaction_id}\n"
        )
        if item_state == "ready":
            history_end = item.find("\n    project_id:")
            if history_end < 0:
                history_end = item.find("\n    order:")
            if history_end < 0:
                history_end = len(item)
            item = (
                item[:history_end]
                + "\n"
                + activation_history.rstrip()
                + item[history_end:]
            )
        return (text[:start] + item + text[end:]).encode()

    def _mutations(
        self,
        contract_path: Path,
        contract: dict[str, Any],
        request: Mapping[str, Any],
        transaction_id: str,
    ) -> dict[Path, bytes]:
        timestamp = _now()
        contract["lifecycle"] = "active"
        contract["approvals"]["activation"] = "approved"
        contract["activation"] = {
            "actor": request["actor"],
            "record": request["approval"]["locator"],
            "request": request["request_id"],
            "transaction": transaction_id,
            "timestamp": timestamp,
        }
        contract["contract_digest"] = contract_digest(contract)

        registry_path = self.root / "engineering/registry/work-registry.yaml"
        registry_original = registry_path.read_bytes()

        project_path = self.root / "docs/project/PROJ-0001-PROJECT_STATE.md"
        evidence = {
            "schema_version": 1,
            "evidence_type": "mission-activation",
            "transaction_id": transaction_id,
            "request_id": request["request_id"],
            "mission_id": contract["mission_id"],
            "contract_id": contract["contract_id"],
            "registry_id": contract["registry_id"],
            "result": "COMMITTED",
            "timestamp": timestamp,
        }
        evidence_path = self.evidence_dir / f"{transaction_id}.json"
        return {
            contract_path: _yaml(contract),
            registry_path: self._registry_state(
                registry_original, contract, request, transaction_id, timestamp
            ),
            project_path: self._project_state(project_path.read_bytes(), contract),
            evidence_path: (json.dumps(evidence, indent=2, sort_keys=True) + "\n").encode(),
        }

    def activate(self, request_path: Path) -> dict[str, Any]:
        request = yaml.safe_load(request_path.read_text())
        if not isinstance(request, Mapping):
            raise MissionContractError("activation request must be a mapping")
        required = {
            "request_id", "mission_id", "contract_id", "actor", "approval",
            "expected_lifecycle",
        }
        if required - set(request):
            raise MissionContractError(
                f"activation request fields missing: {sorted(required - set(request))}"
            )
        contract_path = (
            self.root / "engineering/mission-contracts/contracts"
            / f"{request['contract_id']}.yaml"
        )
        transaction_id = f"TX-{request['request_id']}"
        journal_path = self.transaction_dir / f"{transaction_id}.json"
        if journal_path.is_file():
            journal = json.loads(journal_path.read_text())
            if journal.get("state") == "COMMITTED":
                return journal
            if journal.get("state") != "ROLLED_BACK":
                raise MissionContractError(
                    f"incomplete transaction requires recovery: {transaction_id}"
                )

        lock_path = self.transaction_dir / ".activation.lock"
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        with lock_path.open("a+b") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            contract = load(contract_path)
            if contract.get("lifecycle") in TERMINAL:
                raise MissionContractError("terminal Mission Contract cannot activate")
            if contract.get("lifecycle") != request["expected_lifecycle"]:
                raise MissionContractError(
                    f"expected lifecycle {request['expected_lifecycle']}, "
                    f"observed {contract.get('lifecycle')}"
                )
            active = [
                value for _, value in Resolver(self.root).contracts()
                if value.get("lifecycle") == "active"
                and value.get("contract_id") != contract.get("contract_id")
            ]
            if active:
                raise MissionContractError("another active Mission Contract conflicts")
            admission = Admission(self.root).decide(contract_path, request)
            if admission["decision"] != "ADMIT":
                raise MissionContractError(
                    f"mission admission denied: {','.join(admission['reason_codes'])}"
                )

            mutations = self._mutations(contract_path, contract, request, transaction_id)
            before = {
                str(path.relative_to(self.root)): (
                    path.read_bytes().hex() if path.exists() else None
                )
                for path in mutations
            }
            journal = {
                "schema_version": 1,
                "transaction_id": transaction_id,
                "request_id": request["request_id"],
                "state": "PREPARED",
                "admission": admission,
                "before": before,
                "intended_sha256": {
                    str(path.relative_to(self.root)): hashlib.sha256(data).hexdigest()
                    for path, data in mutations.items()
                },
            }
            _atomic_write(
                journal_path,
                (json.dumps(journal, indent=2, sort_keys=True) + "\n").encode(),
            )
            try:
                for path, data in mutations.items():
                    _atomic_write(path, data)
                journal["state"] = "REPOSITORY_WRITTEN"
                _atomic_write(journal_path, (json.dumps(journal, indent=2, sort_keys=True) + "\n").encode())
                self._fault("repository")

                resolution = Resolver(self.root).resolve(str(request["mission_id"]))
                if resolution["resolution"] != "AUTHORIZED" or resolution["active_count"] != 1:
                    raise MissionContractError(
                        f"post-activation resolution failed: {resolution['resolution']}"
                    )
                registry = yaml.safe_load(
                    (self.root / "engineering/registry/work-registry.yaml").read_text()
                )
                registry_matches = [
                    item for item in registry["entities"]["work_items"]
                    if item.get("registry_id") == contract["registry_id"]
                    and item.get("management_state") == "active"
                ]
                if len(registry_matches) != 1:
                    raise MissionContractError("registry did not reconcile")
                self._fault("reconciliation")
                if self.eos_sync:
                    self.eos_sync()
                self._fault("eos")
                journal["state"] = "COMMITTED"
                journal["completed_at"] = _now()
                journal["resolution"] = resolution
                _atomic_write(journal_path, (json.dumps(journal, indent=2, sort_keys=True) + "\n").encode())
                return journal
            except Exception as error:
                for relative, encoded in before.items():
                    path = self.root / relative
                    if encoded is None:
                        path.unlink(missing_ok=True)
                    else:
                        _atomic_write(path, bytes.fromhex(encoded))
                eos_rollback_failure = None
                if self.eos_sync:
                    try:
                        self.eos_sync()
                    except Exception as rollback_error:
                        eos_rollback_failure = str(rollback_error)
                journal["state"] = "ROLLED_BACK"
                journal["failure"] = str(error)
                if eos_rollback_failure:
                    journal["eos_rollback_failure"] = eos_rollback_failure
                journal["rolled_back_at"] = _now()
                _atomic_write(journal_path, (json.dumps(journal, indent=2, sort_keys=True) + "\n").encode())
                raise

    def recover(self, transaction_id: str) -> dict[str, Any]:
        journal_path = self.transaction_dir / f"{transaction_id}.json"
        journal = json.loads(journal_path.read_text())
        if journal["state"] in {"COMMITTED", "ROLLED_BACK"}:
            return journal
        for relative, encoded in journal["before"].items():
            path = self.root / relative
            if encoded is None:
                path.unlink(missing_ok=True)
            else:
                _atomic_write(path, bytes.fromhex(encoded))
        eos_rollback_failure = None
        if self.eos_sync:
            try:
                self.eos_sync()
            except Exception as error:
                eos_rollback_failure = str(error)
        journal["state"] = "ROLLED_BACK"
        journal["failure"] = "interrupted transaction recovered from before-images"
        if eos_rollback_failure:
            journal["eos_rollback_failure"] = eos_rollback_failure
        journal["rolled_back_at"] = _now()
        _atomic_write(journal_path, (json.dumps(journal, indent=2, sort_keys=True) + "\n").encode())
        return journal
