# Test Results

Focused and regression results:

- P3 mission-scoped cardinality: PASS, 17 tests
- P3 admission boundary: PASS, 8 tests
- Wave 1 canonical resolver: PASS, 7 tests
- Wave 1 canonical read model: PASS, 8 tests
- Wave 2 authority aggregate: PASS, 10 tests
- Wave 3 recovery: PASS, 8 tests
- development-mode recovery: PASS, 13 tests
- automatic canonicalization: PASS, 6 tests
- Python compilation of affected runtime modules: PASS
- admission replay verifier: PASS, `duplicate_admission=IDEMPOTENT`

The pre-existing P4-G3 runtime-discovery test remains a historical Beta
expectation for `MISSION-BETA-562F443E16C69401` and expects
`BEGIN_CONTROLLED_MISSION_WORK`; current canonical behavior returns the
operator-review legacy reconciliation action. It is not a regression of this
mission-scoped P3 corrective and was not changed.

The mission-verification-controller direct-file invocation without
`PYTHONPATH=.` is a test harness import invocation issue, not a corrective
failure. The repository integrated validator independently passed.
