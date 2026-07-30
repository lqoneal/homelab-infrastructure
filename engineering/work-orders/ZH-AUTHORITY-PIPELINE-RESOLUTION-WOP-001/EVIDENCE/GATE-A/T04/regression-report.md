# T04 Regression Report

## Passing affected regressions

- legacy next-action: 9 tests;
- legacy GateApprovalService: 35 tests;
- OA-03 mission-contract discovery: 5 tests;
- controlled documents: 2,647 checks;
- diff whitespace validation: pass.

## Unrelated live-state discrepancies

Broader tests that bind directly to current repository state retain
pre-existing phase assumptions:

- OA-02 Controlled Mission Authority: 7 pass, 4 fail because the current
  active gate is not OA-02;
- OA-04 mission resolution: 1 pass, 4 fail, 2 error because the current active
  gate is not OA-04;
- OA-05 cumulative lifecycle: 11 pass, 1 fail because current OA-06 is
  `IMPLEMENTATION_REQUIRED`, while the test expects `PENDING`.

None of these failures traverses the migrated CLI service calls. T04 did not
rewrite live state, relax fail-closed authority, or implement a later
transition to satisfy stale phase fixtures.

