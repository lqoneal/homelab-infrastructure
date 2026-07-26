---
document_id: POL-0001
title: Engineering Governance Policy
version: 1.2
status: Active
owner: Engineering Governance
created: 2026-07-09
last_updated: 2026-07-26
phase: Governance Framework Modernization
domain: Engineering Governance
classification: Engineering Governance Policy
source_of_truth: true
related_documents:
  - CHAR-0001
  - GEN-0001
  - STD-0000
  - STD-0001
  - STD-0002
  - EGR-000002
  - EWO-000018
  - SPEC-0011
tags:
  - governance
  - policy
  - authority
  - engineering-governance
  - engineering-operating-system
---

# Engineering Governance Policy

## Purpose

This policy establishes the governance principles, delegated authority model, and decision framework for the Engineering Operating System (EOS). It derives its authority through CHAR-0001 — Engineering Charter.

Lawrence O'Neal is the sole ultimate engineering authority for the production
Zeus environment. Principal `loneal` is the authenticated production identity,
and the authenticated Zeus CLI is the authoritative interface through which
that authority is exercised. Engineering Governance is the controlled
governance function defined by CHAR-0001, not an independent authority.

This policy is the highest policy-level normative record within the Engineering Governance hierarchy. It is subordinate to CHAR-0001 and is not the highest foundational governing record.

All subordinate standards, specifications, procedures, templates, and Engineering Work Orders shall conform to this policy and CHAR-0001.

---

## Scope

This policy governs:

* Engineering Governance;
* engineering information;
* engineering execution;
* engineering documentation;
* engineering records;
* engineering evidence;
* engineering work performed within the Engineering Operating System.

It applies to all engineering missions, projects, repositories, assets, and implementation agents operating under EOS governance.

As a Policy, this document defines governance objectives, constraints, and intent. It is not a Charter, Standard, Specification, Procedure, Engineering Work Order, or Project State record. Standards define mandatory rules, Specifications define architectures and models, Procedures define repeatable workflows, and Engineering Work Orders authorize bounded execution.

---

## Governance Objectives

Engineering Governance exists to:

* establish governance direction and controlled authorization within authority exercised by Lawrence O'Neal through CHAR-0001;
* protect engineering integrity;
* ensure deterministic execution;
* preserve engineering history;
* enable deterministic recovery;
* support continuous improvement through controlled governance;
* produce auditable engineering records.

---

## Engineering Governance Principles

### Principle 1 — Governance Before Execution

Engineering work shall be governed before it is executed.

Execution shall proceed only under an approved Governance Baseline.

Controlled documentation is the normal operational source of execution
authority. Zeus shall resolve that authority before execution and shall not
silently bypass it.

---

### Principle 2 — Evidence-Based Decisions

Engineering Governance decisions shall be based upon engineering evidence.

Implementation agents collect evidence.

Engineering Governance interprets evidence.

---

### Principle 3 — Single Source of Authority

Every engineering requirement shall have one authoritative governing document.

Conflicting authority shall not exist.

---

### Principle 4 — Separation of Responsibilities

Engineering Governance establishes governance direction and controlled authorization within its delegated authority.

Implementation agents execute authorized work.

Implementation agents shall not establish governance.

---

### Principle 5 — Engineering Information Integrity

Engineering information is a controlled engineering asset.

Engineering records shall remain:

* authoritative;
* traceable;
* attributable;
* discoverable;
* historically preserved.

---

### Principle 6 — Stable Execution

Engineering execution shall occur against a frozen Governance Baseline.

Process improvements shall not alter execution during an active phase except to correct an execution-blocking defect approved by Engineering Governance.

---

### Principle 7 — Continuous Improvement

Engineering improvement is continuous.

Governance change is controlled.

Validated improvements shall be recorded as Engineering Governance Findings and incorporated through Governance Stabilization after phase completion.

---

## Governance Authority

Within the authority exercised by Lawrence O'Neal through CHAR-0001,
Engineering Governance is the controlled function used to:

* approve policies;
* approve standards;
* approve specifications;
* approve procedures;
* approve templates;
* approve and activate Engineering Work Orders that authorize bounded engineering execution;
* establish Governance Baselines;
* qualify Governance Baselines;
* designate operational Governance Baselines;
* approve governance changes;
* accept completed engineering work;
* authorize governance revisions.

Implementation agents possess only the bounded execution authority explicitly granted by an approved and active Engineering Work Order.

Zeus is the authority-resolution, validation, reconciliation, and execution
system. It does not invent approvals or self-authorize. When normal controlled
authority cannot be resolved, Zeus shall treat the condition as authority
restoration work under SPEC-0011. Bootstrapping authorizes reconciliation of
controlled documentation, never execution outside it.

---

## Roles and Responsibilities

### Engineering Governance

Engineering Governance is responsible for:

* governance direction;
* document approval;
* Governance Baselines;
* work authorization;
* engineering acceptance;
* governance change control.

### Implementation Agent

Implementation agents are responsible for:

* executing approved Engineering Work Orders;
* complying with approved authority;
* collecting engineering evidence;
* producing Completion Reports;
* reporting observations;
* stopping when Engineering Governance authorization is required.

Implementation agents shall not exceed granted authority.

---

## Governance Baseline

Every engineering phase shall operate against an approved Governance Baseline.

The Governance Baseline consists of the applicable approved governance records, including:

* policies;
* standards;
* specifications;
* procedures;
* templates.

Engineering Work Orders authorize bounded execution against the designated operational Governance Baseline.

The Governance Baseline remains frozen throughout phase execution unless Engineering Governance approves a corrective revision to resolve an execution-blocking defect.

---

## Governance Operating Modes

The Engineering Operating System operates in two governance modes.

Standards, Specifications, and Procedures define the mandatory rules, models, architectures, and repeatable workflows that implement these operating modes.

### Mission Execution

Mission Execution exists to execute engineering work using the approved Governance Baseline.

Activities include:

* engineering execution;
* evidence collection;
* Engineering Governance Finding identification.

Governance redesign is prohibited during Mission Execution except for approved defect correction.

### Governance Stabilization

Governance Stabilization exists to review accumulated Engineering Governance Findings.

Activities include:

* governance review;
* policy revision;
* standards revision;
* specifications revision;
* procedure revision;
* template revision;
* Governance Baseline publication.

Future engineering phases inherit the updated Governance Baseline.

---

## Governance Change Control

Ordinary EOS governance changes shall occur only through approved Governance Stabilization activities. Amendments to CHAR-0001 remain governed by the Charter's amendment authority and requirements.

Governance-improvement work affects governance systems, not isolated
documents. Unless Engineering Governance explicitly limits the approving
authority, an authorized governance-improvement mission shall reconcile the
complete directly affected governance subsystem. It shall not knowingly leave
conflicting authority, terminology, procedures, templates, lifecycle rules, or
derived operational behavior.

Silent governance correction is prohibited. A discovered governance gap,
exception, ambiguity, or circumvention condition shall be reported, assessed,
and either corrected under explicit authority or persisted as governed
follow-up work.

During Mission Execution:

* improvements are recorded;
* improvements are not implemented.

Execution-blocking defects may be corrected only through explicit Engineering Governance approval.

## Repository-Governed Engineering Behavior

After an approved governance revision is incorporated into the controlled
repository publication, that publication is the sole operational source for
Engineering Work Initiation, mission classification, mission lifecycle,
Completion Report structure, and Governance Conformance Review requirements.

Conversation history and prompts are historical or mission-input artifacts.
Engineering Handoffs are governed according to CHAR-0001. During Transitional
Engineering Handoff Governance, a Handoff issued by Engineering Governance is
an approved directive and may initiate the subordinate governance processes
within its stated scope. It does not replace their required review, lifecycle,
publication, qualification, evidence, or repository-control activities and it
does not itself confer EWO execution authority.

Outside that Charter-defined transitional treatment, a handoff may identify an
approval or reference repository authority, but shall not redefine, weaken,
replace, or silently extend repository-governed behavior. This
operational-source rule remains subordinate to the authority origin and
hierarchy established by CHAR-0001.

## Governance Architecture Validation

Every governance-improvement mission shall validate the authority hierarchy,
governance hierarchy, controlled-document hierarchy, dependency integrity,
publication traceability, initiation lifecycle, mission lifecycle, Completion
Report architecture, templates, and governance workflow for its complete
affected subsystem.

Future-mission verification shall demonstrate that an implementation agent can
derive classification, lifecycle, reporting, and conformance-review behavior
from repository-controlled governance. During Transitional Engineering Handoff
Governance, initiation may derive from a Governance-issued Handoff as provided
by CHAR-0001; mission-specific Handoff instructions remain bounded by the
Charter and cannot override subordinate lifecycle controls.

---

## Engineering Governance Findings

Engineering Governance Findings record validated observations that may improve the Engineering Operating System.

Engineering Governance Findings:

* do not modify governance;
* enter the Phase Improvement Queue;
* are reviewed during phase closeout.

---

## Engineering Governance Resolutions

Engineering Governance Resolutions record governance decisions.

Engineering Governance Resolutions:

* approve or reject Engineering Governance Findings;
* authorize governance changes;
* establish future Governance Baselines.

---

## Compliance

All Engineering Operating System participants shall comply with:

* approved governance policies;
* approved standards;
* approved specifications;
* approved procedures;
* approved Engineering Work Orders.

Any deviation shall be explicit, traceable, approved by Engineering Governance before execution, and recorded through the appropriate controlled mechanism.

---

## References

CHAR-0001 is the governing record for this policy. GEN-0001 is a related historical governance record, and the Standards listed below are subordinate implementation records. Specifications and Procedures are likewise subordinate implementation records within their delegated roles.

* CHAR-0001 — Engineering Charter
* GEN-0001 — Engineering Operating System Genesis Record
* STD-0000 — Engineering Governance Documentation Architecture
* STD-0001 — Engineering Document Lifecycle Standard
* STD-0002 — Engineering Document Persistence Standard

---

## Success Criteria

This policy is complete when it establishes:

* governance authority;
* governance principles;
* governance responsibilities;
* governance operating modes;
* Governance Baseline management;
* governance change control;

and provides the policy-level governing foundation for all Engineering Operating System standards, specifications, procedures, templates, and Engineering Work Orders.

---

## Revision History

| Version | Date | Description |
| --- | --- | --- |
| 1.0 | 2026-07-09 | Initial Engineering Governance Policy established. |
| 1.1 | 2026-07-17 | Established holistic governance reconciliation, repository-governed workflow behavior, no silent correction, architecture validation, and future-mission verification under EGR-000002 and EWO-000018. |
