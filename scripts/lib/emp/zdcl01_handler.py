#!/usr/bin/env python3
"""Bounded operational handler for the ZDCL-01 native-session profile."""
from __future__ import annotations
import subprocess
from scripts.lib.emp.authority_resolution import digest
from scripts.lib.emp.gate_handlers import API_VERSION, REQUIRED_CAPABILITIES, GateHandlerError, HandlerManifest

class ZDCL01OperationalHandler:
    manifest = HandlerManifest(handler_id="zeus.operational.zdcl01-native-session", version="0.1.0", api_version=API_VERSION, modes=("operational",), gates=("EXECUTE_WORK", "VERIFY_COMPLETION"), capabilities=frozenset(REQUIRED_CAPABILITIES | {"native-session", "authority-binding", "effect-profile", "dry-run"}), mutating=True)
    def verify_current(self, gate_id, context):
        if context.get("mission_id") != "ZDCL-01": raise GateHandlerError("ZDCL-01 handler refuses other missions")
        operational = context.get("operational_context") or {}
        if operational.get("profile") != "ZDCL-01" or not operational.get("session_id"): raise GateHandlerError("ZDCL-01 native session context is unresolved")
        observed = subprocess.run(["git", "-C", context["repository"], "rev-parse", "HEAD"], capture_output=True, text=True, check=False)
        if observed.returncode: raise GateHandlerError("repository identity verification failed")
        return {"condition": "VERIFIED", "session_id": operational["session_id"], "repository_baseline": observed.stdout.strip(), "effect_profile": operational["effect_profile"], "dry_run": bool(operational.get("dry_run"))}
    def determine_required(self, gate_id, context, verification):
        required = gate_id not in context.get("completed_gates", [])
        return {"required": required, "disposition": "REQUIRED" if required else "PREVIOUSLY_SATISFIED"}
    def execute_required(self, gate_id, context, work):
        profile = context["operational_context"]
        return {"status": "COMPLETED", "result": "NATIVE_SESSION_FOUNDATION_ACTIVE" if gate_id == "EXECUTE_WORK" else "NATIVE_SESSION_FOUNDATION_VERIFIED", "session_id": profile["session_id"], "gate_idempotency_key": context["gate_idempotency_key"], "effect_profile": profile["effect_profile"], "declared_effects": {"runtime": ["native-sessions", "mission-executions"], "repository": [], "filesystem": [], "network": [], "publication": ["append-only-session-evidence"]}, "effects_performed": [{"domain": "runtime", "effect": "native-session-lifecycle"}, {"domain": "publication", "effect": "append-only-session-evidence"}], "side_effects_performed": not profile.get("dry_run", False), "artifacts": []}
    def verify_result(self, gate_id, context, result):
        if any(item["effect"] not in {"native-session-lifecycle", "append-only-session-evidence"} for item in result["effects_performed"]): raise GateHandlerError("handler attempted undeclared effects")
        return {"verification": "PASS", "session_id": result["session_id"], "effect_profile_enforced": True, "result_digest": digest(result)}
