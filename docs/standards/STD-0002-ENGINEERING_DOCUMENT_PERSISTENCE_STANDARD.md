---
document_id: STD-0002
title: Engineering Document Persistence Standard
version: 1.4
status: Active
owner: Engineering Governance
created: 2026-07-09
last_updated: 2026-07-19
phase: Engineering Knowledge Repository Foundation
domain: Engineering Governance
classification: Engineering Standard
source_of_truth: true
predecessor_revision: STD-0002@1.3
successor_revision: null
approval_status: Approved
approval_authority: Engineering Governance
approval_reference: Codex Handoff - Mission 0 Engineering Knowledge Repository Foundation and Automated Evidence Persistence
approval_date: 2026-07-19
persistence_status: Pending
declared_deferrals: []
relationships:
  - type: governed_by
    target: CHAR-0001
  - type: conforms_to
    target: POL-0001
  - type: conforms_to
    target: STD-0000
  - type: related_to
    target: STD-0001
  - type: conforms_to
    target: SPEC-0001
  - type: governs
    target: SPEC-0010
  - type: implemented_by
    target: PROC-0005
  - type: related_to
    target: GEN-0001
  - type: indexed_by
    target: DOC-0001
tags:
  - governance
  - persistence
  - controlled-documents
  - engineering-records
  - engineering-operating-system
---

# Engineering Document Persistence Standard

## Purpose

This standard defines how controlled engineering documents become authoritative engineering records within the Engineering Operating System (EOS).

It establishes the requirements for persistence, organization, indexing, traceability, discovery, and integrity of engineering information.

This standard defines the operational controls by which engineering records are preserved and discovered. The revision identity, lineage, supersedence, historical persistence, and reconstruction architecture is defined by SPEC-0001.

It does not define document lifecycle states, governance authority, execution procedures, or document templates.

---

## Scope

This standard applies to every controlled engineering document governed by the Engineering Operating System.

Examples include:

* policies;
* standards;
* procedures;
* templates;
* Engineering Work Orders;
* Engineering Governance Findings;
* Engineering Governance Resolutions;
* Completion Reports;
* Evidence Packages; and
* Engineering Knowledge Objects and their manifests.

Controlled documents remain governed by SPEC-0001. Engineering Knowledge
Objects use the historical knowledge architecture in SPEC-0010 and shall not
be treated as replacement controlled-document revisions.

---

## Engineering Persistence Principles

### Principle 1 — Single Authoritative Record

Every controlled engineering document shall have one authoritative persisted record.

---

### Principle 2 — Deterministic Discovery

An engineer or implementation agent shall be able to locate the authoritative record without undocumented knowledge.

---

### Principle 3 — Persistent Traceability

Engineering records shall maintain traceable relationships throughout their operational lifetime.

---

### Principle 4 — Historical Preservation

Engineering history shall be preserved in conformance with SPEC-0001. Superseded records remain engineering records, and historical engineering evidence shall not be destroyed solely because a newer revision exists.

---

### Principle 5 — Immutable Engineering History

Once persisted, an engineering revision shall not be altered. Subsequent changes shall be recorded through the Controlled Document Model in SPEC-0001 and the lifecycle controls in STD-0001.

---

## Authoritative Engineering Record

An Authoritative Engineering Record is the single controlled copy recognized by Engineering Governance as the official engineering record.

Only one authoritative record may exist for a specific document revision.

---

## Persistence Requirements

A persisted engineering record shall include, at minimum:

* document identifier;
* revision;
* document class;
* lifecycle state;
* approval status;
* governance authority;
* date of persistence;
* relationship references.

Additional metadata may be defined by document-specific standards.

---

## Repository Organization Principles

The Engineering Operating System shall organize engineering information according to document class and engineering relationships.

Repository organization shall support:

* deterministic navigation;
* logical grouping;
* controlled growth;
* future automation.

This standard defines organizational principles rather than repository implementation details.

---

## Engineering Indexes

Controlled engineering records shall be discoverable through authoritative indexes.

Indexes shall support locating:

* current authoritative revision;
* historical revisions;
* related engineering records;
* governing engineering documents.

Indexes shall not replace authoritative engineering records.

---

## Revision Persistence

Revision persistence shall conform to SPEC-0001. Repository operations shall preserve the immutable commit and blob objects used by each recorded historical locator and shall verify those objects before declaring persistence complete.

---

## Supersedence

Supersedence semantics and required records are defined exclusively by SPEC-0001. This standard requires persistence and index operations to retain those records and their referenced Git objects without altering their engineering meaning.

---

## Engineering Relationships

Persisted engineering records shall support relationships between:

* policies;
* standards;
* procedures;
* templates;
* Engineering Work Orders;
* Governance Findings;
* Governance Resolutions;
* Completion Reports;
* Evidence Packages;
* missions;
* phases;
* sprints;
* recovery plans;
* recovery units.

Relationships shall remain traceable throughout the engineering lifecycle.

---

## Evidence Linkage

Engineering evidence shall reference the Engineering Work Order that authorized its creation.

Engineering Work Orders shall reference the Engineering evidence produced during execution.

The relationship shall be bidirectional and discoverable.

---

## Completion Report Linkage

Every Completion Report shall reference:

* the governing Engineering Work Order;
* the executed revision;
* associated engineering evidence.

Engineering Work Orders shall reference their Completion Reports.

---

## Engineering Knowledge Persistence

Validated historical mission knowledge shall be persisted through EKR under
SPEC-0010 when a knowledge capture requirement applies. Persistence shall
record one immutable knowledge object or authoritative source reference,
cryptographic digest, provenance, mission and authority linkage, validation
disposition, subjects, relationships, sensitivity, retention, and limitations.

Record-once persistence is mandatory: when a controlled document, asset
record, Completion Report, Evidence Package, or project record already owns
the content, EKR shall reference its authoritative revision and digest rather
than create a competing copy. EOS shall persist only current knowledge
pointers and synchronization state, not the historical object corpus.

Knowledge publication is incomplete until both the object and its authoritative
index entry are durably persisted. Partial publication shall remain visibly
incomplete and recoverable. Corrections create a successor object; published
content is not edited in place.

Automated capture shall be idempotent, attributable, schema-validated,
sensitivity-aware, and fail closed on ambiguous identity, authority, integrity,
retention, or relationship state. Automation shall not originate approval,
qualification, acceptance, lifecycle transition, or execution authority.

---

## Cold-Start Discovery

The persistence model shall support deterministic recovery after interruption.

Given any current engineering activity, an engineer or implementation agent shall be able to discover:

* current mission;
* current phase;
* governing Engineering Work Order;
* authoritative governing documents;
* associated evidence;
* engineering history;

without requiring undocumented knowledge.

For a historical revision, discovery and reconstruction shall follow SPEC-0001 and shall resolve to one full commit object identifier, repository path, and verified blob object identifier.

Historical discovery shall also locate relevant EKR objects by permanent
identifier, mission, Work Order, asset, repository, controlled document,
decision, symptom, artifact class, date, disposition, and lesson learned.
Cold-start reconstruction shall not depend on conversation history, a search
service, embeddings, or a non-reproducible derived graph.

---

## Persistence Integrity Rules

Engineering persistence shall satisfy the following requirements.

An engineering record shall:

* possess one authoritative persisted copy;
* preserve engineering history;
* preserve superseded revisions;
* preserve engineering relationships;
* remain discoverable;
* remain attributable;
* remain traceable.

Engineering persistence shall never depend upon undocumented engineering knowledge.

---

## References

This standard references:

* GEN-0001 — Engineering Operating System Genesis Record
* STD-0000 — Engineering Governance Documentation Architecture
* STD-0001 — Engineering Document Lifecycle Standard
* POL-0001 — Engineering Governance Policy
* SPEC-0001 — Controlled Document Model
* PROC-0005 — Controlled Document Publication Procedure

---

## Operational Publication Procedure

PROC-0005 defines the common operational method for establishing an exact
publication boundary, applying an authorized atomic publication transaction,
recording immutable locators, and performing post-publication verification.

This Standard remains the authoritative owner of persistence, indexing,
discovery, historical preservation, reconstruction, and integrity requirements.
PROC-0005 executes those requirements and creates no persistence, lifecycle,
Governance, or implementation authority.

---

## Success Criteria

This standard is complete when every controlled engineering document within the Engineering Operating System can be:

* authoritatively persisted;
* deterministically discovered;
* historically preserved;
* revision controlled;
* relationship aware;
* recoverable during a cold-start engineering resume.

Repository-controlled governance revisions, mission classifications,
Completion Report requirements, and Governance Conformance Review requirements
shall be persisted before they are treated as operational behavior. Conversation
history and handoffs are not persistence substitutes. A governance improvement
is incomplete when any approved requirement exists only outside the controlled
publication and its registered planning relationships.

---

## Revision History

| Version | Date | Description |
| ------- | ---- | ----------- |
| 1.0 | 2026-07-09 | Initial Engineering Document Persistence Standard established. |
| 1.1 | 2026-07-10 | Referenced the revision persistence, supersedence, Git locator, and deterministic reconstruction architecture in SPEC-0001 and retained operational persistence controls under EWO-000011 Revision 2. |
| 1.2 | 2026-07-17 | Required persistence of repository-governed workflow behavior and prohibited conversation or handoff history as a substitute under EGR-000002 and EWO-000018. |
| 1.3 | 2026-07-18 | Integrated PROC-0005 as the operational method for exact publication boundaries, atomic persistence, immutable locator capture, and post-publication verification while preserving this Standard's persistence authority. |
| 1.4 | 2026-07-19 | Extended persistence governance to Engineering Knowledge Objects, record-once source referencing, atomic publication and indexing, automated-capture safety, EOS boundary preservation, and cold-start historical discovery under SPEC-0010. |
