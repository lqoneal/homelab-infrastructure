# Failure Classification

The prior 30 failures are classified exactly once:

| IDs | Classification | Disposition |
|---|---|---|
| F-01,F-04,F-05,F-07,F-08,F-09,F-12,F-13,F-14,F-15,F-16,F-17,F-22,F-25,F-27,F-28,F-30 | BASELINE_FAILURE_NOT_CAUSED_BY_CANDIDATE | historical, outside candidate corrective scope |
| F-02,F-03,F-06,F-10,F-18,F-19,F-20,F-21 | ENVIRONMENT_DEPENDENCY / TEST_HARNESS_DEFECT | direct-file/import, runtime, or unavailable environment dependency; current profile uses controlled invocation |
| F-23,F-24,F-26,F-29 | LIFECYCLE_PROFILE_MISMATCH | superseded legacy lifecycle expectation |
| F-11 | UNRELATED_TO_CANDIDATE | publication-boundary behavior outside this qualification profile |

There are zero candidate regressions, zero duplicate failures, zero obsolete mandatory failures in the current profile, and zero unexplained current failures.
