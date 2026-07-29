#!/usr/bin/env python3
"""Validation-only fixtures for the governed ETP baseline."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parent.parent.parent
SPEC_PATH = ROOT / "docs/specifications/SPEC-0008-ENGINEERING_TRANSACTION_PROFILE_SPECIFICATION.md"
TPL_PATH = ROOT / "docs/templates/TPL-0001-ENGINEERING_WORK_ORDER_TEMPLATE.md"
HISTORICAL_EWO = ROOT / "docs/work-orders/EWO-000022-SPEC-0007-REVISION-15-CONTROLLED-PUBLICATION.md"


def load_baseline() -> dict:
    text = SPEC_PATH.read_text(encoding="utf-8")
    assert text.count("```yaml etp-profile") == 1, "exactly one baseline ETP is permitted"
    match = re.search(r"```yaml etp-profile\n(.*?)\n```", text, re.DOTALL)
    assert match, "authoritative ETP YAML block missing"
    profile = yaml.safe_load(match.group(1))
    assert isinstance(profile, dict), "ETP block is not a mapping"
    return profile


def resolve(candidates: list[dict], classification: str, additions: set[str], overrides: set[str]) -> dict:
    matches = [
        profile
        for profile in candidates
        if profile.get("status") == "Active"
        and classification in profile.get("mission_classifications", [])
    ]
    if len(matches) != 1:
        raise ValueError("ETP resolution requires exactly one Active compatible profile")
    profile = matches[0]
    permitted = set(profile.get("permitted_additions", []))
    prohibited = set(profile.get("prohibited_overrides", []))
    if not additions <= permitted:
        raise ValueError("transaction addition is not permitted")
    if overrides & prohibited:
        raise ValueError("prohibited override requested")
    if not profile.get("compatibility", {}).get("requires_authority_preservation"):
        raise ValueError("Authority Preservation is required")
    return profile


baseline = load_baseline()
required_components = {
    "construction": "PROC-0004@1.6",
    "execution": "PROC-0001@1.14",
    "handoff_structure": "TPL-0001@1.9",
    "completion_report_structure": "TPL-0002@1.4",
    "normative_ewo_semantics": "STD-0003@1.5",
    "automation": "deferred",
}
for component, expected in required_components.items():
    assert baseline["components"][component] == expected

resolved = resolve([baseline], "Category A", {"stronger-validation", "narrower-scope"}, set())
manifest = {
    "profile_id": resolved["profile_id"],
    "revision": resolved["revision"],
    "components": resolved["components"],
    "additions": ["narrower-scope", "stronger-validation"],
    "compatibility_result": "COMPATIBLE",
    "authority_preservation_result": "PRESERVED",
}
encoded = json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode()
reencoded = json.dumps(dict(reversed(list(manifest.items()))), sort_keys=True, separators=(",", ":")).encode()
assert hashlib.sha256(encoded).hexdigest() == hashlib.sha256(reencoded).hexdigest()

negative_cases = [
    ([], "Category A", set(), set()),
    ([baseline, dict(baseline)], "Category A", set(), set()),
    ([{**baseline, "status": "Superseded"}], "Category A", set(), set()),
    ([baseline], "Category C", set(), set()),
    ([baseline], "Category A", {"weaker-validation"}, set()),
    ([baseline], "Category A", set(), {"broaden-authority"}),
]
for case in negative_cases:
    try:
        resolve(*case)
    except ValueError:
        pass
    else:
        raise AssertionError(f"fail-closed ETP fixture unexpectedly resolved: {case}")

assert "## Engineering Transaction Profile" in TPL_PATH.read_text(encoding="utf-8")
assert "Engineering Transaction Profile" not in HISTORICAL_EWO.read_text(encoding="utf-8")
print("ETP schema, deterministic resolution, compatibility, authority, manifest, and historical fixtures passed.")
