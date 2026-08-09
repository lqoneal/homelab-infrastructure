#!/usr/bin/env python3
"""Read-only Beta-03G platform invariant self-audit."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.lib.emp import controller_presentation
from scripts.lib.eos import operational_beta


def fail(message: str) -> None:
    raise AssertionError(message)


def main() -> None:
    projection = operational_beta.mission_view(ROOT, "explain", "ZDCL-01")
    if projection.get("current_admission") is not None:
        fail("stale admission leaked into current executable projection")
    if projection.get("current_executable_mission") != "ZEUS-EXECUTION-LIFECYCLE-COMPLETION-01":
        fail("receipt-backed lifecycle mission is not projected as current execution")
    if projection.get("current_platform_mission", {}).get("mission_id") != "BETA-04":
        fail("published platform mission is not projected")
    if projection.get("current_execution") is not None:
        fail("historical execution leaked into current projection")
    historical = projection.get("historical_executions", [])
    if any(item.get("state") in {"Waiting", "Suspended", "Executing", "Running", "Qualifying", "AwaitingAcceptance"} for item in historical):
        fail("historical execution leaked into an active state")

    rendered = controller_presentation.operator_text(projection)
    if "Execution state              : NONE" not in rendered:
        fail("human projection does not expose current execution NONE")
    if historical and "Historical executions" not in rendered:
        fail("human projection does not preserve historical visibility")

    invariant_doc = (ROOT / "engineering/docs/architecture/ENGINEERING-PLATFORM-INVARIANTS.md").read_text()
    required = ["Canonical state ownership", "Canonical resolver", "Projection purity", "Freshness before idempotency", "Fail closed"]
    for phrase in required:
        if phrase not in invariant_doc:
            fail(f"missing normative invariant: {phrase}")

    register = ROOT / "engineering/evidence/operation-beta/beta-03g-platform-invariants-and-controller-governance-001/RECOMMENDATION-DISPOSITION-REGISTER.md"
    register_text = register.read_text()
    for source in ["Alpha", "BETA-00", "BETA-00A", "BETA-01", "BETA-03A", "BETA-03B", "BETA-03C", "BETA-03D", "BETA-03E", "BETA-03F"]:
        if source not in register_text:
            fail(f"recommendation source lacks disposition: {source}")

    presentation = (ROOT / "scripts/lib/emp/controller_presentation.py").read_text()
    beta_resolver = (ROOT / "scripts/lib/eos/operational_beta.py").read_text()
    if "def emit(" not in presentation or "def operator_text(" not in presentation:
        fail("shared controller renderer is missing")
    if "def _mission_projection(" not in beta_resolver:
        fail("canonical Beta mission projection resolver is missing")
    if "current_execution" not in beta_resolver or "historical_executions" not in beta_resolver:
        fail("current/history projection boundary is missing")

    production = subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "OA-v1.0.0"], text=True).strip()
    planning = subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "OB-PLAN-v1.0.0"], text=True).strip()
    if not production or not planning:
        fail("production or planning baseline is unresolved")
    print(json.dumps({"result": "PASS", "audit": "BETA-05 platform invariants", "current_platform_mission": "BETA-04", "future_recommended_mission": "CAGF-01", "current_executable_mission": "ZEUS-EXECUTION-LIFECYCLE-COMPLETION-01", "current_admission": None, "card_local_current_execution": None, "historical_execution_count": len(historical), "production_baseline": production, "planning_baseline": planning, "runtime_changes": False}, sort_keys=True))


if __name__ == "__main__":
    main()
