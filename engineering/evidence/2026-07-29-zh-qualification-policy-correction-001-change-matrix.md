# ZH Qualification Policy Correction 001 — Change Matrix

Date: 2026-07-29
Handoff: `ZH-QUALIFICATION-POLICY-CORRECTION-001`
Scope: Procedure correction only

| Path | Baseline | Revision | Policy effect | Cross-reference disposition |
| --- | --- | --- | --- | --- |
| `docs/procedures/PROC-0001-ENGINEERING_WORK_ORDER_EXECUTION_PROCEDURE.md` | Version 1.17 | Version 1.18 candidate | Preserves raw validator exit status and separately records any classification explicitly governed by the owning procedure | Continues to route controlled publication to PROC-0005 and Governance qualification to PROC-0006 |
| `docs/procedures/PROC-0005-CONTROLLED_DOCUMENT_PUBLICATION_PROCEDURE.md` | Version 1.5 | Version 1.6 candidate | Establishes the single authoritative diff and whitespace qualification policy for controlled publication | Owns publication classification; retains SPEC-0001 Markdown-integrity and PROC-0001/PROC-0006 relationships |
| `docs/procedures/PROC-0006-GOVERNANCE-QUALIFICATION-PROCEDURE.md` | Version 1.3 represented in revision history; header was 1.2 | Version 1.4 candidate | Separates raw tool status from qualification result and requires PROC-0005 classification when publication qualification consumes `git diff --check` | Removes competing interpretation by explicitly delegating publication whitespace classification to PROC-0005 |
| `engineering/evidence/2026-07-29-zh-qualification-policy-correction-001.md` | New | Evidence | Records analysis, decision, consistency review, and recovery impact | References PROC-0001, PROC-0005, PROC-0006, SPEC-0001, PU-01A, and ZH-PUBLICATION-EXECUTION-003 |
| `engineering/evidence/2026-07-29-zh-qualification-policy-correction-001-change-matrix.md` | New | Evidence | Records the exact correction boundary | Self-identifies this bounded procedure-correction set |

## Reviewed Without Revision

| Record | Review result |
| --- | --- |
| `docs/specifications/SPEC-0001-CONTROLLED_DOCUMENT_MODEL.md` | Already establishes Markdown with YAML front matter as the repository representation and requires Markdown integrity; it does not assign terminal-whitespace interpretation and needs no change |
| `docs/standards/STD-0001-ENGINEERING_DOCUMENT_LIFECYCLE_STANDARD.md` | Lifecycle authority is unaffected |
| `docs/standards/STD-0002-ENGINEERING_DOCUMENT_PERSISTENCE_STANDARD.md` | Persistence and integrity requirements are unaffected |
| `docs/standards/STD-0003-ENGINEERING_WORK_ORDER_STANDARD.md` | Reporting requirements are unaffected |
| `docs/standards/STD-0004-ENGINEERING_STATE_FRESHNESS_STANDARD.md` | State freshness and EOS drift classification are unaffected |
| `docs/procedures/PROC-0007-GOVERNANCE-STABILIZATION-PROCEDURE.md` | Consumes qualification and publication results without defining whitespace semantics; no competing rule exists |
| `docs/DOC-0001-REPOSITORY_DOCUMENT_INDEX.md` | Paths, titles, lifecycle states, and relationship registrations remain correct; the index does not carry these procedure version values |
| `engineering/evidence/2026-07-29-zh-publication-plan-001.md` and `.json` | Frozen publication plan remains unchanged |
| `engineering/evidence/2026-07-29-zh-publication-plan-reconciliation-001-manifest.json` | Frozen publication membership and digests remain unchanged |
| `engineering/evidence/2026-07-29-zh-publication-execution-003.md` | Preserved as truthful incident evidence; not rewritten |

No implementation, test, generated artifact, publication-unit assignment,
staging state, commit, EOS projection, or remote state is included in this
change matrix.
