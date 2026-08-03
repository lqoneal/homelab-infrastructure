#!/usr/bin/env python3
"""Current-convergence qualification for OA-05 capability services."""
import unittest
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.lib.eos import capability_registry
from scripts.lib.eos.convergence_runtime import ConvergenceRuntime
from scripts.lib.eos.operational_alpha_status import resolve
WOP="WOP-0ec591ec-7c16-5bf7-8ed8-002ec9c4547f"
HISTORICAL_FIXTURE = ROOT / "scripts/tests/fixtures/oa05-capability-state.json"
class OA05CapabilityRegistryTests(unittest.TestCase):
 def test_registry_is_complete(self):
  report = capability_registry.verify(ROOT)
  listing = capability_registry.list_capabilities(ROOT)
  self.assertEqual("PASS", report["result"])
  capabilities = listing["capabilities"]
  self.assertGreaterEqual(len(capabilities), 5)
  self.assertEqual(len(capabilities), len({item["capability_id"] for item in capabilities}))
  self.assertTrue({"ZEUS-OA-CAP-001", "ZEUS-OA-CAP-002", "ZEUS-OA-CAP-003"}.issubset(
      {item["capability_id"] for item in capabilities}
  ))

 def test_historical_oa05_expectations_use_frozen_fixture(self):
  fixture = json.loads(HISTORICAL_FIXTURE.read_text(encoding="utf-8"))
  self.assertEqual("OA-06", fixture["active_gate"])
  self.assertEqual(5, fixture["capability_count"])
  self.assertEqual(5, len(fixture["capability_ids"]))
 def test_registry_capability_is_resolvable(self):
  self.assertEqual("Mission staging contract", capability_registry.show(ROOT,"ZEUS-OA-CAP-004")["capability"]["name"])
 def test_current_lifecycle_is_bound(self):
  runtime=ConvergenceRuntime(ROOT); _,wop,_=runtime._wop(WOP,1)
  self.assertEqual("ACTIVE",wop["status"])
  current = resolve(ROOT)
  self.assertRegex(current["active_gate"], r"^OA-\d{2}$")
  self.assertEqual(current["status"], current["active_gate_state"])
if __name__ == "__main__": unittest.main()
