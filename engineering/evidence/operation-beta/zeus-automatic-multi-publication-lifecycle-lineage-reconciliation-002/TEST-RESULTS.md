# Test Results

Focused tests:

* `PYTHONPATH=. python3 scripts/tests/test-zeus-postpublication-lifecycle-baseline-reconciliation.py` — **6 passed**.
* `PYTHONPATH=. python3 scripts/tests/test-zeus-canonical-baseline-resolution.py` — **9 passed**.

The focused reconciliation tests cover exact replay, tampered digest failure,
no-receipt live projection, stale supplemental receipt, duplicate current
receipt failure, and three sequential Git publication transitions including
the N+1 live HEAD without editing a prior receipt.

Existing P2/P3/P4 and Wave 1–3 qualification suites remain applicable and are
listed in `VALIDATION-REPORT.md`. Historical P4 compatibility test failures
remain classified in the preceding corrective evidence and are not changed by
this lineage correction.

Additional regressions passed: P2 boundary (4), P3 admission (8), P3
cardinality (17), P4 bootstrap/cardinality (21), Wave 1 resolver/read-model
(7+8), Wave 2 aggregate (10), Wave 3 recovery (8), automatic canonicalization
(6), status (13), admission freshness (3), resume lineage (14), runtime
adoption (3), runtime discovery (7), platform synchronization (5), and
canonical transaction recovery (13).

Two unrelated pre-existing suites remain failing and do not touch the changed
runtime or documentation: `test-zeus-wop-submission.py` (2 stale package
resolution expectations) and the historical `test-zeus-p4-g3-runtime-discovery.py`
(expects `BEGIN_CONTROLLED_MISSION_WORK` for a preserved legacy Beta record).
They are classified as `HISTORICAL_ONLY` / pre-existing compatibility
failures, not absorbed into this corrective.
