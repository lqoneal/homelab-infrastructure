"""Current, discoverable, fail-closed authority for protected Zeus operations."""

from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

import yaml

from scripts.lib.emp import progressive_oa
from scripts.lib.emp.wop_admission import verify_accepted_record
from scripts.lib.eos.mission_contract import MissionContractError, Resolver


AUTHORIZED = "AUTHORIZED"
DENIAL_STATES = {
    "UNAUTHORIZED", "MISSING", "MALFORMED", "AMBIGUOUS", "STALE",
    "MISMATCHED", "INCOMPLETE", "CONFLICTED", "REVOKED", "INACTIVE",
}
EXPECTED_REMOTE = "git@github.com:lqoneal/homelab-infrastructure.git"


class ControlledMissionAuthorityError(ValueError):
    """A protected operation has no valid current authority."""

    def __init__(self, result: Mapping[str, Any]):
        self.result = dict(result)
        super().__init__(
            f"{self.result.get('resolution', 'UNAUTHORIZED')}: "
            f"{self.result.get('reason', 'authority validation failed')}"
        )


def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load(path: Path) -> dict[str, Any]:
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as error:
        raise ValueError(f"{path}: {error}") from error
    if not isinstance(value, dict):
        raise ValueError(f"{path}: mapping required")
    return value


def _git(root: Path, *arguments: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), *arguments],
        text=True, capture_output=True, check=False,
    )
    if result.returncode:
        raise ValueError(result.stderr.strip() or f"git {' '.join(arguments)} failed")
    return result.stdout.strip()


def _denied(
    resolution: str, reason: str, checks: list[dict[str, Any]],
    *, source: str | None = None,
) -> dict[str, Any]:
    value = {
        "schema_version": 1,
        "resolution": resolution,
        "authorized": False,
        "current": False,
        "reason": reason,
        "failed_check": next(
            (item["check"] for item in checks if item["result"] != "PASS"),
            "authority_resolution",
        ),
        "checks": checks,
        "authority_source": source,
        "next_authorized_action": "STOP_FAIL_CLOSED",
        "protected_effects_allowed": False,
    }
    value["authority_digest"] = _digest(value)
    return value


class ControlledMissionAuthority:
    """Resolve all bindings needed by a protected Progressive OA operation.

    ``sources`` and ``observed`` are explicit seams for deterministic negative
    testing. Production callers omit them and consume repository authority.
    """

    def __init__(
        self,
        root: Path | str,
        *,
        sources: Mapping[str, Path | str | None] | None = None,
        observed: Mapping[str, str] | None = None,
        expected_gate: str = "OA-02",
    ):
        self.root = Path(root).resolve()
        self.expected_gate = expected_gate
        package = self.root / progressive_oa.PACKAGE_PATH
        defaults: dict[str, Path | None] = {
            "contract": None,
            "wop": package / "immutable-wop.yaml",
            "admission": package / (
                "admission/ADMISSION-f01c0c2d-8edb-5567-ad19-8d0f4344909f.json"
            ),
            "state": progressive_oa.state_path(self.root),
            "registry": self.root / "engineering/registry/work-registry.yaml",
            "project_state": self.root / "docs/project/PROJ-0001-PROJECT_STATE.md",
            "eos": self.root / "engineering/eos/repository-eos-authority.yaml",
        }
        try:
            progressive_state = progressive_oa.load_state(self.root)
        except (OSError, ValueError, json.JSONDecodeError):
            progressive_state = {"gates": {}}
        for sequence in range(1, 31):
            gate_id = f"OA-{sequence:02d}"
            locator = (
                progressive_state.get("gates", {}).get(gate_id, {})
                .get("acceptance_receipt")
            )
            if isinstance(locator, str) and locator:
                if Path(locator).name == locator:
                    receipt_path = (
                        package / "runtime" / "decisions" / gate_id / locator
                    )
                else:
                    receipt_path = progressive_oa._resolve_receipt_path(
                        self.root, locator
                    )
            else:
                receipt_path = None
            defaults[f"oa{sequence:02d}_receipt"] = receipt_path
        for key, value in (sources or {}).items():
            defaults[key] = None if value is None else Path(value)
        self.sources = defaults
        self.observed = dict(observed or {})

    def _observe(self) -> dict[str, str]:
        return {
            "repository_root": self.observed.get(
                "repository_root", str(Path(_git(self.root, "rev-parse", "--show-toplevel")).resolve())
            ),
            "repository_identity": self.observed.get("repository_identity", self.root.name),
            "branch": self.observed.get("branch", _git(self.root, "branch", "--show-current")),
            "head": self.observed.get("head", _git(self.root, "rev-parse", "HEAD")),
            "upstream": self.observed.get("upstream", _git(self.root, "rev-parse", "@{upstream}")),
            "remote": self.observed.get("remote", _git(self.root, "remote", "get-url", "origin")),
        }

    def resolve(self, *, boundary: str = "observation") -> dict[str, Any]:
        checks: list[dict[str, Any]] = []

        def passed(name: str, detail: str = "valid") -> None:
            checks.append({"check": name, "result": "PASS", "detail": detail})

        def fail(state: str, name: str, reason: str, source: str | None = None):
            checks.append({"check": name, "result": "FAIL", "detail": reason})
            return _denied(state, reason, checks, source=source)

        try:
            observed = self._observe()
        except ValueError as error:
            return fail("MISSING", "repository", str(error))
        if Path(observed["repository_root"]).resolve() != self.root:
            return fail("MISMATCHED", "repository_root", "repository root mismatch")
        if observed["repository_identity"] != self.root.name:
            return fail("MISMATCHED", "repository_identity", "repository identity mismatch")
        if observed["remote"] != EXPECTED_REMOTE:
            return fail("MISMATCHED", "repository_remote", "repository remote mismatch")
        passed("repository_identity")

        contract_override = self.sources["contract"]
        try:
            if contract_override is None:
                resolution = Resolver(self.root).resolve()
                if resolution.get("resolution") == "AMBIGUOUS_AUTHORITY":
                    return fail("AMBIGUOUS", "mission_contract", "multiple active Mission Contracts")
                if resolution.get("resolution") == "NO_AUTHORIZED_WORK":
                    return fail("MISSING", "mission_contract", "active Mission Contract missing")
                if resolution.get("resolution") == "INVALID_CONTRACT":
                    conditions = resolution.get("unresolved_conditions", [])
                    state = (
                        "UNAUTHORIZED"
                        if any("approval" in str(item).lower() for item in conditions)
                        else "MALFORMED"
                    )
                    return fail(state, "mission_contract", "Mission Contract is invalid")
                if resolution.get("resolution") == "REVOKED_AUTHORITY":
                    return fail("REVOKED", "mission_contract", "Mission Contract is revoked")
                if resolution.get("resolution") != AUTHORIZED:
                    state = (
                        "INACTIVE" if resolution.get("resolution") in {
                            "SUSPENDED_AUTHORITY", "EXPIRED_AUTHORITY"
                        } else "MISMATCHED"
                    )
                    return fail(state, "mission_contract", str(resolution.get("resolution")))
                contract = resolution["contract"]
                contract_path = self.root / resolution["contract_path"]
            else:
                contract_path = contract_override
                contract = _load(contract_path)
                from scripts.lib.eos.mission_contract import validate
                errors = validate(contract, self.root)
                if errors:
                    state = (
                        "UNAUTHORIZED"
                        if any("approval" in item.lower() for item in errors)
                        else "MALFORMED"
                    )
                    return fail(state, "mission_contract", "; ".join(errors), str(contract_path))
        except (OSError, ValueError, MissionContractError) as error:
            return fail("MALFORMED", "mission_contract", str(error), str(contract_override or ""))
        if contract.get("lifecycle") == "revoked":
            return fail("REVOKED", "contract_lifecycle", "Mission Contract is revoked")
        if contract.get("lifecycle") != "active":
            return fail("INACTIVE", "contract_lifecycle", "Mission Contract is not active")
        if any(value != "approved" for value in contract.get("approvals", {}).values()):
            return fail("UNAUTHORIZED", "contract_approvals", "Mission Contract approval missing")
        passed("mission_contract")

        try:
            wop_path = self.sources["wop"]
            if wop_path is None or not wop_path.is_file():
                return fail("MISSING", "wop", "admitted WOP missing")
            wop = _load(wop_path)
        except ValueError as error:
            return fail("MALFORMED", "wop", str(error))
        contract_wop = contract.get("wop", {})
        if (
            contract_wop.get("id") != progressive_oa.PACKAGE
            or contract_wop.get("locator") != str(wop_path.relative_to(self.root))
            or contract_wop.get("digest") != _sha256(wop_path)
        ):
            return fail("MISMATCHED", "wop_binding", "Mission Contract WOP binding mismatch")
        if wop.get("status") != "Active":
            return fail("INACTIVE", "wop_lifecycle", "WOP is not Active")
        passed("wop_binding")

        admission_path = self.sources["admission"]
        if admission_path is None or not admission_path.is_file():
            return fail("MISSING", "package_admission", "package admission receipt missing")
        if not verify_accepted_record(
            admission_path, expected_repository=str(self.root),
            expected_wop=str(wop.get("wop_id")),
        ):
            return fail("MALFORMED", "package_admission", "package admission receipt invalid")
        passed("package_admission")

        try:
            state_path = self.sources["state"]
            if state_path is None:
                return fail("MISSING", "progressive_state", "runtime state missing")
            state = json.loads(state_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            return fail("MALFORMED", "progressive_state", str(error))
        active_gate = state.get("active_gate")
        active = [
            gate_id for gate_id, item in state.get("gates", {}).items()
            if item.get("state") not in ("PENDING", "ACCEPTED")
        ]
        if active != [active_gate] or active_gate != self.expected_gate:
            return fail(
                "CONFLICTED", "active_gate",
                f"{self.expected_gate} is not the sole active gate",
            )
        for gate_id, item in state["gates"].items():
            if gate_id > self.expected_gate and (
                item.get("state") != "PENDING" or item.get("acceptance_receipt") is not None
            ):
                return fail("CONFLICTED", "later_gate", f"unexpected activity at {gate_id}")
        passed("active_gate")

        receipt_bindings: dict[str, tuple[str, str]] = {}
        for sequence in range(1, int(self.expected_gate.split("-")[1])):
            prior_gate = f"OA-{sequence:02d}"
            source_key = f"oa{sequence:02d}_receipt"
            receipt_path = self.sources.get(source_key)
            check_name = f"oa{sequence:02d}_acceptance"
            if receipt_path is None or not receipt_path.is_file():
                return fail("MISSING", check_name, f"{prior_gate} acceptance receipt missing")
            try:
                progressive_oa.verify_receipt(self.root, prior_gate)
                receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
                if receipt.get("receipt_digest") != progressive_oa._receipt_digest(receipt):
                    return fail("MALFORMED", check_name, f"{prior_gate} receipt digest mismatch")
                marker = (
                    self.root / progressive_oa.PACKAGE_PATH
                    / f"runtime/evidence/{prior_gate}/VERIFIED"
                )
                if receipt.get("evidence_marker_sha256") != _sha256(marker):
                    return fail("MALFORMED", check_name, f"{prior_gate} marker binding mismatch")
            except (OSError, ValueError, progressive_oa.ProgressiveOAError) as error:
                return fail("MALFORMED", check_name, str(error))
            receipt_bindings[prior_gate] = (
                str(receipt_path.relative_to(self.root)), _sha256(receipt_path)
            )
            passed(check_name)

        repository = contract.get("repository", {})
        context = wop.get("execution_context", {})
        if (
            repository.get("identity") != observed["repository_identity"]
            or Path(str(repository.get("root", ""))).resolve() != self.root
            or Path(str(context.get("repository", ""))).resolve() != self.root
        ):
            return fail("MISMATCHED", "repository_binding", "authority repository mismatch")
        if repository.get("branch") != observed["branch"] or context.get("branch") != observed["branch"]:
            return fail("MISMATCHED", "branch_binding", "authority branch mismatch")
        if observed["head"] != observed["upstream"]:
            return fail("STALE", "head_binding", "HEAD is not synchronized with upstream")
        for baseline in (repository.get("baseline"), context.get("qualified_baseline")):
            check = subprocess.run(
                ["git", "-C", str(self.root), "merge-base", "--is-ancestor",
                 str(baseline), observed["head"]],
                capture_output=True, check=False,
            )
            if check.returncode:
                return fail("STALE", "qualified_baseline", "qualified baseline is not an ancestor")
        passed("repository_binding")
        passed("qualified_baseline")

        try:
            registry_path = self.sources["registry"]
            registry = _load(registry_path) if registry_path else {}
            items = registry.get("entities", {}).get("work_items", [])
            matches = [
                item for item in items
                if item.get("registry_id") == contract.get("registry_id")
            ]
        except ValueError as error:
            return fail("MALFORMED", "work_registry", str(error))
        if len(matches) != 1:
            return fail("CONFLICTED", "work_registry", "work item binding is missing or ambiguous")
        work_item = matches[0]
        if (
            work_item.get("mission_id") != "EMP-MISSION-ZEUS-OPERATIONAL-ALPHA"
            or str(work_item.get("management_state", "")).lower() != "active"
        ):
            return fail("CONFLICTED", "work_registry", "work item lifecycle or mission mismatch")
        passed("work_registry")

        required = {
            "mission_id": contract.get("mission_id"),
            "contract_id": contract.get("contract_id"),
            "operational_mission_id": work_item.get("mission_id"),
            "work_item_id": contract.get("registry_id"),
            "wop_id": wop.get("wop_id"),
        }
        if any(not value for value in required.values()):
            return fail("INCOMPLETE", "identity_bindings", "authority identity is incomplete")

        result = {
            "schema_version": 1,
            "resolution": AUTHORIZED,
            "authorized": True,
            "current": True,
            "reason": "all controlled mission authority checks passed",
            "failed_check": None,
            "checks": checks,
            **required,
            "wop_locator": str(wop_path.relative_to(self.root)),
            "package_id": progressive_oa.PACKAGE,
            "wop_admission_state": "ACCEPTED",
            "contract_lifecycle": contract["lifecycle"],
            "contract_authorization_status": "AUTHORIZED",
            "repository_identity": observed["repository_identity"],
            "repository_root": observed["repository_root"],
            "branch": observed["branch"],
            "head": observed["head"],
            "upstream": observed["upstream"],
            "qualified_baseline": context["qualified_baseline"],
            "contract_baseline": repository["baseline"],
            "active_gate": active_gate,
            "execution_state": state.get("status"),
            "agent_eligibility": "NOT_APPLICABLE",
            "required_approvals": {
                "implementation": "WOP_AUTHORIZED",
                "verification": "INDEPENDENT_VERIFICATION_REQUIRED",
                "acceptance": "EXPLICIT_OPERATOR_DECISION_REQUIRED",
            },
            "authority_source": str(contract_path.relative_to(self.root)),
            "authority_source_digest": _sha256(contract_path),
            "package_admission_receipt": str(admission_path.relative_to(self.root)),
            "package_admission_digest": _sha256(admission_path),
            "prior_acceptance_receipts": {
                gate: {"locator": locator, "digest": digest}
                for gate, (locator, digest) in receipt_bindings.items()
            },
            "resolution_timestamp": datetime.now(timezone.utc).isoformat(),
            "protected_boundary": boundary,
            "protected_effects_allowed": True,
            "next_authorized_action": progressive_oa.next_action(self.root)["next_action"],
        }
        # Time is observation metadata, not authority identity.
        stable = {
            key: value for key, value in result.items()
            if key not in (
                "resolution_timestamp", "protected_boundary", "authority_digest"
            )
        }
        result["authority_digest"] = _digest(stable)
        if "OA-01" in receipt_bindings:
            result["oa01_acceptance_receipt"], result["oa01_acceptance_digest"] = (
                receipt_bindings["OA-01"]
            )
        if "OA-02" in receipt_bindings:
            result["oa02_acceptance_receipt"], result["oa02_acceptance_digest"] = (
                receipt_bindings["OA-02"]
            )
        if "OA-03" in receipt_bindings:
            result["oa03_acceptance_receipt"], result["oa03_acceptance_digest"] = (
                receipt_bindings["OA-03"]
            )
        return result

    def require(self, *, boundary: str) -> dict[str, Any]:
        result = self.resolve(boundary=boundary)
        if not result.get("authorized"):
            raise ControlledMissionAuthorityError(result)
        return result
