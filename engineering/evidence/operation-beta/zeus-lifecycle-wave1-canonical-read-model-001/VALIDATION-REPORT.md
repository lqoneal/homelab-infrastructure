# Validation Report

Focused results:

```text
Wave 1 canonical read-model tests: PASS (6 tests)
P2 submission-boundary tests: PASS (4 tests)
Automatic-canonicalization tests: PASS (6 tests)
```

The existing CLI consistency suite has one unrelated pre-existing failure:
`test_doctor_ready_for_review_on_recovery_branch` expects `READY_FOR_REVIEW`
while the current doctor projection returns `READY`. Its other four tests
pass; this Wave 1 change does not touch doctor behavior.

Final repository qualification after implementation is recorded in the
completion report.

Final repository qualification:

- controlled-document validation: `PASS`, 2897 checks, 0 failures;
- semantic-all: `PASS`, 3805 checks, 0 failures;
- assurance-only: `PASS`, 1 check, 0 failures;
- conformance: `PASS`, 2899 checks, 0 failures;
- implementation coverage: `PASS`, 2901 checks, 0 failures;
- Zeus platform verification: `PASS`;
- Operation Beta verification: `PASS`;
- integrated validation: `PASS`;
- repository/EOS validation: `PASS`;
- `git diff --check`: `PASS`.

The additive synchronization validator remains a candidate-worktree check,
not a publication operation: `OUT_OF_SYNC=5`, `DOCUMENT_CHANGED=2`,
`IMPLEMENTATION_CHANGED=1`, `MISSING_ARTIFACT=0`, `PASS=1`. These are the
previously classified dirty candidate records.

The broader mission-verification regression suite was not absorbed into the
Wave 1 result: its fixture copy encountered `ENOSPC` while copying the large
pre-existing runtime, and its direct legacy expectation still conflicts with
the current projection's `OPERATOR_REVIEW_LEGACY_LIFECYCLE_RECONCILIATION`.
The controller-interface suite likewise retains one unrelated historical
recommendation expectation (`ZDCL-01` versus current `CAGF-01`).
