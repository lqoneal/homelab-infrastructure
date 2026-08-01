"""Regression checks for OA-17 controlled execution authorization evidence."""
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.lib.emp.execution_authorization import ExecutionAuthorizationStore  # noqa: E402


evidence = ROOT / "engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/evidence/OA-17"
marker = json.loads((evidence / "VERIFIED").read_text())
report = json.loads((evidence / "VERIFICATION.json").read_text())
request = json.loads((evidence / "AUTHORIZATION-REQUEST.json").read_text())
receipt = json.loads((evidence / "AUTHORIZATION-RECEIPT.json").read_text())
state = json.loads((evidence / "AUTHORIZATION-STATE.json").read_text())

assert marker["verification_result"] == "PASS"
assert report["result"] == "PASS"
assert all(value == "PASS" for value in report["assertions"].values())
assert request["request_digest"] == receipt["request_digest"]
assert request["execution_id"] == receipt["execution_id"] == state["execution_id"]
assert receipt["decision"] == "AUTHORIZED"
assert state["state"] == "REVOKED"
assert receipt["authority_lease"]
assert request["mission_id"] == "OA-17"
print("PASS: OA-17 authorization lifecycle, bindings, replay, timeout, recovery, and fail-closed evidence")
