---
document_id: EDR-0002
title: Engineering Authority Model
version: 1.0
status: Draft
owner: EOS Program
created: 2026-07-08
last_updated: 2026-07-08
governed_by: EOS-0001
decision_type: Foundational Architecture
source_of_truth: true
---

# Engineering Decision Record (EDR-0002)

## Title

Engineering Authority Model

---

# 1. Purpose

This Engineering Decision Record establishes the Engineering Authority Model for the Engineering Operating System (EOS).

Its purpose is to define where engineering truth resides, how engineering knowledge is governed, and how engineering information is presented without creating multiple sources of truth.

This decision establishes one of the foundational architectural principles of EOS.

---

# 2. Context

During the architectural development of EOS, multiple forms of engineering information were identified, including:

- Controlled Documents
- Project State
- Engineering Checkpoints
- Dashboards
- Validation Reports
- AI-generated Summaries
- Command-line Views
- Published Documentation

Each of these artifacts presents engineering information, but not all are appropriate sources of engineering authority.

Without a formal authority model, engineering knowledge would eventually become duplicated, inconsistent, and difficult to govern.

---

# 3. Problem Statement

Engineering systems frequently suffer from multiple competing sources of truth.

When engineering information exists in multiple authoritative locations:

- synchronization becomes difficult;
- inconsistencies emerge;
- traceability is reduced;
- automation becomes unreliable;
- engineering continuity depends upon human memory.

EOS requires a single, unambiguous authority model.

---

# 4. Decision

EOS adopts the following Engineering Authority Model.

> Engineering knowledge SHALL exist only within Authoritative Engineering Records (AERs).

All other engineering information SHALL be considered derived engineering views.

Derived engineering views SHALL NOT become authoritative.

Engineering truth SHALL be modified only through Authoritative Engineering Records.

---

# 5. Engineering Authority Model

```text
Authoritative Engineering Records
|
+-- Constitution
+-- Engineering Decision Records
+-- Specifications
+-- Services
+-- Project Records
|
v
Engineering Context
|
+-- Resume View
+-- Dashboards
+-- AI Summaries
+-- Reports
+-- Published Views

---

# 6. Authoritative Engineering Records (AER)

An Authoritative Engineering Record (AER) is the single governed source from which engineering knowledge originates.

Every AER SHALL possess:

- a unique identifier;
- a responsible owner;
- governing authority;
- revision history;
- engineering traceability;
- lifecycle status.

Examples include:

- EOS Documents
- Engineering Decision Records
- Specifications
- Standards
- Project Records
- Hardware Records
- Financial Records
- Validation Records

No engineering fact SHALL have more than one authoritative owner.

---

# 7. Derived Engineering Views

Derived Engineering Views exist to present engineering information for specific audiences or interfaces.

Examples include:

- Resume reports
- Status reports
- Dashboards
- AI briefings
- Published documentation
- Command-line output

Derived Engineering Views MAY:

- summarize information;
- reorganize information;
- aggregate information;
- filter information;
- cache information.

Derived Engineering Views SHALL NOT:

- become authoritative;
- replace Authoritative Engineering Records;
- require manual synchronization;
- directly modify engineering truth.

Whenever Authoritative Engineering Records change, derived views SHALL be regenerated.

---

# 8. Ownership and Traceability

Every engineering fact SHALL have exactly one authoritative owner.

Every derived engineering view SHALL be traceable to one or more Authoritative Engineering Records.

Every implementation SHALL be traceable through:

- governing constitutional authority;
- engineering decisions;
- specifications;
- validation evidence.

---

# 9. Architectural Consequences

This decision enables:

- deterministic Resume generation;
- Engineering Context Reconstruction;
- automated publishing;
- engineering dashboards;
- AI engineering assistants;
- validation automation;
- reproducible engineering context.

Because engineering truth exists only once, all engineering views remain consistent.

---

# 10. Alternatives Considered

## Resume as Authority

Rejected.

Reason:

Resume output is a derived engineering view and must never become an authoritative engineering record.

---

## Dashboard as Authority

Rejected.

Reason:

Dashboards present engineering information but do not govern engineering truth.

---

## AI Memory as Authority

Rejected.

Reason:

Engineering knowledge must remain independently verifiable through governed records.

---

## Multiple Authoritative Sources

Rejected.

Reason:

Multiple authorities inevitably create inconsistency, synchronization problems, and governance ambiguity.

---

# 11. Status

Status: Draft 1 - Pending Architecture Sprint Review Approval

This decision governs:

- SPEC-0001 - Controlled Document Model
- SPEC-0004 - Engineering Context Reconstruction Service
- SPEC-0005 - Engineering Control Framework
- SERVICE-0001 - EOS Core Services Catalog

Future engineering services SHALL conform to this authority model unless superseded through a subsequent Engineering Decision Record.

---

# Decision Summary

Engineering knowledge lives in Authoritative Engineering Records.

Engineering tools generate views.

Views never become authoritative.
