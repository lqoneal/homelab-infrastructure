# T02 Regression Report

## Legacy owner regression

```text
python3 -m unittest \
  scripts/tests/test-zeus-gate-approval.py \
  scripts/tests/test-zeus-gate-carry-forward.py \
  scripts/tests/test-zeus-oa02-lifecycle.py \
  scripts/tests/test-zeus-next-action.py
```

Result: **PASS — 53 tests**.

The emitted `fatal: Not a valid commit name ffff...` line belongs to an
expected negative fixture; unittest completed successfully.

## Broader live-fixture run

A 55-test OA-01 through stage-1 selection completed with 43 passes, 10
failures, and 2 errors. Every failure predates and is independent of the T02
decision seam: the checked-in live Progressive state has OA-06 in
`IMPLEMENTATION_REQUIRED`, while OA-02/OA-04 cases require earlier gates to
be active and one OA-05 assertion requires OA-06 to remain `PENDING`.

No failure stack entered `ProgressiveGateService.decide`, and no T02 source
was changed in response. Historical runtime state was not rewritten to make
unrelated live-fixture tests pass.

