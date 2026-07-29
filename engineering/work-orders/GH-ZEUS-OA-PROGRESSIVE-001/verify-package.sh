#!/usr/bin/env bash
set -euo pipefail
package="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$package"
sha256sum --check MANIFEST.sha256
python3 - <<'PY'
from pathlib import Path
import yaml
p = Path("gate-specification.yaml")
data = yaml.safe_load(p.read_text())
gates = data["gates"]
assert len(gates) == 30
assert [g["gate_id"] for g in gates] == [f"OA-{n:02d}" for n in range(1, 31)]
assert len({g["mission_objective"] for g in gates}) == 30
required = {
 "gate_id","title","mission_objective","capability_being_established","rationale",
 "inherited_design_requirements","authoritative_source_references","entry_prerequisites",
 "required_implementation_work","prohibited_effects","positive_test_cases",
 "negative_and_fail_closed_test_cases","idempotency_and_replay_tests",
 "safety_and_recovery_tests","regression_suite","required_evidence",
 "exact_success_criteria","manual_verification_procedure",
 "operator_acceptance_procedure","state_transitions","records_reconciled",
 "completion_marker","next_gate_enabled",
}
for gate in gates:
    assert required <= gate.keys(), (gate["gate_id"], required - gate.keys())
print("PASS: 30 unique cumulative gates and complete verification contracts")
PY
echo "PASS: Progressive OA package integrity"
