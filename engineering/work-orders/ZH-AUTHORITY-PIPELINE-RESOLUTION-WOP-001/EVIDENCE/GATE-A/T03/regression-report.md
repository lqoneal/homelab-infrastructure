# T03 Regression Report

## Affected legacy regression

Command:

```text
python3 -m unittest \
  scripts/tests/test-zeus-next-action.py \
  scripts/tests/test-zeus-gate-approval.py \
  scripts/tests/test-zeus-oa02-lifecycle.py
```

Result: `49 tests`, `PASS`.

`git diff --check` also passed.

## Repository-wide observation

`python3 -m unittest discover -s scripts/tests -p 'test*.py'` reached the
repository's script-inventory meta-test and failed after 142.695 seconds.
That inventory reported five live-state failures:

- mission-assurance fixture expects PROC-0001 version 1.16;
- OA-02 controlled-authority fixture observes conflicting live authority;
- two OA-04 suites observe a different sole active gate; and
- OA-05 expects OA-06 `PENDING` while live state is
  `IMPLEMENTATION_REQUIRED`.

These traces do not import or enter `progressive_lifecycle.py` or the modified
OA-02 compatibility resolver. They are recorded as repository baseline/live
state discrepancies, not T03 regression failures. T03 did not alter the
documents or runtime state named by those failures.

## Controlled documents

Controlled-document validation passed all 2,647 checks with zero failures.
