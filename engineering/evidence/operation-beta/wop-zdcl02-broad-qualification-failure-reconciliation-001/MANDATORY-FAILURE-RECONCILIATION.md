# Mandatory Failure Reconciliation

The authoritative current profile is invoked from repository root with `PYTHONPATH=. python3 <test>`, one isolated process per test, and a bounded timeout. It covers submission bootstrap, direct WOP submission, blocker lifecycle execution, qualification contract, controller interface, CLI consistency, platform lifecycle, and transaction recovery. All eight suites pass. The historical serial loop’s direct-file import failures are harness defects, not mandatory candidate failures. The profile now has zero mandatory failures and a definitive completion result.
