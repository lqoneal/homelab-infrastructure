# Runtime Conformance Matrix

| SPEC-0014 requirement | Result | Evidence |
| --- | --- | --- |
| Exact authority chain resolver | PASS (component) | 3 convergence tests; missing authority fails closed |
| Effective execution chain | FAIL | RQ-REQUAL-001 |
| Single authority owner behavior | FAIL (runtime) | RQ-REQUAL-002 legacy consumers remain |
| Directional generated/sync projections | PARTIAL | component contracts only |
| EOS provenance projection | PASS | 4 EOS tests |
| EENS and EMP runtime integration | FAIL | RQ-REQUAL-003 |
| Qualification/verification service integration | PARTIAL | component result only; not execution-gated |
| Compatibility projection isolation | FAIL | legacy resolver is invoked by `zeus execution` |
