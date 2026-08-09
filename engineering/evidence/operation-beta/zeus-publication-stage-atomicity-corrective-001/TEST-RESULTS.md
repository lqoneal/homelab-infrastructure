# Test Results

## Passing focused and directly affected suites

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  scripts/tests/test-zeus-publication-transaction.py \
  scripts/tests/test-zeus-publication-transaction-cohort-revalidation.py \
  scripts/tests/test-zeus-publication-supersession-cardinality.py \
  scripts/tests/test-zeus-postpublication-verification-routing.py \
  scripts/tests/test-zeus-publication-candidate-authority.py \
  scripts/tests/test-zeus-publication-cohort.py

Ran 61 tests in 4.230s
OK
```

The command also included the publication candidate-authority and cohort suites.
The focused transaction file contains 17 passing tests after the corrective.
`python3 -m py_compile` and `git diff --check` also passed.

Repository controlled-document semantic, conformance, and assurance validation
passed 3,808 checks with zero failures.

## Broader-suite disposition

A 112-test broader publication/CLI run produced 97 passes and 15 unrelated
pre-existing failures. Seven errors and six assertion failures came from
`test-authority-publication.py` expecting a non-repository-fixed runtime
activation pointer. One Beta-controller assertion expected controlled mission
work instead of the live Codex-thread recovery action. One CLI consistency
assertion expected `READY_FOR_REVIEW` instead of the current `READY`. None
executes the corrected publication staging transition; the directly affected
49-test set passed in the same worktree.
