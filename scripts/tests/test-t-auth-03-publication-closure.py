#!/usr/bin/env python3
"""Focused T-AUTH-03 publication-closure qualification."""

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.lib.emp.publication_closure import (  # noqa: E402
    discover_reverse_dependencies,
    publication_preflight,
)


class PublicationClosureTests(unittest.TestCase):
    def test_proc_reverse_dependencies_are_derived_and_historical_is_excluded(self):
        dependents = discover_reverse_dependencies(
            ROOT, source_class="CONTROLLED_DOCUMENT", source="PROC-0001", revision_or_digest="2.11"
        )
        live = {item["dependent"] for item in dependents if item["classification"] == "LIVE_DEPENDENT"}
        self.assertTrue({
            "engineering/execution/execution-interface.yaml",
            "scripts/lib/emp/stage1_execution_resolution.py",
            "scripts/lib/emp/wop_authoring.py",
            "scripts/lib/emp/wop_packaging.py",
            "scripts/lib/emp/wop_validation.py",
        } <= live)
        self.assertTrue(any(item["classification"] == "HISTORICAL_DEPENDENT" for item in dependents))

    def test_current_proc_closure_passes_and_replays(self):
        arguments = dict(source="PROC-0001", source_class="CONTROLLED_DOCUMENT", revision_or_digest="2.11")
        first = publication_preflight(ROOT, **arguments)
        second = publication_preflight(ROOT, **arguments)
        self.assertEqual(first, second)
        self.assertEqual(first["publication_closure"], "PASS")
        self.assertEqual(first["publication_allowed"], "YES")

    def test_stale_proc_binding_fails_closed(self):
        result = publication_preflight(
            ROOT, source="PROC-0001", source_class="CONTROLLED_DOCUMENT", revision_or_digest="2.12"
        )
        self.assertEqual(result["publication_closure"], "FAIL")
        self.assertEqual(result["publication_allowed"], "NO")
        self.assertIn("scripts/lib/emp/wop_validation.py", result["unresolved_dependents"])

    def test_valid_dispositions_close_stale_dependents(self):
        dependents = discover_reverse_dependencies(
            ROOT, source_class="CONTROLLED_DOCUMENT", source="PROC-0001", revision_or_digest="2.12"
        )
        overrides = {
            item["dependent"]: {"disposition": "COMPATIBILITY_PROVEN", "evidence": True}
            for item in dependents if item["classification"] == "LIVE_DEPENDENT"
        }
        result = publication_preflight(
            ROOT, source="PROC-0001", source_class="CONTROLLED_DOCUMENT",
            revision_or_digest="2.12", disposition_overrides=overrides,
        )
        self.assertEqual(result["publication_closure"], "PASS")

    def test_model_b_graph_and_missing_source_fail_closed(self):
        for source_class, source in (
            ("EMM", "OPERATION-BETA-EMM"),
            ("IMMUTABLE_WOP", "WOP-ZEUS-EXECUTION-LIFECYCLE-COMPLETION-001"),
            ("EXECUTABLE_ROADMAP", "OPERATION-BETA-ROADMAP"),
        ):
            result = publication_preflight(
                ROOT, source=source, source_class=source_class, revision_or_digest="current"
            )
            self.assertEqual(result["publication_closure"], "PASS")
            self.assertTrue(result["live_reverse_dependents"])
        missing = publication_preflight(
            ROOT, source="MISSING-EMM", source_class="EMM", revision_or_digest="current"
        )
        self.assertEqual(missing["publication_allowed"], "NO")

    def test_disposition_and_compatibility_evidence_are_fail_closed(self):
        dependents = discover_reverse_dependencies(
            ROOT, source_class="EMM", source="OPERATION-BETA-EMM", revision_or_digest="current"
        )
        path = dependents[0]["dependent"]
        missing = publication_preflight(
            ROOT, source="OPERATION-BETA-EMM", source_class="EMM", revision_or_digest="future",
            disposition_overrides={path: {"disposition": "COMPATIBILITY_PROVEN", "evidence": False}},
        )
        self.assertEqual(missing["publication_allowed"], "NO")
        superseded = publication_preflight(
            ROOT, source="OPERATION-BETA-EMM", source_class="EMM", revision_or_digest="future",
            disposition_overrides={item["dependent"]: "EXPLICITLY_SUPERSEDED" for item in dependents},
        )
        self.assertEqual(superseded["publication_closure"], "PASS")


if __name__ == "__main__":
    unittest.main()
