---
document_id: STD-0001
title: Engineering Document Lifecycle Standard
version: 1.4
status: Active
owner: Engineering Governance
created: 2026-07-09
last_updated: 2026-07-15
phase: Governance Architecture Reconciliation
domain: Engineering Governance
classification: Engineering Standard
source_of_truth: true
predecessor_revision: STD-0001@1.3
successor_revision: null
approval_status: Approved
approval_authority: Engineering Governance
approval_reference: Codex Handoff Procedure - Engineering State Freshness Standard Implementation
approval_date: 2026-07-15
persistence_status: Pending
relationships:
  - type: governed_by
    target: CHAR-0001
  - type: conforms_to
    target: POL-0001
  - type: conforms_to
    target: STD-0000
  - type: implements
    target: EDR-0002
  - type: depends_on
    target: SPEC-0001
  - type: related_to
    target: GEN-0001
  - type: related_to
    target: STD-0002
  - type: related_to
    target: STD-0003
  - type: related_to
    target: STD-0004
  - type: related_to
    target: PROC-0001
  - type: indexed_by
    target: DOC-0001
  - type: authorized_by
    target: EWO-000011
  - type: authorized_by
    target: EWO-000012
declared_deferrals:
  - repository-wide-metadata-rollout
  - historical-locator-backfill
  - repository-wide-persistence-remediation
  - dependent-document-updates
tags:
  - governance
  - lifecycle
  - controlled-documents
  - engineering-standard
  - engineering-operating-system
---

# Engineering Document Lifecycle Standard

## Purpose

This standard defines the mandatory lifecycle behavior governing every controlled engineering document managed by the Engineering Operating System (EOS).

It establishes lifecycle states, transition rules, transition authority, transition evidence, responsibilities, stop conditions, and lifecycle compliance requirements.

This standard defines **when and under what authority** a controlled document changes lifecycle state. It consumes representation semantics from SPEC-0001 — Controlled Document Representation Specification and does not redefine metadata, approval, persistence, relationship, revision-lineage, or historical-reconstruction representations.

---

## Scope

This standard applies to every controlled engineering document governed by EOS, including:

* Charters and Genesis Governance Records;
* repository governance and indexes;
* policies, standards, specifications, procedures, and templates;
* Engineering Decision Records;
* Engineering Work Orders;
* Engineering Governance Findings and Resolutions;
* Evidence Packages and Completion Reports;
* project, infrastructure, service, asset, financial, milestone, validation, and other domain records.

This standard governs lifecycle behavior. It does not define document-class responsibilities, information ownership, persistence operations, repository placement, document templates, or execution procedures.

STD-0004 governs the operational Engineering Lifecycle and the freshness of
Engineering State across milestones, Project State, EOS, checkpoints, and
resume. That operational lifecycle is distinct from the controlled-document
lifecycle defined here. Reconciliation updates remain subject to this
standard's normal document lifecycle controls.

---

## Governing Context

### Authority Chain

Engineering authority originates with the Engineering Organization.

The Engineering Organization delegates governance responsibility to Engineering Governance. Engineering Governance exercises that delegated authority through CHAR-0001 — Engineering Charter and subordinate repository-controlled governance.

This standard is subordinate to CHAR-0001 and POL-0001 — Engineering Governance Policy and conforms to STD-0000 — Engineering Documentation Standard.

### Authority Terminology

Governance Authority and Information Authority have the meanings established by EDR-0002 — Engineering Authority Model and represented by SPEC-0001.

Lifecycle state does not originate or transfer either form of authority. It determines whether an approved controlled revision may exercise the authority or Information Authority assigned to its document class and delegated scope.

An Authoritative Engineering Record designation identifies Information Authority. It is not a lifecycle state and does not independently activate a record.

### Representation Boundary

SPEC-0001 governs representation of:

* lifecycle metadata;
* approval metadata;
* approval traceability and validation;
* persistence status and validation;
* typed relationships;
* revision identity and lineage;
* supersedence records;
* title and version semantics;
* immutable historical locators;
* deterministic reconstruction.

STD-0002 governs operational persistence, indexing, discovery, and integrity controls. PROC-0001 governs execution of an Active Engineering Work Order.

This standard consumes those models and controls without duplicating them.

---

## Lifecycle Principles

### Principle 1 — One Common Lifecycle

Every controlled engineering document shall occupy exactly one lifecycle state.

Every controlled document class uses the common lifecycle defined by this standard. No class may create a separate lifecycle or execution-authority state.

### Principle 2 — Controlled Transitions

Lifecycle transitions require Engineering Governance approval unless superior governance explicitly delegates transition authority.

No implementation agent, repository operation, metadata edit, Git commit, service, interface, or derived view may independently approve or perform a lifecycle transition.

### Principle 3 — Explicit Evidence

Every lifecycle transition shall be attributable and supported by approval and transition evidence represented in accordance with SPEC-0001.

### Principle 4 — Separation of States

Lifecycle state, approval state, and persistence state are independent engineering concepts.

* lifecycle state identifies operational position in the controlled lifecycle;
* approval state records governance disposition of content;
* persistence state records whether immutable repository evidence exists.

No one state shall be inferred solely from another.

### Principle 5 — Class-Scoped Authority

An Active record may exercise only the authority assigned to its document class and delegated scope.

Active status alone does not authorize engineering execution. Only an Active Engineering Work Order authorizes bounded engineering execution.

### Principle 6 — Stable Baselines

During an active engineering phase, the approved Governance Baseline remains frozen.

Governance improvements discovered during Mission Execution shall be recorded as Engineering Governance Findings and deferred until controlled review unless Engineering Governance authorizes correction of an execution-blocking defect.

### Principle 7 — Historical Integrity

Lifecycle transitions shall preserve revision history, decision provenance, and historical meaning. Missing persistence evidence shall be declared and remediated through authorized work; it shall never be fabricated.

---

## Common Lifecycle

EOS recognizes the following lifecycle states:

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

### Draft

Draft represents proposed engineering content under development.

A Draft may define proposed architecture, requirements, decisions, or procedures for evaluation, but it possesses no operational authority and shall not govern engineering execution.

Draft content may be reviewed, analyzed, validated, and revised within explicit authorization.

### Review

Review represents controlled governance evaluation of a complete proposed revision.

The content submitted for Review shall remain stable. Any material change returns the revision to Draft unless Engineering Governance explicitly authorizes another controlled review method.

Review possesses no operational authority.

### Approved

Approved represents content accepted by Engineering Governance.

Approval establishes governance disposition of the content but does not make the revision operationally authoritative, historically persisted, or authorized for engineering execution.

An Approved revision remains non-operational until Engineering Governance authorizes activation.

### Active

Active represents the current operational revision within the authority assigned to the document class and delegated scope.

Examples:

* an Active Policy establishes policy-level objectives and constraints;
* an Active Standard establishes mandatory engineering rules;
* an Active Specification establishes an approved model or architecture;
* an Active Procedure establishes an approved operational method;
* an Active Engineering Work Order authorizes bounded engineering execution;
* an Active index provides authoritative repository discovery without replacing indexed records.

Active status does not expand class responsibility or transfer authority. Only an Active Engineering Work Order authorizes execution.

An Active revision may have `persistence_status: Pending` only when explicit Engineering Governance authority permits activation while prohibiting or deferring commit. Pending persistence shall remain visible and blocks any claim that historical persistence or persistence qualification is complete.

### Superseded

Superseded represents a revision replaced by an approved and activated successor.

The superseded revision no longer governs current operations but retains the authority and historical meaning it possessed during its effective period.

Supersedence shall conform to the lineage, relationship, approval, persistence, and remediation representations defined by SPEC-0001.

### Archived

Archived represents a controlled record removed from operational use and retained for historical, legal, regulatory, or engineering purposes.

Archived records possess no operational authority. Archival shall preserve required identity, relationships, approval evidence, lifecycle evidence, and historical reconstruction information.

---

## Transition Rules

### Ordinary Transition Sequence

Ordinary transitions are:

1. Draft to Review;
2. Review to Approved;
3. Approved to Active;
4. Active to Superseded;
5. Superseded to Archived.

Each transition is a distinct governance action. Approval of content does not imply activation. Activation does not imply persistence completion. Persistence does not imply approval or activation.

### Exceptional Transitions

Engineering Governance may authorize an exceptional transition only through an explicit controlled decision that identifies:

* the source and destination states;
* the reason ordinary sequencing is unsuitable;
* the approving authority;
* the affected revision;
* the transition date;
* the governing authorization;
* the effect on relationships, persistence, baselines, and dependent records.

Exceptional transitions shall not fabricate missing historical states or evidence.

### Transition Preconditions

Before a transition, the responsible agent shall verify:

* the document and revision identity;
* the current lifecycle state;
* the requested destination state;
* authorized transition authority;
* approval evidence required for the destination;
* relationship and dependency effects;
* persistence status;
* applicable validation results;
* repository and index consistency;
* absence of a conflicting successor or transition.

### Transition Completion

A transition is complete only when:

* Engineering Governance approval is recorded;
* lifecycle metadata identifies the new state;
* approval metadata remains consistent;
* transition evidence identifies previous state, new state, authority, reference, and date;
* required relationships and indexes are synchronized or explicitly deferred;
* persistence status truthfully reflects observed repository evidence;
* required whole-document validation passes.

---

## Approval Requirements

Approval representation and validation are governed by SPEC-0001.

This standard requires:

* Draft and Review revisions to remain non-operational;
* Approved, Active, Superseded, and Archived revisions to possess attributable approval evidence;
* activation to reference an authorized lifecycle decision;
* rejected or withdrawn content never to be Active;
* approval authority to be traceable through superior governance;
* approval metadata never to be treated as self-authorizing.

An implementation agent may record authorized approval metadata but shall not originate the underlying approval.

---

## Persistence Requirements

Persistence representation and validation are governed by SPEC-0001. Operational persistence controls are governed by STD-0002.

This standard requires lifecycle decisions to use truthful persistence status:

* `Pending` means immutable persistence is not complete;
* `Persisted` requires a verified historical locator;
* `Legacy` identifies an explicitly registered pre-model record;
* `Remediation Required` identifies missing or invalid persistence evidence.

A lifecycle transition shall not silently change persistence status.

Activation with Pending persistence requires explicit Engineering Governance authority and shall disclose that persistence qualification remains incomplete.

Supersedence and archival shall not claim deterministic reconstruction when required locators are absent. Missing legacy evidence shall be explicitly classified or deferred.

---

## Supersedence Requirements

Engineering Governance alone approves supersedence unless superior governance explicitly delegates that authority.

Supersedence requires:

* one approved immediate successor;
* activation of the successor;
* identification of the predecessor and successor revision identities;
* a non-branching lineage;
* approval and transition evidence;
* successor discovery;
* truthful predecessor persistence status;
* a verified historical locator or explicit legacy-remediation disposition.

Supersedence changes current operational authority. It does not erase or retroactively invalidate the predecessor.

---

## Governance Baseline Controls

Only Active records may contribute operational authority to a Governance Baseline within their assigned class and scope.

Draft, Review, Approved, Superseded, and Archived revisions shall not govern current baseline execution.

A baseline shall identify the exact governing revisions and shall not silently substitute working-tree content, derived views, or later revisions.

Pending persistence may be accepted into an operational baseline only through explicit Engineering Governance disposition. Such a baseline shall not be declared persistence-qualified until required locators and repository controls are complete.

---

## Responsibilities

### Engineering Governance

Engineering Governance is responsible for:

* approving content dispositions;
* approving lifecycle transitions;
* activating controlled revisions;
* approving supersedence and archival;
* authorizing exceptional transitions;
* resolving lifecycle disputes;
* accepting or deferring persistence limitations;
* determining baseline eligibility and qualification.

### Document Owners

Document owners are responsible for:

* maintaining complete proposed revisions;
* identifying lifecycle and dependency effects;
* ensuring required validation is performed;
* presenting accurate approval, lifecycle, relationship, and persistence evidence;
* preserving historical integrity.

Document ownership does not independently grant transition authority.

### Implementation Agents

Implementation agents are responsible for:

* verifying authorization before acting;
* following the approved transition sequence;
* recording authorized metadata and evidence accurately;
* validating repository and relationship state;
* refusing unauthorized transitions;
* reporting uncertainty, inconsistency, and missing evidence;
* stopping when additional Governance Authority is required.

Implementation agents shall not approve content, activate records, infer authority, fabricate evidence, or conceal Pending or deficient persistence.

### Repository Index Owners

Index owners are responsible for synchronizing authoritative discovery with approved lifecycle transitions when separately authorized.

Indexes report lifecycle and discovery information but do not create lifecycle authority or replace controlled records.

---

## Transition Evidence Requirements

Every transition shall provide evidence sufficient to verify:

* permanent document identity;
* controlled revision identity;
* complete publication reviewed;
* previous and new lifecycle states;
* approval status;
* approving authority;
* approval and transition reference;
* transition date;
* validation outcome;
* relationship and dependency effects;
* persistence status;
* index and repository effects;
* scope compliance.

Evidence shall be objective, reproducible, attributable, traceable, and represented in accordance with SPEC-0001.

---

## Stop Conditions

Lifecycle processing shall stop when:

* document or revision identity is ambiguous;
* current lifecycle state cannot be established;
* transition authority cannot be verified;
* approval evidence is missing or conflicting;
* a proposed transition violates the ordinary sequence without authorized exception;
* a competing successor exists;
* required whole-document validation fails;
* persistence status is false or cannot be established;
* relationships or indexes conflict materially;
* repository integrity is compromised;
* the requested action exceeds granted authority.

The responsible agent shall report the observation, evidence, lifecycle impact, and required governance decision. No transition shall proceed until authorized resolution.

---

## Relationship to Other Governing Records

* CHAR-0001 — Engineering Charter establishes the superior authority chain.
* POL-0001 — Engineering Governance Policy establishes governance objectives, responsibilities, baselines, and change control.
* EDR-0002 — Engineering Authority Model distinguishes Governance Authority, Information Authority, AER, and derived views.
* STD-0000 — Engineering Documentation Standard assigns lifecycle responsibility to this Standard and representation responsibility to SPEC-0001.
* SPEC-0001 — Controlled Document Representation Specification defines metadata, approval, persistence, relationship, lineage, title, supersedence, reconstruction, and validation representations.
* STD-0002 — Engineering Document Persistence Standard defines operational persistence, indexing, discovery, and integrity controls.
* STD-0003 — Engineering Work Order Standard defines mandatory EWO content.
* PROC-0001 — Engineering Work Order Execution Procedure defines execution of Active Engineering Work Orders.

---

## Compliance

A controlled lifecycle is compliant when:

* exactly one allowed lifecycle state is assigned;
* current state and transition history agree;
* transition sequence is ordinary or explicitly excepted;
* transition authority and approval evidence are attributable;
* approval, lifecycle, and persistence states are independently represented and mutually consistent;
* Active authority remains within document-class responsibility and delegated scope;
* only an Active Engineering Work Order authorizes engineering execution;
* relationships and dependent records are validated or explicitly deferred;
* supersedence and archival preserve historical meaning;
* persistence claims match verified repository evidence;
* required transition and whole-document validation passes;
* repository discovery agrees or an authorized synchronization deferral is recorded.

Legacy records remain valid under SPEC-0001 backward-compatibility controls until separately revised. Missing historical persistence shall be declared rather than fabricated.

---

## Success Criteria

This standard is complete when engineers and implementation agents can determine, without undocumented knowledge:

* the lifecycle state of a controlled revision;
* the authority required for transition;
* the evidence required for transition;
* the distinction among lifecycle, approval, and persistence;
* the operational authority assigned to each state and document class;
* when execution must stop;
* how lifecycle history remains traceable.

---

## Self-Conformance of STD-0001 Version 1.3

This revision conforms to the lifecycle and representation architecture as follows:

* it is one complete controlled revision;
* identity, revision, approval, persistence, relationships, and deferrals are represented according to SPEC-0001;
* its Active state is supported by the approved transitional implementation authority;
* approval is attributed to Engineering Governance;
* persistence is truthfully `Pending` because this mission prohibits commit and publication;
* no immutable locator is claimed;
* historical locator backfill for Versions 1.1–1.2 is explicitly deferred;
* lifecycle policy remains in this Standard while representation remains in SPEC-0001;
* dependent-document synchronization is explicitly deferred;
* current governing titles and relationships are used.

Version 1.3 is operationally Active but not historically persisted. Persistence qualification requires separately authorized repository work.

---

## Revision History

| Version | Date | Description |
| ------- | ---- | ----------- |
| 1.0 | 2026-07-09 | Initial Engineering Document Lifecycle Standard established. |
| 1.1 | 2026-07-10 | Established Active as the common execution-authority lifecycle state for every controlled document class under EWO-000012. |
| 1.2 | 2026-07-10 | Referenced the revision-lineage, supersedence, and historical-persistence representation in SPEC-0001 instead of duplicating architectural definitions under EWO-000011 Revision 2. |
| 1.3 | 2026-07-11 | Reconciled delegated authority, class-scoped Active authority, EWO execution authority, lifecycle/approval/persistence separation, transition evidence, compliance, current governing titles, and SPEC-0001 representation consumption. |
| 1.4 | 2026-07-15 | Distinguished the controlled-document lifecycle from the STD-0004 operational Engineering Lifecycle and required reconciliation revisions to retain normal lifecycle controls. |

---

## Lifecycle Transition History

| Revision | Date | Previous State | New State | Authority |
| --- | --- | --- | --- | --- |
| STD-0001@1.3 | 2026-07-11 | Draft | Review | EGR-000001 — current ratification of the completed transitional revision |
| STD-0001@1.3 | 2026-07-13 | Review | Approved | EGR-000001 |
| STD-0001@1.3 | 2026-07-13 | Approved | Active | EGR-000001 |
| STD-0001@1.4 | 2026-07-15 | Draft | Review | Codex Handoff Procedure - Engineering State Freshness Standard Implementation |
| STD-0001@1.4 | 2026-07-15 | Review | Approved | Codex Handoff Procedure - Engineering State Freshness Standard Implementation |
| STD-0001@1.4 | 2026-07-15 | Approved | Active | Codex Handoff Procedure - Engineering State Freshness Standard Implementation |
