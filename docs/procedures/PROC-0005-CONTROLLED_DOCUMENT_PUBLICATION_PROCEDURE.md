---
document_id: PROC-0005
title: Controlled Document Publication Procedure
version: 1.7
status: Draft
owner: Engineering Governance
created: 2026-07-18
last_updated: 2026-07-29
phase: Governance Stabilization Procedure Integration
domain: Engineering Governance
classification: Engineering Procedure
predecessor_revision: PROC-0005@1.6
successor_revision: null
approval_status: Pending
approval_authority: null
approval_reference: null
approval_date: null
persistence_status: Pending
source_of_truth: true
information_scope: Controlled document construction, review, remediation, qualification, authorization, publication, verification, evidence, proportional application, and automation boundaries
declared_deferrals:
  - publication-workflow-automation
  - standards-reference-integration
relationships:
  - type: governed_by
    target: CHAR-0001
  - type: conforms_to
    target: POL-0001
  - type: conforms_to
    target: STD-0000
  - type: implements
    target: STD-0001
  - type: implements
    target: STD-0002
  - type: conforms_to
    target: STD-0004
  - type: conforms_to
    target: SPEC-0001
  - type: related_to
    target: PROC-0001
  - type: related_to
    target: PROC-0002
  - type: related_to
    target: PROC-0004
  - type: related_to
    target: PROC-0006
  - type: related_to
    target: PROC-0007
  - type: related_to
    target: TPL-0002
  - type: related_to
    target: EOS-0003
  - type: indexed_by
    target: DOC-0001
tags:
  - controlled-publication
  - governance
  - lifecycle
  - publication-boundary
  - evidence
  - proportional-application
  - automation-boundary
---

# Controlled Document Publication Procedure

## 1. Purpose

This procedure defines one reusable operational method for constructing, reviewing,
qualifying, authorizing, publishing, and verifying controlled engineering
documents. It converts the common lifecycle and publication requirements owned
by existing Governance records into an executable workflow without redefining
those requirements.

The procedure separates technical qualification, Governance approval,
publication execution, persistence, and downstream implementation authority.
It creates none of those authorities and shall not be used as a substitute for
an explicit authorization.

## 2. Scope and Applicability

The procedure is intended for new controlled documents and complete revisions
of existing controlled documents, including specifications, standards,
policies, procedures, Engineering Decision Records, and other document classes
whose class-specific governance permits its use.

It governs the publication workflow from authorized Draft construction through
post-publication verification. It does not:

- define document-class responsibilities;
- originate Governance or Information Authority;
- approve content or lifecycle transitions;
- change the lifecycle, metadata, relationship, or persistence models;
- replace class-specific procedures such as PROC-0002;
- authorize implementation described by a published document; or
- authorize commit, push, tag, deployment, or external publication beyond the
  exact authority of the publication transaction.

Class-specific governance prevails where it imposes additional requirements.
This procedure supplies the common publication path and shall not weaken a
more restrictive requirement.

## 3. Governing Records

Execution shall resolve and apply the current applicable revisions of:

- CHAR-0001 — Engineering Charter;
- POL-0001 — Engineering Governance Policy;
- STD-0000 — Engineering Documentation Standard;
- STD-0001 — Engineering Document Lifecycle Standard;
- STD-0002 — Engineering Document Persistence Standard;
- SPEC-0001 — Controlled Document Representation Specification;
- PROC-0001 — Engineering Work Order Execution Procedure, when an EWO governs
  the publication work;
- PROC-0002 — Engineering Governance Resolution Procedure, when an EGR is the
  publication subject;
- PROC-0004 — Engineering Handoff Construction Procedure, when a governed
  publication handoff must be constructed;
- PROC-0006 — Governance Qualification Procedure, when the publication
  transaction invokes the common Governance qualification capability;
- PROC-0007 — Governance Stabilization Procedure, when a qualified and
  authorized reconciliation returns a publication package to its caller;
- TPL-0002 — Completion Report Template, for the qualified execution report
  when the applicable transaction requires one; and
- DOC-0001 — Repository Document Index, for registered identity and discovery.

These records remain authoritative for their respective requirements. This
procedure references rather than duplicates their semantics.

When PROC-0006 is invoked, this procedure remains the publication lifecycle
and execution owner. PROC-0006 returns a qualification result and routing
recommendation to the caller; it does not authorize Stage 5, invoke this
procedure recursively, or alter a publication outcome.

When PROC-0007 returns an authorized publication package, this procedure
remains the publication lifecycle, boundary, execution, persistence, and
verification owner. PROC-0007 does not invoke this procedure autonomously,
publish, or convert a publication outcome into a Governance or baseline state.

## 4. Terms

- **Publication transaction:** The bounded authorized operation that applies
  approved metadata, lifecycle, registration, persistence, and baseline
  effects to one frozen publication set.
- **Publication set:** Every file whose bytes are intended to enter the atomic
  publication transaction, including the subject document and required index,
  relationship, evidence, or baseline updates.
- **Publication boundary:** The exact included and excluded repository paths,
  revisions, and repository baseline for a publication transaction.
- **Frozen publication content:** The exact qualified subject-document bytes
  presented for final authorization. A material change invalidates the freeze.
- **Technical qualification:** Evidence that content satisfies its engineering,
  consistency, and conformance criteria. It is not Governance approval.
- **Publication authority:** Explicit authority to execute or authorize the
  repository publication transaction and to apply lifecycle effects already
  approved by Engineering Governance or a superior authority that properly
  holds or delegates lifecycle-transition authority. Publication authority
  does not independently approve a lifecycle transition.
- **Implementation authority:** Separate authority to execute engineering work
  described by a controlled document. Publication does not provide it.
- **Immutable baseline:** The verified repository locator that preserves the
  exact published revision and its atomic supporting updates.
- **Publication input manifest:** The immutable exact publication content,
  exclusions, dependencies, and starting baseline authorized before execution.
- **Transaction output ledger:** The append-only inventory of governed control
  artifacts generated by an open publication transaction.
- **Transaction output boundary:** A declared atomic persistence boundary at
  which exact ledger entries are frozen, validated, and published.
- **Transaction finalization:** The one-way close that freezes the complete
  transaction manifest after all required inputs, outputs, persistence
  results, validation, synchronization dispositions, and completion evidence
  are accounted for.

### 4.1 Repository–EOS publication contract

Repository content remains authoritative. EOS is a derived projection for
runtime consumption and never becomes authoritative over repository state. A
repository working-tree change, commit, tag, or push does not automatically
synchronize EOS. Publication authority and EOS synchronization authority are
separate.

Every publication plan and authorization shall use these terms consistently:

- **Working-tree projection:** EOS bytes implied by the current working-tree
  sources.
- **Committed projection:** EOS bytes implied by a selected local commit.
- **Published projection:** EOS bytes implied by the repository baseline that
  completed its authorized publication operation.
- **Synchronized EOS projection:** EOS bytes persisted by a separately
  authorized synchronization and verified against the selected authoritative
  repository baseline.

Before Stage 6 begins, the plan shall identify:

1. **Initial Validation Boundary** — read-only verification of repository
   identity, baseline, health, registry, package, diff, and current EOS
   comparison;
2. **Publication Boundary** — the exact authorized repository paths and
   persistence operations;
3. **Synchronization Boundary** — the separately authorized phase, if any,
   after specified publication units at which a selected repository baseline
   may project to EOS; and
4. **Final Validation Boundary** — final repository validation and, only when
   synchronization was authorized and performed, exact synchronized-EOS and
   runtime verification.

Omitting a Synchronization Boundary means synchronization is out of scope. A
boundary shall identify the operator, authority reference, prerequisites,
selected repository baseline, target project, validation commands, and stop
conditions. An auto-repairing resume or qualification command shall not be
used as read-only publication validation.

### 4.2 Drift classifications

| Classification | Required interpretation and action |
| --- | --- |
| `EXPECTED_PUBLICATION_DRIFT` | The repository advanced within the authorized sequence before its Synchronization Boundary. Record both baselines, do not synchronize, and continue only to the next authorized publication unit. |
| `SYNCHRONIZATION_REQUIRED` | The declared Synchronization Boundary has been reached with prerequisites satisfied. Pause publication advancement until explicit synchronization authority is verified. |
| `SYNCHRONIZATION_FAILURE` | Authorized synchronization or its exact post-check failed. Preserve repository authority and evidence; stop and repair/retry only under applicable EOS operational authority. |
| `AUTHORITATIVE_SOURCE_FAILURE` | Repository identity, health, registry, package, source schema/content, diff, or committed-boundary validation failed. Stop publication; correct repository sources under separate authority and never repair them from EOS. |
| `RUNTIME_STATE_FAILURE` | Authoritative repository sources and deterministic projection validate, but EOS runtime, cache, checkpoint, or persistence state fails. Stop runtime-dependent work and repair only the runtime domain under applicable authority. |

Binary aligned/drifted output from a tool is an observation that the operator
shall map to one of these classifications using the declared boundaries and
source evidence.

### 4.3 Publication transaction and artifact lifecycle

The governing publication model is transaction-oriented and lifecycle-aware.
A commit is an immutable persistence locator. A publication unit is an ordered
atomic persistence boundary. Both are subordinate representations inside one
publication transaction; neither is the complete lifecycle model.

Every repository artifact encountered or generated by a transaction shall
receive exactly one lifecycle classification:

| Classification | Definition and publication responsibility |
| --- | --- |
| Publication content | Approved subject, implementation, document, state, or evidence bytes intentionally frozen as transaction input, or an explicitly authorized corrective revision generated before its destination output freeze; publish through its assigned input or output boundary |
| Execution evidence | Report or receipt produced by executing the transaction; intrinsic output of the active transaction |
| Recovery evidence | Failure, incident, stop, or recovery report produced before immutable finalization; intrinsic output of the active transaction |
| Qualification evidence | Qualification report, findings, or qualification change matrix; intrinsic output when qualification evaluates the active transaction |
| Reconciliation evidence | Inventory, dependency, or consistency analysis produced to reconcile the active transaction; intrinsic output |
| Transaction metadata | Output ledger, final manifest, boundary record, locator ledger, and completion record; intrinsic output |
| Planning artifact | Approved plan used to initiate the transaction is input; a plan or mapping revision produced while correcting the open transaction is a governed output and does not mutate the frozen input manifest |
| Generated artifact | Deterministic derivative; include as an output only when the initiating contract declares it required, otherwise classify it as non-publication |
| Operational state | Repository or runtime state owned by its operational authority; publish or synchronize only at its explicit unit or synchronization boundary, never merely because execution observed it |
| Non-publication artifact | Temporary, local, diagnostic, secret-bearing, cache, or otherwise excluded material; record in exclusions and never publish |

Classification is by engineering purpose, not filename. An artifact shall not
hold two classes. A change matrix is qualification evidence or reconciliation
evidence according to the decision it supports. A replacement publication plan
is a planning artifact. A replacement manifest is transaction metadata.

Execution, recovery, qualification, reconciliation, transaction-metadata, and
explicitly authorized corrective publication-content outputs automatically
belong to the active transaction when created before immutable finalization.
Corrective publication content is eligible only when the transaction output
schema and separate correction authority both cover its document, effect, and
destination boundary. Automatic belonging grants no content approval,
lifecycle transition, or permission to stage. It requires the output ledger to
record:

1. exact path and artifact identity;
2. one lifecycle classification;
3. generating event and predecessor evidence;
4. information owner and publication responsibility;
5. dependency and destination output boundary;
6. current digest or explicit not-yet-frozen state; and
7. inclusion or exclusion disposition.

The input manifest is never regenerated merely because the output ledger
grows. Before each declared output boundary, close the applicable ledger
interval, freeze exact paths and digests, validate it, and persist it
atomically. A newly required intrinsic output before persistence reopens only
that output interval. It does not replan completed or still-frozen input units.

After an output boundary is immutably persisted, later outputs flow to the next
declared output boundary. The final output boundary follows the last planned
input unit and precedes transaction completion. An incident or artifact first
created after immutable transaction finalization belongs to a linked corrective
successor transaction; completed manifests, commits, and history remain
unchanged.

### 4.4 Transaction lifecycle

Every publication transaction follows this lifecycle:

1. **Transaction initiation:** establish authority, identity, roles, input
   units, output schema, exclusions, boundaries, and successor routing.
2. **Input freeze:** freeze exact publication-content bytes and the immutable
   input manifest.
3. **Execution:** execute ordered input and output boundaries while appending
   generated control artifacts to the output ledger.
4. **Correction:** remediate authorized pre-persistence findings without
   changing completed units or silently changing frozen inputs.
5. **Reconciliation:** resolve classifications, dependencies, and ledger
   consistency; append reconciliation evidence rather than regenerating the
   input plan.
6. **Output collection:** account for every intrinsic output and exclusion.
7. **Output freeze:** close the output interval and freeze exact output paths,
   bytes, digests, owners, and dependencies.
8. **Output persistence:** publish the frozen interval at its declared
   transaction output boundary.
9. **Inventory finalization:** produce one complete transaction manifest over
   inputs, outputs, exclusions, and immutable locators.
10. **Publication completion:** perform final validation, synchronization
    disposition, push and remote verification when authorized, then close the
    transaction.

Publication content becomes authoritative according to its approved lifecycle
and immutable persistence boundary. Evidence and metadata become authoritative
records of observed transaction facts when attributable, finalized, and
immutably persisted. Operational state becomes authoritative only through its
existing owner and declared boundary. An open output ledger is authoritative
for output responsibility and routing, but not proof that an output has been
published.

### 4.5 Backward-compatible transaction adoption

Existing commits, publication units, plans, and evidence remain valid under
their contemporaneous procedures. They shall not be rewritten to adopt this
model.

An open legacy publication sequence may adopt this lifecycle through an
explicit migration record that identifies:

1. its immutable completed commits and still-frozen input units;
2. the legacy plan and manifest as the input and provenance baseline;
3. the first eligible transaction output boundary;
4. every seed output already assigned by the legacy plan;
5. every later governed ledger entry and any same-path corrective successor
   bytes;
6. the required final output and transaction-finalization boundaries; and
7. successor routing after finalization.

Adoption does not regenerate the legacy input plan. At the output freeze, the
exact final ledger interval supersedes earlier not-yet-persisted seed bytes for
the same path and becomes the only authorized staged set for that output
boundary. Completed units and their bytes remain immutable.

## 5. Roles and Authority Model

One person or agent may perform multiple roles only when explicitly authorized.
Holding one role never implies authority assigned to another.

| Role | Responsibilities | May Decide | Shall Not Infer |
| --- | --- | --- | --- |
| Document Author | Construct and remediate the complete Draft; inventory dependencies; provide traceability. | Editorial and technical choices within preparation authority. | Approval, lifecycle transition, publication, or implementation authority. |
| Technical Reviewer | Evaluate completeness, correctness, consistency, conformance, risk, and evidence. | PASS or REMEDIATION REQUIRED for the assigned technical gate; recommend rejection. | Governance approval, activation, persistence, or implementation authority. |
| Publication Authority | Execute or authorize the exact repository publication transaction and application of lifecycle effects already approved by Engineering Governance or properly delegated superior authority. | Whether the frozen, Governance-approved transaction may execute within the exact publication authority. | Content approval, lifecycle-transition approval, Governance disposition, or downstream implementation authority. |
| Engineering Governance | Approve, reject, or withdraw content; authorize lifecycle transitions; accept exceptions or deferrals; establish baseline eligibility. | Governance disposition and delegated publication authority. | Execution evidence that has not been produced or technical facts outside reviewed evidence. |
| Repository Custodian | Verify identity availability, placement, boundary, index synchronization, repository integrity, commit isolation, and locator validity. | Repository acceptance within delegated custodial authority. | Content approval, lifecycle authority, Governance disposition, or implementation authority. |
| Publication Executor | Apply only the authorized frozen transaction; run validation; record evidence; stop on variance. | Operational PASS or failure of the publication execution. | Authority to alter frozen content, include unrelated changes, approve exceptions, or begin implementation. |

The Publication Authority may be Engineering Governance or a separately
delegated publication executor. A publication delegation shall identify the
exact document revision, already-approved lifecycle effects, repository
effects, and limits. It shall not delegate or imply lifecycle-transition
approval. Only Engineering Governance or a superior authority permitted by
STD-0001 may approve a lifecycle transition. Repository write access is not
publication authority.

## 6. Preconditions

Before Stage 1 begins, verify:

1. explicit authority to prepare the proposed document or revision;
2. document class, purpose, scope, proposed owner, and information boundary;
3. governing records and class-specific procedure, if any;
4. canonical repository and current baseline;
5. known predecessor, competing Draft, successor, or identifier reservation;
6. affected relationships, indexes, baselines, and dependent records;
7. whether publication, activation, commit, tag, or push authority is included;
8. required reviewers and Governance decision path; and
9. validation entry points and evidence location.

Failure to establish authority, identity context, or repository identity stops
the workflow before content construction.

During Transitional Engineering Handoff Governance, a Governance-issued
Engineering Handoff satisfies the Draft preparation and workflow-initiation
authority precondition when the proposed document and scope are explicit in
that Handoff. It does not by itself satisfy content approval,
lifecycle-transition approval, publication execution, commit, push, tag,
qualification, or downstream implementation authority. Those authorities and
gates remain separately required by this procedure and its governing records.

## 7. Publication Lifecycle

```text
CONTROLLED DRAFT CONSTRUCTION
            |
            v
PUBLICATION READINESS REVIEW <---------+
     | PASS                             |
     |              REMEDIATION REQUIRED|
     v                                  |
CONFORMANCE AND CONSISTENCY ----> REMEDIATION LOOP
QUALIFICATION          |                |
     | PASS            +----------------+
     v
FINAL PUBLICATION AUTHORIZATION REVIEW
     | AUTHORIZED
     v
CONTROLLED PUBLICATION AND VERIFICATION
     | PASS
     v
PUBLISHED BASELINE

REJECTED or WITHDRAWN terminates the current publication transaction.
```

Remediation is a loop, not a lifecycle state. Technical gate outcomes do not
change the controlled-document lifecycle unless Engineering Governance
separately authorizes the applicable transition under STD-0001.

## 8. Stage 1 — Controlled Draft Construction

### Purpose

Produce one complete proposed publication suitable for technical review.

### Inputs

- preparation authority;
- document purpose, class, scope, and owner;
- applicable Governance Baseline;
- current or predecessor revision, when applicable;
- approved decisions and requirements; and
- required representation and class-specific structure.

### Required Authority

Explicit Draft preparation authority. It does not include approval,
publication, activation, or implementation authority.

### Activities and Validation

1. Inventory governing requirements, authoritative information owners,
   dependencies, affected relationships, and known deferrals.
2. Construct the entire document rather than a partial publication.
3. Represent proposed identity and metadata without claiming ungranted status.
4. Preserve predecessor meaning, history, and lineage where applicable.
5. Identify validation criteria, implementation boundaries, and publication
   impacts.
6. Run available structural, syntax, reference, and placeholder checks.

### Required Evidence

- preparation authority reference;
- complete Draft locator;
- governing-record inventory;
- affected-document and relationship inventory;
- initial validation results; and
- disclosed assumptions, deferrals, and unresolved questions.

### Exit Criteria

The complete Draft is stable enough for review, carries no unsupported
authority claim, and all known material questions are disclosed.

### Termination Conditions

Return REMEDIATION REQUIRED for correctable incompleteness. Stop as REJECTED or
WITHDRAWN only through the disposition rules in section 15.

## 9. Stage 2 — Publication Readiness Review

### Purpose

Determine whether the proposed publication is technically complete,
architecturally coherent, appropriately scoped, and suitable for detailed
conformance qualification.

### Inputs

- complete Draft and revision identity;
- Stage 1 evidence;
- governing and dependent records; and
- applicable engineering acceptance criteria.

### Required Authority

Assigned technical review authority. Review authority does not approve content
or authorize publication.

### Activities and Validation

Review the whole document for architectural or subject-matter completeness,
internal coherence, authority boundaries, implementation independence,
dependencies, risks, security and trust boundaries where applicable,
extensibility, class responsibility, and disclosed deferrals.

Classify findings as blocking, non-blocking, or observational. A blocking
finding shall identify the violated criterion, evidence, impact, and bounded
remediation recommendation.

### Required Evidence

- readiness assessment;
- reviewed Draft locator or fingerprint;
- findings with severity and rationale;
- scope and authority-boundary result; and
- PASS or REMEDIATION REQUIRED result.

### Exit Criteria

PASS requires no unresolved blocking readiness finding. REMEDIATION REQUIRED
routes the Draft through Stage 3 and back to this gate when changes are
material. REJECTED or WITHDRAWN terminates the transaction.

## 10. Stage 3 — Remediation Loop

### Purpose

Correct bounded findings without expanding the authorized document scope or
silently changing approved engineering decisions.

### Inputs

- stable finding set;
- Draft revision reviewed;
- remediation authority; and
- regression criteria.

### Required Authority

Existing Draft preparation authority is sufficient for corrections within the
approved scope. Any correction that changes authority, document class,
information ownership, approved decision, risk acceptance, or mission scope
requires new Governance disposition before work continues.

### Activities and Validation

1. Map each blocking finding to a correction or explicit unresolved status.
2. Modify only content necessary to resolve authorized findings.
3. Preserve conclusions and authority boundaries not implicated by a finding.
4. Rerun affected validation and whole-document regression checks.
5. Produce a revised Draft identity or fingerprint and correction trace.

### Required Evidence

- finding-to-correction matrix;
- revised Draft locator or fingerprint;
- regression results;
- remaining findings; and
- authority disposition for any scope-affecting issue.

### Exit Criteria

All blocking findings are resolved or the transaction terminates. Material
changes return to Stage 2. Bounded editorial or representation corrections
identified in Stage 4 may return directly to Stage 4 when the reviewer confirms
that architectural review inputs did not change.

## 11. Stage 4 — Conformance and Consistency Qualification

### Purpose

Qualify the complete Draft for cross-reference consistency, governing
conformance, deterministic representation, and publication integrity.

### Inputs

- readiness-qualified Draft;
- readiness and remediation evidence;
- governing requirements; and
- repository validation entry points.

### Required Authority

Assigned qualification authority independent of publication execution. The
same reviewer may perform Stages 2 and 4 only when proportional tailoring is
authorized and both evidence sets remain distinct.

### Activities and Validation

Verify, as applicable:

- terminology, headings, numbering, internal references, examples, and tables;
- consistency among narratives, models, diagrams, interfaces, and requirements;
- metadata readiness, identity constraints, lineage, and lifecycle claims;
- relationship direction, resolution, ownership, and cardinality;
- conformance to superior Governance and class-specific requirements;
- absence of contradictory, duplicated, or orphaned requirements;
- validation determinism, Markdown integrity, and unresolved placeholders;
- preservation of approval, publication, persistence, and implementation
  boundaries; and
- complete and non-conflicting deferrals.

### Required Evidence

- consistency and conformance audit;
- validator commands and results;
- exact qualified Draft locator or fingerprint;
- exception or deferral inventory; and
- PASS or REMEDIATION REQUIRED result.

### Exit Criteria

PASS requires all mandatory validation to succeed and no unresolved material
contradiction. REMEDIATION REQUIRED follows Stage 3 routing. The exact passing
Draft becomes the candidate frozen publication content.

## 12. Stage 5 — Final Publication Authorization Review

### Purpose

Allow Engineering Governance to determine whether the exact qualified content
may be approved and whether its identified lifecycle and publication effects
may execute.

### Inputs

- exact qualified Draft fingerprint or immutable review locator;
- complete gate evidence;
- proposed controlled identity, owner, metadata, relationships, lifecycle
  transition, persistence treatment, and publication set;
- known repository and dependent-record effects; and
- proposed publication authority and termination conditions.

### Required Authority

Engineering Governance approval authority and the authority required by
STD-0001 for the requested lifecycle transition. A technical reviewer may
recommend but cannot issue this decision.

### Activities and Validation

Engineering Governance verifies evidence sufficiency, complete-publication
scope, approval disposition, lifecycle transition, publication boundary,
deferrals, exceptions, baseline effects, and separation from implementation.

The authorization shall identify the exact content, allowed supporting paths,
metadata and index effects, repository operations, lifecycle destination,
persistence expectation, publication executor, and whether commit, tag, push,
or external publication is permitted.

### Required Evidence

- attributable Governance decision;
- exact approved content fingerprint or locator;
- approval and transition reference;
- allowed publication boundary and effects;
- accepted exceptions or deferrals; and
- PASS, REMEDIATION REQUIRED, REJECTED, or WITHDRAWN disposition.

### Exit Criteria

PASS means the exact transaction is authorized for Stage 6. It does not mean
publication has occurred and does not authorize implementation. Any material
content change after PASS invalidates the authorization and returns the
document to the applicable earlier gate.

## 13. Stage 6 — Controlled Publication and Verification

### Purpose

Execute the authorized frozen publication transaction atomically and prove its
repository, lifecycle, discovery, persistence, and baseline effects.

### Inputs

- Stage 5 authorization;
- frozen content fingerprint;
- cleanly identified repository baseline;
- exact included and excluded paths;
- controlled identifier and canonical path; and
- validation and rollback or stop strategy.

### Required Authority

Explicit publication authority for every intended repository effect and for
application of every lifecycle effect already approved by Engineering
Governance or properly delegated superior authority. Publication Authority and
the Publication Executor shall not independently approve a lifecycle
transition. Commit, tag, push, and external publication each require inclusion
in the publication authority when performed.

### Activities and Validation

1. At the Initial Validation Boundary, reconstruct and record the starting
   repository baseline and run read-only repository health, registry,
   applicable package, diff, and EOS comparison checks.
2. Inventory every tracked, staged, unstaged, and untracked change.
3. Establish the Publication, Transaction Output, Synchronization, Transaction
   Finalization, and Final Validation Boundaries before modifying publication
   state.
4. Verify controlled identifier availability through the authoritative index
   process; never infer availability from numbering alone.
5. Apply only authorized metadata, identity, canonical placement,
   relationships, index, revision-history, and evidence updates.
6. Verify that subject content matches the authorized frozen fingerprint,
   allowing only explicitly authorized publication representation changes.
7. Stage only included paths and compare the staged path set exactly with the
   authorized publication set.
8. Run complete pre-publication validation against the staged content.
9. Create one atomic repository commit or other authorized immutable
   persistence transaction.
10. Resolve and record the full immutable locator and subject blob identity.
11. Verify the committed path set, index state, repository integrity,
    reconstruction, and unit-specific post-publication validation. Read-only
    EOS comparison drift shall be classified; expected intermediate drift
    shall not trigger synchronization.
12. At the declared Synchronization Boundary, stop and verify separate
    synchronization authority and all prerequisites. If authorized, the named
    operator may invoke synchronization and shall immediately run exact
    synchronization, EOS state, persistence, and applicable integrated
    platform validation.
13. At the Final Validation Boundary, verify repository health, registry,
    package and committed-path integrity, all required final publication
    checks, and either the synchronized EOS projection or the explicitly
    recorded out-of-scope/expected-drift disposition.
14. Confirm every excluded change remains outside the transaction.
15. Append every intrinsic control artifact generated before transaction
    finalization to the output ledger and persist each frozen interval only at
    its declared output boundary.
16. At the Transaction Finalization Boundary, verify complete input, output,
    exclusion, dependency, locator, synchronization, and completion state;
    freeze the final transaction manifest; and prohibit later mutation.

If the repository cannot provide a true atomic transaction across all required
effects, stop unless Engineering Governance has approved an explicit ordered
publication protocol and its observable intermediate-state controls.

### Required Evidence

- publication authorization and decision;
- starting baseline and complete working-tree inventory;
- immutable input manifest, append-only output ledger, and output-boundary
  freezes;
- included and excluded publication paths;
- frozen-content verification;
- controlled identity and canonical placement;
- metadata, relationship, lifecycle, and index changes;
- pre-publication validation;
- four declared synchronization boundaries and authority allocation;
- exact staged-boundary verification;
- immutable commit or equivalent locator and subject blob identity;
- committed-path verification;
- post-publication validation and repository-integrity result; and
- drift classifications, synchronization evidence when applicable, and final
  repository/EOS baseline comparison; and
- qualified Completion Report;
- final transaction manifest; and
- successor routing for any post-finalization artifact.

### Exit Criteria

PASS requires verified atomic persistence, truthful metadata, synchronized
discovery, valid immutable locators, complete post-publication validation, and
no unrelated included change. Only then may the transaction certify controlled
publication completed.

Any failure before persistence produces `PUBLICATION FAILED` and stops without
publication. Any failure detected after persistence produces `PUBLICATION
INCIDENT`: preserve the immutable evidence, do not rewrite history, and obtain
Governance disposition for a corrective successor transaction. These
operational outcomes do not replace or alter the existing Governance
disposition.

## 14. Mandatory Publication Boundary Controls

The publication executor shall record a boundary manifest containing:

- repository identity and starting full commit ID;
- subject document identity and exact qualified fingerprint;
- every included path and intended change class;
- every pre-existing modified, staged, untracked, or conflicting path;
- explicit excluded paths;
- allowed metadata, lifecycle, index, evidence, and persistence effects;
- authorized commit, tag, push, or external-publication operations; and
- validation commands and expected results.

The transaction shall also declare its output schema, canonical output
locations or naming constraints, permitted artifact classes, responsible
owners, one or more output boundaries, the finalization boundary, and
post-finalization successor route. Exact output paths and digests may remain
open only in the append-only ledger until their declared output freeze.
Predeclared output slots are not globs and do not authorize staging; the frozen
ledger interval supplies the exact path set.

Boundary verification is fail-closed. Globs, implicit staging, broad commit
commands, and assumptions based on a previously clean tree shall not replace an
exact staged-path comparison. Unrelated work remains owned by its originator
and shall not be modified, discarded, hidden, or included.

Content freeze applies at Stage 5 PASS. Formatting or metadata conversion that
changes approved meaning is material and invalidates the freeze. Pure
publication representation changes are allowed only when listed in the
authorization and verified not to change meaning.

## 15. Gate Disposition and Transition Model

### Governance and Workflow Dispositions

- **PASS:** The gate's criteria are satisfied. Advancement is allowed only to
  the next authorized stage.
- **REMEDIATION REQUIRED:** Correctable blocking findings exist. The Draft
  remains nonqualified and returns through Stage 3.
- **REJECTED:** Engineering Governance rejects the publication proposal or
  determines it cannot proceed within the current authority. The current
  transaction terminates. A technical reviewer or Publication Executor may
  recommend rejection but shall not issue this disposition.
- **WITHDRAWN:** The authorized sponsor or Engineering Governance removes the
  proposal from consideration. The current transaction terminates without a
  publication claim. A technical reviewer or Publication Executor shall not
  withdraw the proposal.

### Operational Publication Outcomes

- **PUBLICATION FAILED:** Stage 6 could not complete before immutable
  persistence. The Publication Executor reports the failure, preserves all
  evidence and unrelated work, and stops without changing the existing
  Governance disposition.
- **PUBLICATION INCIDENT:** Stage 6 detected a failure after immutable
  persistence. The Publication Executor reports the incident, preserves the
  published evidence and history, and stops pending Governance disposition of
  a corrective successor transaction.

The Publication Executor reports operational outcomes. It never rejects or
withdraws a proposal. Operational outcomes and Governance dispositions are
independent state domains.

### Decision Matrix

| Current Stage | PASS | REMEDIATION REQUIRED | REJECTED | WITHDRAWN |
| --- | --- | --- | --- | --- |
| 1. Draft Construction | Stage 2 | Remain Stage 1 | Terminate | Terminate |
| 2. Readiness Review | Stage 4 | Stage 3, then Stage 2 | Terminate | Terminate |
| 3. Remediation | Return to assigning gate | Remain Stage 3 | Terminate | Terminate |
| 4. Conformance Qualification | Stage 5 | Stage 3, then Stage 4 or Stage 2 if material | Terminate | Terminate |
| 5. Authorization Review | Stage 6 under exact authorization | Stage 3 and repeat affected gates | Terminate | Terminate |
| 6. Publication and Verification | Published baseline | Report `PUBLICATION FAILED` before persistence or `PUBLICATION INCIDENT` after persistence; Governance disposition remains unchanged | Only Engineering Governance may reject; executor stops and preserves evidence | Only authorized sponsor or Engineering Governance may withdraw; executor stops and preserves evidence |

### Resumption Rules

- REMEDIATION REQUIRED may resume under existing preparation authority only
  when corrections remain within the approved scope.
- A scope, authority, lifecycle, exception, or risk change requires new
  Governance authority before remediation or review resumes.
- REJECTED work is not resumed. A later proposal is a new publication
  transaction with new authority and explicit reference to the rejection.
- WITHDRAWN work is not resumed. Re-entry requires fresh preparation authority
  and a new transaction identity.
- A publication incident resumes only under an authorized corrective
  transaction that preserves the failed or partial publication evidence.
- `PUBLICATION FAILED` may be retried only under authority that confirms the
  original frozen content, publication boundary, and Governance disposition
  remain valid; otherwise it requires a new or amended authorization.

Every disposition shall identify the gate, exact document revision, actor and
authority, date, rationale, findings, next permitted state, and required
resumption evidence.

## 16. Evidence Model

The publication evidence package or equivalent authorized record shall permit
an independent reviewer to reconstruct:

1. preparation and review authority;
2. exact document and revision evaluated at each gate;
3. findings, remediation, and regression history;
4. technical qualification results;
5. Governance approval and lifecycle-transition decision;
6. exact publication boundary and unrelated-change exclusions;
7. controlled identifier and canonical placement;
8. metadata, relationship, index, and persistence effects;
9. pre- and post-publication validation;
10. immutable repository and blob locators;
11. final repository status and any remaining unrelated work; and
12. qualified Completion Report and final certification.

Evidence shall be objective, reproducible, attributable, traceable, and
value-preserving. A report about a command is not a substitute for retained
output or repository evidence when the governing record requires it.

## 17. Validation Checklist

For every new document or complete successor revision, resolve exactly one
SPEC-0001 semantic validation profile and evaluate every criterion identifier
assigned to it. A prose-only completeness statement is not criterion
evaluation.

Publication evidence shall contain the resolved profile and resolution basis,
a criterion-to-evidence matrix, a completeness summary, an unresolved-
criterion report, the machine-readable automation coverage report,
command-interface results when applicable, and the exact candidate
fingerprint. Results shall distinguish PASS, FAIL, NOT APPLICABLE, and MANUAL
REVIEW.

Automated PASS establishes only the implemented check. Partially automated,
manual, and not-automated criteria require attributable review evidence.
Missing profile, missing criterion, unresolved criterion, missing evidence, or
indeterminate applicability is fail-closed and prevents publication
authorization.

Remediation shall reference the same criterion identifiers and rerun affected
criteria plus the complete profile. Regenerate traceability and unresolved
reports for the exact frozen candidate before authorization and after
publication.

The reusable interface is:

```text
python3 scripts/validate_controlled_documents.py --semantic-path <path> --semantic-report <results.json> --coverage-report <coverage.json>
```

`--help` documents the interface. Exit zero means automated structural and
requested semantic checks passed; non-zero means at least one automated check
failed. The command does not resolve manual criteria, approve content, or
authorize publication.

### 17.1 Diff and whitespace qualification policy

`git diff --check` is the mandatory repository-wide detector for introduced
whitespace errors and conflict markers. Its output and terminal exit status
shall be preserved exactly. The command is not a semantic Markdown validator,
a controlled-document validator, or a repository-integrity validator, and its
non-zero exit status is not by itself the final qualification disposition.

Every reported finding shall be classified against the exact staged or
committed publication boundary:

| Finding class | Qualification treatment |
| --- | --- |
| Conflict marker | Blocking repository finding in every file type |
| Space before tab in indentation | Blocking whitespace finding |
| Whitespace on an otherwise blank line | Blocking whitespace finding |
| Trailing space in a non-Markdown file | Blocking whitespace finding unless an applicable machine-readable format contract explicitly requires the byte sequence |
| Trailing space in Markdown that is not an intentional hard break | Blocking whitespace finding |
| Exactly two ASCII spaces after non-whitespace Markdown content | Permitted only when the author identifies the line as an intentional Markdown hard break and Markdown integrity validation confirms that interpretation |
| Generated Markdown trailing space | Blocking unless the generator's controlled format contract explicitly requires an intentional hard break and deterministic regeneration reproduces it |

A permitted Markdown hard break is a formatting finding, not a semantic
failure, repository-integrity failure, or publication failure. The
qualification record shall retain its path, line, raw detector output,
intentional-rendering rationale, and confirming review. If intent or
applicability is ambiguous, the finding is blocking. Three or more trailing
spaces, trailing spaces on blank lines, tabs used as an asserted hard break,
and accidental editor padding do not receive this exception.

Whitespace qualification passes only when `git diff --check` exits zero or
every reported line is individually confirmed as a permitted Markdown hard
break and no protected finding remains. This classification does not permit
changing frozen bytes, weakening exact digest or path verification, ignoring a
validator exit status, or converting any semantic, structural, cross-reference,
repository-integrity, or conflict-marker failure to PASS.

| Control | Pre-Publication | Post-Publication |
| --- | --- | --- |
| Authority and exact scope resolve | Required | Confirm unchanged |
| Document and revision identity are unique | Required | Required |
| Metadata and lifecycle are valid | Required | Required |
| Approval and transition evidence resolve | Required | Required |
| Relationships resolve and do not conflict | Required | Required |
| Canonical placement is correct | Required | Required |
| Index registration agrees | Required | Required |
| Complete-publication validation passes | Required | Required |
| Publication set equals staged/transaction set | Required | Verify committed set |
| Unrelated changes are excluded | Required | Required |
| Persistence status is truthful | Predict expected state | Verify observed state |
| Immutable locator resolves | Not yet available | Required |
| Historical reconstruction succeeds | Where predecessor applies | Required |
| Deferred work remains unauthorized | Required | Required |
| Repository integrity passes | Required | Required |
| Repository health | Initial Validation Boundary | Each Publication Boundary and Final Validation Boundary |
| Registry validation | Initial Validation Boundary | After an affected unit and at Final Validation Boundary |
| Package verification | Initial Validation Boundary when applicable | During each affected unit and at Final Validation Boundary |
| Diff / exact path verification | Before persistence | During staging, after each commit, and at Final Validation Boundary |
| EOS comparison (`sync-validate`) | Initial Validation Boundary, read-only | Classify after publication units and verify exactly at Synchronization and Final Validation Boundaries |
| EOS synchronization | Prohibited as validation | Only at the declared Synchronization Boundary under separate authority |
| EOS runtime and persistence validation | Observe initially when required | Required immediately after synchronization and at Final Validation Boundary when EOS is in scope |

Validation failure is never converted to PASS merely because a repository
operation succeeded.

## 18. Proportional Application

Proportionality changes the depth, independence, or combination of technical
review activities. It never removes Governance approval, lifecycle authority,
publication-boundary control, truthful persistence, or post-publication
verification.

| Document or Change Class | Minimum Tailoring |
| --- | --- |
| New specification or major architectural revision | Full six-stage workflow with distinct readiness and consistency evidence. |
| Standard or policy | Full workflow plus superior-authority, subordinate-impact, and complete governance-subsystem analysis. |
| Procedure | Full workflow; readiness and consistency may share a reviewer when authorized, while evidence remains distinct. Include operational usability and governing-requirement traceability. |
| Engineering Decision Record | Apply this common workflow together with its decision-specific procedure; the decision procedure controls disposition. |
| Minor revision | Stages 2 and 4 may be combined if risk classification and authorization permit, but both criteria and results remain recorded. |
| Editorial correction | Technical gates may use a bounded combined checklist when meaning, requirements, authority, lifecycle, and relationships are unchanged. Publication authorization and boundary verification remain mandatory. |
| Emergency correction | Follow STD-0001 exceptional-transition authority. Urgency does not waive evidence, boundary, validation, or post-publication verification. |

The tailoring decision shall be recorded before review and identify rationale,
risk, combined activities, retained mandatory controls, and approving authority.

## 19. Automation Contract

Future automation may represent the workflow using these states:

```text
DRAFT_CONSTRUCTION
READINESS_REVIEW
REMEDIATION
CONFORMANCE_QUALIFICATION
AUTHORIZATION_REVIEW
PUBLICATION_PREPARED
PUBLICATION_PERSISTED
POST_PUBLICATION_VERIFIED
PUBLICATION_FAILED
TERMINATED_REJECTED
TERMINATED_WITHDRAWN
PUBLICATION_INCIDENT
```

Each transition shall require an attributable actor, authority reference,
document fingerprint, evidence locator, timestamp, and permitted next state.
Automation may validate, assemble evidence, compare boundaries, stage exact
paths, and execute authorized repository operations. It shall fail closed and
shall not select Governance dispositions, approve exceptions, expand a
publication set, infer lifecycle authority, or begin implementation.

Automation output is a derived view until persisted through the applicable
controlled evidence model.

## 20. Stop Conditions

Stop the workflow when:

- preparation, review, approval, transition, or publication authority is
  missing, ambiguous, expired, or exceeded;
- document identity, revision, owner, class, predecessor, or canonical path is
  ambiguous;
- the reviewed content differs materially from the authorized frozen content;
- a required gate has no attributable evidence;
- a blocking finding, validation failure, or relationship conflict remains;
- lifecycle, approval, or persistence claims disagree;
- a competing successor, identifier reservation, repository operation, or
  publication transaction exists;
- the staged or transaction path set differs from the publication boundary;
- unrelated changes cannot be safely isolated;
- repository integrity or immutable persistence cannot be verified;
- an atomic transaction cannot be performed and no ordered protocol is
  explicitly authorized; or
- publication would imply unauthorized implementation or Governance effect.

Stop conditions are reported, not silently repaired beyond the authorized
remediation scope.

## 21. Synchronization Publication Checks

When a publication set contains a document with implementation synchronization
declarations, readiness review shall include the additive synchronization
report. `UNKNOWN`, `MISSING_ARTIFACT`, `IMPLEMENTATION_CHANGED`,
`DOCUMENT_CHANGED`, or `OUT_OF_SYNC` shall be preserved as findings and routed
to the applicable review or qualification owner. They shall not be converted
to PASS by publication.

The frozen publication evidence shall record documentation and implementation
fingerprints, affected documents, qualification impact, and required actions.
After publication, rerun synchronization validation against the committed
locator. A changed documentation fingerprint is expected only when included in
the authorized publication set; it does not authorize implementation changes.
Likewise, implementation changes never authorize document publication.

The synchronization report is derived evidence. The Publication Authority and
Publication Executor retain exactly their existing roles, and no report status
approves content, lifecycle, publication, or implementation.

## 22. Implementation Coverage Publication Checks

Readiness review for a publication that changes implementation or
synchronization declarations shall run the independently selectable coverage
layer:

```bash
python3 scripts/validate_controlled_documents.py \
  --implementation-coverage \
  --implementation-coverage-report <coverage-results.json>
```

The review shall reconcile every `undocumented`, `orphaned_declaration`,
`obsolete_declaration`, and `unknown_classification` finding to its recorded
repository and declaration evidence. Optional, prohibited, generated, and
external artifacts may be excluded only by the applicable classification
policy. A filename, nearby document, or apparent owner shall not be used to
infer an authoritative relationship.

Coverage results are derived readiness evidence. They do not add an artifact to
the publication set, authorize remediation, assign documentation ownership, or
make a publication or lifecycle decision. A changed coverage policy,
declaration, implementation root, or implementation artifact shall be included
in the frozen publication evidence when it is within the authorized boundary.

## 22.1 Engineering Contract Conformance Publication Checks

When a publication changes an explicitly documented Engineering Contract or
its declared implementation surface, readiness review shall run the
independently selectable conformance layer:

```bash
python3 scripts/validate_controlled_documents.py \
  --conformance-only \
  --conformance-report <conformance-results.json>
```

The review shall preserve contract extraction, discovery, determination,
invariant, compatibility, and recommended-action evidence. Missing,
incompatible, partial, obsolete, ambiguous, or undocumented findings shall be
routed to the existing technical review owner. They shall not be treated as
functional-test results or converted into authorization.

Conformance evidence does not add paths to a publication boundary, approve
content, authorize remediation, qualify implementation, or change lifecycle.
PROC-0005 retains publication execution ownership and consumes conformance
only as derived readiness evidence.

## 23. Compliance and Success Criteria

A publication conforms to this procedure when:

- all applicable stages and tailored controls are attributable;
- technical qualification, Governance approval, publication, and
  implementation authority remain separate;
- the common lifecycle and class-specific requirements are preserved;
- one exact frozen publication set is authorized and published atomically;
- the immutable input manifest, append-only output ledger, frozen output
  intervals, exclusions, and final transaction manifest reconstruct without
  recursive input-plan regeneration;
- unrelated work is excluded and preserved;
- metadata, relationships, lifecycle, discovery, and persistence agree;
- the immutable baseline and subject revision reconstruct deterministically;
- pre- and post-publication validation pass;
- all four boundaries are declared, every EOS comparison is classified, and
  synchronization occurs only under separate authority at its declared
  boundary;
- evidence supports every gate and transition; and
- the Completion Report accurately certifies the observed outcome.

The procedure succeeds when a qualified executor can reproduce the workflow
across controlled document classes without undocumented knowledge or inferred
authority.

## 24. Adoption and Future Integration

This procedure is the single reusable operational publication workflow for the
controlled document classes in section 2. Class-specific procedures supplement
it and retain their existing responsibilities.

Future work initiation and publication planning should reference this procedure
as the authoritative operational workflow. Any standards-reference integration,
workflow automation, or class-specific extension requires separate authority.
Automation shall continue to obey section 19 and Appendix A and shall not
acquire Governance decision-making authority.

## Appendix A — Illustrative Automation Transition Table

This appendix is informative. It supports deterministic automation but creates
no authority and does not modify lifecycle semantics. The governing standards
and the operative requirements in sections 7 through 20 take precedence over
this table if any inconsistency is discovered.

| Current State | Authorized Event | Next State | Permitted Actor | Required Evidence |
| --- | --- | --- | --- | --- |
| `DRAFT_CONSTRUCTION` | Complete Draft submitted | `READINESS_REVIEW` | Document Author under preparation authority | Preparation authority, Draft fingerprint, inventories, initial validation |
| `READINESS_REVIEW` | Readiness PASS | `CONFORMANCE_QUALIFICATION` | Technical Reviewer | Readiness assessment, findings, reviewed fingerprint |
| `READINESS_REVIEW` | REMEDIATION REQUIRED | `REMEDIATION` | Technical Reviewer | Blocking findings and bounded remediation criteria |
| `REMEDIATION` | Material corrections completed | `READINESS_REVIEW` | Document Author under remediation authority | Correction matrix, revised fingerprint, regression results |
| `REMEDIATION` | Bounded corrections completed | Assigning technical gate under section 10 | Document Author and assigning Technical Reviewer | Correction matrix and confirmation that earlier review inputs did not change |
| `CONFORMANCE_QUALIFICATION` | Qualification PASS | `AUTHORIZATION_REVIEW` | Qualification Reviewer | Conformance audit, validator results, qualified fingerprint |
| `CONFORMANCE_QUALIFICATION` | REMEDIATION REQUIRED | `REMEDIATION` | Qualification Reviewer | Blocking consistency findings and return-gate classification |
| `AUTHORIZATION_REVIEW` | Governance PASS and exact publication authorization | `PUBLICATION_PREPARED` | Engineering Governance | Approval decision, lifecycle-transition authority, frozen fingerprint, authorized boundary |
| Any pre-publication state | REJECTED | `TERMINATED_REJECTED` | Engineering Governance | Rejection decision, authority, rationale, document fingerprint |
| Any pre-publication state | WITHDRAWN | `TERMINATED_WITHDRAWN` | Authorized sponsor or Engineering Governance | Withdrawal record, authority, rationale, document fingerprint |
| `PUBLICATION_PREPARED` | Atomic persistence succeeds | `PUBLICATION_PERSISTED` | Publication Executor under exact publication authority | Boundary manifest, staged-path proof, pre-publication validation, immutable locator |
| `PUBLICATION_PREPARED` | Execution fails before persistence | `PUBLICATION_FAILED` | Publication Executor reports outcome | Failure evidence, unchanged Governance disposition, repository status |
| `PUBLICATION_PERSISTED` | Post-publication verification passes | `POST_PUBLICATION_VERIFIED` | Publication Executor or authorized independent verifier | Committed-path proof, locator verification, post-publication validation |
| `PUBLICATION_PERSISTED` | Post-publication verification fails | `PUBLICATION_INCIDENT` | Publication Executor or verifier reports outcome | Incident evidence, immutable locator, repository status, failed checks |
| `PUBLICATION_FAILED` | Retry explicitly authorized with unchanged freeze and boundary | `PUBLICATION_PREPARED` | Publication Authority after required Governance confirmation | Retry authority, frozen-content verification, boundary revalidation |
| `PUBLICATION_INCIDENT` | Corrective successor transaction authorized | `DRAFT_CONSTRUCTION` for the successor transaction | Engineering Governance | Incident disposition, successor authority, preserved publication evidence |
| Open transaction | Intrinsic control artifact generated | Current execution/correction/reconciliation state | Artifact owner under current transaction authority | Output-ledger entry with class, owner, event, dependency, destination boundary, and digest state |
| Output collection | Output interval frozen | `TRANSACTION_OUTPUT_FROZEN` | Publication Executor and applicable reviewers | Exact output paths, bytes, digests, classifications, dependencies, and exclusions |
| `TRANSACTION_OUTPUT_FROZEN` | Atomic output persistence succeeds | `TRANSACTION_OUTPUT_PERSISTED` | Publication Executor under exact publication authority | Staged-path proof, immutable locator, committed-path verification |
| All input and output obligations complete | Final transaction manifest frozen and persisted | `TRANSACTION_FINALIZED` | Publication Executor under finalization authority | Complete input/output/exclusion/locator manifest and final validation evidence |
| `TRANSACTION_FINALIZED` | Later control artifact required | Successor transaction intake | Applicable artifact owner and successor authority | Link to finalized transaction and immutable evidence; no history mutation |

Automation shall validate the actor and authority reference before accepting an
event. It shall not synthesize PASS, REJECTED, WITHDRAWN, lifecycle approval,
publication authority, or corrective authority from repository state.

## Engineering Assurance Evidence in Publication

When an authorized publication package declares Engineering Properties, the
readiness and conformance evidence may include the independently executable
Engineering Assurance layer after structural, semantic, synchronization,
implementation coverage, and implementation conformance validation. The
publication review shall preserve every property determination, unresolved
condition, advisory impact, canonical report digest, and authority-boundary
statement. A successful assurance result is evidence only: it does not
authorize publication, imply approval or qualification, change lifecycle
state, or replace the publication transaction and its existing owners.

## Revision History

| Version | Date | Description |
| --- | --- | --- |
| 1.0 | 2026-07-18 | Published the qualified reusable six-stage controlled-document publication workflow, separated authority and outcome domains, exact publication-boundary controls, evidence and validation models, proportional application, and informative automation transition appendix without authorizing automation or downstream implementation. |
| 1.1 | 2026-07-18 | Integrated Active PROC-0006 as an optional external qualification dependency while preserving PROC-0005 publication lifecycle, authorization, execution, outcome, and verification ownership. |
| 1.2 | 2026-07-18 | Integrated Active PROC-0007 as an optional source of qualified and authorized reconciliation publication packages while preserving PROC-0005 publication ownership. |
| 1.3 | 2026-07-28 | Draft successor adds profile resolution, criterion-to-evidence traceability, completeness and unresolved-criterion summaries, automation coverage, command evidence, fail-closed semantic disposition, additive synchronization, repository-wide implementation coverage, and Engineering Contract conformance evidence without changing publication ownership. |
| 1.4 | 2026-07-28 | Adds optional Engineering Assurance evidence consumption and canonical report preservation without changing publication authority, lifecycle ownership, or execution. |
| 1.5 | 2026-07-29 | Established the repository-authoritative EOS publication contract, four explicit boundaries, projection semantics, five drift classifications, synchronization authority, and phase-specific validation sequencing. |
| 1.6 | 2026-07-29 | Established file-type-aware diff and whitespace qualification: protected Git findings remain blocking while individually verified two-space Markdown hard breaks are permitted formatting findings. |
| 1.7 | 2026-07-29 | Established the transaction-oriented publication lifecycle with immutable inputs, exact artifact classifications, append-only governed outputs, output freezes, final transaction manifests, and post-finalization successor routing. |
