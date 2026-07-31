#!/usr/bin/env python3
"""Current-convergence qualification for OA-05 capability services."""
import unittest
from pathlib import Path
from scripts.lib.eos import capability_registry
from scripts.lib.eos.convergence_runtime import ConvergenceRuntime
from scripts.lib.eos.operational_alpha_status import resolve
ROOT=Path(__file__).resolve().parents[2]
WOP="WOP-0ec591ec-7c16-5bf7-8ed8-002ec9c4547f"
class OA05CapabilityRegistryTests(unittest.TestCase):
 def test_registry_is_complete(self):
  self.assertEqual("PASS", capability_registry.verify(ROOT)["result"])
  self.assertEqual(4, len(capability_registry.list_capabilities(ROOT)["capabilities"]))
 def test_registry_capability_is_resolvable(self):
  self.assertEqual("Mission staging contract", capability_registry.show(ROOT,"ZEUS-OA-CAP-004")["capability"]["name"])
 def test_current_lifecycle_is_bound(self):
  runtime=ConvergenceRuntime(ROOT); _,wop,_=runtime._wop(WOP,1)
  self.assertEqual("ACTIVE",wop["status"]); self.assertEqual("OA-05",resolve(ROOT)["active_gate"])
if __name__ == "__main__": unittest.main()
