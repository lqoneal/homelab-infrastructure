---
document_id: STD-0001
title: Engineering Document Lifecycle Standard
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
  - STD-0002
  - POL-0001
tags:
  - governance
  - lifecycle
  - controlled-documents
  - engineering-standard
  - engineering-operating-system
---

# Engineering Document Lifecycle Standard

## Purpose

This standard defines the mandatory lifecycle governing every controlled engineering document managed by the Engineering Operating System (EOS).

It establishes the required lifecycle states, transition rules, approval requirements, supersedence requirements, and retirement process for controlled engineering documentation.

This standard defines **when** documents change state. It does not define document storage, indexing, or persistence mechanisms.

Those responsibilities are governed by the Engineering Document Persistence Standard.

---

## Scope

This standard applies to every controlled engineering document governed by the Engineering Operating System, including:

* policies;
* standards;
* procedures;
* templates;
* Engineering Work Orders;
* engineering specifications;
* engineering records;
* engineering evidence packages;
* engineering completion reports;
* governance findings;
* governance resolutions.

---

## Lifecycle Principles

### Principle 1 — Single Lifecycle

Every controlled engineering document shall exist in exactly one lifecycle state.

A document shall never occupy multiple lifecycle states simultaneously.

---

### Principle 2 — Controlled Transitions

Lifecycle transitions require Engineering Governance approval unless explicitly delegated by policy.

No implementation agent shall change a document lifecycle state without authorization.

---

### Principle 3 — Traceability

Every lifecycle transition shall be recorded and traceable.

Transitions shall identify:

* previous state;
* new state;
* approving authority;
* transition date;
* governing work order or governance decision.

---

### Principle 4 — Supersedence

A document revision supersedes a previous revision only after approval.

Superseded revisions remain historical engineering records and shall not be destroyed unless governed by an approved archival policy.

---

### Principle 5 — Stable Baselines

During an active engineering phase, the approved Governance Baseline remains frozen.

Governance improvements discovered during execution shall be recorded as Engineering Governance Findings and deferred until phase closeout unless an execution-blocking defect requires immediate Engineering Governance approval.

---

## Lifecycle States

The Engineering Operating System recognizes the following lifecycle states.

### Draft

The document is under development.

It is not authoritative.

It shall not govern engineering execution.

---

### Review

The document has been submitted for Engineering Governance review.

No uncontrolled edits shall occur during review.

---

### Approved

Engineering Governance has approved the document content.

The document is eligible for publication according to the Engineering Document Persistence Standard.

---

### Active

The document has been published and is the current authoritative engineering record.

Only Active documents govern engineering execution.

---

### Superseded

A newer approved revision has replaced the document.

The document remains part of the permanent engineering record.

Superseded documents shall remain discoverable.

---

### Archived

The document has been removed from operational use but retained for historical, legal, or engineering purposes.

Archived documents shall not govern engineering execution.

---

## Lifecycle Transitions

Permitted transitions are:

```text
Draft
  ↓
Review
  ↓
Approved
  ↓
Active
  ↓
Superseded
  ↓
Archived
```

Engineering Governance may authorize exceptional transitions only through an approved governance decision.

---

## Governance Requirements

Lifecycle changes shall satisfy the following requirements:

* approval authority identified;
* revision identified;
* transition recorded;
* supersedence documented when applicable;
* related documents updated where required.

---

## Responsibilities

### Engineering Governance

Responsible for:

* approving lifecycle transitions;
* approving revisions;
* approving supersedence;
* resolving lifecycle disputes.

### Implementation Agents

Responsible for:

* following the approved lifecycle;
* refusing unauthorized transitions;
* reporting lifecycle inconsistencies.

Implementation agents shall not independently approve lifecycle transitions.

---

## Relationship to Other Standards

This standard defines lifecycle behavior.

The Engineering Document Persistence Standard defines:

* repository persistence;
* indexing;
* discoverability;
* authoritative source management.

The Engineering Governance Documentation Architecture defines how lifecycle-controlled documents relate to one another.

---

## Compliance

A controlled engineering document is compliant with this standard only if:

* exactly one lifecycle state is assigned;
* lifecycle state matches repository status;
* supersedence is correctly documented;
* governing authority is identifiable;
* transitions are traceable.

---

## Success Criteria

This standard is complete when every controlled engineering document within the Engineering Operating System can be placed into a single, traceable lifecycle state governed by Engineering Governance and consistently interpreted by both engineers and implementation agents.

