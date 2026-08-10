# Validation Report

Status: PASS WITH PRE-EXISTING FAILURES RECORDED

Evaluated at: `2026-08-10T01:40:04Z`

## Baseline and safety

- Repository root: `/data/engineering/repositories/homelab`
- Branch: `main`
- Starting and final working `HEAD`: `3321b43e38e2c2058629473d171dbc14d3988aaa`
- `origin/main`: `3321b43e38e2c2058629473d171dbc14d3988aaa`
- Preservation reference: `preservation/ob-lifecycle-pre-rebuild-20260809T235039Z` at `4f5626d39f0924d3551cdabfcb61788153706774`
- Preservation mode: `REFERENCE_ONLY`; no preservation content was merged.
- C02 result: not recorded; no C02 `RESULT.yaml` exists.
- C02 and C03 were not executed. EOS was not synchronized. Zeus was not repaired.
- No publication transaction, commit, or push was performed.

## Passing validation

| Validation surface | Result | Evidence |
| --- | --- | --- |
| Controlled-document structure and DOC-0001 registration | PASS | Targeted STD-0006/PROC-0009 semantic checks passed; full repository assurance retains pre-existing failures |
| STD-0006 semantic validation | PASS | Targeted semantic validation |
| PROC-0009 semantic validation | PASS | Targeted semantic validation |
| Controlled-document relationships | PASS | 3 tests |
| Roadmap, state, mixed-generation gate, historical-gate, result, playbook, and evaluation schemas | PASS | Provenance-selected historical schema for C00-C02; prospective generic schema for C03+ |
| Structural roadmap validation | PASS | `STRUCTURAL_VALIDITY=PASS` |
| Executable-roadmap evaluation | PASS | `EXECUTION_SUFFICIENCY=PASS`, `EXECUTABLE=YES` |
| Gate resolution | PASS | C00 through C20 resolve; C00-C02 are NOT_APPLICABLE to STD-0006 and C03+ evaluate PASS |
| Terminal semantics | PASS | C20 is terminal, has `next_gate: null`, and names the external continuation authority and action |
| Negative and command tests | PASS | 29 roadmap tests, including mixed-generation provenance, identity/order separation, unknown dependency, contradictory state/evidence, missing playbook, classification, artifact schema, completeness test, ambiguous terminal continuation, and planning-only nonqualification |
| Project State binding | PASS | Project State program, gate, action, roadmap version, and qualification match resolved state |
| EMM binding | PASS | Every required bound source exists and matches its SHA-256 digest |
| EOS synchronization tests | PASS | 4 tests; temporary directories only |
| EOS runtime tests | PASS | Isolated temporary workspace; final result `EOS runtime tests passed.` |
| Fresh-shell resume | PASS | Exit 0; C02 and its authorized action recovered; roadmap tree and EOS state hashes unchanged |
| Python and shell syntax | PASS | `py_compile` and `bash -n` |
| Authored-content whitespace | PASS | `git diff --check` |

Historical C00/C01 result evidence remains digest-validated; it was not
whitespace-normalized or rewritten.

## Negative coverage exercised

The reusable evaluator was proven fail-closed for an unknown dependency,
missing execution playbook, missing classification contract, missing artifact
schema, missing completeness test, ambiguous terminal continuation, malformed
or contradictory roadmap state, incomplete current-gate dependency, evidence
digest drift, and missing gate definition. A `PLANNING_ONLY` fixture remained
structurally valid while reporting `EXECUTABLE=NO`.

## Pre-existing failures

The following failures reproduce from the untouched starting commit
`3321b43e38e2c2058629473d171dbc14d3988aaa` and are outside this corrective's
authorized scope:

1. `test-controlled-document-semantic-validation.py` has four failures:
   `zeus --help` exits 1 and does not expose the documented `--operator`
   option; three legacy Zeus documents do not resolve to the Procedure semantic
   profile:
   `ZEUS-WOP-SUBMISSION-PROCEDURE.md`, `ZEUS-DEVELOPMENT-MODE.md`, and
   `ZEUS-EXECUTION-LIFECYCLE-PROCEDURE.md`.
2. `test-zeus-oa04-context-reconstruction.py` has three errors because the
   existing Mission Contract is rejected as malformed. The same failure was
   reproduced from an archive of the starting commit using the repository Git
   metadata.

No repair was attempted. These findings do not alter the PASS result of the
roadmap-specific structural or execution-sufficiency evaluation.
