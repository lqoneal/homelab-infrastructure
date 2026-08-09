# Test Results

## Focused passes

- canonical baseline resolution: 9 tests;
- durable reconciliation receipt: 2 tests;
- P2 submission boundary: 4 tests;
- P3 admission boundary: 8 tests;
- P3 mission-scoped cardinality: 17 tests;
- P4 bootstrap/cardinality: 21 tests;
- Wave 1 resolver/read model: 15 tests;
- Wave 2 authority aggregate: 10 tests;
- Wave 3 recovery: 8 tests;
- automatic canonicalization: 6 tests;
- operator status contract: 13 tests;
- admission freshness/supersession: 3 tests;
- resume admission lineage: 14 tests.

The exact reconciliation replay produced the same immutable receipt ID and
digest. The current receipt digest was independently recomputed as:

`7b67bd95f29329755ebf436a51cf6c16c456c8b17854df54d1cbb1d0a93b1c`

## Classified historical result

`test-zeus-p4-g3-runtime-discovery.py` remains a historical Beta compatibility
test and expects `BEGIN_CONTROLLED_MISSION_WORK` for a preserved Beta record.
The current runtime returns `OPERATOR_REVIEW_LEGACY_LIFECYCLE_RECONCILIATION`.
The existing P4 evidence classifies this as historical compatibility, not a
current lifecycle regression; the test and historical record were not
rewritten.

## Negative proof

Lineage tests cover missing/unreachable provenance, non-descendant history,
publication parity failure, runtime identity mismatch, digest tampering, and
receipt identity collision. P3/P4 suites cover historical-only, wrong
identity, duplicate-current, and superseded-artifact fail-closed cases.

