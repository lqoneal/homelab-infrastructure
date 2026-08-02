#!/usr/bin/env python3
import json, sys, tempfile, unittest
from datetime import datetime, timezone
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.lib.emp.native_session import NativeSessionError, NativeSessionStore, session_identifier
from scripts.lib.emp.gate_handlers import operational_framework

NOW = datetime(2026, 8, 1, tzinfo=timezone.utc)

class NativeSessionFoundationTests(unittest.TestCase):
    def binding(self):
        return {"operation":"BETA","mission_id":"ZDCL-01","wop_id":"WOP-ZDCL-01-FOUNDATION-001","wop_revision":1,"submission_id":"SUB-1","admission_id":"ADM-1","execution_id":"EXE-1","repository_identity":"homelab","admitted_baseline":"a"*40,"principal":"loneal","submitter":"loneal","execution_agent":"Codex","session_classification":"DEVELOPMENT_IMPLEMENTATION","authorized_effect_profile":"ZDCL-01-NATIVE-SESSION-FOUNDATION"}
    def test_identity_lifecycle_replay_and_append_only_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            store=NativeSessionStore(directory); first=store.create(self.binding(),at=NOW); replay=store.create(self.binding(),at=NOW)
            self.assertEqual(first["session_id"],session_identifier("EXE-1")); self.assertEqual(first["state_digest"],replay["state_digest"])
            sid=first["session_id"]
            store.transition(sid,"VERIFIED",at=NOW,event="SESSION_VERIFIED"); store.transition(sid,"ACTIVE",at=NOW,event="SESSION_ACTIVE")
            store.transition(sid,"SUSPENDED",at=NOW,event="SESSION_SUSPENDED"); store.transition(sid,"RESUMED",at=NOW,event="SESSION_RESUMED")
            store.transition(sid,"VERIFYING",at=NOW,event="SESSION_VERIFYING"); final=store.transition(sid,"COMPLETED",at=NOW,event="SESSION_COMPLETED")
            self.assertEqual(final["lifecycle_state"],"COMPLETED"); self.assertEqual(len(final["evidence"]),7)
            published=list((Path(directory)/"published-evidence"/sid).glob("*.json")); self.assertEqual(len(published),7)
    def test_incomplete_identity_and_invalid_transition_fail_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            binding=self.binding(); binding["principal"]=None; store=NativeSessionStore(directory)
            with self.assertRaises(NativeSessionError): store.create(binding,at=NOW)
            state=store.create(self.binding(),at=NOW)
            with self.assertRaises(NativeSessionError): store.transition(state["session_id"],"COMPLETED",at=NOW,event="INVALID")
    def test_registry_keeps_qualification_and_resolves_native_handler(self):
        root=Path(__file__).resolve().parents[2]; framework=operational_framework(root)
        inventory=framework.registry.inventory(); ids={item["handler_id"] for item in inventory}
        self.assertIn("zeus.operational.zdcl01-native-session",ids); self.assertIn("zeus.operational.artifact",ids)
        result=framework.execute(mode="operational",gate_id="EXECUTE_WORK",context={"mission_id":"ZDCL-01","repository":str(root),"wop":{"submission_digest":"x"*64},"completed_gates":[],"cancellation_requested":False,"gate_idempotency_key":"EXE:GATE","operational_context":{"profile":"ZDCL-01","session_id":"ZEUS-SESSION-X","effect_profile":"ZDCL-01-NATIVE-SESSION-FOUNDATION","dry_run":True}})
        self.assertEqual(result["handler_id"],"zeus.operational.zdcl01-native-session"); self.assertFalse(result["side_effects_performed"])

if __name__ == "__main__": unittest.main()
