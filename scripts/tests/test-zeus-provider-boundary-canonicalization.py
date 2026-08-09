"""Focused provider-boundary canonicalization regression tests."""
from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.lib.emp import provider_selection, provider_session


ROOT = Path(__file__).resolve().parents[2]
MISSION = "ZEUS-EXECUTION-LIFECYCLE-COMPLETION-01"


class ProviderBoundaryCanonicalizationTests(unittest.TestCase):
    def test_same_mission_historical_provider_set_is_subordinate(self) -> None:
        expected = {
            "mission_id": MISSION, "wop_id": "WOP-01", "submission_id": "SUB-01",
            "admission_id": "ADM-01", "bootstrap_id": "BOOT-01",
            "repository_identity": str(ROOT), "mission_provenance_baseline": "BASE-01",
            "current_published_baseline": "HEAD-02",
        }
        found = {key: [] for key in provider_selection.STAGE_DIRS}
        for key in found:
            current = {**expected, "artifact_type": provider_selection.ARTIFACT_TYPES[key]}
            historical = {**current, "mission_provenance_baseline": "BASE-OLD"}
            found[key] = [(Path(f"/tmp/current-{key}.json"), current), (Path(f"/tmp/historical-{key}.json"), historical)]
        scoped = provider_selection._scoped_mission_artifacts(found, expected)
        self.assertTrue(all(len(items) == 1 for items in scoped.values()))
        self.assertTrue(all(items[0][0].name.startswith("current-") for items in scoped.values()))

    def test_stale_recorded_baseline_remains_valid_on_live_descendant(self) -> None:
        anchor = {
            "mission_provenance_baseline": "a" * 40,
            "current_published_baseline": "b" * 40,
        }
        live = {
            "result": "PASS",
            "current_published_baseline": "c" * 40,
        }
        valid = {"result": "PASS", "baseline_relationship": "ANCESTOR"}
        with patch.object(provider_selection, "resolve_provenance_lineage", return_value=live), \
             patch.object(provider_selection, "resolve_commit_lineage", return_value=valid):
            value = provider_selection._validate_live_lineage(ROOT, anchor)
        self.assertEqual(value["recorded_published_baseline"], "b" * 40)
        self.assertEqual(value["current_published_baseline"], "c" * 40)

    def test_live_provider_selection_reuses_receipt_after_publication(self) -> None:
        runtime = provider_selection._runtime(ROOT, None)
        path = runtime / provider_selection.STAGE_DIRS["provider_selection"]
        anchors = sorted(path.glob("*.json"))
        target = next(item for item in anchors if json.loads(item.read_text())["mission_id"] == MISSION)
        anchor = json.loads(target.read_text())
        before = target.read_bytes()
        lineage = provider_selection._validate_live_lineage(ROOT, anchor)
        live_head = subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip()
        self.assertEqual(lineage["current_published_baseline"], live_head)
        self.assertNotEqual(anchor["current_published_baseline"], live_head)
        self.assertEqual(target.read_bytes(), before)

    def test_two_valid_baseline_sets_same_identity_fail_closed(self) -> None:
        expected = {
            "mission_id": MISSION, "wop_id": "WOP-01", "submission_id": "SUB-01",
            "admission_id": "ADM-01", "bootstrap_id": "BOOT-01",
            "repository_identity": str(ROOT), "mission_provenance_baseline": "a" * 40,
            "current_published_baseline": "b" * 40,
        }
        found = {key: [] for key in provider_selection.STAGE_DIRS}
        for key in found:
            artifact_type = provider_selection.ARTIFACT_TYPES[key]
            found[key] = [
                (Path(f"/tmp/a-{key}.json"), {**expected, "artifact_type": artifact_type}),
                (Path(f"/tmp/b-{key}.json"), {**expected, "current_published_baseline": "c" * 40, "artifact_type": artifact_type}),
            ]
        with self.assertRaises(provider_selection.ProviderSelectionError) as context:
            provider_selection._verify_set(Path("/tmp"), found)
        self.assertEqual(context.exception.code, "PROVIDER_SELECTION_CARDINALITY_CONFLICT")

    def test_non_descendant_provider_baseline_fails_closed(self) -> None:
        anchor = {
            "mission_provenance_baseline": "a" * 40,
            "current_published_baseline": "b" * 40,
        }
        live = {"result": "PASS", "current_published_baseline": "c" * 40}
        invalid = {"result": "FAIL", "baseline_relationship": "UNRELATED"}
        with patch.object(provider_selection, "resolve_provenance_lineage", return_value=live), \
             patch.object(provider_selection, "resolve_commit_lineage", return_value=invalid), \
             self.assertRaises(provider_selection.ProviderSelectionError) as context:
            provider_selection._validate_live_lineage(ROOT, anchor)
        self.assertEqual(context.exception.code, "PROVIDER_RECORDED_BASELINE_INVALID")

    def test_two_current_provider_sets_fail_closed(self) -> None:
        expected = {
            "mission_id": MISSION, "wop_id": "WOP-01", "submission_id": "SUB-01",
            "admission_id": "ADM-01", "bootstrap_id": "BOOT-01",
            "repository_identity": str(ROOT), "mission_provenance_baseline": "BASE-01",
            "current_published_baseline": "HEAD-02",
        }
        found = {key: [] for key in provider_selection.STAGE_DIRS}
        for key in found:
            artifact_type = provider_selection.ARTIFACT_TYPES[key]
            values = [({**expected, "artifact_type": artifact_type}, f"/tmp/a-{key}.json"),
                      ({**expected, "artifact_type": artifact_type}, f"/tmp/b-{key}.json")]
            found[key] = [(Path(path), value) for value, path in values]
        with self.assertRaises(provider_selection.ProviderSelectionError) as context:
            provider_selection._verify_set(Path("/tmp"), found)
        self.assertEqual(context.exception.code, "PROVIDER_SELECTION_CARDINALITY_CONFLICT")

    def test_live_provider_selection_projects_through_all_mission_surfaces(self) -> None:
        surfaces = ("show", "state", "authority", "blockers", "readiness", "eligibility", "next", "snapshot")
        values = []
        for surface in surfaces:
            result = subprocess.run(
                [str(ROOT / "scripts/zeus"), "mission", surface, MISSION, "--json"],
                cwd=ROOT, capture_output=True, text=True, check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            values.append(json.loads(result.stdout))
        for value in values:
            self.assertEqual(value["result"], "PASS")
            self.assertEqual(value["mission_id"], MISSION)
            self.assertEqual(value["wop_id"], "WOP-ZEUS-EXECUTION-LIFECYCLE-COMPLETION-001")
            self.assertEqual(value["provider_id"], "zeus-local-loneal-01")
            self.assertEqual(value["provider_selected"], True)
            self.assertIn(value["next_authorized_action"], {
                "EVALUATE_PROVIDER_DISPATCH",
                "ESTABLISH_PROVIDER_SESSION",
                "INVOKE_PROVIDER",
                "START_EXECUTION",
                "BEGIN_CONTROLLED_MISSION_WORK",
            })
            self.assertEqual(value["blockers"], [])
        self.assertEqual({value["lifecycle_state"] for value in values}, {"READY_FOR_CONTROLLED_EXECUTION"})

    def test_other_mission_dispatch_does_not_block_target_pre_provider_state(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            (runtime / "dispatches").mkdir()
            (runtime / "dispatches" / "historical-other-mission.json").write_text(
                json.dumps({"mission_id": "MISSION-BETA-HISTORICAL-01", "dispatch_id": "DISPATCH-HISTORICAL"}),
                encoding="utf-8",
            )
            result = provider_session.verify(ROOT, MISSION, runtime_root=runtime)
            self.assertEqual(result["result"], "FAIL")
            self.assertEqual(result["blockers"][0]["code"], "DISPATCH_NOT_READY")
            self.assertNotEqual(result["blockers"][0]["code"], "DISPATCH_CROSS_MISSION")

    def test_target_orphaned_session_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            (runtime / "provider-sessions").mkdir()
            (runtime / "provider-sessions" / "orphan.json").write_text(
                json.dumps({"mission_id": MISSION, "provider_session_id": "SESSION-ORPHAN"}),
                encoding="utf-8",
            )
            result = provider_session.verify(ROOT, MISSION, runtime_root=runtime)
            self.assertEqual(result["result"], "FAIL")
            self.assertEqual(result["blockers"][0]["code"], "PROVIDER_SESSION_ORPHANED")

    def test_cli_provider_path_does_not_apply_mission_beta_prefix_guard(self) -> None:
        environment = dict(os.environ)
        environment["ZEUS_RUNTIME_ROOT"] = "/nonexistent/zeus-provider-boundary-test"
        result = subprocess.run(
            [str(ROOT / "scripts/zeus"), "provider", "verify", MISSION, "--json"],
            cwd=ROOT,
            env=environment,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertNotIn("provider selection requires a canonical Beta mission", result.stderr)
        self.assertNotIn("MISSION_NOT_CANONICAL", result.stderr)


if __name__ == "__main__":
    unittest.main()
