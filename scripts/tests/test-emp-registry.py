#!/usr/bin/env python3
"""Regression tests for the EMP Work Registry model and validator."""

from __future__ import annotations

import copy
import importlib.util
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parent.parent.parent
MODULE_PATH = ROOT / "scripts/lib/emp/registry.py"
SPEC = importlib.util.spec_from_file_location("emp_registry", MODULE_PATH)
assert SPEC and SPEC.loader
registry_module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(registry_module)


def fresh_registry():
    return registry_module.WorkRegistry(
        ROOT / "engineering/registry/work-registry.yaml",
        ROOT / "engineering/registry/work-registry.schema.yaml",
    )


registry = fresh_registry()
assert registry.validate() == []
assert len(registry.objects) == 50
assert {
    "EMP-WORK-CODEX-NTFY-STAGE-1",
    "EMP-WORK-CODEX-NTFY-STAGE-2",
    "EMP-WORK-CODEX-NTFY-STAGE-3",
    "EMP-DEFERRAL-CODEX-NTFY-STAGE-2",
    "EMP-DEFERRAL-CODEX-NTFY-STAGE-3",
    "EMP-WORK-GOVERNANCE-FRAMEWORK-MODERNIZATION",
    "EMP-WORK-CODEX-WRAPPER-ENFORCEMENT",
    "EMP-WORK-ENGINEERING-NOTIFICATION-SERVICE",
    "EMP-MISSION-SPEC-0007-REVISION-15-PUBLICATION",
    "EMP-WORK-SPEC-0007-REVISION-15-PUBLICATION",
    "EMP-MISSION-GOVERNANCE-AUTHORITY-ARCHITECTURE",
    "EMP-WORK-GOVERNANCE-AUTHORITY-ARCHITECTURE",
    "EMP-MISSION-GOVERNANCE-REVIEW-PATTERN-INSTITUTIONALIZATION",
    "EMP-WORK-APPROVAL-PACKAGE-GOVERNANCE-CONTROLS",
    "EMP-WORK-GOVERNANCE-RECORD-TRANSACTION-ARCHITECTURE",
    "EMP-WORK-ENGINEERING-LIFECYCLE-CLOSEOUT-CONTROLS",
    "EMP-WORK-GOVERNANCE-PLANNING-INTEGRATION",
    "EMP-DEFERRAL-APPROVAL-PACKAGE-GOVERNANCE-CONTROLS",
    "EMP-DEFERRAL-GOVERNANCE-RECORD-TRANSACTION-ARCHITECTURE",
    "EMP-DEFERRAL-ENGINEERING-LIFECYCLE-CLOSEOUT-CONTROLS",
    "EMP-DEFERRAL-GOVERNANCE-PLANNING-INTEGRATION",
    "EMP-MILESTONE-GOVERNANCE-AUTHORITY-TRANSACTION-QUALIFIED",
}.issubset(registry.objects)
assert registry.data["serialization"] == "yaml"
assert registry.data["authority_boundary"]["registry"] == "operational-management-state-only"
assert "management_project_id=EMP-PROJECT-HOMELAB" in registry.context("homelab")
assert "management_project_state=active" in registry.context("sprinteros")
assert "management_planned_work=EMP-WORK-SPRINTEROS-PRODUCT" in registry.context("sprinteros")
assert "management_current_phases=EMP-PHASE-SPRINTEROS-1" in registry.context("sprinteros")
assert "management_current_sprints=EMP-SPRINT-SPRINTEROS-1-1" in registry.context("sprinteros")
assert (
    "management_milestones=EMP-MILESTONE-SPRINTEROS-PHASE-1-QUALIFIED"
    in registry.context("sprinteros")
)
assert "management_active_deferrals=none" in registry.context("sprinteros")
assert "management_blocking_dependencies=none" in registry.context("sprinteros")
assert (
    registry.objects["EMP-DEPENDENCY-SPRINTEROS-PHASE-1-QUALIFICATION"]["management_state"]
    == "satisfied"
)
assert any(
    line.startswith("management_completed_work=EMP-WORK-REGISTRY-FOUNDATION")
    for line in registry.context("homelab")
)

try:
    yaml.load("duplicate: one\nduplicate: two\n", Loader=registry_module.UniqueKeyLoader)
except yaml.constructor.ConstructorError:
    pass
else:
    raise AssertionError("duplicate YAML keys were accepted")

duplicate = fresh_registry()
duplicate.data = copy.deepcopy(duplicate.data)
duplicate.data["entities"]["projects"][1]["registry_id"] = "EMP-PROJECT-HOMELAB"
assert any("duplicate registry_id" in error for error in duplicate.validate())

authority = fresh_registry()
authority.data = copy.deepcopy(authority.data)
authority.data["authority_boundary"]["registry"] = "governance-authority"
assert any("authority_boundary" in error for error in authority.validate())

deferral = fresh_registry()
deferral.data = copy.deepcopy(deferral.data)
deferral.data["entities"]["deferrals"] = [
    item
    for item in deferral.data["entities"]["deferrals"]
    if item["registry_id"] != "EMP-DEFERRAL-PRIVATE-AI-PRODUCT"
]
assert any("exactly one active deferral" in error for error in deferral.validate())

dependency = fresh_registry()
dependency.data = copy.deepcopy(dependency.data)
dependency.data["entities"]["dependencies"][0]["prerequisite_id"] = "EMP-WORK-SPRINTEROS-PRODUCT"
assert any("cannot depend on itself" in error for error in dependency.validate())

print("EMP Work Registry tests passed.")
