---
document_id: TPL-0001
title: Engineering Work Order Template
version: 1.9
status: Draft
owner: Engineering Governance
created: 2026-07-09
last_updated: 2026-07-28
phase: Engineering Execution Interface Standardization
domain: Engineering Governance
classification: Engineering Template
source_of_truth: true
related_documents:
  - GEN-0001
  - STD-0000
  - STD-0001
  - STD-0002
  - STD-0003
  - STD-0004
  - PROC-0001
  - PROC-0004
  - PROC-0005
  - TPL-0002
  - SPEC-0008
  - EWO-000012
  - EGR-000002
  - EWO-000018
tags:
  - governance
  - template
  - work-order
  - authorization-contract
  - engineering-operating-system
---

# Engineering Work Order Template

This template owns only the reusable structure of a concise,
transaction-specific authorization contract. Construct Engineering Handoffs
under PROC-0004. Reusable lifecycle, persistence, execution, validation,
publication, state, and reporting behavior remains authoritative in the
referenced controlled documents and shall not be restated here.

## Transaction Identification

Engineering Operating System: `<Engineering Operating System>`

Engineering Governance Authority: `<Engineering Governance Authority>`

Implementation Agent: `<Implementation Agent>`

Mission: `<Mission Identifier>`

Phase: `<Phase Identifier>`

Engineering Work Order: `<EWO Identifier>`

Revision: `<Revision Number>`

Title: `<Engineering Work Order Title>`

Status: `<Draft | Review | Approved | Active | Superseded | Archived>`

Execution Mode: `<Execution Mode>`

Repository Mission Contract: `<Work Registry work-item locator>`

Engineering Execution Interface: `engineering/execution/execution-interface.yaml`

## Authorization

Approval Authority: `<Engineering Governance Authority>`

Approval Reference: `<Controlled authorization reference>`

Approval Date: `<Date>`

Authorized Lifecycle State: `<Approved | Active>`

Authorization Statement: `<Exact bounded authorization granted by this Work Order>`

This Work Order grants no authority beyond its explicit scope and does not
self-authorize lifecycle promotion, publication, or additional work.

## Purpose and Expected Outcome

Purpose: `<Transaction-specific engineering objective>`

Expected Outcome: `<Observable result expected from the authorized transaction>`

## Mission Classification

Classification: `<Category A | Category B | Category C>`

Classification Rationale: `<Transaction-specific rationale>`

Approved Gate Exceptions: `<Explicit exceptions or None>`

Apply the classification and initiation gates defined by PROC-0001.

## Governing References

This Work Order conforms to the applicable controlled authorities, including:

- STD-0000 — Engineering Governance Documentation Architecture
- STD-0001 — Engineering Document Lifecycle Standard
- STD-0002 — Engineering Document Persistence Standard
- STD-0003 — Engineering Work Order Standard
- STD-0004 — Engineering State Standard
- PROC-0001 — Engineering Work Order Execution Procedure
- PROC-0004 — Engineering Handoff Construction Procedure
- TPL-0002 — Engineering Completion Report Template

Transaction-Specific Governing References: `<Identifiers and revisions or None>`

## Engineering Transaction Profile

Selected Profile: `<ETP identity and revision or Not Applicable>`

Selection Authority: `<Authorization Kernel locator or Not Applicable>`

Resolved Components: `<Component identities and revisions or Not Applicable>`

Permitted Transaction Additions: `<Additions or None>`

Compatibility Result: `<COMPATIBLE | NOT COMPATIBLE | Not Applicable>`

Authority Preservation Result: `<PRESERVED | NOT PRESERVED | Not Applicable>`

Resolved Manifest Fingerprint or Locator: `<Fingerprint, locator, or Not Applicable>`

Resolve and validate ETPs under SPEC-0008 through PROC-0004. This template
records the frozen result; it does not define profile semantics or selection
authority. Historical Engineering Work Orders require no retrospective ETP.

## Scope

In Scope: `<Authorized transaction boundary>`

Out of Scope: `<Explicit exclusions>`

Affected Repositories: `<Repository identifiers or None>`

Affected Records or Systems: `<Identifiers or None>`

## Explicit Authority

Authorized Operational Activities: `<Transaction-specific activities or None>`

Authorized Repository Changes: `<Exact files, document classes, or None>`

Authorized External Effects: `<Exact effects or None>`

Authorized Exceptions: `<Explicit exceptions, authority reference, or None>`

## Prohibited Activities and Scope Restrictions

Prohibited Activities: `<Transaction-specific prohibitions>`

Scope Restrictions: `<Transaction-specific limits>`

Authority Expansion Conditions: `<Conditions requiring new authorization or None>`

## Dependencies and Entry Criteria

Dependencies: `<Authoritative prerequisites and locators or None>`

Entry Criteria: `<Conditions that must be true before execution>`

Blocking Conditions: `<Known blockers or None>`

## Deliverables

1. `<Transaction-specific deliverable>`
2. `<Transaction-specific deliverable or remove>`

Required Repository Locators: `<Locator requirements or Not Applicable>`

## Transaction-Specific Execution Sequence

Execute the standard workflow in PROC-0001. Record only transaction-specific
ordering, gates, dependencies, or authorized deviations below.

1. `<Transaction-specific step or Not Applicable>`
2. `<Transaction-specific step or remove>`

Authorized Workflow Deviations: `<Deviation and authority reference or None>`

## Success and Acceptance Criteria

Success Criteria: `<Objective, observable criteria>`

Acceptance Criteria: `<Governance acceptance conditions>`

Definition of Done: `<Transaction-specific completion boundary>`

## Validation Profile Reference

Standard Validation Profile: `<Controlled validation profile or PROC-0001 default>`

Transaction-Specific Validation Additions: `<Additional checks or None>`

Required Fixtures or Evidence: `<Identifiers or None>`

Validation Exceptions: `<Approved exceptions and authority reference or None>`

Validator completion, complete output, and terminal exit status shall be handled
through PROC-0001 rather than redefined by this Work Order.

## Publication and Synchronization Requirements

Publication Requirement: `<Atomic publication boundary, separate publication, or None>`

Synchronization Targets: `<DOC-0001, Project State, Work Registry, EOS, checkpoint, or None>`

Required Repository History Action: `<Commit, tag, push, or None>`

Publication Exceptions: `<Approved exceptions and authority reference or None>`

Apply lifecycle and persistence requirements from STD-0001 and STD-0002 and the
common controlled publication workflow from PROC-0005. PROC-0001 remains the
Engineering Work Order execution procedure.

## Final Certification Question

Question: `<Exact transaction-specific certification question or Not Applicable>`

Allowed Answer Set: `<Exact allowed answers or Not Applicable>`

Required Supporting Evidence: `<Evidence requirement or Not Applicable>`

## Transaction-Specific Stop, Resume, and Escalation Additions

Common stop, resume, escalation, checkpoint, and freshness behavior is owned by
STD-0003, PROC-0001, and STD-0004. State only transaction-specific additions.

Additional Stop Conditions: `<Conditions or None>`

Additional Resume Requirements: `<Requirements or None>`

Additional Escalation Triggers: `<Triggers or None>`

## Completion Report Requirement

Produce the repository-standard Completion Report required by STD-0003 through
the workflow in PROC-0001 and the authoritative structure in TPL-0002.

Transaction-Specific Reporting Additions: `<Additions or None>`

Transaction-Specific Evidence Attachments: `<Attachments or None>`

## Engineering Governance Review

Engineering Governance Disposition: `<To be completed during governance review>`

Engineering Governance Acceptance: `<Approved | Rejected | Requires Revision>`

Authorized Revision: `<Revision>`

Approved By: `<Engineering Governance Authority>`

Approval Date: `<Date>`

## Revision History

| Version | Date | Description |
| --- | --- | --- |
| 1.3 | 2026-07-17 | Referenced the repository-standard Completion Report authorities and preserved transaction-specific certification fields. |
| 1.4 | 2026-07-18 | Refined the template into a concise authorization contract with single-owner references for reusable lifecycle, execution, validation, publication, state, and reporting behavior. |
| 1.5 | 2026-07-18 | Assigned construction behavior to PROC-0004 and retained TPL-0001 as the sole reusable structural owner. |
| 1.6 | 2026-07-18 | Added structural fields for an explicitly selected ETP and frozen resolved manifest while assigning model and resolution semantics to SPEC-0008 and PROC-0004. |
| 1.7 | 2026-07-18 | Corrected the controlled-publication workflow reference to PROC-0005 while preserving PROC-0001 ownership of Engineering Work Order execution. |
| 1.8 | 2026-07-28 | Added repository Mission Contract and Engineering Execution Interface locators without duplicating their semantics. |
