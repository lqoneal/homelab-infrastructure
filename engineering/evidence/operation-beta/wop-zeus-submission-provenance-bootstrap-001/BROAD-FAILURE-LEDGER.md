# Broad Failure Ledger

The 30 failures reported by the original broad run are listed exactly once.

| ID | Test | Candidate | Baseline | Classification |
|---|---|---:|---:|---|
| F-01 | test-admission-freshness-and-supersession.py | 1 | 1 | BASELINE_FAILURE_NOT_CAUSED_BY_CANDIDATE |
| F-02 | test-authority-publication.py | timeout/fail | timeout/fail | ENVIRONMENT_DEPENDENCY |
| F-03 | test-beta-closeout.py | 1 | 1 | ENVIRONMENT_DEPENDENCY |
| F-04 | test-beta-mission-projection.py | 1 | 1 | BASELINE_FAILURE_NOT_CAUSED_BY_CANDIDATE |
| F-05 | test-beta-platform-invariants.py | 1 | 1 | BASELINE_FAILURE_NOT_CAUSED_BY_CANDIDATE |
| F-06 | test-controlled-document-semantic-validation.py | 1 | env | ENVIRONMENT_DEPENDENCY |
| F-07 | test-convergence-runtime.py | 1 | 1 | BASELINE_FAILURE_NOT_CAUSED_BY_CANDIDATE |
| F-08 | test-operational-gate-handler.py | 1 | 1 | BASELINE_FAILURE_NOT_CAUSED_BY_CANDIDATE |
| F-09 | test-progressive-runtime-consolidation.py | 1 | 1 | BASELINE_FAILURE_NOT_CAUSED_BY_CANDIDATE |
| F-10 | test-progressive-runtime-implementation-synchronization.py | timeout/fail | 1 | ENVIRONMENT_DEPENDENCY |
| F-11 | test-publication-boundary-guard.py | 0 | 1 | UNRELATED_TO_CANDIDATE |
| F-12 | test-resume-admission-supersession-lineage.py | 1 | 1 | BASELINE_FAILURE_NOT_CAUSED_BY_CANDIDATE |
| F-13 | test-stage1-execution-resolution.py | 1 | 1 | BASELINE_FAILURE_NOT_CAUSED_BY_CANDIDATE |
| F-14 | test-zeus-oa02-controlled-authority.py | 1 | 1 | BASELINE_FAILURE_NOT_CAUSED_BY_CANDIDATE |
| F-15 | test-zeus-oa04-context-reconstruction.py | 1 | 1 | BASELINE_FAILURE_NOT_CAUSED_BY_CANDIDATE |
| F-16 | test-zeus-oa04-current-context.py | 1 | 1 | BASELINE_FAILURE_NOT_CAUSED_BY_CANDIDATE |
| F-17 | test-zeus-oa04-mission-resolution.py | 1 | 1 | BASELINE_FAILURE_NOT_CAUSED_BY_CANDIDATE |
| F-18 | test-zeus-operational-bootstrap.py | 1 | 1 | ENVIRONMENT_DEPENDENCY |
| F-19 | test-zeus-operator-interface.py | timeout/fail | timeout/fail | ENVIRONMENT_DEPENDENCY |
| F-20 | test-zeus-gate-carry-forward.py | 1 | 1 | ENVIRONMENT_DEPENDENCY |
| F-21 | test-zeus-hung-wop-termination.py | 1 | 1 | ENVIRONMENT_DEPENDENCY |
| F-22 | test-zeus-mission-count-status.py | 1 | 1 | BASELINE_FAILURE_NOT_CAUSED_BY_CANDIDATE |
| F-23 | test-zeus-oa01-verification.py | timeout/fail | timeout/fail | LIFECYCLE_PROFILE_MISMATCH |
| F-24 | test-zeus-oa02-lifecycle.py | timeout/fail | timeout/fail | LIFECYCLE_PROFILE_MISMATCH |
| F-25 | test-zeus-oa03-mission-contract-discovery.py | timeout/fail | timeout/fail | BASELINE_FAILURE_NOT_CAUSED_BY_CANDIDATE |
| F-26 | test-zeus-oa05-mission-staging.py | timeout/fail | timeout/fail | LIFECYCLE_PROFILE_MISMATCH |
| F-27 | test-zeus-oa06-mission-knowledge.py | timeout/fail | timeout/fail | BASELINE_FAILURE_NOT_CAUSED_BY_CANDIDATE |
| F-28 | test-zeus-oa06-mission-eligibility.py | timeout/fail | timeout/fail | BASELINE_FAILURE_NOT_CAUSED_BY_CANDIDATE |
| F-29 | test-zeus-oa16-execution-start.py | timeout/fail | timeout/fail | LIFECYCLE_PROFILE_MISMATCH |
| F-30 | test-zeus-oa25-controlled-state-reconciliation.py | timeout/fail | timeout/fail | BASELINE_FAILURE_NOT_CAUSED_BY_CANDIDATE |
