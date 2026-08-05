#!/usr/bin/env python3
import json
import shutil
import tempfile
import unittest
from pathlib import Path

import yaml

from scripts.lib.emp.canonical_mission_lifecycle import (
    CanonicalMissionLifecycleError,
    activate,
    derive_linkage,
    discover,
)


class CanonicalMissionLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "engineering/mission-contracts/candidates").mkdir(parents=True)
        (self.root / "engineering/mission-contracts/contracts").mkdir()
        (self.root / "engineering/mission-contracts/transactions").mkdir()
        (self.root / "engineering/registry").mkdir()
        (self.root / "engineering/operational-packages/STOPQ-01").mkdir(parents=True)
        (self.root / "engineering/registry/work-registry.yaml").write_text(
            yaml.safe_dump({"revision": 1, "entities": {"work_items": []}})
        )
        package = self.root / "engineering/operational-packages/STOPQ-01/mission.yaml"
        package.write_text("status: Active\nmission_id: STOPQ-01\n")
        candidate = {
            "contract_id": "MC-STOPQ-01", "mission_id": "STOPQ-01",
            "registry_id": "EMP-WORK-BETA-STOPQ-01", "approvals": {"activation": "pending"},
            "lifecycle": "candidate", "wop": {"id": "WOP-ZEUS-STOPQ01-CANONICAL-MISSION-PUBLICATION-001",
            "locator": "engineering/operational-packages/STOPQ-01/mission.yaml"},
        }
        (self.root / "engineering/mission-contracts/candidates/MC-STOPQ-01.yaml").write_text(yaml.safe_dump(candidate))
        self.transaction = {"wop_id": "WOP-ZEUS-STOPQ01-CANONICAL-MISSION-PUBLICATION-001", "package": "development-package", "package_digest": "98cb16c4ea7328360181f6b806ff4b89990901c785339fff7a92c8bce6084636"}

    def tearDown(self):
        self.temp.cleanup()

    def test_exact_legacy_linkage_and_prepublication_block(self):
        linkage = derive_linkage(self.transaction, "development-package", package_digest=self.transaction["package_digest"])
        self.assertEqual("STOPQ-01", linkage["target_mission_id"])
        self.assertEqual("publication-triggered", linkage["activation_policy"])
        self.assertEqual("BLOCKED", discover(self.root)["result"])

    def test_activation_gate_and_atomic_rollback(self):
        with self.assertRaisesRegex(CanonicalMissionLifecycleError, "PUBLICATION_BOUNDARY"):
            activate(self.root, self.transaction, publication_approved=False, eos_synchronized=True, platform_validated=True)
        with self.assertRaisesRegex(CanonicalMissionLifecycleError, "INJECTED"):
            activate(self.root, self.transaction, publication_approved=True, eos_synchronized=True, platform_validated=True, fault_after="repository")
        self.assertFalse((self.root / "engineering/mission-contracts/contracts/MC-STOPQ-01.yaml").exists())
        result = activate(self.root, self.transaction, publication_approved=True, eos_synchronized=True, platform_validated=True)
        self.assertEqual("ACTIVATED", result["resolution"])
        replay = activate(self.root, self.transaction, publication_approved=True, eos_synchronized=True, platform_validated=True)
        self.assertEqual("IDEMPOTENT_REPLAY", replay["resolution"])
        self.assertEqual(1, len(yaml.safe_load((self.root / "engineering/registry/work-registry.yaml").read_text())["entities"]["work_items"]))


if __name__ == "__main__":
    unittest.main()
