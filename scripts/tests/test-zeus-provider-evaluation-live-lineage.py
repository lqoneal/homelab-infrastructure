"""Provider-selection live publication-lineage qualification."""
from __future__ import annotations

import hashlib
import json
import subprocess
import unittest
from pathlib import Path

from scripts.lib.emp import provider_selection


ROOT = Path(__file__).resolve().parents[2]
MISSION = "ZEUS-EXECUTION-LIFECYCLE-COMPLETION-01"


class ProviderEvaluationLiveLineageTests(unittest.TestCase):
    def _runtime_and_anchor(self):
        runtime = provider_selection._runtime(ROOT, None)
        paths = sorted((runtime / provider_selection.STAGE_DIRS["provider_selection"]).glob("*.json"))
        path = next(item for item in paths if json.loads(item.read_text())["mission_id"] == MISSION)
        return runtime, path, json.loads(path.read_text())

    def test_n_plus_one_live_publication_projects_existing_selection(self):
        runtime, path, anchor = self._runtime_and_anchor()
        before = hashlib.sha256(path.read_bytes()).hexdigest()
        value = provider_selection.verify(ROOT, MISSION, runtime_root=runtime)
        current = subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip()
        self.assertEqual(value["result"], "PASS")
        self.assertTrue(value["provider_selected"])
        self.assertEqual(value["provider_id"], anchor["provider_id"])
        self.assertEqual(value["provider_selection_lineage"]["current_published_baseline"], current)
        self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), before)

    def test_live_lineage_rejects_unrelated_recorded_baseline(self):
        anchor = {"mission_provenance_baseline": "a" * 40, "current_published_baseline": "b" * 40}
        value = provider_selection._validate_live_lineage
        with self.assertRaises(provider_selection.ProviderSelectionError):
            # Invalid commit operands fail closed before any provider state is projected.
            value(ROOT, anchor)

    def test_provider_selection_replay_is_idempotent_and_read_only(self):
        runtime, path, _ = self._runtime_and_anchor()
        before = {str(item): hashlib.sha256(item.read_bytes()).hexdigest() for item in runtime.rglob("*.json")}
        value = provider_selection.verify(ROOT, MISSION, runtime_root=runtime)
        after = {str(item): hashlib.sha256(item.read_bytes()).hexdigest() for item in runtime.rglob("*.json")}
        self.assertEqual(value["result"], "PASS")
        self.assertEqual(value["replay"], "IDEMPOTENT")
        self.assertEqual(before, after)
        self.assertEqual(path.exists(), True)


if __name__ == "__main__":
    unittest.main()
