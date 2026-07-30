# REPO-CONVERGENCE-HF-001 Repository Disposition Matrix

Date: 2026-07-30

Source inventory:
`engineering/evidence/2026-07-30-spec-0002-hf-001-repository-convergence-inventory.md`

Source inventory SHA-256:
`d99d313b57eec008024dd9764116711e7d642f6c8f502985a19da9c3889b41ff`

## Disposition semantics

Each exact path listed under a source-inventory group inherits exactly the one
final disposition assigned to that group below. The source inventory proves
that the groups are non-overlapping and contain all 435 original deviations.
No path is assigned by a filename heuristic alone.

| Disposition | Meaning |
|---|---|
| `RETAIN` | Include unchanged or reconciled content in the local repository candidate as current, supporting, generated-reference, or non-authorizing candidate material. |
| `PRESERVE` | Include exact historical/protected bytes in the local repository candidate; do not reinterpret them as current authority or delete them. |

No original path has an `IGNORE`, `REMOVE`, or new `ARCHIVE` disposition. The
archive cohort was already in its intended archive location and therefore has
the single final disposition `PRESERVE`.

## Original deviation dispositions

| Group | Paths | Final disposition | Information role | Verification and justification |
|---|---:|---|---|---|
| G01 Current architecture reconciliation deliverables | 10 | `RETAIN` | current Draft documents and supporting qualification evidence | revisions and registration resolve; controlled validation passes; no lifecycle effect inferred |
| G02 Protected architecture inputs | 2 | `PRESERVE` | qualified ARCH/ADR inputs | exact SHA-256 values unchanged; content is protected |
| G03 Historical archive | 8 | `PRESERVE` | immutable historical evidence | `sha256sum -c SHA256SUMS` passes; manifest/provenance roles resolve |
| G04 Explicit superseded-name artifact | 1 | `PRESERVE` | historical Runtime decision lineage | live references exist in replay tests, successor evidence, state, and manifests |
| G05 Engineering reviews and redesign assessments | 14 | `RETAIN` | source/reference assessments | original source role remains distinct from immutable archive role; five source/archive byte comparisons pass |
| G06 Other central engineering evidence | 62 | `RETAIN` | attributable multi-subject engineering evidence | filenames, report headings, internal locators, and related WOP/subject records provide producer/subject routing; deletion has no retention authorization |
| G07 Generated architecture metadata | 8 | `RETAIN` | versioned generated reference data | all eight paths have named generator modules and qualification/test consumers |
| G08 Other controlled/supporting documentation and planning | 14 | `RETAIN` | controlled revisions and supporting plans | revision lineage and DOC-0001 relationships validate; planning records remain non-authorizing |
| G09 Registry, mission-authority, execution-projection, and state candidates | 7 | `RETAIN` | typed sources, candidates, and projections | active/candidate boundaries remain explicit; candidate architecture Mission Contract is not admitted or activated; no reverse synchronization performed |
| G10 Runtime decision and evidence artifacts | 48 | `PRESERVE` | append-only decision, attempt, and verification history | attempt/subject lineage and accepted/superseded relationships remain required by replay and recovery |
| G11 WOP packages and package-local records | 172 | `RETAIN` | executable/historical WOP and local evidence records | package placement, local manifests, and authority boundaries validate; historical records remain discoverable |
| G12 Tests and qualification support | 39 | `RETAIN` | executable verification and qualification support | repository verification exercises the cohort; no obsolete test was proven unreachable |
| G13 Runtime, service, CLI, and operational implementation | 50 | `RETAIN` | implementation and operational documentation | implementation/test cohort passes repository verification; no architecture content was changed by convergence |
| **Total** | **435** | **376 `RETAIN`; 59 `PRESERVE`** | complete original inventory | **zero duplicate assignments; zero orphan paths** |

## Intrinsic convergence output dispositions

These six outputs did not exist in the source AQR inventory. They are intrinsic
to this reconciliation and each has the single final disposition `RETAIN`.

| Exact path | Final disposition | Subject |
|---|---|---|
| `engineering/evidence/2026-07-30-repo-convergence-hf-001-repository-convergence-report.md` | `RETAIN` | overall convergence result |
| `engineering/evidence/2026-07-30-repo-convergence-hf-001-repository-disposition-matrix.md` | `RETAIN` | exact group-to-disposition mapping |
| `engineering/evidence/2026-07-30-repo-convergence-hf-001-final-repository-inventory.md` | `RETAIN` | final candidate inventory |
| `engineering/evidence/2026-07-30-repo-convergence-hf-001-repository-reconciliation-report.md` | `RETAIN` | owner, record, and cross-reference reconciliation |
| `engineering/evidence/2026-07-30-repo-convergence-hf-001-change-summary.md` | `RETAIN` | bounded change summary |
| `engineering/evidence/2026-07-30-repo-convergence-hf-001-validation.md` | `RETAIN` | validation and reconstruction evidence |

## Completeness proof

```text
original exact paths:              435
original group memberships:        435
duplicate original memberships:      0
orphan original paths:               0
intrinsic output paths:               6
candidate paths relative to start:  441
```

The final Git index/commit boundary is checked against this 441-path total
before local persistence. Any mismatch is a stop condition.

