# T01 Qualification and Regression Report

Date: 2026-07-29

## Qualification

Command:

```text
python3 -m unittest scripts/tests/test-progressive-gate-primitives.py scripts/tests/test-zeus-progressive-oa.py
```

Result: **PASS — 32 tests**.

Coverage includes valid verification dispatch, valid receipt and predecessor,
deterministic replay, missing/corrupt/stale receipts, invalid predecessor,
wrong gate binding, receipt and evidence digest mismatches, supersedence
replay conflict, absent repository qualification, unsupported-verifier
fail-closed behavior, state consistency, interruption recovery, immutable
historical evidence, and exactly-one-gate advancement.

Syntax qualification:

```text
python3 -m py_compile scripts/lib/emp/progressive_gate.py \
  scripts/lib/emp/progressive_oa.py \
  scripts/tests/test-progressive-gate-primitives.py
```

Result: **PASS**.

## Legacy and routing regression

Command:

```text
python3 -m unittest \
  scripts/tests/test-zeus-gate-approval.py \
  scripts/tests/test-zeus-gate-carry-forward.py \
  scripts/tests/test-zeus-oa02-lifecycle.py \
  scripts/tests/test-zeus-next-action.py
```

Result: **PASS — 53 tests**. `GateApprovalService`,
`gate_carry_forward.py`, `oa02_lifecycle.py`, and legacy next-action behavior
remain operational.

## Cumulative repository-state run

A 115-test OA-01 through OA-05 plus legacy run completed with 104 passes,
9 failures, and 2 errors. The failures are live-fixture precondition
conflicts: current repository state has OA-06 active in
`IMPLEMENTATION_REQUIRED`, while OA-02/OA-04/OA-05 tests require those earlier
gates to be active or later gates to remain `PENDING`. No failure originated
in `test-progressive-gate-primitives.py`,
`test-zeus-progressive-oa.py`, or the legacy regression files above.

This cumulative result is recorded as a repository fixture-state limitation,
not a clean regression pass and not a reason to mutate historical runtime
state in T01.
