import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.lib.emp.stage1_execution_resolution import _derived_admission
from scripts.lib.emp.wop_admission import AdmissionController


class DevelopmentWopCanonicalContractTests(unittest.TestCase):
    def test_existing_immutable_package_gets_canonical_in_memory_projection(self):
        package = ROOT / "engineering/work-orders/WOP-ZEUS-STOP-DISPOSABLE-QUALIFICATION-001/465506561ba772d1dd533706"
        record = {
            "instance_id": "ZEUS-DEVELOPMENT-530cda01-7883-57cb-a67e-c8dc4bc010dc",
            "wop_id": "WOP-ZEUS-STOP-DISPOSABLE-QUALIFICATION-001",
            "mission_id": "MISSION-ZEUS-STOP-DISPOSABLE-QUALIFICATION-001",
            "repository": str(ROOT), "execution_mode": "DEVELOPMENT", "operator": "qualification-operator",
            "package": str(package), "package_digest": "814361acbc225619ade3614a5c8027a06bb5c0ca1ed3fbd0b49e93ce86c3f94f",
            "source_digest": "0b41100481802772007df28f41fee9a7c195d81f2e9c30f42799218c3a3da8f",
            "authority_snapshot": {"authority_snapshot_digest": "bd269d39d0ceddcab1d08b74a6d2d5ec0c28a20b0f82bc3444dc22c6e27d5b3d"},
            "receipts": {
                "admission": {"admission_id": "EMM-DEV-ADMISSION-120e6eb0b34c6cadf46fd857d5e43bc4"},
                "dispatch": {"receipt_id": "DISPATCH-EXISTING"},
            },
        }
        admission = _derived_admission(record, record["receipts"]["admission"]["admission_id"])
        wop = admission["artifacts"]["wop_result"]["wop"]
        self.assertEqual(AdmissionController().validate(wop, str(ROOT)), ())
        self.assertEqual(wop["wop_id"], record["wop_id"])
        self.assertEqual(wop["approval"]["authorized_lifecycle_state"], "Active")
        self.assertEqual(wop["execution_package_references"]["authority_node_id"], "work-package")


if __name__ == "__main__":
    unittest.main()
