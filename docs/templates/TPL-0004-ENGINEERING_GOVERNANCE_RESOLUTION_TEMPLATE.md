---
document_id: TPL-0004
title: Engineering Governance Resolution Template
version: 1.0
status: Active
owner: Engineering Governance
created: 2026-07-13
last_updated: 2026-07-13
phase: EGR Framework Implementation
domain: Engineering Governance
classification: Engineering Template
predecessor_revision: null
successor_revision: null
approval_status: Approved
approval_authority: Engineering Governance
approval_reference: EGR-000001
approval_date: 2026-07-13
persistence_status: Pending
source_of_truth: true
declared_deferrals: []
relationships:
  - type: governed_by
    target: CHAR-0001
  - type: governed_by
    target: POL-0001
  - type: governed_by
    target: STD-0000
  - type: conforms_to
    target: STD-0000
  - type: conforms_to
    target: STD-0001
  - type: conforms_to
    target: STD-0002
  - type: conforms_to
    target: SPEC-0001
  - type: conforms_to
    target: PROC-0002
  - type: indexed_by
    target: DOC-0001
tags:
  - governance
  - template
  - engineering-governance-resolution
  - controlled-decisions
  - lifecycle
  - engineering-operating-system
---

# Engineering Governance Resolution Template

## Template Use

Instantiate this template as one complete Engineering Governance Resolution in accordance with STD-0000 and PROC-0002.

All bracketed instructions in the instantiation form are intentional template variables. Replace every variable with verified controlled information before the EGR enters Review. Remove instructional text that does not form part of the completed Resolution.

This template provides reusable structure only. It does not establish Governance Authority, select a disposition, approve a Resolution, authorize a lifecycle transition, or authorize engineering execution.

---

## Instantiation Form

```yaml
---
document_id: "[permanent EGR identifier assigned through the authoritative index]"
title: "[approved descriptive Resolution title]"
version: 1.0
status: Draft
owner: Engineering Governance
created: "[YYYY-MM-DD]"
last_updated: "[YYYY-MM-DD]"
phase: "[applicable mission, phase, or governance activity]"
domain: Engineering Governance
classification: Engineering Governance Resolution
predecessor_revision: null
successor_revision: null
approval_status: Pending
approval_authority: null
approval_reference: null
approval_date: null
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
  # Add authorized_by, authorizes, validates, related_to, supersedes, and
  # other canonical relationships only when their SPEC-0001 meanings apply.
tags:
  - governance
  - engineering-governance-resolution
  - "[decision-domain tag]"
---
```

---

## Engineering Governance Resolution Header

EGR Identifier:

`[Permanent EGR identifier]`

Title:

`[Engineering Governance Resolution title]`

Revision:

`[Document version]`

Lifecycle State:

`[Draft | Review | Approved | Active | Superseded | Archived]`

Owner:

`Engineering Governance`

Decision Date:

`[YYYY-MM-DD or Pending while Draft/Review]`

Approving Governance Authority:

`[Engineering Governance authority or Pending while Draft/Review]`

---

## Purpose

`[State the governance decision this Resolution records and why an authoritative disposition is required.]`

---

## Decision Subject

Subject Type:

`[Engineering Governance Finding | governance proposal | completed engineering outcome | controlled document revision | lifecycle transition | baseline matter | other existing EGR-authorized subject]`

Subject Identifier:

`[Permanent controlled identifier]`

Subject Revision:

`[Exact version or not applicable with explanation]`

Governance Question:

`[State the exact question presented to Engineering Governance.]`

Current State:

`[Describe the verified pre-decision lifecycle, approval, persistence, implementation, and baseline state.]`

---

## Governing Authority

Superior Governance:

`[Identify CHAR-0001, POL-0001, and any narrower applicable controlled authority.]`

Preparation Authority:

`[Identify the controlled authority permitting preparation and review of this EGR.]`

Decision Authority:

`[Identify the Engineering Governance authority making the disposition.]`

Authority Boundary:

`[State what this Resolution may decide and what remains outside its scope.]`

---

## Evidence Considered

| Evidence or Record | Identifier and Revision | Relevance | Validation State |
| --- | --- | --- | --- |
| `[Evidence item]` | `[Controlled reference]` | `[Decision relevance]` | `[Verified state]` |

Evidence Sufficiency Assessment:

`[Explain why the cited evidence is sufficient for governance disposition or identify an explicit deferral.]`

---

## Affected Records and Revisions

| Controlled Record | Exact Revision | Current State | Decision Effect |
| --- | --- | --- | --- |
| `[Document identifier]` | `[Version]` | `[Verified state]` | `[Approval, transition, deferral, rejection, supersedence, baseline, or no direct effect]` |

No affected record or revision may be inferred from a general title or narrative reference.

---

## Engineering Governance Disposition

Disposition:

`[Accepted | Rejected | Deferred | Superseded]`

Disposition Statement:

`[Record the exact decision made by Engineering Governance.]`

Decision Scope:

`[Define the complete and bounded scope of the disposition.]`

Decision Rationale:

`[Record the evidence-based governance rationale.]`

Authority Not Granted:

`[Identify excluded, prohibited, or separately authorized actions.]`

The subject disposition above is distinct from this EGR publication's `approval_status`.

---

## Authorized Governance Effects

Governance Changes:

`[Identify authorized governance changes or state None.]`

Lifecycle Transitions:

`[Identify each affected document revision, source state, destination state, authority, and effective condition or state None.]`

Baseline Effects:

`[Identify inclusion, exclusion, qualification, or deferral effects or state None.]`

Approval-Reference Effects:

`[Identify records authorized to cite this EGR as approval_reference or state None.]`

Implementation Preconditions:

`[Identify required authorization, validation, persistence, indexing, or dependency conditions.]`

This EGR does not itself perform controlled-document edits, repository operations, runtime changes, or other engineering execution.

---

## Required Follow-up

| Required Action | Governing Authority Required | Responsible Role | Completion Evidence |
| --- | --- | --- | --- |
| `[Follow-up action]` | `[Active EWO or superior controlled authority]` | `[Responsible role]` | `[Required evidence]` |

Deferred Work:

`[List explicit deferrals with authority and conditions or state None.]`

---

## Relationships and Traceability

Governing Engineering Work Order:

`[EWO identifier and revision, or not applicable with reason]`

Applicable Completion Report:

`[Controlled reference, or not applicable with reason]`

Applicable Evidence Package:

`[Controlled reference, or not applicable with reason]`

Engineering Governance Finding or Proposal:

`[Controlled reference]`

Affected Controlled Revisions:

`[Controlled references]`

Related or Predecessor Resolutions:

`[Controlled references or None]`

Authoritative Index:

`DOC-0001`

---

## Lifecycle Decision

EGR Content Approval:

`[Approved | Rejected | Requires Revision | Pending]`

Approved By:

`[Engineering Governance authority or Pending]`

Approval Reference:

`[Controlled approval reference or explicitly approved transitional authority]`

Approval Date:

`[YYYY-MM-DD or Pending]`

Activation Decision:

`[Authorized | Not Authorized | Deferred | Pending]`

Activation Authority:

`[Engineering Governance authority or Pending]`

Activation Date:

`[YYYY-MM-DD or Pending]`

Persistence State:

`[Pending | Persisted | Legacy | Remediation Required]`

Index State:

`[Registered | Registration Deferred with authority]`

---

## Supersedence and Historical Effect

Predecessor EGR:

`[Exact EGR revision or None]`

Successor EGR:

`[Exact EGR revision or None]`

Superseded Scope:

`[Identify replaced decision scope or state None]`

Preserved Historical Effect:

`[Describe the prior decision meaning and effective period that remain historically authoritative.]`

---

## Validation Record

YAML and Structure Validation:

`[Result and evidence]`

Identity and Revision Validation:

`[Result and evidence]`

Authority and Approval Validation:

`[Result and evidence]`

Lifecycle Validation:

`[Result and evidence]`

Relationship and Target Resolution:

`[Result and evidence]`

Scope and Affected-Revision Validation:

`[Result and evidence]`

Persistence and Index Validation:

`[Result and evidence]`

Whole-Document Validation:

`[Result and evidence]`

---

## Revision History

| Version | Date | Description |
| --- | --- | --- |
| 1.0 | `[YYYY-MM-DD]` | `[Describe the initial controlled Resolution publication.]` |

---

## Template Conformance

A completed EGR instantiated from this template is conformant only when:

* every intentional template variable has been replaced by verified controlled information;
* all STD-0000 required record elements are present;
* metadata and relationships conform to SPEC-0001;
* lifecycle and transition evidence conform to STD-0001;
* persistence and discovery claims conform to STD-0002;
* creation and governance review conform to PROC-0002;
* the subject disposition and EGR publication approval remain distinct;
* no authority or historical evidence is inferred or fabricated; and
* required validation passes.

---

## Template Revision History

| Version | Date | Description |
| ------- | ---- | ----------- |
| 1.0 | 2026-07-13 | Established the reusable Engineering Governance Resolution publication structure conforming to STD-0000, SPEC-0001, STD-0001, STD-0002, and PROC-0002. |
