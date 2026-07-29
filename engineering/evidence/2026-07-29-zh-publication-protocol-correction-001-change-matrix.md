# ZH Publication Protocol Correction 001 — Change Matrix

Date: 2026-07-29  
Scope: Documentation and workflow correction only  
Publication status: Paused after successful PU-01

| Affected document | Modified sections | Rationale | Downstream implementation impact |
| --- | --- | --- | --- |
| `docs/procedures/PROC-0005-CONTROLLED_DOCUMENT_PUBLICATION_PROCEDURE.md` | Metadata and relationships; terms; repository–EOS contract; drift classifications; Stage 6; evidence; validation checklist; success criteria; revision history | Make the common publication procedure the explicit owner of publication/synchronization boundary declaration and validation sequencing. | Future publication handoffs must name four boundaries, classify every EOS comparison, and establish separate synchronization authority. |
| `docs/procedures/PROC-0001-ENGINEERING_WORK_ORDER_EXECUTION_PROCEDURE.md` | Metadata; Category A Work Initiation; revision history | Prevent initiation/qualification from treating expected intermediate drift as a failure or silently repairing it. | Publication initiation must use read-only EOS comparison and resolve PROC-0005 before execution. |
| `docs/standards/STD-0004-ENGINEERING_STATE_FRESHNESS_STANDARD.md` | Metadata; reconciliation scope; policy statement; revision history | Reconcile freshness requirements with an authorized publication sequence whose EOS projection intentionally lags until a declared boundary. | Freshness tooling and operators must distinguish expected publication drift from stale authoritative state. |
| `docs/eos/EOS-0003-OPERATIONAL_PERSISTENCE_PROFILE.md` | Metadata; Repository–EOS Synchronization; revision history | State that repository publication and EOS synchronization are distinct and define projection semantics. | EOS tooling remains one-way; invocations require explicit authority and post-checks. |
| `engineering/operations/repository-eos-synchronization.md` | Authority; projection semantics; boundaries; classifications; synchronization contract; integrated qualification; authority/prerequisites | Provide the executable Engineering Platform synchronization procedure referenced by controlled documents. | Operators gain deterministic prerequisites, stop conditions, classifications, and post-synchronization checks. |
| `engineering/evidence/2026-07-29-zh-publication-plan-001.md` | Disposition; validation requirements | Correct the active plan after PU-01 and prohibit successor execution under the old embedded synchronization behavior. | PU-02 and later require a new execution handoff referencing corrected PROC-0005; synchronization remains after PU-08 and separately authorized. |
| `docs/DOC-0001-REPOSITORY_DOCUMENT_INDEX.md` | Metadata; revision history | Reconcile indexed controlled-document revisions. | Discovery identifies the coordinated protocol revision set. |
| `engineering/evidence/2026-07-29-zh-publication-protocol-correction-001.md` | New evidence report | Preserve initiation, evidence, contract, changes, validation, risks, and recommendation. | Becomes the review record for approval of a later publication execution handoff. |

No code, repository runtime, EOS state, Project State, registry state, gate
state, or Operational Alpha state is modified by this matrix.
