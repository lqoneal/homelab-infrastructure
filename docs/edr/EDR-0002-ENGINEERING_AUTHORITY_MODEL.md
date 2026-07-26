---
document_id: EDR-0002
title: Engineering Authority Model
version: 1.2
status: Draft
owner: EOS Program
created: 2026-07-08
last_updated: 2026-07-26
phase: Governance Architecture Reconciliation
domain: Engineering Governance
classification: Foundational Architecture Decision Record
governed_by: CHAR-0001
source_of_truth: true
related_documents:
  - CHAR-0001
  - POL-0001
  - GEN-0001
  - EOS-0001
  - SPEC-0001
  - SPEC-0004
  - SPEC-0005
  - SERVICE-0001
  - SPEC-0011
tags:
  - engineering
  - authority
  - governance-authority
  - information-authority
  - authoritative-engineering-records
  - derived-views
  - engineering-operating-system
---

# Engineering Authority Model

## Purpose

This Engineering Decision Record establishes the Engineering Authority Model for the Engineering Operating System (EOS).

It distinguishes the authority to govern engineering activity from the authority assigned to engineering information. It defines where controlled engineering knowledge resides, how that knowledge remains attributable and traceable, and how engineering information may be presented without creating competing sources of authority.

This record preserves the historical architectural principle that engineering knowledge is captured once in governed records and presented through non-governing derived views.

## Scope

This decision applies to:

* Governance Authority exercised within EOS;
* controlled engineering records and the information they own;
* Authoritative Engineering Record designations;
* ownership and traceability of engineering facts;
* generated, aggregated, cached, summarized, and published views of engineering information.

This decision does not originate engineering authority, redefine the governance hierarchy established by CHAR-0001, or authorize engineering execution. It operates only within authority delegated through the governing records and applicable Engineering Work Orders.

## Governing and Related Records

### Governing Record

CHAR-0001 — Engineering Charter is the governing record for this decision.

CHAR-0001 establishes the authority chain from Lawrence O'Neal through
authenticated principal `loneal`, the Zeus CLI, authority resolution, and
subordinate repository-controlled records. No statement in this decision may
be interpreted to supersede or redefine that chain.

### Related Records

* POL-0001 — Engineering Governance Policy defines policy-level governance objectives, constraints, responsibilities, and controlled authorization within the authority delegated through CHAR-0001.
* GEN-0001 — Engineering Operating System Genesis Record preserves the historical context of the one-time Governance Bootstrap. It is related historical context and does not govern this decision.
* EOS-0001 — Engineering Operating System Constitution preserves foundational architectural principles associated with authoritative records, derived views, continuity, and traceability. It is a related Draft architectural record and is not the source of governance authority for this decision.
* SPEC-0001 — Controlled Document Model represents controlled-record classes, lifecycle attributes, relationships, and revision identity.
* SPEC-0004 — Engineering Context Reconstruction Service consumes authoritative engineering information without replacing it.
* SPEC-0005 — Engineering Control Framework applies the authority model to engineering controls.
* SERVICE-0001 — EOS Core Services Catalog identifies services that consume records and produce derived outputs.

## Authority Foundation

### Origin and Delegation of Governance Authority

Engineering authority for the production Zeus environment originates solely
with Lawrence O'Neal. Principal `loneal` is the authenticated production
identity, and the Zeus CLI is the authoritative interface through which that
authority is exercised. Engineering Governance is a controlled function, not a
separate human or organizational authority.

The governing chain is:

```text
Lawrence O'Neal
        ↓
Authenticated principal loneal
        ↓
Zeus CLI
        ↓
Authority Resolution Runtime
        ↓
Repository-controlled governance and engineering records
        ↓
Authorized engineering execution and evidence
```

Repository-controlled records are the normal operational source of execution
authority. They derive their authority ultimately from Lawrence O'Neal and
operate within their document class and lifecycle state, but they do not
originate ultimate engineering authority.

No subordinate record, including this Engineering Decision Record, may establish a competing governance hierarchy or expand its own delegated authority.

### Bootstrap Authority

Bootstrap authority is defined by CHAR-0001 and historically documented by GEN-0001.

This decision preserves bootstrap authority by reference to CHAR-0001 and
SPEC-0011. Bootstrapping authorizes reconciliation of controlled documentation
when normal authority cannot be resolved. It does not bypass controlled
documentation or authorize operational execution. After reconciliation, Zeus
validates the repository and re-runs normal authority resolution.

## Two Distinct Forms of Authority

EOS distinguishes Governance Authority from Information Authority. The two concepts are related but are not interchangeable.

### Governance Authority

Governance Authority is the delegated authority to establish governance direction, approve controlled records and lifecycle transitions, authorize bounded work, establish baselines, and accept engineering outcomes.

Governance Authority flows through the Charter hierarchy and is exercised only by the roles and controlled mechanisms authorized by CHAR-0001 and POL-0001.

An implementation agent, engineering service, controlled record, repository, database, dashboard, or generated output does not acquire Governance Authority merely by storing, processing, or presenting authoritative information.

### Information Authority

Information Authority identifies the controlled record that owns a defined engineering fact, decision, requirement, state, or evidence item within its delegated scope.

Information Authority answers:

> Which controlled record is the authoritative source for this engineering information?

It does not answer:

> Who originates or exercises engineering governance authority?

A record possesses Information Authority only for the information assigned to it by the applicable governance, document architecture, and record relationships. Information Authority does not elevate a record within the governance hierarchy and does not authorize execution.

## Decision

EOS adopts the following Engineering Authority Model:

1. Governance Authority derives from Lawrence O'Neal and is exercised through authenticated principal `loneal`, the Zeus CLI, and CHAR-0001.
2. Repository-controlled records operate only within delegated authority and according to their document class and lifecycle state.
3. Each governed engineering fact shall have one authoritative information owner.
4. An Authoritative Engineering Record designation identifies that information owner; it does not create a governance tier.
5. Derived Engineering Views possess no Governance Authority or Information Authority and shall remain traceable to their authoritative sources.
6. Engineering information shall be changed through the controlled record that owns it and through the lifecycle and authorization mechanisms applicable to that record.
7. Authority resolution failures shall enter the Authority Restoration Principle defined by SPEC-0011 and shall return to normal controlled-document authority before execution.

## Information Authority Model

```text
Delegated Governance Authority
        ↓ establishes scope, controls, and authorization
Controlled Engineering Records
        ↓ assign one authoritative information owner per fact
Authoritative Engineering Information
        ↓ consumed without transfer of authority
Derived Engineering Views
```

The model does not place all Authoritative Engineering Records at one governance level. Policies, Standards, Specifications, Procedures, Engineering Work Orders, project records, evidence, and other controlled records retain the distinct roles and relationships assigned by the governing documentation architecture.

## Authoritative Engineering Records

### Designation

An Authoritative Engineering Record (AER) is a controlled record designated as the authoritative information source for defined engineering knowledge within its scope.

AER is an Information Authority designation. It is not:

* the origin of engineering authority;
* a governance role;
* a document class;
* a lifecycle state;
* a separate governance hierarchy;
* an authorization to execute engineering work.

A Policy and an Evidence Package may each be authoritative for different information while occupying different positions and serving different purposes within the documentation architecture. Their shared AER quality does not make them peers in Governance Authority.

### Required Properties

An AER shall possess, directly or through its controlled-document model:

* a unique identity;
* an accountable owner;
* a defined information scope;
* identifiable governing authority;
* lifecycle status;
* revision and historical traceability;
* relationships to governing and related records;
* validation or qualification status where applicable.

### Single Information Owner

Every governed engineering fact shall have one authoritative information owner.

Multiple controlled records may refer to the same fact, but only one shall own it. References, indexes, aggregates, and summaries shall identify or resolve to the owning record rather than silently duplicating its authority.

When two records appear to claim the same information, the conflict shall be resolved through the applicable governance and document-control process. A derived view shall never be used to resolve or override such a conflict.

### Lifecycle Effect

The `Draft` lifecycle semantics defined by STD-0001 remain applicable to this decision and to every other controlled record.

A Draft record is under development, is not authoritative, and shall not govern engineering execution. The `source_of_truth` metadata field identifies the intended repository source for the controlled record; it does not override Draft lifecycle status or activate the record.

Only an Active record may exercise the operational Information Authority assigned to its class and scope. Historical revisions remain reconstructable according to their lifecycle and persistence requirements but do not compete with the current Active revision.

## Derived Engineering Views

Derived Engineering Views present information obtained from one or more controlled engineering records for a particular audience, interface, or operational need.

Examples include:

* resume and recovery views;
* status reports;
* dashboards;
* validation summaries;
* AI-generated briefings;
* command-line output;
* published documentation generated from controlled sources;
* cached or indexed representations.

Derived Engineering Views may:

* summarize information;
* reorganize information;
* aggregate information;
* filter information;
* transform presentation;
* cache information for deterministic retrieval.

Derived Engineering Views shall:

* identify or preserve traceability to their authoritative sources;
* remain reproducible where the applicable service requires reproducibility;
* be refreshed or regenerated when source information changes;
* clearly disclose material scope, currency, or transformation limitations when needed to prevent misinterpretation.

Derived Engineering Views shall not:

* possess Governance Authority;
* possess Information Authority;
* become authoritative merely through publication, repetition, convenience, or operational use;
* replace the controlled record that owns the information;
* directly modify authoritative engineering information;
* require an independent manual truth-maintenance process;
* expand an Engineering Work Order or other authorization boundary.

If a derived output must become a governed source, it shall first be established as an appropriate controlled record through the authorized document lifecycle. Until that transition is approved and activated, it remains a view with no governing authority.

## Ownership and Traceability

Every controlled engineering record shall identify its governing and related records sufficiently to reconstruct its authority and information context.

Every derived view shall be traceable to one or more authoritative information sources.

Engineering implementation shall be traceable, as applicable, through:

* Lawrence O'Neal, principal `loneal`, the Zeus CLI, and the controlled Engineering Governance authority chain;
* CHAR-0001 and applicable subordinate governance;
* engineering decisions;
* specifications, standards, and procedures;
* the Active Engineering Work Order authorizing bounded execution;
* implementation evidence and validation records;
* qualification and baseline decisions.

Traceability does not transfer authority. Referencing an authoritative record allows a consumer to rely on its information within the record's scope; it does not make the consumer authoritative.

## Architectural Consequences

This decision enables:

* deterministic Engineering Context Reconstruction;
* resumable engineering activity;
* capture-once, publish-many information flows;
* automated publishing and dashboards;
* AI engineering assistance grounded in controlled records;
* validation automation;
* explicit ownership of engineering facts;
* reconstruction of governance, decisions, execution, and evidence without relying on human memory.

The model prevents a repository, service, interface, or generated output from becoming a competing governing authority. It also prevents the AER designation from flattening the controlled-document architecture into an alternative hierarchy.

Consistency among views depends upon source traceability, deterministic transformation, and timely regeneration. A view that is stale or incorrectly generated is defective; it does not become an alternate source of truth.

## Alternatives Considered

### Repository as Originating Authority

Rejected.

The repository is a governed system operating within delegated authority. Treating repository state as the origin of authority would conflict with CHAR-0001.

### AER as a Governance Hierarchy

Rejected.

AER identifies Information Authority. Treating it as a governance hierarchy would collapse distinct document classes and compete with the Charter-established delegation chain.

### Resume or Dashboard as Authority

Rejected.

Resume output and dashboards are derived views. They may aggregate authoritative information but possess no governing authority.

### AI Memory as Authority

Rejected.

AI-generated or retained context is a derived view unless separately established as a controlled record through an authorized lifecycle. Engineering knowledge must remain independently verifiable from governed records.

### Published Documentation as Independent Authority

Rejected.

Publication does not transfer Information Authority from the controlled source to a generated representation.

### Multiple Information Owners

Rejected.

Multiple owners for the same engineering fact create synchronization defects, ambiguous accountability, and unreliable automation.

## Status and Adoption

This revision remains Draft pending Engineering Governance review and an authorized lifecycle transition.

While Draft, it does not govern engineering execution and does not supersede any Active record. Its intended architectural consumers include:

* SPEC-0001 — Controlled Document Model;
* SPEC-0004 — Engineering Context Reconstruction Service;
* SPEC-0005 — Engineering Control Framework;
* SERVICE-0001 — EOS Core Services Catalog.

Upon activation, subordinate records and services within its scope shall conform to this authority model unless an authorized subsequent decision supersedes it.

## Decision Summary

Lawrence O'Neal exercises ultimate engineering authority through authenticated
principal `loneal` and the Zeus CLI. Engineering Governance is the controlled
function formalized by CHAR-0001.

Controlled records own engineering information only within their delegated scope.

AER identifies Information Authority, not a governance hierarchy.

Engineering tools and services generate traceable views.

Derived views never govern and never become authoritative by use alone.

## Revision History

| Version | Date | Description |
| ------- | ---- | ----------- |
| 1.0 | 2026-07-08 | Established the original single-source Authoritative Engineering Record and derived-view architecture. |
| 1.1 | 2026-07-10 | Reconciled Governance Authority, Information Authority, Charter delegation, Draft lifecycle semantics, related-record traceability, and derived-view constraints under the Gate B Governance Architecture Reconciliation. |
| 1.2 | 2026-07-26 | Reconciled the production authority hierarchy and authority-restoration model with CHAR-0001 and SPEC-0011. |
