---
document_id: TPL-0001
title: Engineering Work Order Template
version: 1.2
status: Active
owner: Engineering Governance
created: 2026-07-09
last_updated: 2026-07-17
phase: Governance Framework Modernization
domain: Engineering Governance
classification: Engineering Template
source_of_truth: true
related_documents:
  - GEN-0001
  - STD-0000
  - STD-0003
  - PROC-0001
  - EWO-000012
  - EGR-000002
  - EWO-000018
tags:
  - governance
  - template
  - work-order
  - execution
  - engineering-operating-system
---

# Engineering Work Order Template

## Engineering Governance Header

Engineering Operating System:

`<Engineering Operating System>`

Engineering Governance:

`<Engineering Governance Authority>`

Implementation Agent:

`<Implementation Agent>`

Mission:

`<Mission Identifier>`

Phase:

`<Phase Identifier>`

Engineering Work Order:

`<EWO Identifier>`

Revision:

`<Revision Number>`

Title:

`<Engineering Work Order Title>`

Classification:

`<Classification>`

Status:

`<Draft | Review | Approved | Active | Superseded | Archived>`

Execution Mode:

`<Execution Mode>`

---

## Governing References

This Engineering Work Order shall comply with:

* POL-0001 — Engineering Governance Policy
* STD-0000 — Engineering Governance Documentation Architecture
* STD-0001 — Engineering Document Lifecycle Standard
* STD-0002 — Engineering Document Persistence Standard
* STD-0003 — Engineering Work Order Standard
* PROC-0001 — Engineering Work Order Execution Procedure

---

## Engineering Governance Intent

### Mission Classification

`<Category A — Repository Engineering Work | Category B — Local Engineering Environment Work | Category C — Operational / Diagnostic Work>`

State the classification rationale, applicable risk-proportional initiation
gates, repository-interaction status, and any explicitly approved exception.

### Purpose

`<Mission-specific engineering objective>`

### Engineering Governance Objectives

`<Objectives>`

### Mission Scope

`<Authorized scope>`

### Mission Constraints

`<Constraints>`

---

## Authority Model

### Operational Authority

`<Explicitly authorized operational activities>`

### Engineering Authority

`<Explicitly authorized engineering actions>`

### Prohibited Activities

`<Activities not authorized>`

### Escalation Requirements

`<Conditions requiring Engineering Governance authorization>`

---

## Execution Overview

Engineering phases authorized by this Engineering Work Order:

### Phase 0

`<Description>`

### Phase 1

`<Description>`

### Phase 2

`<Description>`

### Final Phase

`<Description>`

---

## Success Criteria

### Mission Success

`<Mission success definition>`

### Definition of Done

`<Definition of Done>`

### Acceptance Criteria

`<Acceptance criteria>`

---

## Phase Execution

For each engineering phase provide:

### Phase `<Identifier>`

Purpose:

`<Purpose>`

Inputs:

`<Required inputs>`

Activities:

`<Authorized activities>`

Expected Outputs:

`<Expected outputs>`

Evidence Required:

`<Evidence requirements>`

Phase Completion Criteria:

`<Completion criteria>`

Stop Conditions:

`<Phase-specific stop conditions>`

Repeat for each authorized engineering phase.

---

## Resume Policy

Upon interruption, the Implementation Agent shall:

1. Verify the Active Engineering Work Order.
2. Perform Operational Inventory.
3. Perform Operational Preparation.
4. Perform Baseline Verification.
5. Resume at the first incomplete engineering phase.

Completed phases remain complete unless Engineering Governance authorizes repetition.

---

## Communication Contract

The Implementation Agent shall report:

* observations;
* supporting evidence;
* mission impact;
* recommendations.

The Implementation Agent shall not:

* infer Engineering Governance intent;
* exceed granted authority;
* continue beyond approved stop conditions.

---

## Stop Conditions

Execution shall stop when:

* authority is exceeded;
* governance authorization is required;
* baseline integrity is compromised;
* deterministic execution cannot be maintained;
* Engineering Work Order-defined stop conditions are encountered.

The Implementation Agent shall produce a Completion Report prior to stopping whenever practical.

---

## Completion Report Requirements

The Completion Report shall include:

* the exact title `Completion Report`;

* Work Order Summary;
* Mission Status;
* Execution Status;
* Scope Compliance;
* Definition of Done;
* Acceptance Criteria;
* Files Modified;
* Runtime Changes;
* Repository Integrity, when applicable;
* Engineering Findings;
* Operational Observations;
* Recommended Next Engineering Work Order;
* Engineering Governance Notes; and
* a completed Governance Conformance Review containing Authority Verification,
  Mission Scope Compliance, Trust Boundary Verification, Controlled Document
  Compliance, Authority Circumvention Assessment, Governance Gap Assessment,
  Documentation Requirement, and Overall Governance Status.

Mission completion shall not be reported until this review is complete.

---

## Engineering Governance Review

### Engineering Governance Disposition

`<To be completed during governance review>`

### Engineering Governance Acceptance

`<Approved | Rejected | Requires Revision>`

### Authorized Revision

`<Revision>`

### Approved By

`<Engineering Governance Authority>`

### Approval Date

`<Date>`

---

## References

Mission-specific references:

`<References>`

Applicable engineering standards:

`<References>`

Applicable engineering procedures:

`<References>`

Applicable engineering records:

`<References>`

---

## Revision History

| Version | Date | Description |
| ------- | ---- | ----------- |
| 1.0 | 2026-07-09 | Initial Engineering Work Order Template established. |
| 1.1 | 2026-07-10 | Removed Issued and established Active as the Engineering Work Order execution-authority lifecycle state under EWO-000012. |
| 1.2 | 2026-07-17 | Added repository-governed mission classification, exact Completion Report title, and mandatory Governance Conformance Review under EGR-000002 and EWO-000018. |
