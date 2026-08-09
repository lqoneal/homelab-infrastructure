# Test Results

Passed focused suites:

* P5-G2 dispatch foundation: 3 tests.
* P5-G3 provider session: 3 tests.
* provider-boundary canonicalization: 10 tests.
* Wave 1 resolver/read-model: 7 + 8 tests.
* P3 admission boundary: 8 tests.
* P4 bootstrap boundary: 21 tests.
* P5-G1 provider selection: 3 tests.
* Wave 2 authority aggregate: 10 tests.
* Wave 3 recovery: 8 tests.
* provider live-lineage regression: 3 tests.

The P5-G2 fixture was corrected to select the requested mission's dispatch
artifacts rather than the first filesystem entry. Read-only snapshots cover
canonical lifecycle JSON artifacts and intentionally exclude unrelated shared
Codex transcript SQLite activity.
