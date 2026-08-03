#!/usr/bin/env python3
"""Current-registry invariants and historical-fixture separation."""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.lib.emp.production_execution import digest, load_registry
from scripts.lib.eos import capability_registry
from scripts.lib.eos.operational_alpha_status import resolve

CAPABILITY_PATH = ROOT / capability_registry.PATH
AGENT_PATH = ROOT / "engineering/dispatch/execution-agent-registry.json"


class RegistryReconciliationTests(unittest.TestCase):
    def test_capability_ids_and_dependencies_are_current_and_unique(self):
        value = capability_registry.load(ROOT)
        items = value["capabilities"]
        ids = {item["capability_id"] for item in items}
        self.assertEqual(len(items), len(ids))
        for item in items:
            for dependency in item.get("dependencies", []):
                if dependency.startswith("ZEUS-OA-CAP-"):
                    self.assertIn(dependency, ids)

    def test_current_active_gate_is_a_valid_authoritative_projection(self):
        current = resolve(ROOT)
        self.assertIn(current["active_gate"], {f"OA-{n:02d}" for n in range(1, 31)})
        self.assertEqual(current["status"], current["active_gate_state"])
        self.assertTrue(current["authoritative_sources"])

    def test_execution_agent_registry_digest_and_identity(self):
        value = json.loads(AGENT_PATH.read_text(encoding="utf-8"))
        self.assertEqual(value["registry_digest"], digest({k: v for k, v in value.items() if k != "registry_digest"}))
        agents = load_registry(AGENT_PATH)
        self.assertEqual(len(agents), len({agent["agent_id"] for agent in agents}))
        self.assertTrue(any(agent["qualification_status"] == "QUALIFIED" for agent in agents))

    def test_historical_fixture_is_not_live_registry(self):
        fixture = json.loads((ROOT / "scripts/tests/fixtures/oa05-capability-state.json").read_text())
        live = capability_registry.list_capabilities(ROOT)
        self.assertEqual(5, fixture["capability_count"])
        self.assertNotEqual(fixture["capability_count"], len(live["capabilities"]))


if __name__ == "__main__":
    unittest.main()
