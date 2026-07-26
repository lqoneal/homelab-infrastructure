#!/usr/bin/env python3
"""Mission O supervised reasoning and WOP generation tests."""
from __future__ import annotations
import json, subprocess, sys, tempfile, unittest
from datetime import datetime, timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; sys.path.insert(0,str(ROOT))
from scripts.lib.emp.reasoning import ContextManager, ConversationEngine, EngineeringExplanationEngine, ReasoningError, WopGenerator, WopGuidanceService  # noqa:E402
from scripts.lib.emp.wop_admission import AdmissionController, AdmissionLedger, AUTHORITATIVE_SCHEMA, CONTRACT, REQUIRED_SECTIONS, submission_digest  # noqa:E402

class ReasoningTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.root=Path(self.temp.name)
        self.g=WopGuidanceService()
    def tearDown(self): self.temp.cleanup()
    def generated(self):
        return WopGenerator().generate(intent="Implement bounded diagnostic capability",mission_id="ZEUS-O-TEST",phase_id="SUPERVISED-REASONING",repository_identity=str(ROOT),submitter_identity="operator",approval_authority="operator",approval_reference="APPROVAL-O-1",approval_date="2026-07-25",authority_node_id="work-package",adr_reference="ADR-test",immutable_wop_reference="WOP-test")
    def test_identical_intent_produces_identical_wop(self):
        self.assertEqual(self.generated(),self.generated())
    def test_generated_wop_passes_admission_validation(self):
        result=self.g.validate(self.generated()["wop"],str(ROOT))
        self.assertEqual(result["admission_decision"],"ACCEPTED")
    def test_generated_wop_requires_review_and_is_not_submitted(self):
        result=self.generated(); self.assertTrue(result["review_required"]); self.assertFalse(result["automatically_submitted"])
    def test_guidance_derives_from_authoritative_schema(self):
        req=self.g.requirements()
        self.assertEqual(req["schema_required"],AUTHORITATIVE_SCHEMA["required"])
        self.assertEqual(req["required_sections"],CONTRACT["required_sections"])
    def test_template_and_example_are_deterministic(self):
        self.assertEqual(self.g.template(),self.g.template())
        self.assertEqual(self.g.example(),self.g.example())
    def test_example_passes_admission(self):
        example=self.g.example()
        self.assertEqual(self.g.validate(example,example["repository_identity"])["admission_decision"],"ACCEPTED")
    def test_conversation_and_cli_guidance_are_identical(self):
        conversational=ConversationEngine().respond("Show me the WOP template.")["response"]
        result=subprocess.run([str(ROOT/"scripts/zeus"),"--state",str(self.root/"state.json"),"show","wop-template"],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(conversational,json.loads(result.stdout))
    def test_equivalent_conversational_requirements(self):
        response=ConversationEngine().respond("What is required in a WOP?")
        self.assertEqual(response["response"],self.g.requirements())
    def rejection(self):
        bad=self.generated()["wop"]; bad["status"]="Draft"; bad["submission_digest"]=submission_digest(bad)
        decision=AdmissionController().decide(bad,expected_repository=str(ROOT),evaluated_at=datetime(2026,7,25,tzinfo=timezone.utc))
        return AdmissionLedger(self.root/"ledger").record(decision),decision
    def test_rejection_explanation_matches_admission(self):
        path,decision=self.rejection(); explanation=self.g.explain_rejection(path)
        self.assertEqual([x["reason_code"] for x in explanation["explanations"]],[x["reason_code"] for x in decision.data["validation_failures"]])
        self.assertEqual(explanation["execution_status"],"No engineering work has begun.")
    def test_conversational_validation_matches_cli_service(self):
        wop=self.generated()["wop"]
        response=ConversationEngine().respond("Validate this WOP.",repository=str(ROOT),package=wop)
        self.assertEqual(response["response"],self.g.validate(wop,str(ROOT)))
    def test_context_is_deterministic_non_authoritative_metadata(self):
        context=ContextManager(self.root/"context.json")
        response=ConversationEngine().respond("Give me engineering planning guidance.")
        data=context.record("Give me engineering planning guidance.",response)
        self.assertTrue(data["non_authoritative"]); self.assertEqual(data["referenced_missions"],[])
    def test_explanations_are_deterministic_and_record_bound(self):
        record={"selected_mission":"MISSION-A","policy_evaluations":{"policy_id":"p"}}
        engine=EngineeringExplanationEngine()
        self.assertEqual(engine.explain("mission_selection",record),engine.explain("mission_selection",record))
    def test_unknown_conversation_intent_fails_closed(self):
        with self.assertRaises(ReasoningError): ConversationEngine().respond("Run arbitrary shell commands")
    def test_no_autonomous_effects_exist(self):
        source=(ROOT/"scripts/lib/emp/reasoning.py").read_text()
        for prohibited in ("subprocess.","execute_wop(","dispatch_work(","approve_work(","modify_repository(","submit_admission("):
            self.assertNotIn(prohibited,source)

if __name__=="__main__": unittest.main()
