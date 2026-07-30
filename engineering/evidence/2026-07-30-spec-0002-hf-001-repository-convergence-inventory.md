# SPEC-0002 HF-001 Repository Convergence Inventory

Date: 2026-07-30

Repository: `/data/engineering/repositories/homelab`

Remote: `git@github.com:lqoneal/homelab-infrastructure.git`

Branch: `main`

HEAD: `d0861dc62b8199de03230152c4ed3cfb687dd9a7`

Upstream: `origin/main`, ahead 2, behind 0

Repository determination: `NOT CONVERGED`

This inventory is an observational direct non-EWO record. It uses
`git status --porcelain=v1 --untracked-files=all` so every untracked file is
listed rather than collapsed to a directory. It performs no cleanup, deletion,
rename, staging, commit, publication, synchronization, reconciliation, or
promotion.

## Status legend and cardinality

| Porcelain state | Meaning | Count |
|---|---|---:|
| staged | index differs from HEAD | 0 |
| modified | tracked path has `M` in index or worktree state | 37 |
| deleted | tracked path has `D` in index or worktree state | 0 |
| renamed/copied | tracked path has `R` or `C` | 0 |
| other tracked conflict/type state | tracked state outside M/D/R/C | 0 |
| untracked | file-level `??` artifact | 398 |
| total deviations | each listed path once | 435 |

No path is classified as objectively obsolete or safely deletable from status
alone. “Duplicate candidate,” “superseded-name,” “generated,” “temporary,”
“historical,” and “archival” classifications require the retention and
consumer evidence stated below before any destructive disposition.

## Classification rules

Each group supplies one content class, current convergence state, risk, owner
route, and required disposition for every exact path in its list. A path name
may make an artifact a candidate for a class; only its information owner can
confirm final disposition. The inventory therefore fails closed instead of
using filename, recency, or location as authority.

## G01 — Current architecture reconciliation deliverables

- **Content class:** Controlled architecture/evidence candidate
- **Convergence state:** Current direct-review deliverable; Pending persistence
- **Risk:** May be mixed with unrelated tree changes if not isolated
- **Owner route:** Controlled-document and evidence owners
- **Required disposition:** Retain; bind exact candidate manifest; validate; do not stage or publish without separate authority
- **Path count:** 10

| Status | Exact repository path |
|---|---|
| `??` | `docs/architecture/AQR-0001-ARCHITECTURE-QUALIFICATION-REPORT.md` |
| ` M` | `docs/DOC-0001-REPOSITORY_DOCUMENT_INDEX.md` |
| `??` | `docs/specifications/SPEC-0002-ZEUS-CANONICAL-ARCHITECTURE-SPECIFICATION.md` |
| `??` | `engineering/evidence/2026-07-30-spec-0002-hf-001-architecture-qualification-matrix.md` |
| `??` | `engineering/evidence/2026-07-30-spec-0002-hf-001-architecture-readiness-report.md` |
| `??` | `engineering/evidence/2026-07-30-spec-0002-hf-001-change-summary.md` |
| `??` | `engineering/evidence/2026-07-30-spec-0002-hf-001-prioritized-repository-convergence-backlog.md` |
| `??` | `engineering/evidence/2026-07-30-spec-0002-hf-001-repository-convergence-inventory.md` |
| `??` | `engineering/evidence/2026-07-30-spec-0002-hf-001-repository-convergence-qualification-matrix.md` |
| `??` | `engineering/evidence/2026-07-30-spec-0002-hf-001-validation.md` |

## G02 — Protected architecture inputs

- **Content class:** Controlled architecture input
- **Convergence state:** Pre-existing untracked Draft input; content protected
- **Risk:** Mutable/unpersisted despite qualification use
- **Owner route:** ARCH/ADR controlled-document owners
- **Required disposition:** Retain exact bytes; preserve digests; include only in the later exact architecture candidate
- **Path count:** 2

| Status | Exact repository path |
|---|---|
| `??` | `docs/architecture/ADR-0001-ZEUS-CANONICAL-ARCHITECTURE-DECISION.md` |
| `??` | `docs/architecture/ARCH-0001-ENGINEERING-CONVERGENCE-ASSESSMENT.md` |

## G03 — Historical archive

- **Content class:** Archival/historical evidence
- **Convergence state:** Immutable preservation candidate
- **Risk:** Loss or editorial change would break provenance
- **Owner route:** Historical evidence/archive owner
- **Required disposition:** Retain byte-for-byte; verify hashes; never treat as current authority or delete by duplication inference
- **Path count:** 8

| Status | Exact repository path |
|---|---|
| `??` | `engineering/archive/Engineering_Convergence_Review_Original/artifacts/Architecture_Convergence_Report.md` |
| `??` | `engineering/archive/Engineering_Convergence_Review_Original/artifacts/Capability_Inventory.md` |
| `??` | `engineering/archive/Engineering_Convergence_Review_Original/artifacts/Duplicate_Capability_Report.md` |
| `??` | `engineering/archive/Engineering_Convergence_Review_Original/artifacts/Engineering_Convergence_Review.md` |
| `??` | `engineering/archive/Engineering_Convergence_Review_Original/artifacts/Operational_Alpha_Rebaseline.md` |
| `??` | `engineering/archive/Engineering_Convergence_Review_Original/MANIFEST.md` |
| `??` | `engineering/archive/Engineering_Convergence_Review_Original/PROVENANCE.md` |
| `??` | `engineering/archive/Engineering_Convergence_Review_Original/SHA256SUMS` |

## G04 — Explicit superseded-name artifacts

- **Content class:** Superseded historical/Runtime evidence candidate
- **Convergence state:** Preservation required pending owner verification
- **Risk:** Filename indicates supersession but not safe deletion
- **Owner route:** Producing Runtime/WOP evidence owner
- **Required disposition:** Retain; verify successor lineage and consumers; classify inclusion/exclusion without deletion
- **Path count:** 1

| Status | Exact repository path |
|---|---|
| `??` | `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/decisions/OA-04/superseded-by-contract-correction.json` |

## G05 — Engineering reviews and redesign assessments

- **Content class:** Review/reference evidence; duplicate-location candidate where archived copies exist
- **Convergence state:** Untracked assessment cohort requiring provenance grouping
- **Risk:** Source review and archive copies may be confused or published together
- **Owner route:** Review/evidence owner
- **Required disposition:** Retain; identify source versus archive/reference role; hash and group before persistence
- **Path count:** 14

| Status | Exact repository path |
|---|---|
| `??` | `engineering/reviews/Architecture_Convergence_Report.md` |
| `??` | `engineering/reviews/Capability_Inventory.md` |
| `??` | `engineering/reviews/Duplicate_Capability_Report.md` |
| `??` | `engineering/reviews/Engineering_Convergence_Review.md` |
| `??` | `engineering/reviews/Governance_Architecture_Simplification_Initiative/01-GOVERNANCE-ARCHITECTURE-ASSESSMENT.md` |
| `??` | `engineering/reviews/Governance_Architecture_Simplification_Initiative/02-BOOTSTRAP-AND-CIRCULAR-AUTHORITY-ROOT-CAUSE.md` |
| `??` | `engineering/reviews/Governance_Architecture_Simplification_Initiative/03-PROPOSED-GOVERNANCE-ARCHITECTURE.md` |
| `??` | `engineering/reviews/Governance_Architecture_Simplification_Initiative/04-LIFECYCLE-AND-AUTHORITY-MODEL.md` |
| `??` | `engineering/reviews/Governance_Architecture_Simplification_Initiative/05-MIGRATION-STRATEGY-AND-IMPLEMENTATION-ROADMAP.md` |
| `??` | `engineering/reviews/Governance_Architecture_Simplification_Initiative/06-RISK-AND-CONTROLLED-DOCUMENT-IMPACT.md` |
| `??` | `engineering/reviews/Governance_Architecture_Simplification_Initiative/COMPLETION-REPORT.md` |
| `??` | `engineering/reviews/Governance_Architecture_Simplification_Initiative/README.md` |
| `??` | `engineering/reviews/Governance_Architecture_Simplification_Initiative/SHA256SUMS` |
| `??` | `engineering/reviews/Operational_Alpha_Rebaseline.md` |

## G06 — Other central engineering evidence

- **Content class:** Evidence candidate
- **Convergence state:** Untracked multi-subject evidence cohort
- **Risk:** Orphan, duplicate, stale, or unrelated evidence may enter a candidate
- **Owner route:** Each evidence producer and subject owner
- **Required disposition:** Retain; bind producer, subject, provenance, digest, retention, and candidate membership
- **Path count:** 62

| Status | Exact repository path |
|---|---|
| `??` | `engineering/evidence/2026-07-28-zeus-operational-alpha-stage1-completion-report.md` |
| `??` | `engineering/evidence/2026-07-29-oa04-approval-replay-lifecycle-correction.md` |
| `??` | `engineering/evidence/2026-07-29-zh-authority-infrastructure-reconciliation-001.md` |
| `??` | `engineering/evidence/2026-07-29-zh-authorization-bundle-contract-001.md` |
| `??` | `engineering/evidence/2026-07-29-zh-controlled-working-tree-baseline-001.md` |
| `??` | `engineering/evidence/2026-07-29-zh-oa01-implementation-003.md` |
| `??` | `engineering/evidence/2026-07-29-zh-oa01-qualification-002.md` |
| `??` | `engineering/evidence/2026-07-29-zh-oa03-mission-contract-discovery-001-completion-report.md` |
| `??` | `engineering/evidence/2026-07-29-zh-oa04-acceptance-replay-corrective-001.md` |
| `??` | `engineering/evidence/2026-07-29-zh-oa04-contract-conformance-review-001.md` |
| `??` | `engineering/evidence/2026-07-29-zh-oa04-mission-resolution-001-completion-report.md` |
| `??` | `engineering/evidence/2026-07-29-zh-oa05-contract-conformance-review-001.md` |
| `??` | `engineering/evidence/2026-07-29-zh-oa05-mission-count-investigation-001.md` |
| `??` | `engineering/evidence/2026-07-29-zh-oa05-mission-staging-001-completion-report.md` |
| `??` | `engineering/evidence/2026-07-29-zh-publication-execution-003.md` |
| `??` | `engineering/evidence/2026-07-29-zh-publication-inventory-reconciliation-001-change-matrix.md` |
| `??` | `engineering/evidence/2026-07-29-zh-publication-inventory-reconciliation-001.md` |
| `??` | `engineering/evidence/2026-07-29-zh-publication-plan-002-manifest.json` |
| `??` | `engineering/evidence/2026-07-29-zh-publication-plan-002.json` |
| `??` | `engineering/evidence/2026-07-29-zh-publication-recovery-execution-001.md` |
| `??` | `engineering/evidence/2026-07-29-zh-publication-transaction-lifecycle-001-change-matrix.md` |
| `??` | `engineering/evidence/2026-07-29-zh-publication-transaction-lifecycle-001.md` |
| `??` | `engineering/evidence/2026-07-29-zh-qualification-policy-correction-001-change-matrix.md` |
| `??` | `engineering/evidence/2026-07-29-zh-qualification-policy-correction-001.md` |
| `??` | `engineering/evidence/2026-07-29-zh-working-tree-reconciliation-001-inventory.json` |
| `??` | `engineering/evidence/2026-07-29-zh-working-tree-reconciliation-001.md` |
| `??` | `engineering/evidence/2026-07-29-zh-zeus-controlled-document-architecture-001.md` |
| `??` | `engineering/evidence/2026-07-29-zh-zeus-oa-admission-001-work-initiation.md` |
| `??` | `engineering/evidence/2026-07-30-adr-0001-hf-001-architecture-traceability-matrix.md` |
| `??` | `engineering/evidence/2026-07-30-adr-0001-hf-001-change-summary.md` |
| `??` | `engineering/evidence/2026-07-30-adr-0001-hf-001-decision-request-resolution-matrix.md` |
| `??` | `engineering/evidence/2026-07-30-adr-0001-hf-001-validation.md` |
| `??` | `engineering/evidence/2026-07-30-aqr-0001-hf-001-architecture-qualification-matrix.md` |
| `??` | `engineering/evidence/2026-07-30-aqr-0001-hf-001-architecture-readiness-report.md` |
| `??` | `engineering/evidence/2026-07-30-aqr-0001-hf-001-change-summary.md` |
| `??` | `engineering/evidence/2026-07-30-aqr-0001-hf-001-prioritized-reconciliation-backlog.md` |
| `??` | `engineering/evidence/2026-07-30-aqr-0001-hf-001-validation.md` |
| `??` | `engineering/evidence/2026-07-30-arch-0001-hf-001-change-summary.md` |
| `??` | `engineering/evidence/2026-07-30-arch-0001-hf-001-validation.md` |
| `??` | `engineering/evidence/2026-07-30-arch-0001-hf-002-change-summary.md` |
| `??` | `engineering/evidence/2026-07-30-arch-0001-hf-002-validation.md` |
| `??` | `engineering/evidence/2026-07-30-arch-0001-review-001-completion-report.md` |
| `??` | `engineering/evidence/2026-07-30-arch-0001-review-001-reconciliation.md` |
| `??` | `engineering/evidence/2026-07-30-arch-0001-review-001-review-matrix.md` |
| `??` | `engineering/evidence/2026-07-30-arch-0001-review-001-validation.md` |
| `??` | `engineering/evidence/2026-07-30-arch-0001-revision-001-completion-report.md` |
| `??` | `engineering/evidence/2026-07-30-arch-0001-revision-001-reconciliation.md` |
| `??` | `engineering/evidence/2026-07-30-arch-0001-revision-001-validation.md` |
| `??` | `engineering/evidence/2026-07-30-architecture-documentation-suite-001-completion-report.md` |
| `??` | `engineering/evidence/2026-07-30-architecture-documentation-suite-001-reconciliation.md` |
| `??` | `engineering/evidence/2026-07-30-architecture-documentation-suite-001-validation.md` |
| `??` | `engineering/evidence/2026-07-30-architecture-refinement-operational-alpha-readiness-completion-report.md` |
| `??` | `engineering/evidence/2026-07-30-architecture-refinement-operational-alpha-readiness-reconciliation.md` |
| `??` | `engineering/evidence/2026-07-30-architecture-refinement-operational-alpha-readiness-review-summary.md` |
| `??` | `engineering/evidence/2026-07-30-architecture-refinement-operational-alpha-readiness-validation.md` |
| `??` | `engineering/evidence/2026-07-30-architecture-review-incorporation-completion-report.md` |
| `??` | `engineering/evidence/2026-07-30-governance-architecture-simplification-initiative-validation.md` |
| `??` | `engineering/evidence/2026-07-30-zeus-architecture-baseline-mission-contract-completion-report.md` |
| `??` | `engineering/evidence/2026-07-30-zeus-architecture-baseline-mission-contract-lifecycle-reconciliation.md` |
| `??` | `engineering/evidence/2026-07-30-zeus-architecture-baseline-mission-contract-validation.md` |
| `??` | `engineering/evidence/2026-07-30-zeus-architecture-baseline-mission-establishment-completion-report.md` |
| `??` | `engineering/evidence/2026-07-30-zeus-architecture-baseline-mission-establishment-reconciliation.md` |

## G07 — Generated architecture metadata

- **Content class:** Generated/reference artifact
- **Convergence state:** Untracked generated candidate
- **Risk:** May be stale, duplicate source facts, or lack a reproducible generator boundary
- **Owner route:** Architecture metadata generator/source owner
- **Required disposition:** Verify generator, inputs, digest, consumers, and publication/ignore treatment; do not infer source authority
- **Path count:** 8

| Status | Exact repository path |
|---|---|
| `??` | `engineering/architecture/progressive-runtime-capabilities.json` |
| `??` | `engineering/architecture/progressive-runtime-classification.json` |
| `??` | `engineering/architecture/progressive-runtime-consumers.json` |
| `??` | `engineering/architecture/progressive-runtime-execution-contracts.json` |
| `??` | `engineering/architecture/progressive-runtime-outcomes.json` |
| `??` | `engineering/architecture/progressive-runtime-policies.json` |
| `??` | `engineering/architecture/progressive-runtime-states.json` |
| `??` | `engineering/architecture/progressive-runtime-transitions.json` |

## G08 — Other controlled/supporting documentation and planning

- **Content class:** Controlled/supporting documentation or planning candidate
- **Convergence state:** Pre-existing modified/untracked cohort outside current architecture scope
- **Risk:** Revision, lifecycle, registration, or semantic dependencies may be mixed
- **Owner route:** Named document/planning information owners
- **Required disposition:** Partition by controlled revision; validate lineage/registration/relationships; exclude unless explicitly in candidate
- **Path count:** 14

| Status | Exact repository path |
|---|---|
| ` M` | `docs/procedures/PROC-0001-ENGINEERING_WORK_ORDER_EXECUTION_PROCEDURE.md` |
| ` M` | `docs/procedures/PROC-0005-CONTROLLED_DOCUMENT_PUBLICATION_PROCEDURE.md` |
| ` M` | `docs/procedures/PROC-0006-GOVERNANCE-QUALIFICATION-PROCEDURE.md` |
| ` M` | `docs/project/PROJ-0001-PROJECT_STATE.md` |
| ` M` | `docs/specifications/SPEC-0001-CONTROLLED_DOCUMENT_MODEL.md` |
| ` M` | `docs/specifications/SPEC-0012-PRODUCTION-EXECUTION-FOUNDATION.md` |
| `??` | `engineering/docs/architecture/authorization-bundle-contract.md` |
| `??` | `engineering/docs/architecture/ZEUS-CONTROLLED-DOCUMENTATION-ARCHITECTURE.md` |
| `??` | `engineering/docs/architecture/ZEUS-STAGE1-RUNTIME.md` |
| ` M` | `engineering/docs/cli/ZEUS-USER-GUIDE.md` |
| `??` | `engineering/planning/ZH-AUTHORITY-PIPELINE-INTEGRATION-PLANNING-001/01-authority-pipeline-specification.md` |
| `??` | `engineering/planning/ZH-AUTHORITY-PIPELINE-INTEGRATION-PLANNING-001/02-repository-consolidation-plan.md` |
| `??` | `engineering/planning/ZH-AUTHORITY-PIPELINE-INTEGRATION-PLANNING-001/03-integration-roadmap-and-verification.md` |
| `??` | `engineering/planning/ZH-AUTHORITY-PIPELINE-INTEGRATION-PLANNING-001/04-completion-report.md` |

## G09 — Registry, mission-authority, execution-projection, and state candidates

- **Content class:** Registry/state/authority/projection candidate
- **Convergence state:** Concurrent source/projection cohort; not reconciled
- **Risk:** Duplicate authority, reverse synchronization, or state drift if newest/path is selected
- **Owner route:** Project, EMP, Governance, mission, execution, or projection owner named by each record
- **Required disposition:** Compare declared owners; classify source versus projection; record authorized direction; do not reconcile here
- **Path count:** 7

| Status | Exact repository path |
|---|---|
| `??` | `engineering/authorization/authorization-bundle.schema.yaml` |
| `??` | `engineering/execution/controlled-working-tree-baseline.json` |
| `??` | `engineering/execution/missions/GH-ZEUS-OA-PROGRESSIVE-001.yaml` |
| `??` | `engineering/mission-contracts/contracts/MC-ZEUS-ARCHITECTURE-BASELINE-COMPLETION-001.yaml` |
| `??` | `engineering/mission-contracts/requests/ACTIVATE-ZEUS-ARCHITECTURE-BASELINE-COMPLETION-001.yaml` |
| ` M` | `engineering/registry/work-registry.yaml` |
| ` M` | `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/state.json` |

## G10 — Runtime decision and evidence artifacts

- **Content class:** Runtime-generated decision/evidence
- **Convergence state:** Untracked WOP-local Runtime cohort
- **Risk:** Attempt duplicates, superseded results, mutable evidence, or accidental publication
- **Owner route:** Progressive Runtime decision/evidence owners
- **Required disposition:** Preserve; bind attempt and subject lineage; verify seals/retention; classify publication exclusion/inclusion explicitly
- **Path count:** 48

| Status | Exact repository path |
|---|---|
| `??` | `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/decisions/OA-01/accepted.json` |
| `??` | `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/decisions/OA-02/accepted.json` |
| `??` | `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/decisions/OA-03/accepted.json` |
| `??` | `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/decisions/OA-04/accepted-59cbfe3e60b09f1483fe165276f3b247577ccc83bcd084ea212fa78689f972c0.json` |
| `??` | `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/decisions/OA-04/accepted.json` |
| `??` | `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/decisions/OA-05/accepted-31c196a0ef998f1e9cc59988eac81eaa015d134bf1a1ee1a9d15cb401d274be9.json` |
| `??` | `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/evidence/OA-01/attempts/0c721f239604ca12d5d59af0db2c857b097b8cbdec44c045f36058d790b13c91/VERIFICATION.json` |
| `??` | `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/evidence/OA-01/attempts/0c721f239604ca12d5d59af0db2c857b097b8cbdec44c045f36058d790b13c91/VERIFIED` |
| `??` | `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/evidence/OA-01/attempts/a337b7ade99bb67790d51e0bc09a07777ae06096454540af005adb99dfa4024d/VERIFICATION.json` |
| `??` | `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/evidence/OA-01/attempts/a337b7ade99bb67790d51e0bc09a07777ae06096454540af005adb99dfa4024d/VERIFIED` |
| `??` | `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/evidence/OA-01/IMPLEMENTATION.json` |
| `??` | `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/evidence/OA-01/VERIFICATION.json` |
| `??` | `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/evidence/OA-01/VERIFIED` |
| `??` | `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/evidence/OA-01/ZH-OA01-VERIFICATION-CORRECTIVE-004-COMPLETION.md` |
| `??` | `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/evidence/OA-02/attempts/2fe7fb97fab8e62a70167a71048cf35de1080fc11b9a6a44f43d5cbcaa9ac92d/IMPLEMENTATION.json` |
| `??` | `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/evidence/OA-02/attempts/af955eb13c8a91130651c74ca91f6e8cbd6a44ca814926c0ca2f06d1856f5f7d/VERIFICATION.json` |
| `??` | `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/evidence/OA-02/attempts/af955eb13c8a91130651c74ca91f6e8cbd6a44ca814926c0ca2f06d1856f5f7d/VERIFIED` |
| `??` | `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/evidence/OA-02/IMPLEMENTATION.json` |
| `??` | `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/evidence/OA-02/VERIFICATION.json` |
| `??` | `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/evidence/OA-02/VERIFIED` |
| `??` | `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/evidence/OA-02/ZH-OA02-CONTROLLED-MISSION-AUTHORITY-001-COMPLETION.md` |
| `??` | `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/evidence/OA-03/attempts/d87249a0cc7e04fa895a696a801da5bfe41b04e3b08b04c844ded6890db7237a/VERIFICATION.json` |
| `??` | `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/evidence/OA-03/attempts/d87249a0cc7e04fa895a696a801da5bfe41b04e3b08b04c844ded6890db7237a/VERIFIED` |
| `??` | `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/evidence/OA-03/IMPLEMENTATION.json` |
| `??` | `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/evidence/OA-03/VERIFICATION.json` |
| `??` | `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/evidence/OA-03/VERIFIED` |
| `??` | `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/evidence/OA-04/attempts/0b538ce2262bf9a7a33a88e47ebd12b48becfc0a675701fb72e96a5679225e55/VERIFICATION.json` |
| `??` | `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/evidence/OA-04/attempts/0b538ce2262bf9a7a33a88e47ebd12b48becfc0a675701fb72e96a5679225e55/VERIFIED` |
| `??` | `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/evidence/OA-04/attempts/1734b9295a029c9ecddb6440cd86d1faf7aee7af1d2269d33180876e0a188b87/VERIFICATION.json` |
| `??` | `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/evidence/OA-04/attempts/1734b9295a029c9ecddb6440cd86d1faf7aee7af1d2269d33180876e0a188b87/VERIFIED` |
| `??` | `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/evidence/OA-04/attempts/23cc5af0c6b56b31f1fb92108cac3150fb4d58578f1f148d8e534b9c2335565a/VERIFICATION.json` |
| `??` | `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/evidence/OA-04/attempts/23cc5af0c6b56b31f1fb92108cac3150fb4d58578f1f148d8e534b9c2335565a/VERIFIED` |
| `??` | `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/evidence/OA-04/attempts/37cd9ee4f0e0e9a4d91d3289d2a4694ef5da9474dc979293673e9aa68353d7c0/VERIFICATION.json` |
| `??` | `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/evidence/OA-04/attempts/37cd9ee4f0e0e9a4d91d3289d2a4694ef5da9474dc979293673e9aa68353d7c0/VERIFIED` |
| `??` | `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/evidence/OA-04/attempts/8996960699a4970b2fda196eecc043ddcda1608ffd3321ee90531cc5c55091e3/VERIFICATION.json` |
| `??` | `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/evidence/OA-04/attempts/8996960699a4970b2fda196eecc043ddcda1608ffd3321ee90531cc5c55091e3/VERIFIED` |
| `??` | `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/evidence/OA-04/attempts/95d3457565ff128521e19305444a1e80613598c9a9f51a715eb4ed9d81f03c6f/IMPLEMENTATION.json` |
| `??` | `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/evidence/OA-04/attempts/cdbf93a74bc687fa622dbea84b011f37d5b0879d95523c7f5c473663cf92deee/IMPLEMENTATION.json` |
| `??` | `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/evidence/OA-04/attempts/dbbab47a902ee5c431bfd824ef1ead1a9d423e377f3443b258a80724314e97d3/VERIFICATION.json` |
| `??` | `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/evidence/OA-04/attempts/dbbab47a902ee5c431bfd824ef1ead1a9d423e377f3443b258a80724314e97d3/VERIFIED` |
| `??` | `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/evidence/OA-04/IMPLEMENTATION.json` |
| `??` | `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/evidence/OA-04/VERIFICATION.json` |
| `??` | `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/evidence/OA-04/VERIFIED` |
| `??` | `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/evidence/OA-05/attempts/1c96738d313cb6f3759be8f3c62e44da199bc85cd3b1aec61918964ad639fa62/VERIFICATION.json` |
| `??` | `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/evidence/OA-05/attempts/1c96738d313cb6f3759be8f3c62e44da199bc85cd3b1aec61918964ad639fa62/VERIFIED` |
| `??` | `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/evidence/OA-05/IMPLEMENTATION.json` |
| `??` | `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/evidence/OA-05/VERIFICATION.json` |
| `??` | `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/evidence/OA-05/VERIFIED` |

## G11 — WOP packages and package-local records

- **Content class:** WOP/package/evidence candidate
- **Convergence state:** Mixed tracked/untracked package cohort outside current action
- **Risk:** Manifest drift, stale package state, unrelated publication content, or implied execution authority
- **Owner route:** Each WOP/package owner
- **Required disposition:** Retain; verify manifest, package identity, state/evidence owner, historical role, and candidate boundary separately
- **Path count:** 172

| Status | Exact repository path |
|---|---|
| ` M` | `engineering/work-orders/GH-ZEUS-OA-CERTIFICATION-001/BOOTSTRAP.md` |
| ` M` | `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/gates/OA-05/implementation.md` |
| ` M` | `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/gates/OA-05/verification.md` |
| ` M` | `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/MANIFEST.sha256` |
| `??` | `engineering/work-orders/ZEUS-ARCHITECTURE-BASELINE-COMPLETION-001/immutable-wop.yaml` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/BOOTSTRAP.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/COMPLETION-REPORT-TEMPLATE.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/dead-and-transitional-consumer-elimination-plan.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/external-wop-inventory.json` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/gate-a-inventory-report.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/PU-01C/AUTHORITY-VERIFICATION-BOUNDARY-FREEZE/authority-reconciliation-report.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/PU-01C/AUTHORITY-VERIFICATION-BOUNDARY-FREEZE/boundary-verification-report.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/PU-01C/AUTHORITY-VERIFICATION-BOUNDARY-FREEZE/completion-report.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/PU-01C/AUTHORITY-VERIFICATION-BOUNDARY-FREEZE/determinism-report.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/PU-01C/AUTHORITY-VERIFICATION-BOUNDARY-FREEZE/pu-01c-boundary-manifest.json` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/PU-01C/AUTHORITY-VERIFICATION-BOUNDARY-FREEZE/state-authority-report.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/PU-01C/completion-report.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/PU-01C/controlled-documentation-reconciliation-report.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/PU-01C/cross-reference-validation-report.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/PU-01C/GOVERNANCE-BASELINE-INDEPENDENCE/boundary-verification-report.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/PU-01C/GOVERNANCE-BASELINE-INDEPENDENCE/completion-report.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/PU-01C/GOVERNANCE-BASELINE-INDEPENDENCE/determinism-report.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/PU-01C/GOVERNANCE-BASELINE-INDEPENDENCE/governance-independence-assessment.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/PU-01C/GOVERNANCE-BASELINE-INDEPENDENCE/qualification-dependency-report.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/PU-01C/GOVERNANCE-BASELINE-INDEPENDENCE/qualification-refactoring-report.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/PU-01C/GOVERNANCE-BASELINE-INDEPENDENCE/updated-qualification-evidence.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/PU-01C/GOVERNANCE-BASELINE-INDEPENDENCE/updated-qualification-fingerprint.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/PU-01C/PUBLICATION-CONTRACT-RECONCILIATION/completion-report.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/PU-01C/PUBLICATION-CONTRACT-RECONCILIATION/lifecycle-reconciliation-report.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/PU-01C/PUBLICATION-CONTRACT-RECONCILIATION/publication-contract-reconciliation-report.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/PU-01C/PUBLICATION-CONTRACT-RECONCILIATION/publication-inventory-reconciliation-report.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/PU-01C/PUBLICATION-CONTRACT-RECONCILIATION/publication-readiness-report.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/PU-01C/PUBLICATION-CONTRACT-RECONCILIATION/qualification-lineage-reconciliation-report.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/PU-01C/PUBLICATION-CONTRACT-RECONCILIATION/runtime-preservation-report.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/PU-01C/PUBLICATION-CONTRACT-RECONCILIATION/semantic-validation-assessment.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/PU-01C/publication-dependency-report.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/PU-01C/publication-inventory-reconciliation-report.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/PU-01C/PUBLICATION/publication-completion-report.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/PU-01C/PUBLICATION/publication-metadata-report.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/PU-01C/PUBLICATION/publication-reproducibility-report.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/PU-01C/PUBLICATION/publication-verification-report.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/PU-01C/PUBLICATION/runtime-preservation-report.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/PU-01C/runtime-publication-boundary-freeze-blocker-report.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/T01/consumer-and-dependency-assessment.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/T01/primitive-interface-specification.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/T01/qualification-and-regression-report.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/T01/t01-implementation-completion-report.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/T02/completion-report.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/T02/consumer-impact-assessment.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/T02/decision-service-specification.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/T02/qualification-report.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/T02/regression-report.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/T02/t02-implementation-report.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/T03/appr-controlled-document-revision.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/T03/architecture-delta-report.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/T03/completion-report.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/T03/consumer-impact-assessment.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/T03/lifecycle-projection-specification.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/T03/qualification-report.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/T03/regression-report.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/T03/t03-implementation-report.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/T04/completion-report.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/T04/consumer-impact-assessment.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/T04/controlled-document-revision.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/T04/qualification-report.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/T04/regression-report.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/T04/runtime-consumer-migration-report.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/T04/runtime-layer-architecture-update.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/T04/t04-implementation-report.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/T05/completion-report.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/T05/consumer-impact-assessment.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/T05/controlled-document-revision.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/T05/qualification-report.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/T05/regression-report.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/T05/runtime-dependency-analysis.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/T05/runtime-dependency-validation-report.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/T05/t05-implementation-report.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/T06/completion-report.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/T06/consumer-impact-assessment.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/T06/controlled-document-revision.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/T06/qualification-report.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/T06/regression-report.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/T06/runtime-classification-report.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/T06/runtime-extension-analysis.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/T06/t06-implementation-report.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/T07/completion-report.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/T07/consumer-impact-assessment.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/T07/controlled-document-revision.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/T07/qualification-report.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/T07/regression-report.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/T07/runtime-registration-analysis.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/T07/runtime-registration-validation-report.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/T07/t07-implementation-report.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/T08/completion-report.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/T08/consumer-impact-assessment.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/T08/controlled-document-revision.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/T08/qualification-report.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/T08/regression-report.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/T08/runtime-capability-analysis.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/T08/runtime-capability-validation-report.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/T08/t08-implementation-report.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/T09/completion-report.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/T09/consumer-impact-assessment.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/T09/controlled-document-revision.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/T09/qualification-report.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/T09/regression-report.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/T09/runtime-policy-analysis.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/T09/runtime-policy-validation-report.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/T09/t09-implementation-report.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/T10/completion-report.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/T10/consumer-impact-assessment.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/T10/controlled-document-revision.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/T10/qualification-report.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/T10/regression-report.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/T10/runtime-state-analysis.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/T10/runtime-state-validation-report.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/T10/t10-implementation-report.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/T11/completion-report.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/T11/consumer-impact-assessment.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/T11/controlled-document-revision.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/T11/qualification-report.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/T11/regression-report.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/T11/runtime-transition-analysis.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/T11/runtime-transition-validation-report.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/T11/t11-implementation-report.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/T12/completion-report.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/T12/consumer-impact-assessment.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/T12/controlled-document-revision.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/T12/qualification-report.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/T12/regression-report.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/T12/runtime-execution-contract-analysis.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/T12/runtime-execution-contract-validation-report.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/T12/t12-implementation-report.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/T13/completion-report.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/T13/consumer-impact-assessment.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/T13/controlled-document-revision.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/T13/qualification-report.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/T13/regression-report.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/T13/runtime-outcome-analysis.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/T13/runtime-outcome-validation-report.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/T13/t13-implementation-report.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/T15/completion-report.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/T15/controlled-document-reconciliation-report.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/T15/cross-registry-validation-report.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/T15/progressive-runtime-consolidation-report.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/T15/qualification-report.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/T15/regression-report.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/T15/runtime-boundary-verification-report.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/T15/runtime-determinism-report.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/T15/runtime-traceability-report.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/T15/technical-debt-assessment.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/test-fixture-isolation-review-unit-1.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/GATE-A/unique-record-classification.json` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EVIDENCE/README.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/EXECUTION-ORDER.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/GATES/A.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/GATES/B.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/GATES/C.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/GATES/D.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/GATES/E.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/GATES/F.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/GATES/G.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/MANIFEST.yaml` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/MISSION-CONTRACT.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/PATCHES/README.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/RECONCILIATION.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/RECOVERY.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/ROLLBACK/README.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/SCRIPTS/verify-package` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/SECOND-WINDOW-VERIFICATION.md` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/STATE.json` |
| `??` | `engineering/work-orders/ZH-AUTHORITY-PIPELINE-RESOLUTION-WOP-001/TESTS/README.md` |

## G12 — Test and qualification-support candidates

- **Content class:** Test/verification candidate
- **Convergence state:** Pre-existing tracked/untracked implementation-support cohort
- **Risk:** Tests may target mixed architecture generations or lack implementation grouping
- **Owner route:** Owning implementation/test subsystem
- **Required disposition:** Group with exact implementation subject and qualification evidence; exclude from architecture-only candidate unless declared
- **Path count:** 39

| Status | Exact repository path |
|---|---|
| ` M` | `engineering/tests/zeus-operational-alpha/PMCT-CAPABILITY-MATRIX.yaml` |
| ` M` | `engineering/tests/zeus-operational-alpha/PMCT-CONTRACT.md` |
| `??` | `engineering/tests/zeus-operational-alpha/tests/test_discovery.py` |
| ` M` | `engineering/tests/zeus-operational-alpha/tests/test-result-model.py` |
| ` M` | `engineering/tests/zeus-operational-alpha/tests/test-state-protection.py` |
| `??` | `scripts/tests/test_discovery.py` |
| `??` | `scripts/tests/test-authority-pipeline-repository.py` |
| `??` | `scripts/tests/test-authorization-bundle.py` |
| ` M` | `scripts/tests/test-emp-registry.py` |
| `??` | `scripts/tests/test-external-wop-inventory.py` |
| `??` | `scripts/tests/test-progressive-gate-primitives.py` |
| `??` | `scripts/tests/test-progressive-lifecycle-projection.py` |
| `??` | `scripts/tests/test-progressive-runtime-capabilities.py` |
| `??` | `scripts/tests/test-progressive-runtime-consolidation.py` |
| `??` | `scripts/tests/test-progressive-runtime-consumer-migration.py` |
| `??` | `scripts/tests/test-progressive-runtime-dependencies.py` |
| `??` | `scripts/tests/test-progressive-runtime-execution-contracts.py` |
| `??` | `scripts/tests/test-progressive-runtime-implementation-synchronization.py` |
| `??` | `scripts/tests/test-progressive-runtime-outcomes.py` |
| `??` | `scripts/tests/test-progressive-runtime-policies.py` |
| `??` | `scripts/tests/test-progressive-runtime-registration.py` |
| `??` | `scripts/tests/test-progressive-runtime-states.py` |
| `??` | `scripts/tests/test-progressive-runtime-transitions.py` |
| `??` | `scripts/tests/test-working-tree-baseline.py` |
| ` M` | `scripts/tests/test-zeus-gate-approval.py` |
| ` M` | `scripts/tests/test-zeus-mission-assurance.py` |
| `??` | `scripts/tests/test-zeus-mission-count-status.py` |
| ` M` | `scripts/tests/test-zeus-next-action.py` |
| `??` | `scripts/tests/test-zeus-oa01-implementation.py` |
| `??` | `scripts/tests/test-zeus-oa01-verification.py` |
| `??` | `scripts/tests/test-zeus-oa02-controlled-authority.py` |
| ` M` | `scripts/tests/test-zeus-oa02-lifecycle.py` |
| `??` | `scripts/tests/test-zeus-oa03-mission-contract-discovery.py` |
| `??` | `scripts/tests/test-zeus-oa04-context-reconstruction.py` |
| `??` | `scripts/tests/test-zeus-oa04-mission-resolution.py` |
| `??` | `scripts/tests/test-zeus-oa05-mission-staging.py` |
| `??` | `scripts/tests/test-zeus-oa06-mission-eligibility.py` |
| ` M` | `scripts/tests/test-zeus-progressive-oa.py` |
| `??` | `scripts/tests/test-zeus-stage1-runtime.py` |

## G13 — Runtime, service, CLI, and operational implementation candidates

- **Content class:** Implementation/runtime candidate
- **Convergence state:** Pre-existing modified/untracked cohort; untouched by this documentation work
- **Risk:** Unrelated behavior change, mixed implementation generations, or unqualified production reachability
- **Owner route:** Owning EMP/Zeus/EOS/EENS/operations subsystem
- **Required disposition:** Preserve; split into bounded implementation candidates; validate independently; exclude from documentation candidate
- **Path count:** 50

| Status | Exact repository path |
|---|---|
| ` M` | `engineering/execution/execution-interface.yaml` |
| ` M` | `engineering/operations/authority-ownership-specification.md` |
| ` M` | `engineering/operations/zeus-mission-admission-runtime.md` |
| ` M` | `engineering/operations/zeus-mission-execution-runtime.md` |
| `??` | `engineering/operations/zeus-oa01-mission-verification.md` |
| ` M` | `engineering/operations/zeus-operational-alpha-progress.md` |
| ` M` | `engineering/operations/zeus-operational-runtime.md` |
| ` M` | `engineering/operations/zeus-operator-interface.md` |
| `??` | `scripts/authority-pipeline-preflight` |
| `??` | `scripts/inventory-external-wop` |
| `??` | `scripts/lib/authority_pipeline/__init__.py` |
| `??` | `scripts/lib/authority_pipeline/external_wop_inventory.py` |
| `??` | `scripts/lib/authority_pipeline/progressive_runtime_capabilities.py` |
| `??` | `scripts/lib/authority_pipeline/progressive_runtime_consolidation.py` |
| `??` | `scripts/lib/authority_pipeline/progressive_runtime_dependencies.py` |
| `??` | `scripts/lib/authority_pipeline/progressive_runtime_execution_contracts.py` |
| `??` | `scripts/lib/authority_pipeline/progressive_runtime_outcomes.py` |
| `??` | `scripts/lib/authority_pipeline/progressive_runtime_policies.py` |
| `??` | `scripts/lib/authority_pipeline/progressive_runtime_registration.py` |
| `??` | `scripts/lib/authority_pipeline/progressive_runtime_states.py` |
| `??` | `scripts/lib/authority_pipeline/progressive_runtime_transitions.py` |
| `??` | `scripts/lib/authority_pipeline/repository.py` |
| `??` | `scripts/lib/emp/controlled_mission_authority.py` |
| `??` | `scripts/lib/emp/mission_contract_discovery.py` |
| `??` | `scripts/lib/emp/mission_eligibility.py` |
| `??` | `scripts/lib/emp/mission_resolution.py` |
| `??` | `scripts/lib/emp/oa01_gate_verification.py` |
| `??` | `scripts/lib/emp/oa01_implementation.py` |
| `??` | `scripts/lib/emp/oa01_verification.py` |
| `??` | `scripts/lib/emp/oa02_gate_verification.py` |
| `??` | `scripts/lib/emp/oa02_implementation.py` |
| ` M` | `scripts/lib/emp/oa02_lifecycle.py` |
| `??` | `scripts/lib/emp/oa03_gate_verification.py` |
| `??` | `scripts/lib/emp/oa03_implementation.py` |
| `??` | `scripts/lib/emp/oa04_gate_verification.py` |
| `??` | `scripts/lib/emp/oa04_implementation.py` |
| `??` | `scripts/lib/emp/oa05_gate_verification.py` |
| `??` | `scripts/lib/emp/oa05_implementation.py` |
| `??` | `scripts/lib/emp/progressive_gate.py` |
| `??` | `scripts/lib/emp/progressive_lifecycle.py` |
| ` M` | `scripts/lib/emp/progressive_oa.py` |
| `??` | `scripts/lib/emp/progressive_runtime_support.py` |
| `??` | `scripts/lib/emp/project_operational_context.py` |
| `??` | `scripts/lib/emp/stage1_runtime.py` |
| ` M` | `scripts/lib/eos/platform.sh` |
| `??` | `scripts/lib/eos/working_tree_baseline.py` |
| `??` | `scripts/lib/work_initiation/authorization_bundle.py` |
| ` M` | `scripts/verify.sh` |
| ` M` | `scripts/zeus` |
| ` M` | `services/eens/README.md` |

## Completeness and safety determination

- Every observed tracked and untracked file-level deviation appears exactly
  once in one classification group.
- Staged, deletion, rename/copy, and other tracked-state counts are reported
  explicitly even when zero.
- Historical/archive and superseded-name artifacts are preservation
  candidates, not deletion candidates.
- Review/source copies and generated metadata are duplicate-location or
  derived-data candidates only; consumer and provenance review must precede
  consolidation.
- Runtime decision/evidence records are retained pending seal, attempt,
  successor, and publication-treatment verification.
- Unknown or owner-ambiguous disposition fails closed.
- The working tree remains `NOT CONVERGED`; this inventory is the input to a
  later separately authorized convergence action, not evidence that
  convergence occurred.

