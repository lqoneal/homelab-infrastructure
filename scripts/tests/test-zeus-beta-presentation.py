#!/usr/bin/env python3
"""Qualification for active/history Beta controller presentation."""

import json
import os
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def command(*args: str) -> tuple[dict, str]:
    with tempfile.TemporaryDirectory(dir="/home/loneal") as directory:
        operator = Path(directory) / "operator.json"
        operator.write_text('{"invocation_count": 0, "orientation_limit": 100, "schema_version": 1}\n')
        env = os.environ.copy()
        env.update({"ZEUS_TESTING": "1", "ZEUS_OPERATOR_STATE": str(operator), "ZEUS_NO_INTRO": "1"})
        json_result = subprocess.run(
            [str(ROOT / "scripts/zeus"), *args, "--json"],
            cwd=ROOT, env=env, text=True, capture_output=True, check=True,
        )
        human_result = subprocess.run(
            [str(ROOT / "scripts/zeus"), *args],
            cwd=ROOT, env=env, text=True, capture_output=True, check=True,
        )
        return json.loads(json_result.stdout), human_result.stdout


def main() -> None:
    active, active_text = command("mission", "list")
    assert {item["mission_id"] for item in active["missions"]} == {"CAGF-01", "EPE-01"}
    assert "OA-30" not in active_text
    assert not any(line.startswith("ZDCL-01") for line in active_text.splitlines())

    explain, explain_text = command("mission", "explain", "ZDCL-01")
    for field in ("operation", "readiness", "selection_rationale", "production_baseline", "development_baseline"):
        assert field in explain
        assert str(explain[field]) in explain_text

    queue, queue_text = command("mission", "queue", "list")
    assert queue["queue_scope"] == "OPERATION"
    assert queue["execution_environment"] == "ADMITTED_MISSION_ATTRIBUTE"
    assert "Queue scope" in queue_text
    assert "ZDCL-01" in queue_text

    history, _ = command("mission", "history")
    assert history["historical"] is True
    assert len(history["missions"]) == 30

    zdcl_history, _ = command("mission", "history", "ZDCL-01")
    assert zdcl_history["historical"] is True
    assert zdcl_history["historical_executions"]

    print("Beta controller presentation tests: PASS")


if __name__ == "__main__":
    main()
