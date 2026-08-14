# Engineering System Convergence Roadmap

The canonical machine-readable roadmap is `roadmap.yaml`; this file is its
compact human review surface and does not duplicate gate execution contracts.
Open the listed `GATE.yaml` for purpose, problem, objective, rationale, scope,
dependencies, entry conditions, inputs, procedure, outputs, evidence,
acceptance, fail-closed conditions, stop boundary, result location, and resume
instructions.

| Gate | Title | Current status |
| --- | --- | --- |
| C00 | Preservation and Rollback | COMPLETE |
| C01 | Repository and Infrastructure Baseline Assessment | COMPLETE_WITH_FINDINGS |
| C02 | Controlled Documentation and Authority Assessment | COMPLETE_WITH_FINDINGS |
| C03 | EOS and Engineering State Assessment | CURRENT |
| C04 | engctl and Resume Assessment | PENDING |
| C05 | Roadmap / Project State / Registry Assessment | PENDING |
| C06 | WOP and Execution Contract Assessment | PENDING |
| C07 | EMP Assessment | PENDING |
| C08 | Zeus Assessment | PENDING |
| C09 | EENS Assessment | PENDING |
| C10 | Provider / Codex / Execution Runtime Assessment | PENDING |
| C11 | Evidence / Qualification / Acceptance Assessment | PENDING |
| C12 | Git / Publication / Synchronization Assessment | PENDING |
| C13 | Recovery / Interruption / Resume Assessment | PENDING |
| C14 | Validation / Tests / Observability Assessment | PENDING |
| C15 | Cross-System Dependency and Authority Reconciliation | PENDING |
| C16 | Redundancy / Simplification Analysis | PENDING |
| C17 | Canonical Target Architecture | PENDING |
| C18 | System Convergence Roadmap | PENDING |
| C19 | engctl Resume Contract and Cold-Resume Qualification | PENDING |
| C20 | Begin Controlled Convergence Implementation | PENDING |

Current gate: `C03`. Next authorized action:
`BEGIN_C03_EOS_AND_ENGINEERING_STATE_ASSESSMENT`.

C20 marks entry into one separately authorized migration gate. It never grants
automatic authority to execute the complete convergence roadmap.

## Strategic publication topology

Publication is capability-boundary driven. Gate completion never implies
publication, and publication authority never grants the next gate.

| Gate | Capability boundary | Publication class | Downstream baseline effect |
| --- | --- | --- | --- |
| C00 | Preserved repository and rollback baseline | REQUIRED_BOUNDARY | Baseline for C01 and all later recovery |
| C01 | Repository/infrastructure observations | NOT_A_PUBLICATION_BOUNDARY | Findings feed C02 |
| C02 | Controlled authority disposition | CONDITIONAL_BOUNDARY | Publish only if canonical authority/state changes before C03-C06 |
| C03 | EOS/state assessment | NOT_A_PUBLICATION_BOUNDARY | Findings feed C04 |
| C04 | engctl/resume assessment | NOT_A_PUBLICATION_BOUNDARY | Findings feed C05 |
| C05 | State/registry ownership disposition | CONDITIONAL_BOUNDARY | Publish only if canonical ownership/bindings change before C06 |
| C06 | Foundational WOP + minimum EENS | REQUIRED_BOUNDARY | Baseline required by C07-C09 and later lifecycle consumers |
| C07 | EMP assessment | NOT_A_PUBLICATION_BOUNDARY | Findings feed C08 and C15 |
| C08 | Zeus assessment | NOT_A_PUBLICATION_BOUNDARY | Findings feed C09 and C10 |
| C09 | Primary EENS capability | REQUIRED_BOUNDARY | Baseline required by C10-C20 consumers |
| C10 | Provider/runtime assessment | NOT_A_PUBLICATION_BOUNDARY | Findings feed C11 and C13 |
| C11 | Qualification/evidence authority disposition | CONDITIONAL_BOUNDARY | Publish only if qualification authority changes before C12-C19 |
| C12 | Publication transaction assessment | NOT_A_PUBLICATION_BOUNDARY | Findings define later transaction controls |
| C13 | Recovery/resume assessment | NOT_A_PUBLICATION_BOUNDARY | Findings feed C14-C17 |
| C14 | Validation/observability assessment | NOT_A_PUBLICATION_BOUNDARY | Findings feed C15 |
| C15 | Cross-system authority reconciliation | REQUIRED_BOUNDARY | Baseline required by C16-C20 architecture/planning |
| C16 | Simplification dispositions | NOT_A_PUBLICATION_BOUNDARY | Dispositions feed C17 |
| C17 | Canonical target architecture | REQUIRED_BOUNDARY | Baseline required by C18-C20 |
| C18 | System-level convergence planning | REQUIRED_BOUNDARY | Published plan required by C19/C20 |
| C19 | Cold-resume qualification | REQUIRED_BOUNDARY | Qualified baseline required before C20 entry |
| C20 | Qualified implementation tranche | REQUIRED_BOUNDARY | Baseline required before the next separately authorized tranche |

For a required boundary the controlled sequence is:
`CAPABILITY_COMPLETE -> QUALIFY -> RECONCILE -> RESOLVE_PUBLICATION_AUTHORITY -> PUBLISH -> VERIFY_PUBLISHED_BASELINE -> RESOLVE_NEXT_GATE_AUTHORITY`.
Conditional boundaries publish only when their machine-readable authority or
baseline-change condition is true. No publication is required before C06 in
the current state unless C02 or C05 changes the canonical authority/state
baseline. EOS synchronization is required only when an affected published
capability changes an EOS-owned projection or baseline.
