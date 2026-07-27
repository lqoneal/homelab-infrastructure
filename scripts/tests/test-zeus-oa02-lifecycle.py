#!/usr/bin/env python3
import tempfile,unittest,sys
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from scripts.lib.emp import oa02_lifecycle

class OA02Tests(unittest.TestCase):
    def test_current_resolution_is_deterministic_and_safe(self):
        root=Path(__file__).resolve().parents[2]
        first=oa02_lifecycle.resolve(root); second=oa02_lifecycle.resolve(root)
        self.assertEqual(first["decision_digest"],second["decision_digest"])
        self.assertEqual(first["operational_dispatch"],"DISABLED")
        self.assertFalse(first["dispatcher_active"])
        self.assertEqual(first["mission_execution"],"NOT_STARTED")
        self.assertEqual(first["current_binding_pmct_result"],"PASS")

    def test_not_ready_record_is_integrity_protected_and_idempotent(self):
        root=Path(__file__).resolve().parents[2]
        value=oa02_lifecycle.resolve(root); value["verification_record"]=None
        with tempfile.TemporaryDirectory() as td, patch.object(oa02_lifecycle,"resolve",return_value=value):
            path=Path(td)/"OA-02.verification.json"
            first,replay=oa02_lifecycle.verify(root,path)
            second,replay2=oa02_lifecycle.verify(root,path)
            self.assertFalse(replay); self.assertTrue(replay2)
            self.assertEqual(first["decision_digest"],second["decision_digest"])
            self.assertTrue(path.with_suffix(".json.sha256").is_file())

if __name__=="__main__": unittest.main()
