#!/usr/bin/env python3
"""BETA-03F current-versus-historical mission projection qualification."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.lib.eos import operational_beta  # noqa: E402


def main() -> None:
    projection = operational_beta.mission_view(ROOT, "explain", "ZDCL-01")
    assert projection["current_admission"]["admission_id"] == "MISSION-ADMISSION-e8a3b130-f4b6-50d0-9bf4-21b1a2c5cefd"
    assert projection["current_execution"] is None
    assert [item["state"] for item in projection["historical_executions"]] == ["Cancelled"]
    assert projection["historical_executions"][0]["execution_id"] == "MISSION-EXECUTION-8c444488-9ee3-5e03-949f-dc750a0b918c"
    history = operational_beta.mission_history(ROOT, "ZDCL-01")
    assert history["historical"] is True
    assert history["historical_executions"][0]["state"] == "Cancelled"
    assert projection["current_execution"] not in history["historical_executions"]
    print("Beta mission projection tests: PASS")


if __name__ == "__main__":
    main()
