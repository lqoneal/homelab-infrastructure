#!/usr/bin/env python3
"""Canonical repository discovery and engineering execution-state pipeline."""

from __future__ import annotations

import argparse
import fnmatch
import json
import subprocess
from pathlib import Path
from typing import Any, Mapping

import yaml

from scripts.lib.eos.assurance_language import AssuranceLanguage, AssuranceLanguageError
from scripts.lib.eos.convergence_runtime import ConvergenceRuntime


class ExecutionInterfaceError(ValueError):
    """The repository execution interface cannot resolve safely."""


def _load(path: Path) -> Mapping[str, Any]:
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as error:
        raise ExecutionInterfaceError(f"cannot read {path}: {error}") from error
    if not isinstance(value, Mapping):
        raise ExecutionInterfaceError(f"{path} must contain a mapping")
    return value


def _norm(value: Any) -> str:
    return str(value).strip().lower().replace(" ", "_")


class ExecutionInterface:
    """Resolve all execution surfaces from one repository-authoritative pipeline."""

    def __init__(self, root: Path | str):
        self.root = Path(root).resolve()
        self.manifest_path = self.root / "engineering/execution/execution-interface.yaml"
        self.registry_path = self.root / "engineering/registry/work-registry.yaml"
        self.manifest = _load(self.manifest_path)
        self.registry = _load(self.registry_path)
        if self.manifest.get("schema_version") not in {2, 3}:
            raise ExecutionInterfaceError("unsupported execution-interface schema")

    def _git(self, *arguments: str) -> str:
        result = subprocess.run(
            ["git", "-C", str(self.root), *arguments],
            text=True,
            capture_output=True,
            check=False,
        )
        if result.returncode:
            raise ExecutionInterfaceError(
                result.stderr.strip() or "repository inspection failed"
            )
        return result.stdout.strip()

    def convergence(self) -> ConvergenceRuntime:
        """Return the SPEC-0014 runtime; it is independent of legacy projections."""
        if self.manifest.get("schema_version") != 3:
            raise ExecutionInterfaceError("convergence runtime requires interface schema 3")
        return ConvergenceRuntime(self.root)

    def resolve_implementation_wop(
        self, *, wop_id: str, revision: str | int, action: str,
        correlation_id: str, authority_record_id: str | None = None,
    ) -> dict[str, Any]:
        return self.convergence().resolve(
            wop_id=wop_id, revision=revision, action=action,
            correlation_id=correlation_id, authority_record_id=authority_record_id,
        )

    def _controlled_documents(self) -> dict[str, list[dict[str, Any]]]:
        records: dict[str, list[dict[str, Any]]] = {}
        for path in sorted(self.root.glob("**/*.md")):
            if ".git" in path.parts:
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except OSError:
                continue
            if path.name == "PMCT-CONTRACT.md":
                version = next(
                    (
                        line.partition(":")[2].strip()
                        for line in text.splitlines()
                        if line.startswith("Version:")
                    ),
                    "",
                )
                records.setdefault("PMCT-CONTRACT", []).append(
                    {
                        "document_id": "PMCT-CONTRACT",
                        "version": version,
                        "status": "Active",
                        "path": str(path.relative_to(self.root)),
                    }
                )
                continue
            if not text.startswith("---\n"):
                continue
            end = text.find("\n---", 4)
            if end < 0:
                continue
            try:
                metadata = yaml.safe_load(text[4:end])
            except yaml.YAMLError:
                continue
            if isinstance(metadata, Mapping) and metadata.get("document_id"):
                record = dict(metadata)
                record["path"] = str(path.relative_to(self.root))
                records.setdefault(str(metadata["document_id"]), []).append(record)
        return records

    def _resolve_owners(self) -> dict[str, dict[str, Any]]:
        documents = self._controlled_documents()
        resolved: dict[str, dict[str, Any]] = {}
        seen_owner_revision: dict[tuple[str, str], str] = {}
        for capability, binding in self.manifest.get("semantic_bindings", {}).items():
            if not isinstance(binding, Mapping):
                raise ExecutionInterfaceError(f"invalid binding for {capability}")
            owner, revision = str(binding.get("owner", "")), str(binding.get("revision", ""))
            matches = [
                item for item in documents.get(owner, [])
                if str(item.get("version")) == revision
            ]
            if len(matches) != 1:
                raise ExecutionInterfaceError(
                    f"semantic owner {owner}@{revision} for {capability} "
                    f"resolved {len(matches)} times"
                )
            status = _norm(matches[0].get("status"))
            if status not in {"active", "draft"}:
                raise ExecutionInterfaceError(
                    f"semantic owner {owner}@{revision} has unavailable status {status}"
                )
            key = (owner, revision)
            # One document may intentionally own multiple distinct capabilities.
            prior = seen_owner_revision.get(key)
            if prior and matches[0]["path"] != resolved[prior]["path"]:
                raise ExecutionInterfaceError(f"conflicting owner identity {owner}@{revision}")
            seen_owner_revision[key] = capability
            resolved[capability] = {
                "document_id": owner,
                "revision": revision,
                "status": matches[0].get("status"),
                "path": matches[0]["path"],
                "mission_assurance_requirements": matches[0].get(
                    "mission_assurance_requirements", []
                ),
            }
        if not resolved:
            raise ExecutionInterfaceError("no semantic bindings resolved")
        return resolved

    def assurance_requirements(self) -> list[dict[str, Any]]:
        """Resolve requirement declarations from their controlled owners."""
        owners = self._resolve_owners()
        language_definition = self.assurance_language_definition(owners)
        try:
            language = AssuranceLanguage(self.root, language_definition)
        except AssuranceLanguageError as error:
            raise ExecutionInterfaceError(str(error)) from error
        requirements: list[dict[str, Any]] = []
        identities: dict[str, str] = {}
        consumed_owners: set[tuple[str, str, str]] = set()
        for capability, owner in sorted(owners.items()):
            owner_key = (owner["document_id"], owner["revision"], owner["path"])
            if owner_key in consumed_owners:
                continue
            consumed_owners.add(owner_key)
            declared = owner.get("mission_assurance_requirements", [])
            if not isinstance(declared, list):
                raise ExecutionInterfaceError(
                    f"{owner['document_id']}@{owner['revision']} assurance "
                    "requirements must be a list"
                )
            for raw in declared:
                if not isinstance(raw, Mapping):
                    raise ExecutionInterfaceError(
                        f"{owner['document_id']}@{owner['revision']} has an "
                        "invalid assurance requirement"
                    )
                requirement = dict(raw)
                try:
                    language.validate_declaration(requirement)
                except AssuranceLanguageError as error:
                    raise ExecutionInterfaceError(
                        f"{owner['document_id']}@{owner['revision']}: {error}"
                    ) from error
                identity = str(requirement["id"])
                source = f"{owner['document_id']}@{owner['revision']}"
                if identity in identities:
                    raise ExecutionInterfaceError(
                        f"conflicting assurance requirement {identity}: "
                        f"{identities[identity]} and {source}"
                    )
                identities[identity] = source
                requirement["authoritative_source"] = {
                    "document_id": owner["document_id"],
                    "revision": owner["revision"],
                    "path": owner["path"],
                    "capability_binding": capability,
                }
                requirements.append(requirement)
        if not requirements:
            raise ExecutionInterfaceError(
                "no mission assurance requirements resolved from controlled owners"
            )
        phases = {item["phase"] for item in requirements}
        missing_phases = sorted(set(language.phases) - phases)
        if missing_phases:
            raise ExecutionInterfaceError(
                f"mission assurance requirement phases unresolved: {missing_phases}"
            )
        return sorted(requirements, key=lambda item: (item["phase"], item["id"]))

    def assurance_language_definition(
        self, owners: Mapping[str, Mapping[str, Any]] | None = None
    ) -> dict[str, Any]:
        """Resolve the exact controlled assurance-language revision."""
        resolved = owners if owners is not None else self._resolve_owners()
        owner = resolved.get("assurance_language")
        if not isinstance(owner, Mapping):
            raise ExecutionInterfaceError("assurance language binding is unresolved")
        documents = self._controlled_documents()
        matches = [
            item for item in documents.get(str(owner["document_id"]), [])
            if str(item.get("version")) == str(owner["revision"])
        ]
        if len(matches) != 1:
            raise ExecutionInterfaceError(
                f"assurance language {owner['document_id']}@{owner['revision']} "
                f"resolved {len(matches)} times"
            )
        definition = matches[0].get("assurance_language")
        if not isinstance(definition, Mapping):
            raise ExecutionInterfaceError("controlled assurance language is missing")
        value = dict(definition)
        value["authoritative_source"] = {
            "document_id": owner["document_id"],
            "revision": owner["revision"],
            "path": owner["path"],
        }
        return value

    def _contract_paths(self) -> list[Path]:
        paths: list[Path] = []
        patterns = self.manifest.get("legacy_mission_projection", {}).get("search_paths", [])
        if not isinstance(patterns, list) or not patterns:
            raise ExecutionInterfaceError("mission contract discovery is not configured")
        for pattern in patterns:
            paths.extend(self.root.glob(str(pattern)))
        return sorted(set(paths))

    def discover_mission_contracts(self, mission: str | None = None) -> dict[str, Any]:
        """Return discovery evidence before applying the cardinality gate."""
        candidates: list[str] = []
        for path in self._contract_paths():
            value = _load(path)
            if value.get("document_type") != "MissionContract":
                continue
            if mission is None:
                if _norm(value.get("status")) != "active":
                    continue
            elif value.get("mission_id") != mission:
                continue
            candidates.append(str(path.relative_to(self.root)))
        return {
            "search_paths": list(
                self.manifest.get("legacy_mission_projection", {}).get("search_paths", [])
            ),
            "candidate_paths": sorted(candidates),
            "count": len(candidates),
        }

    def mission(self, mission: str | None = None) -> Mapping[str, Any]:
        discovery = self.discover_mission_contracts(mission)
        if discovery["count"] != 1:
            raise ExecutionInterfaceError(
                "expected exactly one repository Mission Contract, "
                f"derived {discovery['count']} from discovery; "
                f"candidates={discovery['candidate_paths']}"
            )
        path = self.root / discovery["candidate_paths"][0]
        contract = _load(path)
        registry_id = contract.get("registry_id")
        registry_matches = [
            item
            for item in self.registry.get("entities", {}).get("work_items", [])
            if isinstance(item, Mapping) and item.get("registry_id") == registry_id
        ]
        if len(registry_matches) != 1:
            raise ExecutionInterfaceError(
                f"Mission Contract registry binding {registry_id} resolved "
                f"{len(registry_matches)} times"
            )
        if registry_matches[0].get("scope") != contract.get("mission_id"):
            raise ExecutionInterfaceError("Mission Contract and registry scope conflict")
        result = dict(contract)
        result["_path"] = str(path.relative_to(self.root))
        result["_registry"] = dict(registry_matches[0])
        return result

    def _derive_blockers(
        self, contract: Mapping[str, Any], owners: Mapping[str, Any]
    ) -> list[str]:
        blockers: list[str] = []
        if str(self.root) != str(contract.get("repository_identity")):
            blockers.append("REPOSITORY_IDENTITY_MISMATCH")
        if not owners:
            blockers.append("SEMANTIC_OWNERS_UNRESOLVED")
        if _norm(contract.get("status")) not in {"active", "completed"}:
            blockers.append("MISSION_LIFECYCLE_INELIGIBLE")
        authority = contract.get("authority", {})
        if authority.get("applies_to") != contract.get("mission_id"):
            blockers.append("AUTHORITY_TARGET_MISMATCH")
        if authority.get("reusable_for_other_missions") is not False:
            blockers.append("AUTHORITY_REUSE_NOT_PROHIBITED")
        for gate, state in contract.get("review_gates", {}).items():
            if state.get("required") and _norm(state.get("state")) not in {
                "approved", "not_recorded"
            }:
                blockers.append(f"REVIEW_GATE_{gate.upper()}_{_norm(state.get('state')).upper()}")
            if (
                gate != "operator_acceptance"
                and state.get("required")
                and _norm(state.get("state")) != "approved"
            ):
                blockers.append(f"REVIEW_GATE_{gate.upper()}_NOT_APPROVED")
        wop = contract.get("wop", {})
        applicability = _norm(wop.get("applicability"))
        if applicability not in {"applicable", "not_applicable"}:
            blockers.append("WOP_APPLICABILITY_UNRESOLVED")
        elif applicability == "applicable" and not wop.get("references"):
            blockers.append("APPLICABLE_WOP_MISSING")
        elif applicability == "not_applicable" and not wop.get("reason"):
            blockers.append("WOP_NON_APPLICABILITY_UNJUSTIFIED")
        declared = str(contract.get("next_authorized_action", ""))
        if not declared:
            blockers.append("NEXT_AUTHORIZED_ACTION_UNRESOLVED")
        return sorted(set(blockers))

    def resolve(self, mission: str | None = None) -> dict[str, Any]:
        owners = self._resolve_owners()
        contract = self.mission(mission)
        registry = contract["_registry"]
        status = _norm(contract.get("status")).upper()
        registry_status = _norm(registry.get("management_state")).upper()
        blockers = self._derive_blockers(contract, owners)
        if status != registry_status:
            blockers.append("MISSION_REGISTRY_LIFECYCLE_CONFLICT")
        changed = self._git("status", "--porcelain=v1").splitlines()
        return {
            "schema_version": 2,
            "repository": {
                "identity": str(Path(self._git("rev-parse", "--show-toplevel")).resolve()),
                "branch": self._git("branch", "--show-current"),
                "head": self._git("rev-parse", "HEAD"),
                "working_tree": "CLEAN" if not changed else "MODIFIED",
                "changed_paths": sorted(line[3:] for line in changed if len(line) > 3),
            },
            "mission": {
                "id": contract["mission_id"],
                "registry_id": contract["registry_id"],
                "title": contract["title"],
                "revision": contract["revision"],
                "status": status,
                "classification": contract["classification"],
                "project_id": contract["project_id"],
            },
            "phase": {
                "id": contract["phase_id"],
                "mission_record_id": contract["mission_record_id"],
            },
            "contract": {
                "path": contract["_path"],
                "objective": contract["objective"],
                "scope": contract["scope"],
                "completion_criteria": contract["completion_criteria"],
                "source_records": contract["source_records"],
            },
            "authority": contract["authority"],
            "command_permissions": contract["command_permissions"],
            "review_gates": contract["review_gates"],
            "wop": contract["wop"],
            "controlled_owners": owners,
            "lifecycle": contract["lifecycle"],
            "blockers": sorted(set(blockers)),
            "next_authorized_action": contract["next_authorized_action"],
            "sources": sorted(
                {
                    str(self.manifest_path.relative_to(self.root)),
                    str(self.registry_path.relative_to(self.root)),
                    contract["_path"],
                    *[item["path"] for item in owners.values()],
                    *contract["source_records"],
                }
            ),
        }

    def inventory(self) -> dict[str, Any]:
        snapshot = self.resolve()
        return {
            "interface_id": self.manifest["interface_id"],
            "operational_owner": self.manifest["operational_owner"],
            "bindings": snapshot["controlled_owners"],
            "routes": dict(self.manifest["routes"]),
        }

    def snapshot(self, mission: str | None = None) -> dict[str, Any]:
        return self.resolve(mission)

    def qualify(self, mission: str) -> dict[str, Any]:
        """Qualify one mission through the canonical operational pipeline."""
        discovery = self.discover_mission_contracts(mission)
        if discovery["count"] != 1:
            raise ExecutionInterfaceError(
                f"mission qualification failed closed: derived "
                f"{discovery['count']} Mission Contracts; "
                f"candidates={discovery['candidate_paths']}"
            )
        snapshot = self.resolve(mission)
        lifecycle = snapshot["lifecycle"]
        required = {
            "state": lifecycle.get("state"),
            "implementation_status": lifecycle.get("implementation_status"),
            "acceptance_status": lifecycle.get("acceptance_status"),
            "blockers": snapshot.get("blockers"),
            "review_gates": snapshot.get("review_gates"),
            "next_authorized_action": snapshot.get("next_authorized_action"),
        }
        unresolved = sorted(
            key for key, value in required.items() if value is None or value == ""
        )
        if unresolved:
            raise ExecutionInterfaceError(
                f"mission qualification fields unresolved: {unresolved}"
            )
        return {
            "result": "PASS",
            "interface": self.manifest["interface_id"],
            "mission_contract_count": discovery["count"],
            "mission_contract_discovery": discovery,
            "mission_id": snapshot["mission"]["id"],
            "mission_contract": snapshot["contract"]["path"],
            "lifecycle_state": lifecycle["state"],
            "implementation_status": lifecycle["implementation_status"],
            "acceptance_status": lifecycle["acceptance_status"],
            "blockers": snapshot["blockers"],
            "approvals": snapshot["review_gates"],
            "next_authorized_action": snapshot["next_authorized_action"],
            "snapshot": snapshot,
        }

    def validate_handoff(self, path: Path | str) -> dict[str, Any]:
        value = _load(Path(path))
        required = {"mission", "procedure", "action", "completion_report"}
        missing, extra = sorted(required - set(value)), sorted(set(value) - required)
        expected = {
            "procedure": "Engineering Work Initiation Procedure",
            "action": "Complete the mission.",
            "completion_report": "Produce the completion report.",
        }
        mismatched = [key for key, item in expected.items() if value.get(key) != item]
        if missing or extra or mismatched:
            raise ExecutionInterfaceError(
                f"invalid minimal handoff: missing={missing}, extra={extra}, "
                f"mismatched={mismatched}"
            )
        snapshot = self.resolve(str(value["mission"]))
        if snapshot["blockers"]:
            raise ExecutionInterfaceError(
                f"handoff blocked by repository state: {snapshot['blockers']}"
            )
        if snapshot["mission"]["status"] != "ACTIVE":
            raise ExecutionInterfaceError("handoff mission is not active")
        if snapshot["next_authorized_action"] != "EXECUTE_P2_038_CORRECTIVE":
            raise ExecutionInterfaceError("handoff action is not currently authorized")
        return {"result": "PASS", "handoff": dict(value), "snapshot": snapshot}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository", type=Path, required=True)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("inventory")
    snapshot = sub.add_parser("snapshot")
    snapshot.add_argument("--mission")
    qualify = sub.add_parser("qualify")
    qualify.add_argument("mission")
    validate = sub.add_parser("validate-handoff")
    validate.add_argument("path", type=Path)
    args = parser.parse_args(argv)
    try:
        interface = ExecutionInterface(args.repository)
        value = (
            interface.inventory()
            if args.command == "inventory"
            else interface.snapshot(args.mission)
            if args.command == "snapshot"
            else interface.qualify(args.mission)
            if args.command == "qualify"
            else interface.validate_handoff(args.path)
        )
    except ExecutionInterfaceError as error:
        print(f"FAIL: {error}", file=__import__("sys").stderr)
        return 78
    print(json.dumps(value, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
