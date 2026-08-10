# Controlled-Document Authority Decision

## Decision

Create and activate two narrowly scoped controlled authorities under the
explicit operator directive:

- `STD-0006@1.0` — Engineering Executable Roadmap Standard; and
- `PROC-0009@1.0` — Executable Roadmap Evaluation Procedure.

Both report `persistence_status: Pending` because commit and push are
prohibited.

## Rationale

STD-0003 and PROC-0001 own WOP authorization and execution. PROC-0006 owns
Governance qualification. SPEC-0007 describes a developing planning layer but
does not own roadmap construction quality. The existing semantic Roadmap
profile validates only planning structure. Revising one of those authorities
to own all-roadmap execution sufficiency would cross established document-class
and semantic boundaries.

STD-0006 is therefore the canonical normative owner of what an executable
roadmap shall contain. PROC-0009 is its subordinate repeatable method. Existing
Draft PROC-0008 reserves its own identifier, so PROC-0009 is the next
non-conflicting procedure ID. DOC-0001 Version 2.79 registers both.
