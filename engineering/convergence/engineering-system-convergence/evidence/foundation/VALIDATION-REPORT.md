# Validation Report

## Foundation results

| Validation | Result |
| --- | --- |
| Focused roadmap persistence/resume suite | PASS — 17 tests |
| Roadmap/schema/Project-State/EMM/evidence validation | PASS |
| Missing/malformed/unknown/dependency/contradiction/digest negative cases | PASS — fail closed |
| `engctl roadmap` status/show/gate/results/validate | PASS, read-only |
| Fresh-shell `engctl resume` convergence projection | PASS, exit 0 |
| Resume EOS mutation comparison | PASS — EOS file metadata unchanged |
| Isolated EOS runtime shell suite | PASS |
| EOS synchronization Python suite | PASS — 4 tests |
| Registry/EMP context suites | PASS — 4 tests; registry validation PASS (87 objects) |
| Work Initiation shadow suite after engctl version update | PASS — 11 tests |
| Structural controlled-document validation | PASS — 2,863 checks, 0 failures |
| C01 external/canonical byte comparison | PASS — all 20 files identical |
| Python compilation | PASS |
| Bash syntax | PASS |
| `git diff --check` | PASS |

Resume correctly reports the pre-existing repository–EOS synchronization
failure and Project State/Work Registry reconciliation requirement while still
showing C02 and its next action. No synchronization or refresh is attempted for
the active Homelab convergence program.

## Pre-existing unrelated failures

The following failures reproduce in a clean clone at
`6a26d2ea378248a4a9e9fe0d58b5df1c45a8c882` and were not corrected:

- Engineering CLI standard: 1 passed, 1 failed because `zeus --help` imports
  missing `scripts.lib.emp.repository_projection`.
- OA04 context suites: 3 passed, 4 failed because the historical Mission
  Contract is invalid, the same missing Zeus module prevents CLI execution,
  and one stale test expects OA-04 while the baseline resolves OA-08.
- Targeted semantic validation cannot resolve profiles for PROJ-0001 or
  SPEC-0004; the same profile gap exists on the clean baseline. The aggregate
  structural controlled-document validator passes.

These are C01 findings and inputs to C02/C04/C08/C14, not foundation
regressions.
