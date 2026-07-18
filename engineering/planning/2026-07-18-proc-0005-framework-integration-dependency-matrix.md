# PROC-0005 Governance Framework Integration Dependency Matrix

Date: 2026-07-18

Authority: Handoff — Engineering Governance Publication Framework Integration

Status: Approved execution matrix for this mission

## Modification Matrix

| Document | Priority | Modification Classes | Depends On | Downstream Impact | Atomic Requirement |
| --- | --- | --- | --- | --- | --- |
| STD-0000 | Required | Normative ownership clarification; reference-only; metadata; relationship | Active PROC-0005; STD-0001; STD-0002 | All controlled document classes and Governance discovery | Publish with all Required revisions. |
| STD-0001 | Required by subsystem analysis | Normative boundary clarification; reference-only; metadata; relationship | STD-0000; PROC-0005; SPEC-0001; STD-0002 | Lifecycle-transition execution and review planning | Publish with STD-0000, STD-0002, and consumers. |
| STD-0002 | Required by subsystem analysis | Normative boundary clarification; reference-only; canonical metadata migration; relationship | STD-0000; STD-0001; SPEC-0001; PROC-0005 | Persistence, indexing, reconstruction, and publication evidence | Publish with lifecycle and operational consumers. |
| PROC-0001 | Required | Operational precedence; reference-only; metadata; relationship | Active EWO; STD-0001; STD-0002; PROC-0005 | All EWO-governed controlled publication missions | Publish with PROC-0004 and DOC-0001. |
| PROC-0002 | Required | Specialized-procedure preservation; operational reference; metadata; relationship | STD-0000; STD-0001; STD-0002; SPEC-0001; PROC-0005 | EGR preparation, disposition, activation, and publication | Publish with common procedure references. |
| PROC-0004 | Required | Handoff-resolution rule; responsibility mapping; reference-only; metadata; relationship | Authorization Kernel; PROC-0001; PROC-0005 | Future publication-capable EWOs and handoffs | Publish with PROC-0001 and DOC-0001. |
| DOC-0001 | Required | Work Initiation guidance; metadata; relationship/index revision | All six revised records and active PROC-0005 | Repository-wide deterministic discovery | Same atomic commit as every revised record. |
| STD-0003/TPL-0001 | Recommended, deferred | Future reference and structural guidance | Separate complete revision authority | Publication-specific EWO completeness | Not part of this transaction. |
| SPEC-0001 | Optional, excluded | None | Existing inverse-resolution semantics | No immediate impact | No revision. |
| SPEC-0008/ETP | Optional, excluded | None | Separate ETP authority | Future profile-based publication consumption | No revision. |

## Ownership Matrix

| Concern | Authoritative Owner | Integration Rule |
| --- | --- | --- |
| Governance authority | Engineering Governance under CHAR-0001 and POL-0001 | PROC-0005 never originates it. |
| Documentation architecture | STD-0000 | Names PROC-0005 as operational owner without transferring architecture. |
| Lifecycle requirements | STD-0001 | PROC-0005 executes already-authorized transitions. |
| Persistence requirements | STD-0002 | PROC-0005 executes boundary, persistence, and verification controls. |
| Representation | SPEC-0001 | No revision; metadata and relationship semantics remain authoritative. |
| EWO execution and commit planning | PROC-0001 | Continues to govern execution; publication missions additionally consume PROC-0005. |
| EGR-specific processing | PROC-0002 | Continues to govern EGR content and disposition. |
| Handoff construction | PROC-0004 | Resolves PROC-0005 only when controlled publication is anticipated. |
| Common publication execution | PROC-0005 | Owns the reusable six-stage publication workflow. |
| Repository discovery | DOC-0001 | Indexes and routes; creates no authority. |

## Validation Dependencies

1. Canonical YAML metadata parses for all seven controlled revisions.
2. Every new relationship target resolves and preserves meaningful direction.
3. STD-0001 and STD-0002 retain their complete normative requirements.
4. PROC-0001, PROC-0002, and PROC-0004 retain specialized ownership.
5. Generic publication mechanics resolve uniquely to PROC-0005.
6. DOC-0001 metadata, relationship, registration, and revision history agree.
7. Whole-subsystem terminology and authority searches find no competing owner.
8. Controlled-document, whitespace, and repository-integrity validation pass.
9. The staged path set equals the ten-path publication boundary exactly.
10. Post-publication validation and immutable locator verification pass.

## Deferred Opportunities

- Add publication-specific fields or references to STD-0003 and TPL-0001.
- Evaluate ETP-aware publication-procedure consumption under separate ETP
  semantic authority.
- Implement automation only under separate authority and qualification.
- Add stronger automated consumer-reference validation if future evidence
  demonstrates a maintainability need.
