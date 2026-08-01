#!/usr/bin/env python3
"""Regression checks for OA-18 approval-boundary qualification evidence."""
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

evidence = ROOT / "engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/evidence/OA-18"
marker = json.loads((evidence / "VERIFIED").read_text())
report = json.loads((evidence / "VERIFICATION.json").read_text())

assert marker["verification_result"] == "PASS"
assert report["result"] == "PASS"
assert all(value == "PASS" for value in report["assertions"].values())
assert report["authoritative_inputs"]["capability_id"] == "ZEUS-OA-CAP-017"
assert report["qualification"]["execution_state"] == "Running"
print("PASS: OA-18 protected-action approval boundary, replay, recovery, and fail-closed evidence")
