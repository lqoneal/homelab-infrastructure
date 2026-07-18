# PROC-0005 Governance Framework Integration Inventory

Date: 2026-07-18

Authority: Handoff — Engineering Governance Publication Framework Integration

Status: Approved execution inventory for this mission

## Integration Decision

The integration set is limited to seven controlled records, two execution-plan
artifacts, and one publication-evidence record. STD-0001 and STD-0002 are
directly affected because active PROC-0005 implements their requirements and
future engineers must discover the operational procedure from both standards.
SPEC-0001 is not directly affected: its representation model is complete and
its inverse-relationship rules already resolve PROC-0005.

## Controlled Revision Set

| Document | Reason Affected | Publication-Related Area | Integration Treatment |
| --- | --- | --- | --- |
| STD-0000 | Owns documentation architecture and operational information-owner separation. | Repository-Governed Workflow Publications; relationships; references. | Identify PROC-0005 as the common operational publication owner without moving normative architecture. |
| STD-0001 | Owns lifecycle requirements implemented by PROC-0005. | Relationship to governing records; metadata relationships. | Reference PROC-0005 as the operational execution procedure; retain every lifecycle rule. |
| STD-0002 | Owns persistence requirements implemented by PROC-0005. | References; persistence execution boundary; metadata relationships. | Reference PROC-0005 for boundary, atomic persistence, and verification; retain every persistence rule. |
| PROC-0001 | Owns EWO execution and commit planning for publication missions. | References; commit/publication boundary; metadata relationships. | Require controlled-publication work to consume PROC-0005 while retaining PROC-0001 execution and commit ownership. |
| PROC-0002 | Owns EGR-specific construction, disposition, activation, and traceability. | Governing records; workflow; publication execution; metadata relationships. | Preserve class-specific steps and use PROC-0005 for common publication mechanics. |
| PROC-0004 | Owns handoff construction and authority-kernel mapping. | Responsibility matrix; scope resolution; references; metadata relationships. | Resolve and insert PROC-0005 whenever a constructed handoff anticipates controlled publication. |
| DOC-0001 | Owns deterministic index discovery and Work Initiation guidance. | Work Initiation; controlled-document registration; revision metadata. | Direct publication-capable missions to PROC-0005 while retaining PROC-0001 commit controls. |

## Excluded Controlled Records

| Record | Disposition | Rationale |
| --- | --- | --- |
| SPEC-0001 | Excluded | Representation requirements are unchanged; inverse relationships need not be duplicated. |
| STD-0003 and TPL-0001 | Deferred | Useful future handoff/template integration, but not required for the approved core framework refactoring. |
| SPEC-0008 and ETP profiles | Excluded | Profile membership or resolution changes would modify ETP semantics. |
| PROC-0005 | Excluded | The authoritative procedure is already qualified and shall not be redesigned or revised. |
| Historical EWOs, evidence, reports, milestones, and plans | Excluded | Historical integrity prohibits retrospective workflow substitution. |
| EOS, runtime, wrappers, tooling, and Work Registry | Excluded | Outside Governance-integration scope. |

## Publication Boundary

The atomic publication transaction shall contain exactly:

1. `docs/standards/STD-0000-ENGINEERING_GOVERNANCE_DOCUMENTATION_ARCHITECTURE.md`
2. `docs/standards/STD-0001-ENGINEERING_DOCUMENT_LIFECYCLE_STANDARD.md`
3. `docs/standards/STD-0002-ENGINEERING_DOCUMENT_PERSISTENCE_STANDARD.md`
4. `docs/procedures/PROC-0001-ENGINEERING_WORK_ORDER_EXECUTION_PROCEDURE.md`
5. `docs/procedures/PROC-0002-ENGINEERING_GOVERNANCE_RESOLUTION_PROCEDURE.md`
6. `docs/procedures/PROC-0004-ENGINEERING_HANDOFF_CONSTRUCTION_PROCEDURE.md`
7. `docs/DOC-0001-REPOSITORY_DOCUMENT_INDEX.md`
8. `engineering/planning/2026-07-18-proc-0005-framework-integration-inventory.md`
9. `engineering/planning/2026-07-18-proc-0005-framework-integration-dependency-matrix.md`
10. `engineering/evidence/2026-07-18-proc-0005-framework-integration-publication.md`

All pre-existing wrapper, runtime, test, and untracked qualifier changes are
excluded. No bulk staging is permitted.

## Success Boundary

The integration is complete when all seven controlled revisions reference the
same operational ownership model, validation passes, the exact ten-path set is
committed atomically, and unrelated changes remain outside the commit.
