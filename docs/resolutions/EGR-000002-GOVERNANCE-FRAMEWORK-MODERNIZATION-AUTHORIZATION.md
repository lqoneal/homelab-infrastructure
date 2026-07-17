---
document_id: EGR-000002
title: Governance Framework Modernization Authorization
version: 1.0
status: Active
owner: Engineering Governance
created: 2026-07-17
last_updated: 2026-07-17
phase: Governance Framework Modernization
domain: Engineering Governance
classification: Engineering Governance Resolution
predecessor_revision: null
successor_revision: null
approval_status: Approved
approval_authority: Engineering Governance
approval_reference: EGR-000002
approval_date: 2026-07-17
persistence_status: Pending
source_of_truth: true
declared_deferrals: []
relationships:
  - type: governed_by
    target: CHAR-0001
  - type: governed_by
    target: POL-0001
  - type: conforms_to
    target: STD-0000
  - type: conforms_to
    target: STD-0001
  - type: conforms_to
    target: STD-0002
  - type: conforms_to
    target: SPEC-0001
  - type: indexed_by
    target: DOC-0001
  - type: authorizes
    target: EWO-000018
  - type: related_to
    target: EWO-000017
tags:
  - governance
  - engineering-governance-resolution
  - governance-modernization
  - work-initiation
  - completion-report
---

# Engineering Governance Resolution

## Engineering Governance Resolution Header

EGR Identifier: `EGR-000002`

Title: Governance Framework Modernization Authorization

Revision: 1.0

Lifecycle State: Active

Owner: Engineering Governance

Decision Date: 2026-07-17

Approving Governance Authority: Engineering Governance

## Purpose

Record Engineering Governance approval for a bounded, holistic modernization
of Engineering Work Initiation and Codex completion-report governance, and
authorize EWO-000018 as the implementation contract.

## Decision Subject

Subject Type: Governance proposal

Subject Identifier: `GOVERNANCE-FRAMEWORK-MODERNIZATION-2026-07-17`

Subject Revision: 1

Governance Question:

Whether Engineering Governance should authorize risk-proportional mission
classification before initiation gates, mandatory Governance Conformance
Review in Codex completion reports, and complete reconciliation of the affected
governance subsystem.

Current State:

PROC-0001 applies repository-oriented baseline gates before classifying work.
STD-0003 and TPL-0002 do not require the specified Governance Conformance
Review. EWO-000017 has an authorized, uncommitted working tree and added five
valid Work Registry objects without updating a hard-coded regression count.

## Governing Authority

Superior Governance: CHAR-0001 and POL-0001.

Preparation Authority: Engineering Governance directive, Governance
Authorization & Framework Modernization, dated 2026-07-17, acting through the
superior-governance preparation path in PROC-0002.

Decision Authority: Engineering Governance.

Authority Boundary:

This Resolution may approve the defined modernization, activate EWO-000018,
and approve a bounded dirty-tree exception for unrelated EWO-000017 work. It
does not itself revise the governance framework, complete EWO-000017, send a
notification, authorize Stage 2 or Stage 3 notification work, push, or modify
the Charter.

## Evidence Considered

| Evidence or Record | Identifier and Revision | Relevance | Validation State |
| --- | --- | --- | --- |
| Engineering Charter | CHAR-0001 1.0 | Superior authority and bootstrap boundary | Reviewed |
| Governance Policy | POL-0001 1.0 | Governance Stabilization and change control | Reviewed |
| Authority Model | EDR-0002 1.1 Draft | Authority-chain design context | Reviewed as Draft, not operational authority |
| Work Order Standard | STD-0003 1.1 | EWO and Completion Report requirements | Reviewed |
| Execution Procedure | PROC-0001 1.5 | Current Work Initiation and mission lifecycle | Reviewed |
| Completion Report Template | TPL-0002 1.0 | Current report architecture | Reviewed |
| Repository Index | DOC-0001 2.20 working revision | Initiation and discovery | Reviewed |
| Notification integration | EWO-000017 1.0 | Existing working-tree authority | Reviewed |
| Platform validation | 2026-07-17 | Registry regression evidence | Reproduced |

Evidence Sufficiency Assessment:

The authority chain, current controlled publications, deterministic registry
delta, and working-tree inventory are sufficient to approve bounded future
implementation without performing that implementation in this mission.

## Affected Records and Revisions

| Controlled Record | Exact Revision | Current State | Decision Effect |
| --- | --- | --- | --- |
| CHAR-0001 | 1.0 | Active | Superior authority; unchanged |
| POL-0001 | 1.0 | Active | Superior policy; unchanged |
| EDR-0002 | 1.1 | Draft | Design context; no lifecycle change |
| STD-0000 | 1.4 | Active | Reconcile documentation architecture if references require it |
| STD-0001 | 1.3 | Active | Reconcile lifecycle requirements if directly affected |
| STD-0003 | 1.1 | Active | Revise Completion Report requirements |
| STD-0004 | 1.0 | Active | Reconcile freshness and initiation interaction |
| SPEC-0001 | 1.4 | Active | Reconcile controlled-record relationships if required |
| SPEC-0005 | 1.0 | Active | Reconcile governance controls if required |
| PROC-0001 | 1.5 | Active | Add Mission Classification Gate and proportional initiation |
| PROC-0002 | 1.0 | Active | Reconcile governance-review workflow if required |
| DOC-0001 | 2.20 | Active working revision | Reconcile index and Work Initiation ritual |
| TPL-0001 | 1.1 | Active | Reconcile EWO mission-classification requirements |
| TPL-0002 | 1.0 | Active | Add mandatory Governance Conformance Review |
| EWO-000017 | 1.0 | Active, uncommitted implementation | Preserve and checkpoint; no scope expansion |
| EWO-000018 | 1.0 | Active upon this decision | Authorized implementation contract |

## Engineering Governance Disposition

Disposition: **Accepted**

Disposition Statement:

Engineering Governance approves the complete modernization scope recorded in
this Resolution and authorizes EWO-000018 to implement and validate it as one
holistically reconciled governance subsystem.

Decision Scope:

The authorized system improvements are: Mission Classification Gate;
Category A, B, and C classifications; risk-proportional initiation gates;
mandatory Governance Conformance Review; holistic governance reconciliation;
governance architecture validation; future-mission verification;
repository-governed completion reports and mission classifications;
Governance Gap documentation; Authority Circumvention reporting; no silent
governance correction; whole-document revision; and whole-subsystem
reconciliation.

Decision Rationale:

Repository cleanliness is a material integrity gate for repository work but is
not inherently a blocker for local-only or read-only work. Classification before
gating preserves authority while preventing unrelated repository state from
blocking safe missions. Mandatory conformance review makes authority and scope
assessment explicit at completion.

Authority Not Granted:

No Charter amendment, unrelated policy redesign, EWO-000017 completion, live
notification test, Stage 2 or Stage 3 implementation, daemon deployment,
history rewrite, push, or silent correction is authorized.

## Authorized Governance Effects

Governance Changes:

- EWO-000018 may revise every directly affected controlled document needed to
  keep the complete governance subsystem internally consistent.
- Future Codex missions shall derive classification and completion-report
  behavior from the resulting repository governance rather than handoff text.
- Governance improvements affect systems, not isolated documents; unless the
  approving authority explicitly limits scope, the complete affected subsystem
  shall be reconciled in one mission.

Lifecycle Transitions:

- Approve and activate EGR-000002 Version 1.0.
- Approve and activate EWO-000018 Version 1.0.

Baseline Effects:

The current Governance Foundation remains operational until EWO-000018 is
implemented, validated, committed, and accepted. Approval does not prematurely
place proposed revisions into the active baseline.

Approval-Reference Effects:

EWO-000018 and its directly authorized planning records may cite EGR-000002.

Implementation Preconditions:

- Re-run Work Initiation under the then-current active baseline.
- Preserve and inventory the EWO-000017 working tree.
- Use isolated staging and prove that the governance commit contains no
  EWO-000017 implementation paths except an explicitly reconciled shared record.
- Complete whole-document and whole-subsystem validation before reporting
  completion.

## EWO-000017 Disposition and Repository Exception

EWO-000017 remains Active and is checkpointed at its current incomplete
acceptance boundary. Its five registry additions are valid; the regression was
a stale hard-coded test expectation. Live acceptance remains separately gated.

For EWO-000018 only, the identified EWO-000017 working tree is an approved
repository-cleanliness exception. The dirty tree shall be recorded, shall not
be treated as governance implementation, and shall not be included in the
governance publication commit. Any overlap in DOC-0001, PROJ-0001, INF-0001,
or the Work Registry shall be reconciled deliberately with both authorities
preserved.

## Required Follow-up

| Required Action | Governing Authority | Responsible Role | Completion Evidence |
| --- | --- | --- | --- |
| Implement holistic governance reconciliation | EGR-000002 and EWO-000018 | Codex implementation agent | Validated controlled revisions |
| Create isolated documentation-only commit | EWO-000018 | Codex implementation agent | Commit classification and staged-path evidence |
| Preserve and later complete EWO-000017 acceptance | EWO-000017 | Separately authorized agent | Controlled acceptance evidence |
| Review and accept modernization outcome | Engineering Governance | Engineering Governance | Completion Report and governance review |

Deferred Work: EWO-000017 live acceptance and all notification Stage 2/3 work.

## Relationships and Traceability

Supporting Engineering Work Order: EWO-000017.

Engineering Governance Proposal: Governance Authorization & Framework
Modernization directive dated 2026-07-17.

Affected Controlled Revisions: Listed in **Affected Records and Revisions**.

Related Resolution: EGR-000001.

Authoritative Index: DOC-0001.

## Lifecycle Decision

EGR Content Approval: Approved

Approved By: Engineering Governance

Approval Reference: EGR-000002

Approval Date: 2026-07-17

Activation Decision: Authorized

Activation Authority: Engineering Governance

Activation Date: 2026-07-17

Persistence State: Pending until committed by an authorized publication mission.

Index State: Registered by the current DOC-0001 working revision.

## Supersedence and Historical Effect

Predecessor EGR: None.

Successor EGR: None.

Superseded Scope: None.

Historical Effect:

This Resolution does not retroactively alter prior mission gates or completion
reports. It records the present decision and authorizes prospective controlled
revision through EWO-000018.

## Validation Record

Identity, authority, lifecycle, relationship, index, dependency, scope, and
whole-document validation are required before publication. EWO-000018 owns
validation of the implemented governance subsystem.

## Revision History

| Version | Date | Description |
| --- | --- | --- |
| 1.0 | 2026-07-17 | Approved governance-framework modernization, activated EWO-000018, and established the bounded EWO-000017 repository exception. |
