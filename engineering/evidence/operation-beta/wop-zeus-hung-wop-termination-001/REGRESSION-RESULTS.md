# Regression Results

Focused disposable termination tests: 7 passed.

Existing mission execution and safe-interruption tests: 11 passed.

Controlled-document semantic and synchronization tests: 13 passed.

Controlled-document validation: 2,863 passed, 0 failed.

Registry validation: 87 objects passed.

Engineering Platform validation: all four stages passed.

`git diff --check`: passed.

The full repository pytest invocation was stopped after several minutes with
no test output. One standalone CLI consistency test expects a recovery branch
and therefore fails on the current `main` branch (`READY` versus
`READY_FOR_REVIEW`); this is an environment-sensitive pre-existing assertion,
not a termination failure.

Live missions, live ZDCL-02, dispatch, execute, and resume were not used.
Controlled-document, Registry, platform, and full regression qualification
remain to be run after the implementation diff is complete.
