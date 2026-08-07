# Qualification Results

The bounded convergence qualification completed with the following results.

Managed-controller and semantic-profile focused command:

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest -v scripts/tests/test-managed-codex-handoff.py scripts/tests/test-controlled-document-semantic-validation.py
```

Result: 25 passed.

Default controlled-document validation passed 2,897/2,897 checks. The three
affected procedures each resolve to the existing `Procedure` profile and pass
focused semantic validation with zero errors. Read-only `zeus platform
verify --json` and `zeus operation verify --json` passed.

The known active-tree recovery error remains classified as
`ENVIRONMENTAL_DIRTY_TREE_CONTAMINATION`; the isolated recovery fixture passed
13/13. The broader focused inventory also contains legacy fixture failures
outside this bounded corrective (WOP packaging metadata, stale runtime
fixtures, and reconciliation fixtures); those were not changed or suppressed.
Their exact evidence and preservation rationale are in
`COMPLETE-QUALIFICATION-REPORT.md`.
