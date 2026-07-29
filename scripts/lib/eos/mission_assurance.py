#!/usr/bin/env python3
"""Independent, read-only mission assurance over authoritative execution state."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from scripts.lib.eos.assurance_language import AssuranceLanguage, AssuranceLanguageError
from scripts.lib.eos.execution_interface import ExecutionInterface, ExecutionInterfaceError


class MissionAssuranceError(ValueError):
    """Mission assurance cannot resolve authoritative state safely."""


def _digest(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


class MissionAssurance:
    """Verify lifecycle obligations without owning or mutating their source state."""

    def __init__(self, root: Path | str):
        self.root = Path(root).resolve()
        self.interface = ExecutionInterface(self.root)
        try:
            self.language = AssuranceLanguage(
                self.root, self.interface.assurance_language_definition()
            )
        except (AssuranceLanguageError, ExecutionInterfaceError) as error:
            raise MissionAssuranceError(str(error)) from error

    def capabilities(self) -> dict[str, Any]:
        value = {
            "schema_version": 1,
            "capability": "ZEUS_MISSION_ASSURANCE",
            "mode": "READ_ONLY_INDEPENDENT_VERIFICATION",
            "authoritative_interface": self.interface.manifest["interface_id"],
            "language": {
                "id": self.language.language_id,
                "version": self.language.version,
                "authoritative_source": self.language.definition["authoritative_source"],
            },
            "phases": list(self.language.phases),
            "commands": [
                "zeus mission requirements <MISSION-ID>",
                "zeus mission preflight <MISSION-ID>",
                "zeus mission verify <MISSION-ID>",
                "zeus mission synchronization <MISSION-ID>",
            ],
            "lifecycle_ownership": "PRESERVED",
        }
        return {**value, "evidence_digest": _digest(value)}

    def _discovery(self, mission_id: str) -> dict[str, Any]:
        discovery = self.interface.discover_mission_contracts(mission_id)
        return {
            "search_paths": discovery["search_paths"],
            "candidate_paths": discovery["candidate_paths"],
            "mission_contract_count": discovery["count"],
            "requirement": "exactly_one_mission_contract",
            "satisfied": discovery["count"] == 1,
        }

    def _state(self, mission_id: str) -> tuple[dict[str, Any], dict[str, Any]]:
        discovery = self._discovery(mission_id)
        if not discovery["satisfied"]:
            raise MissionAssuranceError(
                f"mission contract cardinality failed for {mission_id}: "
                f"derived {discovery['mission_contract_count']}, expected exactly 1; "
                f"candidates={discovery['candidate_paths']}"
            )
        try:
            return discovery, self.interface.resolve(mission_id)
        except ExecutionInterfaceError as error:
            raise MissionAssuranceError(str(error)) from error

    def _clause(self, clause: Mapping[str, Any], context: Mapping[str, Any]) -> tuple[bool, Any]:
        try:
            return self.language.evaluate(clause, context)
        except AssuranceLanguageError as error:
            raise MissionAssuranceError(str(error)) from error

    def _requirements(
        self, mission_id: str, discovery: dict[str, Any], state: dict[str, Any]
    ) -> list[dict[str, Any]]:
        context = {
            "root": str(self.root),
            "mission_id": mission_id,
            "discovery": discovery,
            "state": state,
        }
        try:
            declarations = self.interface.assurance_requirements()
        except ExecutionInterfaceError as error:
            raise MissionAssuranceError(str(error)) from error
        resolved = []
        for declaration in declarations:
            controlled_declaration = {
                key: value for key, value in declaration.items()
                if key != "authoritative_source"
            }
            try:
                self.language.validate_declaration(controlled_declaration)
            except AssuranceLanguageError as error:
                raise MissionAssuranceError(str(error)) from error
            applicable = True
            applicability_observed: Any = None
            if "applicability" in declaration:
                applicable, applicability_observed = self._clause(
                    declaration["applicability"], context
                )
            satisfied, observed = (
                self._clause(declaration["assertion"], context)
                if applicable else (True, None)
            )
            resolved.append({
                "id": declaration["id"],
                "phase": declaration["phase"],
                "description": declaration["description"],
                "authoritative_source": declaration["authoritative_source"],
                "applicable": applicable,
                "applicability_observed": applicability_observed,
                "observed": observed,
                "status": "SATISFIED" if satisfied else "UNSATISFIED",
            })
        return resolved

    def requirements(self, mission_id: str) -> dict[str, Any]:
        discovery, state = self._state(mission_id)
        requirements = self._requirements(mission_id, discovery, state)
        value = {
            "schema_version": 1,
            "language_version": self.language.version,
            "mission_id": mission_id,
            "discovery": discovery,
            "requirements": requirements,
            "authoritative_sources": state["sources"],
        }
        return {**value, "evidence_digest": _digest(value)}

    def evaluate(self, mission_id: str, phase: str) -> dict[str, Any]:
        if phase not in self.language.phases:
            raise MissionAssuranceError(f"unknown assurance phase: {phase}")
        resolved = self.requirements(mission_id)
        selected = [
            item for item in resolved["requirements"]
            if item["phase"] == phase and item["applicable"]
        ]
        unsatisfied = [item["id"] for item in selected if item["status"] != "SATISFIED"]
        value = {
            "schema_version": 1,
            "language_version": self.language.version,
            "mission_id": mission_id,
            "phase": phase,
            "result": "PASS" if selected and not unsatisfied else "FAIL",
            "eligible": bool(selected) and not unsatisfied,
            "requirement_count": len(selected),
            "satisfied_count": len(selected) - len(unsatisfied),
            "unsatisfied_requirements": unsatisfied,
            "requirements": selected,
            "discovery": resolved["discovery"],
            "authoritative_sources": resolved["authoritative_sources"],
        }
        return {**value, "evidence_digest": _digest(value)}

    def verify(self, mission_id: str) -> dict[str, Any]:
        evaluations = {
            phase: self.evaluate(mission_id, phase) for phase in self.language.phases
        }
        value = {
            "schema_version": 1,
            "language_version": self.language.version,
            "mission_id": mission_id,
            "result": (
                "PASS"
                if all(item["result"] == "PASS" for item in evaluations.values())
                else "FAIL"
            ),
            "evaluations": evaluations,
        }
        legacy_names = {
            "preflight": "pre_mission_readiness",
            "execution": "execution_eligibility",
            "synchronization": "synchronization_status",
            "closeout": "closeout_eligibility",
        }
        value.update({
            output_name: evaluations[phase]
            for phase, output_name in legacy_names.items()
            if phase in evaluations
        })
        return {**value, "evidence_digest": _digest(value)}
