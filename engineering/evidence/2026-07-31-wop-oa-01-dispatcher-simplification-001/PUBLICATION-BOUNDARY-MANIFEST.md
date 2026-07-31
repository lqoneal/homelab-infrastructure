# Publication Boundary Manifest

## Included paths

The following paths are the complete publication boundary for
`WOP-OA-01-DISPATCHER-SIMPLIFICATION-PUBLICATION-001`:

```text
docs/specifications/SPEC-0014-OPERATIONAL-ALPHA-CONVERGENCE-AUTHORITY.md
engineering/evidence/2026-07-31-wop-oa-01-dispatcher-simplification-001/
engineering/execution/execution-interface.yaml
engineering/execution/operational-alpha-execution-contract.yaml
engineering/metadata/operational-alpha-emm.yaml
engineering/operations/zeus-mission-admission-runtime.md
scripts/lib/emp/mission_admission_runtime.py
scripts/tests/test-operational-alpha-status.py
scripts/zeus
```

## Explicit exclusions

The following pre-existing user work is outside this publication: the modified
`docs/architecture/AQR-0001-ARCHITECTURE-QUALIFICATION-REPORT.md`; untracked
AQR/HF-002 evidence; prior OA-01 evidence and reassessments; OA roadmap
directories HF-001 through HF-004; and all other untracked working-tree paths.
No excluded path is staged, committed, synchronized, or represented by this
publication.

## Scope assertion

The boundary contains only the qualified removal of Progressive PMCT and
authority gating from Operational Alpha dispatcher decisions, its controlled
documentation/EMM reconciliation, regression coverage, and publication
evidence. It contains no lifecycle transition, Authority Record, Operational
Gate Plan, activation, mission execution, or foundational architecture.
