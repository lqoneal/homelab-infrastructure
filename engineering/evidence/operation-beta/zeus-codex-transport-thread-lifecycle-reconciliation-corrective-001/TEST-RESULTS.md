# Test Results

Focused lifecycle suite: 24 tests, PASS. It covers all required state classes,
same-native-thread resume, binding preservation, no-work invariants,
idempotency, duplicate ownership, missing/corrupt persistence, mission,
execution, provider, repository, and authority failures, explicit fork and
lineage, no implicit new-thread fallback, coherent status, remote disconnect,
and read-only status.

Existing managed adapter: 32 tests PASS (2 skipped). Existing wrapper
supersession: 19 PASS. Existing execution lifecycle corrective: 12 PASS.
Managed handoff: 20 PASS. Interactive Codex: 21 PASS (3 skipped). Canonical
mission lifecycle: 2 PASS. Wave 1 canonical resolver: 10 PASS. Mission
verification controller: 5 PASS.

Provider invocation: 9 PASS. Execution-start: 12 of 13 PASS; the remaining
candidate-scope assertion correctly reports the already-dirty, unpublished
multi-workstream tree as outside its older accepted candidate. Execution
monitoring: 6 of 9 PASS; three live-state expectations target historical gate
6/`EXECUTING` state while the repository now records gate 10/reconciled
historical state. These failures are environmental/pre-existing and were not
weakened.

The provider-session suite contains a pre-existing live-runtime tamper test
hard-coded outside the writable workspace. Its two non-destructive tests pass;
the tamper case cannot run under the managed read-only runtime permission and
was not weakened or altered.

`validate_controlled_documents.py --semantic-all` passed 3,805 checks with zero
failures. The relationship unit suite passed. One separate semantic-validator
unit retains a pre-existing generated/historical path-classification assertion
failure even though semantic-all passes. `git diff --check` passed.
