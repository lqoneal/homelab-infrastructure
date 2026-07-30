# ZH Publication Transaction Lifecycle 001 — Change Matrix

Date: 2026-07-29
Handoff: `ZH-PUBLICATION-TRANSACTION-LIFECYCLE-001`
Scope: Framework architecture enhancement; no publication execution

## Controlled-Document Revisions

| Path | Baseline | Candidate | Owning responsibility | Architectural effect |
| --- | --- | --- | --- | --- |
| `docs/specifications/SPEC-0001-CONTROLLED_DOCUMENT_MODEL.md` | Version 1.6 | Version 1.7 | Controlled-document representation | Represents a transaction as immutable inputs, append-only outputs, exclusions, persistence results, and a final manifest |
| `docs/procedures/PROC-0001-ENGINEERING_WORK_ORDER_EXECUTION_PROCEDURE.md` | Version 1.18 | Version 1.19 | Work execution and report production | Routes generated publication-control artifacts to the active output ledger or a post-finalization successor |
| `docs/procedures/PROC-0005-CONTROLLED_DOCUMENT_PUBLICATION_PROCEDURE.md` | Version 1.6 | Version 1.7 | Publication lifecycle and transaction ownership | Defines the governing transaction model, artifact taxonomy, output ledger, output freezes, finalization, and compatibility adoption |
| `docs/procedures/PROC-0006-GOVERNANCE-QUALIFICATION-PROCEDURE.md` | Version 1.4 | Version 1.5 | Independent qualification | Routes qualification reports and finding matrices to PROC-0005 without recursive publication invocation |

## Current Transaction Output Ledger

These entries are outputs of the still-open corrective publication transaction.
They do not modify Publication Plan 002's frozen input/provenance baseline.

| Path | Lifecycle classification | Origin | Owner | Destination boundary | Digest state |
| --- | --- | --- | --- | --- | --- |
| `docs/specifications/SPEC-0001-CONTROLLED_DOCUMENT_MODEL.md` | Publication content | ZH-PUBLICATION-TRANSACTION-LIFECYCLE-001 | Controlled-document owner | PU-01B transaction output boundary | Open; freeze before persistence |
| `docs/procedures/PROC-0001-ENGINEERING_WORK_ORDER_EXECUTION_PROCEDURE.md` | Publication content | ZH-PUBLICATION-TRANSACTION-LIFECYCLE-001 | Engineering Governance | PU-01B transaction output boundary; supersedes unpersisted seed bytes | Open; freeze before persistence |
| `docs/procedures/PROC-0005-CONTROLLED_DOCUMENT_PUBLICATION_PROCEDURE.md` | Publication content | ZH-PUBLICATION-TRANSACTION-LIFECYCLE-001 | Engineering Governance | PU-01B transaction output boundary; supersedes unpersisted seed bytes | Open; freeze before persistence |
| `docs/procedures/PROC-0006-GOVERNANCE-QUALIFICATION-PROCEDURE.md` | Publication content | ZH-PUBLICATION-TRANSACTION-LIFECYCLE-001 | Engineering Governance | PU-01B transaction output boundary; supersedes unpersisted seed bytes | Open; freeze before persistence |
| `engineering/evidence/2026-07-29-zh-publication-transaction-lifecycle-001.md` | Reconciliation evidence | ZH-PUBLICATION-TRANSACTION-LIFECYCLE-001 | Publication framework evidence owner | PU-01B transaction output boundary | Open; freeze before persistence |
| `engineering/evidence/2026-07-29-zh-publication-transaction-lifecycle-001-change-matrix.md` | Reconciliation evidence | ZH-PUBLICATION-TRANSACTION-LIFECYCLE-001 | Publication framework evidence owner | PU-01B transaction output boundary | Open; freeze before persistence |

## Artifact-Class Disposition

| Class | Current examples | Transaction role | Publication responsibility |
| --- | --- | --- | --- |
| Publication content | Controlled documents, implementation, planned OA evidence, project state | Input, or explicitly authorized corrective output | Assigned input unit or declared output boundary |
| Execution evidence | `2026-07-29-zh-publication-execution-003.md` | Intrinsic output | Active transaction |
| Recovery evidence | `2026-07-29-zh-publication-recovery-execution-001.md`, publication-resume stop evidence | Intrinsic output | Active transaction before finalization; successor after finalization |
| Qualification evidence | Qualification-policy report and change matrix | Intrinsic output | Active transaction |
| Reconciliation evidence | Working-tree, plan, inventory, and lifecycle reconciliation reports/matrices | Intrinsic output | Active transaction |
| Transaction metadata | Reconciled manifests, boundary records, locator ledger, final manifest | Intrinsic output | Active transaction |
| Planning artifact | Publication Plans 001 and 002 | Frozen input when initiating; governed output when revised during correction | Input boundary or active output ledger according to production event |
| Generated artifact | Deterministic validator or projection output | Conditional output | Include only when the initiating output schema requires it |
| Operational state | Project State, Work Registry, EOS projection/runtime state | Explicit operational input/effect | Assigned unit or separately authorized synchronization boundary |
| Non-publication artifact | Temporary files, caches, secrets, local diagnostics | Excluded | Never publish |

Every listed artifact has exactly one lifecycle classification. Transaction
role is a separate property and does not create a second classification.

## Reviewed Without Revision

| Record | Disposition |
| --- | --- |
| STD-0001 | Existing lifecycle and transition authority remains unchanged |
| STD-0002 | Existing persistence, locator, and historical reconstruction requirements support immutable input/output boundaries |
| STD-0004 | Repository/EOS authority and synchronization drift rules remain unchanged |
| EOS-0003 | Operational persistence remains outside automatic transaction-output collection |
| `engineering/operations/repository-eos-synchronization.md` | Synchronization remains a separately authorized boundary |
| Publication Plan 002 and its manifest | Preserved as legacy input/provenance baseline; not regenerated or executed |
| PU-01 and PU-01A | Immutable and unchanged |

No staging, commit, synchronization, push, plan execution, publication-unit
execution, or history operation is part of this change matrix.
