# PROC-0006 Controlled Publication Evidence

## Transaction

- Mission: Engineering Governance Qualification Procedure Approval and Controlled Publication
- Parent baseline: `621be66deb9b5356ef97510aa402d3a18e580b12`
- Governance decision: EGR-000005
- Publication owner: PROC-0005
- Date: 2026-07-18

## Frozen Atomic Boundary

1. `docs/resolutions/EGR-000005-PROC-0006-APPROVAL-AND-ACTIVATION.md`
2. `docs/procedures/PROC-0006-GOVERNANCE-QUALIFICATION-PROCEDURE.md`
3. `docs/procedures/PROC-0001-ENGINEERING_WORK_ORDER_EXECUTION_PROCEDURE.md`
4. `docs/procedures/PROC-0002-ENGINEERING_GOVERNANCE_RESOLUTION_PROCEDURE.md`
5. `docs/procedures/PROC-0004-ENGINEERING_HANDOFF_CONSTRUCTION_PROCEDURE.md`
6. `docs/procedures/PROC-0005-CONTROLLED_DOCUMENT_PUBLICATION_PROCEDURE.md`
7. `docs/DOC-0001-REPOSITORY_DOCUMENT_INDEX.md`
8. `engineering/evidence/2026-07-18-proc-0006-controlled-publication.md`

Pre-existing runtime and test work is unrelated and excluded. No standard,
template, EOS, ETP, historical record, or implementation path participates.

## Approval and Lifecycle

EGR-000005 records acceptance, approval, Draft-to-Active authorization,
publication authority, exact affected revisions, exclusions, and baseline
eligibility. PROC-0006 Version 1.0 changes no qualified procedural semantics.

## Reference Integration

- PROC-0001 consumes PROC-0006 when an EWO includes Governance qualification.
- PROC-0002 consumes qualification evidence without surrendering decision-recording ownership.
- PROC-0004 resolves PROC-0006 when a handoff requires Governance qualification.
- PROC-0005 may consume a bounded qualification profile while retaining publication ownership.
- DOC-0001 registers Active PROC-0006 and EGR-000005.

## Validation Requirements

- exact staged boundary equals the eight paths above;
- controlled-document validation passes;
- reference and relationship targets resolve;
- unrelated changes remain excluded;
- immutable commit and blob locators resolve;
- post-publication validation passes; and
- PROC-0006 is Active only when the transaction is persisted successfully.

The Completion Report records immutable object locators after the
self-containing transaction exists.
