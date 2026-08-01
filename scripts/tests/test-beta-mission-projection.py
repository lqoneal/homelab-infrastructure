#!/usr/bin/env python3
"""BETA-03F current-versus-historical mission projection qualification."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.lib.eos import operational_beta  # noqa: E402


def main() -> None:
    projection = operational_beta.mission_view(ROOT, "explain", "ZDCL-01")
    assert projection["current_admission"]["admission_id"].startswith("MISSION-ADMISSION-")
    assert projection["current_execution"] is None
    historical_states = {item["state"] for item in projection["historical_executions"]}
    assert "Cancelled" in historical_states
    assert historical_states.isdisjoint({"Waiting", "Suspended", "Executing", "Running", "Qualifying", "AwaitingAcceptance"})
    history = operational_beta.mission_history(ROOT, "ZDCL-01")
    assert history["historical"] is True
    assert "Cancelled" in {item["state"] for item in history["historical_executions"]}
    assert projection["current_execution"] not in history["historical_executions"]
    print("Beta mission projection tests: PASS")


if __name__ == "__main__":
    main()
