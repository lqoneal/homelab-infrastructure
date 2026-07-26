---
document_id: PROC-0004
title: Engineering Handoff Construction Procedure
version: 1.4
status: Active
owner: Engineering Governance
created: 2026-07-18
last_updated: 2026-07-18
phase: Governance Stabilization Procedure Integration
domain: Engineering Governance
classification: Engineering Procedure
predecessor_revision: PROC-0004@1.3
successor_revision: null
approval_status: Approved
approval_authority: Engineering Governance
approval_reference: EGR-000006
approval_date: 2026-07-18
persistence_status: Persisted
source_of_truth: true
declared_deferrals:
  - automated-handoff-construction
  - egas-ekrs-emls-orchestration-integration
relationships:
  - type: governed_by
    target: CHAR-0001
  - type: conforms_to
    target: POL-0001
  - type: conforms_to
    target: STD-0000
  - type: conforms_to
    target: STD-0001
  - type: conforms_to
    target: STD-0002
  - type: conforms_to
    target: STD-0003
  - type: conforms_to
    target: STD-0004
  - type: related_to
    target: PROC-0001
  - type: related_to
    target: PROC-0005
  - type: related_to
    target: PROC-0006
  - type: related_to
    target: PROC-0007
  - type: depends_on
    target: TPL-0001
  - type: related_to
    target: TPL-0002
  - type: related_to
    target: EDR-0002
  - type: related_to
    target: SPEC-0007
  - type: depends_on
    target: SPEC-0008
  - type: indexed_by
    target: DOC-0001
tags:
  - governance
  - procedure
  - handoff
  - authorization-kernel
  - authority-preservation
  - construction
---

# Engineering Handoff Construction Procedure

## Purpose

This procedure is the single authoritative owner of converting Engineering
Governance intent into a complete Engineering Work Order. During Transitional
Engineering Handoff Governance, an Engineering Handoff issued by Engineering
Governance is the approved initiating directive. An Engineering Authorization
Kernel may be embedded in or referenced by that Handoff as structured input;
it is not a separate constitutional prerequisite.

Construction preserves Governance authority; it does not originate, expand, or
activate that authority. PROC-0001 governs execution only after Engineering
Governance has approved and activated the completed Engineering Work Order.

## Scope

This procedure governs:

- Governance-issued Handoff intake and, when present, Authorization Kernel intake;
- repository and engineering-context reconstruction;
- controlled-document discovery and authority resolution;
- inheritance, precedence, and reference insertion;
- deterministic and judgment-based template population;
- structural, semantic, and Authority Preservation Validation; and
- submission of the constructed handoff for Engineering Governance review.

It does not govern execution, Completion Report production, Governance
approval decisions, lifecycle activation, or future platform-service
implementation.

## Responsibility Matrix

| Responsibility | Authoritative owner | Construction treatment |
| --- | --- | --- |
| Mission authorization, purpose, and expected outcome | Engineering Governance through the Governance-issued Handoff | Preserve without expansion |
| Scope, authority ceiling, prohibitions, exceptions, risk, publication authority, and certification | Engineering Governance through the Governance-issued Handoff | Preserve without expansion; non-delegable |
| Normative Engineering Work Order semantics | STD-0003 | Resolve and reference |
| Handoff construction workflow | PROC-0004 | Apply this procedure |
| Reusable handoff structure | TPL-0001 | Instantiate; do not treat as procedural authority |
| Engineering Work Order execution | PROC-0001 | Begins only after Active lifecycle verification |
| Controlled document publication workflow | PROC-0005 | Resolve and insert when the Kernel authorizes controlled publication; do not treat as publication authority |
| Governance qualification workflow | PROC-0006 | Resolve and insert when the Kernel requires Governance qualification; preserve external decision authority |
| Governance stabilization orchestration | PROC-0007 | Resolve and insert when the Kernel requires Governance subsystem reconciliation; preserve all external owners |
| Lifecycle and persistence | STD-0001 and STD-0002 | Resolve and apply |
| Engineering State, checkpoint, and resume freshness | STD-0004 | Resolve and apply |
| Completion Report structure | TPL-0002 | Reference for the execution deliverable |
| Controlled-document and technical facts | Their authoritative controlled owners | Reference current applicable records |
| Final approval and activation | Engineering Governance | Construction terminates at approval or rejection |

## Engineering Authorization Kernel

### Definition

The Engineering Authorization Kernel is an optional structured representation
of Governance-authored content used during EWO construction. During
Transitional Engineering Handoff Governance, the Governance-issued Handoff is
the required initiating input and may itself contain every Kernel field. A
separate Kernel shall not be required when the Handoff is complete. Neither a
Kernel nor a Handoff is an Engineering Work Order or execution authority.

The Kernel shall identify:

1. mission identity;
2. mission purpose;
3. expected outcome;
4. approved scope;
5. authority ceiling;
6. explicit prohibitions;
7. approved exceptions, or `None`;
8. required deliverables;
9. success and acceptance criteria;
10. publication authority; and
11. the exact final certification question and allowed answer set.

The Handoff, or an incorporated Kernel, shall also carry its Governance issuer
identity, date, and authoritative locator. Missing required content blocks EWO
construction unless Engineering Governance supplies clarification.

### Content Boundary

Engineering Governance authors and owns Handoff and Kernel content. The Operational
Engineer may normalize formatting, resolve identifiers, insert authoritative
references, clarify non-substantive wording, and narrow an execution boundary
to preserve the stated ceiling. The Operational Engineer shall not originate
or materially reinterpret Kernel authority.

## Construction Lifecycle

The construction lifecycle is:

```text
Engineering Governance Authorization
        -> Governance-issued Engineering Handoff
        -> optional embedded or referenced Authorization Kernel
        -> Operational Engineer EWO Construction
        -> Engineering Governance Review
        -> Approved Active Engineering Work Order or Rejection
```

Construction terminates when Engineering Governance approves or rejects the
submitted handoff. Execution and Completion Report production are outside this
procedure.

## Construction Sequence

### Step 1 — Governance-Issued Handoff Intake

Record the Handoff locator and verify its Governance issuer, completeness, and
internal consistency. When a Kernel is present, record its locator and verify
that it agrees with the Handoff. Do not require a separate Kernel during the
transitional period and do not begin assembly from conversation history,
unpublished notes, or an unattributable summary.

Resolve the Kernel's explicit Engineering Transaction Profile selection when
present. During the initial baseline pilot, selection shall be explicit; a
profile creates no default and conveys no authority.

### Step 2 — Repository Context Reconstruction

Resolve the canonical repository, current branch and commit, DOC-0001, Project
State, current mission state, Work Registry references, EOS operational state,
and applicable checkpoint. Apply STD-0004 freshness and conflict rules.

### Step 3 — Controlled-Document Discovery

Discover all governing and transaction-specific records using authoritative
indexes and repository locators. Discovery output is a navigation aid and
does not replace the controlled record it resolves.

### Step 4 — Authority Resolution

Resolve the authority chain from CHAR-0001 through the Governance-issued
Handoff and then through applicable policy, standards, procedures,
specifications, Governance decisions, and any Kernel. Confirm that the Handoff
issuer has the authority represented and that no
subordinate or derived record is being used to originate Governance authority.

### Step 5 — Scope and Inheritance Resolution

Map the Handoff scope and any incorporated Kernel scope, authority ceiling, prohibitions, exceptions,
dependencies, deliverables, success criteria, publication authority, and
certification into TPL-0001 fields. Inherit reusable behavior only through its
authoritative owner. Do not inherit authority from context, precedent, a prior
Work Order, Project State, the Work Registry, EOS, or automation output.

When an ETP is selected, apply SPEC-0008. Require exactly one Active compatible
profile, resolve every component owner and revision, and fail closed for no
match, multiple matches, inactive state, missing references, incompatibility,
or a prohibited override. PROC-0004 consumes and validates profiles; SPEC-0008
owns their model and compatibility semantics.

When the Handoff or its incorporated Kernel authorizes controlled document publication, resolve PROC-0005
and include its common publication workflow, evidence, boundary, and
verification obligations in the constructed handoff. Preserve PROC-0001 as the
execution owner and the applicable standards and specifications as requirement
owners. PROC-0005 supplies no publication or lifecycle authority.

When the Handoff or its incorporated Kernel requires Governance qualification, resolve PROC-0006 and
include its invocation, evidence, stage, result, and caller-return obligations.
PROC-0006 supplies no Governance decision, lifecycle, publication, baseline,
or implementation authority.

When the Handoff or its incorporated Kernel requires Governance stabilization, resolve PROC-0007 and
include its authorization, baseline, inventory, dependency, coordination,
external-qualification, routing, state-separation, and closeout obligations.
PROC-0007 supplies no execution, qualification, Governance decision,
publication, baseline-designation, or implementation authority.

### Step 6 — TPL-0001 Structural Assembly

Instantiate the current Active TPL-0001 revision. Preserve its section order
and populate every required field. Use `None` or `Not Applicable` with a short
rationale when permitted; do not silently omit mandatory sections.

### Step 7 — Deterministic Population

Populate mechanically resolvable content, including identifiers, approved
revisions, repository locators, standard references, current state facts,
section ordering, dependencies, and an existing validation or publication
profile selected by unambiguous controlled rules.

For ETP-driven construction, populate the selected identity and revision,
selection-authority locator, resolved component versions, permitted additions,
compatibility result, and deterministic manifest fingerprint or locator. The
frozen manifest becomes part of the submitted EWO revision.

### Step 8 — Engineering Judgment Additions

The Operational Engineer may add bounded technical detail necessary to make
the authorized transaction executable, testable, and traceable. Judgment may
clarify sequencing, dependencies, evidence, validation additions, and stop or
resume additions, but may not change the Kernel.

Any ambiguity that could change authority, scope, risk, exception treatment,
publication authority, acceptance, or certification shall be returned to
Engineering Governance for disposition.

### Step 9 — Structural Validation

Verify metadata, identifier, lifecycle readiness, TPL-0001 completeness,
required section presence and order, reference syntax, and repository locator
resolution.

### Step 10 — Semantic Validation

Verify that each requirement has one authoritative owner, all references
resolve to applicable controlled records, constructed instructions are
consistent, reusable procedures have not been duplicated, and the handoff is
sufficient for deterministic execution and resume.

For ETP-driven construction, also verify lifecycle, unique selection,
component compatibility, permitted additions, prohibited overrides, and
resolved-manifest completeness. Failure or ambiguity blocks submission.

### Step 11 — Authority Preservation Validation

Execute the mandatory gate defined below. A failure blocks submission as an
approvable handoff and requires correction or Governance disposition.

### Step 12 — Submission for Governance Approval

Submit the completed handoff, Kernel locator, resolved-reference inventory,
validation results, ambiguities and dispositions, and Authority Preservation
Validation result to Engineering Governance. Engineering Governance alone may
approve, reject, require revision, or activate the Engineering Work Order.

## Controlled Document Resolution Model

### Resolution Order

Resolve applicable records in this order:

1. CHAR-0001;
2. POL-0001;
3. STD-0000 and EDR-0002;
4. applicable Active standards;
5. applicable Active procedures;
6. approved specifications and baselines within their maturity limits;
7. the Governance-issued Engineering Handoff, any incorporated Engineering Authorization Kernel, and related Governance decisions;
8. current Project State, mission records, and authoritative technical owners;
9. Work Registry and EOS records within their declared information boundaries;
10. the current Active TPL-0001 revision; and
11. transaction-specific controlled references.

TPL-0002 is resolved as the structural owner of the later Completion Report;
it does not govern handoff construction.

### Precedence and Revision Selection

- Superior governing authority prevails over subordinate authority.
- The current approved applicable revision prevails over an older revision.
- A newer supported authoritative state record prevails over an older
  checkpoint or derived view.
- A transaction-specific requirement may narrow a general behavior but shall
  not silently override a superior requirement.
- An exception applies only when the Kernel supplies its explicit Governance
  approval and scope.
- Historical records remain evidence and shall not be rewritten to match the
  current construction model.

### Conflict and Ambiguity Handling

Report and stop for Governance disposition when:

- authoritative owners conflict;
- no authoritative owner resolves;
- revision applicability is indeterminate;
- the Kernel conflicts with a superior authority;
- an exception lacks explicit approval;
- state freshness blocks reliable construction; or
- a choice could materially alter authority, scope, risk, or acceptance.

References shall replace copied procedural language wherever the referenced
record provides the reusable behavior. A reference transfers neither
Governance Authority nor Information Authority.

## Authority Preservation Validation

Authority Preservation Validation is mandatory before submission. Compare the
constructed EWO directly with the Governance-issued Handoff and, when present,
the Authorization Kernel, and verify that
construction has not:

- broadened authority;
- enlarged scope;
- removed or weakened a prohibition or limitation;
- accepted additional risk;
- introduced an unauthorized exception;
- enlarged publication authority;
- changed acceptance or certification; or
- converted a derived fact or prior precedent into authority.

Construction may preserve authority, narrow authority, clarify wording,
resolve references, and derive deterministic information. Any material change
to authorization requires a revised or supplemental Kernel from Engineering
Governance.

The validation record shall identify:

- Handoff locator and identity, plus any Kernel locator and identity;
- constructed handoff identity and revision;
- field-by-field authority and scope comparison;
- every narrowing or clarification;
- every exception and its approval locator;
- unresolved ambiguity; and
- one result: `PRESERVED` or `NOT PRESERVED`.

Only `PRESERVED` is eligible for Governance approval. This result does not
approve or activate the Engineering Work Order.

When an ETP is used, compare both the handoff and its frozen manifest with the
Kernel. Neither selection nor component resolution may change Governance-owned
content or enlarge transaction effects.

## Operational Engineer Responsibilities

The Operational Engineer shall:

- verify and intake the Kernel;
- reconstruct current authoritative context;
- resolve applicable controlled documentation;
- instantiate and populate TPL-0001;
- distinguish deterministic facts from engineering judgment;
- identify ambiguity, conflict, and missing authority;
- request Governance clarification where required;
- perform construction validation; and
- prepare the completed handoff for Governance approval.

The Operational Engineer shall not originate Governance authority, approve
scope or exceptions, accept risk, activate a Work Order, or issue final
certification.

## Engineering Governance Responsibilities

Engineering Governance retains exclusive, non-delegable responsibility for:

- mission authorization;
- scope and authority approval;
- exception approval;
- risk acceptance;
- publication authority;
- disposition of material ambiguity or conflict;
- final approval or rejection; and
- Engineering Work Order lifecycle activation.

## Automation Boundary

Future Engineering Platform services may assist deterministically with
document discovery, revision resolution, reference insertion, template
population, metadata generation, state reconstruction, dependency discovery,
structural validation, and lifecycle verification after their specifications
and implementations are separately authorized and qualified.

Automation shall not approve scope, grant authority, accept risk, approve
exceptions, activate an Engineering Work Order, issue final certification, or
silently resolve material ambiguity. EGAS, EKRS, EMLS, and orchestration
integration remains deferred and is not implemented by this procedure.

## Submission Package

The submission package shall contain:

1. the completed Engineering Work Order;
2. the authoritative Kernel locator;
3. the resolved controlled-document inventory;
4. structural and semantic validation results;
5. the Authority Preservation Validation record;
6. ambiguities and their Governance dispositions; and
7. any transaction-specific evidence required for approval.

## Completion Criteria

Construction is complete only when the submission package is complete and
Engineering Governance has issued an approval or rejection. Approval does not
authorize execution until the Engineering Work Order is in the Active
lifecycle state under STD-0001 and STD-0003.

## References

- CHAR-0001 — Engineering Charter
- POL-0001 — Engineering Governance Policy
- STD-0000 — Engineering Governance Documentation Architecture
- STD-0001 — Engineering Document Lifecycle Standard
- STD-0002 — Engineering Document Persistence Standard
- STD-0003 — Engineering Work Order Standard
- STD-0004 — Engineering State Freshness Standard
- PROC-0001 — Engineering Work Order Execution Procedure
- PROC-0005 — Controlled Document Publication Procedure
- PROC-0006 — Governance Qualification Procedure
- PROC-0007 — Governance Stabilization Procedure
- TPL-0001 — Engineering Work Order Template
- TPL-0002 — Completion Report Template
- EDR-0002 — Engineering Authority Model
- SPEC-0007 — Engineering Platform Construction Specification
- SPEC-0008 — Engineering Transaction Profile Specification

## Revision History

| Version | Date | Description |
| --- | --- | --- |
| 1.0 | 2026-07-18 | Established the authoritative Engineering Handoff construction procedure, Authorization Kernel, resolution and inheritance model, Authority Preservation Validation, responsibility boundary, and bounded automation interface. |
| 1.1 | 2026-07-18 | Integrated explicit ETP consumption, deterministic fail-closed resolution, compatibility validation, and frozen resolved-manifest evidence while preserving construction and Governance authority boundaries. |
| 1.2 | 2026-07-18 | Integrated conditional PROC-0005 resolution for publication-capable handoffs while preserving Authorization Kernel, PROC-0001 execution, ETP, lifecycle, and Governance authority ownership. |
| 1.3 | 2026-07-18 | Integrated conditional Active PROC-0006 resolution for Governance qualification handoffs while preserving Authorization Kernel and external Governance decision authority. |
| 1.4 | 2026-07-18 | Integrated conditional Active PROC-0007 resolution for Governance stabilization handoffs while preserving Authorization Kernel and all external operational and decision owners. |
