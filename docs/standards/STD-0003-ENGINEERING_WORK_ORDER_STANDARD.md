---
document_id: STD-0003
title: Engineering Work Order Standard
version: 1.0
status: Active
owner: Engineering Governance
created: 2026-07-09
last_updated: 2026-07-09
phase: Governance Bootstrap
domain: Engineering Governance
classification: Engineering Standard
source_of_truth: true
related_documents:
  - GEN-0001
  - STD-0000
  - STD-0001
  - STD-0002
  - POL-0001
  - PROC-0001
tags:
  - governance
  - work-order
  - engineering-standard
  - execution
  - engineering-operating-system
---

# Engineering Work Order Standard

## Purpose

This standard defines the mandatory requirements for all Engineering Work Orders issued under the Engineering Operating System.

It establishes what every Engineering Work Order shall contain, what authority it conveys, and the minimum requirements for engineering execution.

This standard defines what an Engineering Work Order must require.

It does not define operational execution procedures or document formatting.

---

## Scope

This standard applies to every Engineering Work Order executed within the Engineering Operating System.

---

## Engineering Work Order Principles

### Principle 1 — Explicit Authorization

Engineering work shall be performed only under an approved Engineering Work Order.

---

### Principle 2 — Mission Specificity

Each Engineering Work Order shall authorize only one defined engineering mission or clearly bounded scope.

---

### Principle 3 — Defined Authority

Every Engineering Work Order shall explicitly define the authority granted to the implementation agent.

Authority not explicitly granted is prohibited.

---

### Principle 4 — Deterministic Execution

Every Engineering Work Order shall support deterministic execution and deterministic resume.

---

### Principle 5 — Evidence-Based Completion

Engineering Work Orders are completed through engineering evidence, not assumptions.

---

## Required Engineering Work Order Elements

Every Engineering Work Order shall include, at minimum:

* identifier;
* revision;
* status;
* title;
* mission;
* phase;
* scope;
* purpose;
* Engineering Governance intent;
* authority model;
* resume policy;
* communication contract;
* success criteria;
* stop conditions;
* Completion Report requirements;
* references.

---

## Governance Requirements

Every Engineering Work Order shall:

* identify the governing policy;
* identify applicable standards;
* identify applicable procedures;
* identify applicable templates.

The Engineering Work Order shall not redefine those documents.

---

## Authority Requirements

Every Engineering Work Order shall define:

* operational authority;
* engineering authority;
* prohibited actions;
* escalation requirements.

Authority shall be explicit.

---

## Resume Requirements

Every Engineering Work Order shall support deterministic resume.

Resume requirements shall include:

* verification of the governing work order revision;
* operational inventory;
* operational preparation;
* baseline verification;
* identification of the first incomplete engineering phase.

---

## Communication Requirements

Every Engineering Work Order shall require the implementation agent to report:

* observations;
* supporting evidence;
* mission impact;
* recommendations.

Implementation agents shall not infer Engineering Governance intent.

---

## Evidence Requirements

Every Engineering Work Order shall require production of sufficient engineering evidence to permit Engineering Governance to determine whether the mission objectives have been achieved.

---

## Completion Report Requirements

Every Engineering Work Order shall require a Completion Report containing, at minimum:

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
* Engineering Governance Notes.

---

## Stop Conditions

Every Engineering Work Order shall define explicit stop conditions.

Execution shall stop when:

* authority is exceeded;
* Engineering Governance authorization is required;
* repository integrity is compromised;
* deterministic execution can no longer be maintained;
* approved stop conditions are encountered.

---

## Lifecycle Requirements

Engineering Work Orders shall comply with:

* Engineering Document Lifecycle Standard;
* Engineering Document Persistence Standard.

Implementation agents verify the issued Engineering Work Order before execution.

Lifecycle state transitions remain the responsibility of Engineering Governance.

---

## Compliance

Engineering Work Orders shall comply with:

* Engineering Governance Policy;
* Engineering Governance Documentation Architecture;
* Engineering Document Lifecycle Standard;
* Engineering Document Persistence Standard.

---

## References

This standard references:

* GEN-0001 — Engineering Operating System Genesis Record
* STD-0000 — Engineering Governance Documentation Architecture
* STD-0001 — Engineering Document Lifecycle Standard
* STD-0002 — Engineering Document Persistence Standard
* POL-0001 — Engineering Governance Policy
* PROC-0001 — Engineering Work Order Execution Procedure

---

## Success Criteria

This standard is complete when every Engineering Work Order issued under the Engineering Operating System:

* conveys explicit authority;
* defines mission scope;
* supports deterministic execution;
* supports deterministic resume;
* requires sufficient engineering evidence;
* provides explicit completion requirements;
* defines explicit stop conditions;
* complies with the Engineering Governance framework.

