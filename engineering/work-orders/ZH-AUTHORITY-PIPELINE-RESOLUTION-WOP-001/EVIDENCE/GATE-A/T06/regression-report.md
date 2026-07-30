# T06 Regression Report

T06 changes no production runtime code, persistence format, decision behavior,
projection behavior, compatibility interface, or consumer call path.

Affected regression covered the dependency validator, authority primitives,
decision/replay behavior, lifecycle projection, migrated consumers, protected
compatibility adapters, and gate consumers. The final command and result are
127 tests passed and 0 failed.

Two consecutive repository classifications returned equal structured results,
including exactly three ordered layers, unchanged downward edges, explicit
non-runtime categories, and `PASS`.

Protected implementations remain present:

- `ProgressiveGateService`;
- `GateApprovalService`;
- `scripts/lib/emp/gate_carry_forward.py`;
- `scripts/lib/emp/progressive_oa.py`; and
- `scripts/lib/emp/oa02_lifecycle.py`.

All protected files and both service classes remain present.
