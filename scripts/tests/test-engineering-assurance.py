#!/usr/bin/env python3
"""Regression tests for generic Engineering Assurance validation."""

from __future__ import annotations

import copy
import hashlib
import re
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from lib.engineering_assurance import analyze, canonical_report, load_catalog


BASE = {
    "property_id": "EP-TEST-001",
    "authoritative_source": {"document_id": "TEST", "locator": "source.md"},
    "category": "Safety Invariant",
    "engineering_objective": "Preserve a declared invariant.",
    "subject": "fixture",
    "preconditions": [],
    "required_invariant": "safe marker exists",
    "prohibited_condition": "unsafe marker exists",
    "applicable_states": ["ready", "done"],
    "applicable_transitions": [["ready", "done"]],
    "dependency_assumptions": [],
    "validation_strategy": ["Static Inspection"],
    "required_evidence": ["source", "subject"],
    "failure_classification": "fixture finding",
    "assurance_impact": ["engineering review required"],
    "review_owner": "fixture owner",
    "authority_boundary": {"grants_authority": False},
    "checks": [{"kind": "contains", "locator": "subject.txt", "pattern": "safe"}],
}


class EngineeringAssuranceTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        (self.root / "source.md").write_text("authoritative property\n", encoding="utf-8")
        (self.root / "subject.txt").write_text("safe\n", encoding="utf-8")

    def tearDown(self):
        self.temporary.cleanup()

    def result(self, property_value):
        report = analyze(self.root, {"properties": [property_value]})
        return report["declared_engineering_properties"][0], report

    def test_assured_property_and_byte_reproducibility(self):
        result, report = self.result(copy.deepcopy(BASE))
        self.assertEqual("ASSURED", result["assurance_determination"])
        first = canonical_report(report).encode()
        second = canonical_report(analyze(self.root, {"properties": [copy.deepcopy(BASE)]})).encode()
        self.assertEqual(first, second)
        self.assertEqual(hashlib.sha256(first).digest(), hashlib.sha256(second).digest())

    def test_partial_assurance(self):
        prop = copy.deepcopy(BASE)
        prop["checks"].append({"kind": "contains", "locator": "subject.txt", "pattern": "missing"})
        self.assertEqual("PARTIALLY_ASSURED", self.result(prop)[0]["assurance_determination"])

    def test_violated_invariant(self):
        prop = copy.deepcopy(BASE)
        prop["checks"] = [{"kind": "contains", "locator": "subject.txt", "pattern": "unsafe"}]
        self.assertEqual("VIOLATED", self.result(prop)[0]["assurance_determination"])

    def test_missing_approval_boundary(self):
        prop = copy.deepcopy(BASE)
        prop["category"] = "Approval Boundary"
        prop["checks"] = [{"kind": "contains", "locator": "subject.txt", "pattern": "approval"}]
        self.assertEqual("VIOLATED", self.result(prop)[0]["assurance_determination"])

    def test_illegal_state_transition(self):
        prop = copy.deepcopy(BASE)
        prop["checks"] = [{
            "kind": "state_machine", "states": ["ready", "done"],
            "terminal_states": ["done"], "transitions": [["done", "ready"]],
            "result_group": "transition_results",
        }]
        result, _ = self.result(prop)
        self.assertEqual("VIOLATED", result["assurance_determination"])

    def test_replay_risk_and_failure_path_gap(self):
        for pattern in ("idempotency", "recovery"):
            prop = copy.deepcopy(BASE)
            prop["checks"] = [{"kind": "contains", "locator": "subject.txt", "pattern": pattern}]
            self.assertEqual("VIOLATED", self.result(prop)[0]["assurance_determination"])

    def test_insufficient_evidence(self):
        prop = copy.deepcopy(BASE)
        prop["checks"] = [{"kind": "file_exists", "locator": "absent.txt"}]
        self.assertEqual("VIOLATED", self.result(prop)[0]["assurance_determination"])
        prop["authoritative_source"]["locator"] = "absent-source.md"
        self.assertEqual("INSUFFICIENT_EVIDENCE", self.result(prop)[0]["assurance_determination"])

    def test_obsolete_ambiguous_and_not_applicable(self):
        expected = {
            "obsolete": "OBSOLETE_PROPERTY",
            "ambiguous": "AMBIGUOUS_PROPERTY",
            "not_applicable": "NOT_APPLICABLE",
        }
        for status, determination in expected.items():
            prop = copy.deepcopy(BASE)
            prop["property_status"] = status
            self.assertEqual(determination, self.result(prop)[0]["assurance_determination"])

    def test_catalog_rejects_undocumented_or_invalid_declarations(self):
        catalog = self.root / "properties.yaml"
        invalid = copy.deepcopy(BASE)
        del invalid["authoritative_source"]
        catalog.write_text(yaml.safe_dump({"properties": [invalid]}), encoding="utf-8")
        with self.assertRaises(ValueError):
            load_catalog(catalog)

    def test_catalog_contains_no_service_logic_in_engine(self):
        engine = (ROOT / "scripts/lib/engineering_assurance.py").read_text(encoding="utf-8").lower()
        for service in ("zeus", "eens", "emp"):
            self.assertIsNone(re.search(rf"\b{service}\b", engine))


if __name__ == "__main__":
    unittest.main()
