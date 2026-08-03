"""Canonical rules shared by WOP submission, execution, and authoring."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any

SEMANTIC_WOP_ID = re.compile(r"^WOP-[A-Z0-9]+(?:-[A-Z0-9.]+)+$")
UUID_WOP_ID = re.compile(r"^WOP-[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$")


def is_wop_id(value: Any) -> bool:
    return isinstance(value, str) and bool(SEMANTIC_WOP_ID.fullmatch(value) or UUID_WOP_ID.fullmatch(value))


def validate_optional_approval_date(value: Any) -> bool:
    if value in (None, ""):
        return True
    if not isinstance(value, str):
        return False
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return True

SCHEMA_VERSION = "development-wop/1"
REQUIRED_FIELDS = (
    "wop_id", "mission_id", "title", "objective", "scope", "dependencies",
    "execution_mode", "governance_authority", "repository_identity",
    "effect_profile", "protected_baselines", "gates",
    "qualification_requirements", "completion_requirements",
)
OPTIONAL_FIELDS = ("revision", "priority", "development_operator")
FIELD_DESCRIPTIONS = {
    "wop_id": "Immutable WOP identity (WOP-...)",
    "mission_id": "Mission identity governed by this WOP",
    "title": "Human-readable title",
    "objective": "Bounded engineering objective",
    "scope": "Bounded scope; no production capability work",
    "dependencies": "Prerequisite identities, or none",
    "execution_mode": "DEVELOPMENT",
    "governance_authority": "Issuing authority; normally Engineering Governance",
    "repository_identity": "Canonical repository path or identity",
    "effect_profile": "Non-production effect profile",
    "protected_baselines": "Immutable baseline references",
    "gates": "Validation and lifecycle gates",
    "qualification_requirements": "Evidence required for qualification",
    "completion_requirements": "Evidence required for closeout",
}


def format_description() -> dict:
    return {
        "schema_version": SCHEMA_VERSION,
        "required_fields": list(REQUIRED_FIELDS),
        "optional_fields": list(OPTIONAL_FIELDS),
        "field_descriptions": FIELD_DESCRIPTIONS,
        "supported_sources": ["Markdown", "DOCX", "canonical package directory", "repository-resolved WOP ID"],
        "execution_modes": ["DEVELOPMENT"],
        "governance_authority": "Engineering Governance",
        "package_behavior": "Validate source, construct and validate an immutable package in isolation, then atomically promote it.",
        "validation_sequence": ["extract", "resolve required metadata", "validate package", "preserve source", "verify digest", "promote", "initialize runtime", "submit"],
        "canonical_command": "zeus submit <WOP_ID_OR_SOURCE>",
    }
