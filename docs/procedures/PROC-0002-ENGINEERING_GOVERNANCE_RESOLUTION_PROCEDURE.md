---
document_id: PROC-0002
title: Engineering Governance Resolution Procedure
version: 1.1
status: Active
owner: Engineering Governance
created: 2026-07-13
last_updated: 2026-07-17
phase: Governance Framework Modernization
domain: Engineering Governance
classification: Engineering Procedure
predecessor_revision: PROC-0002@1.0
successor_revision: null
approval_status: Approved
approval_authority: Engineering Governance
approval_reference: EGR-000002
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
  - type: implements
    target: STD-0000
  - type: conforms_to
    target: STD-0001
  - type: conforms_to
    target: STD-0002
  - type: conforms_to
    target: SPEC-0001
  - type: constrains
    target: TPL-0004
  - type: indexed_by
    target: DOC-0001
tags:
  - governance
  - procedure
  - engineering-governance-resolution
  - controlled-decisions
  - lifecycle
  - engineering-operating-system
---

# Engineering Governance Resolution Procedure

## Purpose

This procedure defines the approved repeatable method for preparing, reviewing, approving, activating, superseding, and archiving an Engineering Governance Resolution within the Engineering Operating System.

It implements the EGR record architecture established by STD-0000. It does not originate Governance Authority, select a governance disposition, redefine lifecycle requirements, or authorize engineering execution.

---

## Scope

This procedure applies whenever Engineering Governance records an authoritative disposition concerning an Engineering Governance Finding or other governance proposal through an EGR.

It applies to Resolutions concerning completed engineering outcomes, controlled document revisions, governance changes, lifecycle transitions, baseline effects, deferrals, rejections, and supersedence within the scope defined by STD-0000.

---

## Governing Records

EGR preparation and lifecycle operations shall conform to:

* CHAR-0001 — Engineering Charter;
* POL-0001 — Engineering Governance Policy;
* STD-0000 — Engineering Documentation Standard;
* STD-0001 — Engineering Document Lifecycle Standard;
* STD-0002 — Engineering Document Persistence Standard;
* SPEC-0001 — Controlled Document Representation Specification; and
* TPL-0004 — Engineering Governance Resolution Template.

---

## Roles and Authority

### Engineering Governance

Engineering Governance:

* determines the governance disposition;
* approves or rejects EGR content;
* authorizes lifecycle transitions;
* defines the exact decision scope and authorized effects;
* accepts or defers disclosed persistence and indexing limitations; and
* approves supersedence and archival.

### Resolution Preparer

The authorized Resolution preparer:

* inventories the decision subject and applicable evidence;
* prepares a complete EGR publication using TPL-0004;
* records only decisions actually made by Engineering Governance;
* validates identity, metadata, relationships, scope, and lifecycle consistency;
* preserves staged, unstaged, historical, and unrelated work; and
* stops when authority, evidence, identity, or disposition is unresolved.

The preparer shall not infer Engineering Governance intent, choose a disposition, expand scope, approve the EGR, activate it, or perform downstream engineering execution without separate authority.

### Repository Index Owner

The repository index owner assigns or verifies the permanent EGR identifier, registers its canonical location and current revision, and preserves discovery of historical revisions. Index registration provides discovery and does not create or expand the Resolution's authority.

---

## Procedure Preconditions

Before EGR creation begins, verify:

* repository identity and integrity;
* absence of an active conflicting Git or lifecycle operation;
* explicit authority to prepare the Resolution;
* the governance question or proposal requiring disposition;
* exact identity and revision of every affected controlled record;
* availability of material evidence and review records;
* absence of a competing Resolution or successor addressing the same decision scope;
* the applicable Governance Baseline; and
* the required repository index and validation entry points.

If a required precondition cannot be verified, stop and report the missing evidence or authority.

---

## Resolution Workflow

```text
Authority and Subject Verification
        ↓
Evidence and Relationship Inventory
        ↓
Permanent Identifier Assignment
        ↓
Complete Draft Resolution
        ↓
Whole-Document Validation
        ↓
Engineering Governance Review
        ↓
Governance Approval
        ↓
Lifecycle Activation
        ↓
Index and Traceability Synchronization
        ↓
Authorized Follow-up Work
```

Approval and activation are separate governance actions. Follow-up work begins only when separately authorized.

---

## Step 1 — Verify Authority and Decision Subject

Identify the controlled authority permitting preparation of the EGR. Preparation authority may arise from an Active EWO, superior governance, or another explicit controlled authorization mechanism.

Record the decision subject precisely. When the subject is a controlled document revision, identify its permanent `document_id` and exact version. When the subject is completed engineering execution, identify the governing EWO and applicable Completion Report and Evidence Package.

Do not create a Resolution for an unidentified proposal, unresolved revision, or assumed decision.

---

## Step 2 — Inventory Evidence and Relationships

Read the complete current controlled records relevant to the decision and inventory:

* the governing baseline;
* the Finding or governance proposal;
* affected document revisions;
* governing EWOs;
* Completion Reports;
* Evidence Packages;
* validation and qualification results;
* existing Resolutions; and
* dependent records and baseline effects.

Classify each relationship using SPEC-0001. Evidence supports review but does not approve its own acceptance.

---

## Step 3 — Assign the Permanent Identifier

Obtain the next valid permanent EGR identifier through the authoritative repository index's registered numbering process.

Verify that the identifier:

* begins with the `EGR-` class prefix;
* is unique across current, historical, staged, unstaged, and untracked records;
* is not reserved for another record; and
* is represented identically in metadata, title references, relationships, filename, and index registration.

Do not infer the next identifier or reuse an identifier.

---

## Step 4 — Prepare the Complete Draft

Instantiate TPL-0004 as one complete controlled publication.

The Draft shall include every element required by STD-0000 and SPEC-0001. Proposed disposition text shall remain visibly proposed until Engineering Governance makes the decision. The Draft shall not claim Approved or Active status and shall not claim authority over another record.

Partially populated or piecemeal EGR publications shall not enter Review.

---

## Step 5 — Validate the Draft

Before Review, validate:

* YAML and complete publication structure;
* permanent identity and revision lineage;
* lifecycle, approval, and persistence metadata;
* governing authority;
* exact decision subject and affected revisions;
* evidence references;
* relationship types, direction, targets, and cardinality;
* disposition, scope, rationale, and authorized effects;
* identifier uniqueness and canonical placement;
* index consistency or explicit registration deferral;
* absence of unresolved implementation placeholders; and
* absence of conflicting or circular authority.

Validation failure returns the record to Draft and blocks governance review.

---

## Step 6 — Conduct Engineering Governance Review

Submit the complete stable Draft and its validation evidence to Engineering Governance.

Engineering Governance shall review:

* the decision question;
* evidence sufficiency;
* proposed disposition;
* decision scope;
* affected records and revisions;
* authority and lifecycle effects;
* implementation prerequisites;
* persistence and index state;
* dependent-record effects; and
* historical consequences.

A material content change returns the EGR to Draft unless Engineering Governance explicitly authorizes another controlled review method.

---

## Step 7 — Record Governance Approval and Disposition

Engineering Governance determines the EGR disposition as Accepted, Rejected, Deferred, or Superseded and records the exact scope, rationale, approving authority, and decision date.

The EGR publication's `approval_status` records Engineering Governance's disposition of the EGR content. It is distinct from the Resolution's disposition concerning its subject. An EGR that records rejection or deferral of its subject may itself be Approved.

Approval metadata shall identify the controlled approval reference or explicitly approved transitional authority that records the approval action. Metadata shall not be treated as self-authorizing.

If Engineering Governance rejects the EGR publication or requires revision, it shall not proceed to activation.

---

## Step 8 — Activate the Resolution

After content approval, Engineering Governance may authorize the Approved-to-Active transition.

Before activation, verify:

* approval evidence is attributable;
* the final disposition and decision scope are stable;
* the activation authority and date are recorded;
* required relationships resolve;
* index synchronization is complete or explicitly deferred;
* persistence status is truthful; and
* all required whole-document validation passes.

Only the Active EGR exercises the governance effect assigned to its class and explicit scope. Active EGR status does not authorize engineering execution.

---

## Step 9 — Synchronize Traceability and Discovery

Synchronize or explicitly defer:

* authoritative index registration;
* affected-record approval references;
* relationship inverses where represented;
* baseline eligibility and qualification records;
* lifecycle-transition history;
* Completion Report governance references; and
* follow-up implementation or validation records.

An EGR shall not be represented as registered, persisted, or reference-ready until the corresponding evidence exists.

---

## Step 10 — Authorize and Execute Follow-up Work

An Active EGR may authorize governance changes or identify required follow-up within its decision scope. It does not perform those changes.

Any document revision, repository update, runtime change, or other engineering execution required to implement the Resolution shall occur under an Active EWO or superior controlled execution authority. The follow-up work shall preserve the EGR as its approval or authorization reference when applicable.

---

## Supersedence

When a governance decision changes, Engineering Governance shall determine whether a new EGR revision or a successor EGR is required under SPEC-0001 lineage rules.

A successor that replaces a prior Resolution shall:

* identify the predecessor EGR and exact revision;
* state which disposition or scope is replaced;
* preserve unaffected historical meaning;
* use the required `supersedes` relationship;
* receive independent approval and activation; and
* transition the predecessor to Superseded only as part of the authorized decision.

The prior EGR shall not be rewritten to express the later decision.

---

## Archival

An EGR may transition from Superseded to Archived only through Engineering Governance approval.

Archival shall preserve:

* complete decision content;
* original authority and approval evidence;
* effective period;
* relationships and affected revisions;
* supersedence history;
* immutable persistence locators when available; and
* deterministic discovery through the authoritative index.

Archived status removes the EGR from current operational use but does not erase its historical effect.

---

## Stop Conditions

Stop and report when:

* preparation or transition authority is missing;
* Engineering Governance disposition is unresolved;
* the decision subject or affected revision cannot be identified;
* material evidence is missing or contradictory;
* a competing EGR or successor exists;
* the permanent identifier cannot be assigned deterministically;
* required relationships cannot be resolved;
* lifecycle, approval, or persistence state is inconsistent;
* the proposed decision would exceed delegated authority;
* activation would imply unauthorized engineering execution;
* historical meaning would be overwritten; or
* validation fails.

No EGR lifecycle transition or follow-up work shall proceed until the stop condition is resolved through authorized governance.

---

## Compliance

An EGR operation complies with this procedure when:

* one complete EGR publication represents the decision;
* the record conforms to STD-0000 and SPEC-0001;
* the common lifecycle and transition evidence conform to STD-0001;
* persistence and discovery claims conform to STD-0002;
* Governance Authority remains with Engineering Governance;
* execution authority remains with an Active EWO or superior controlled authority;
* relationships and affected revisions are traceable;
* historical decisions remain reconstructable; and
* every validation and synchronization gate passes or is explicitly deferred by Engineering Governance.

---

## Success Criteria

This procedure is complete when an authorized preparer can create and advance an EGR deterministically from verified decision subject and evidence through Engineering Governance review, approval, activation, traceability synchronization, supersedence, and archival without inferring authority or expanding governance scope.

---

## Holistic Governance Reconciliation Review

When an EGR approves a governance improvement, the Resolution shall identify
the complete affected governance subsystem and state whether the authority is
explicitly limited. Unless limited, follow-up implementation shall reconcile
every directly affected standard, specification, procedure, template, index,
lifecycle relationship, planning record, and derived operational view.

Engineering Governance review shall reject silent corrections, intentionally
inconsistent partial updates, and completion claims made before governance
architecture validation and the mandatory Governance Conformance Review.
Any deferral shall identify the exact record, dependency, reason, impact, and
required follow-up EWO.

## Revision History

| Version | Date | Description |
| ------- | ---- | ----------- |
| 1.0 | 2026-07-13 | Established the Engineering Governance Resolution creation, review, approval, activation, traceability, supersedence, archival, and execution-boundary procedure. |
| 1.1 | 2026-07-17 | Required holistic affected-subsystem reconciliation, explicit deferrals, architecture validation, and Governance Conformance Review under EGR-000002 and EWO-000018. |
