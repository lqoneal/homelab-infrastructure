---
document_id: PROC-0005
title: Controlled Document Publication Procedure
version: 1.1
status: Active
owner: Engineering Governance
created: 2026-07-18
last_updated: 2026-07-18
phase: Governance Qualification Procedure Integration
domain: Engineering Governance
classification: Engineering Procedure
predecessor_revision: PROC-0005@1.0
successor_revision: null
approval_status: Approved
approval_authority: Engineering Governance
approval_reference: EGR-000005
approval_date: 2026-07-18
persistence_status: Persisted
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
    target: TPL-0002
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
- TPL-0002 — Completion Report Template, for the qualified execution report
  when the applicable transaction requires one; and
- DOC-0001 — Repository Document Index, for registered identity and discovery.

These records remain authoritative for their respective requirements. This
procedure references rather than duplicates their semantics.

When PROC-0006 is invoked, this procedure remains the publication lifecycle
and execution owner. PROC-0006 returns a qualification result and routing
recommendation to the caller; it does not authorize Stage 5, invoke this
procedure recursively, or alter a publication outcome.

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

1. Reconstruct and record the starting repository baseline.
2. Inventory every tracked, staged, unstaged, and untracked change.
3. Establish the exact publication boundary before modifying publication
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
    reconstruction, and complete post-publication validation.
12. Confirm every excluded change remains outside the transaction.

If the repository cannot provide a true atomic transaction across all required
effects, stop unless Engineering Governance has approved an explicit ordered
publication protocol and its observable intermediate-state controls.

### Required Evidence

- publication authorization and decision;
- starting baseline and complete working-tree inventory;
- included and excluded publication paths;
- frozen-content verification;
- controlled identity and canonical placement;
- metadata, relationship, lifecycle, and index changes;
- pre-publication validation;
- exact staged-boundary verification;
- immutable commit or equivalent locator and subject blob identity;
- committed-path verification;
- post-publication validation and repository-integrity result; and
- qualified Completion Report.

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

## 21. Compliance and Success Criteria

A publication conforms to this procedure when:

- all applicable stages and tailored controls are attributable;
- technical qualification, Governance approval, publication, and
  implementation authority remain separate;
- the common lifecycle and class-specific requirements are preserved;
- one exact frozen publication set is authorized and published atomically;
- unrelated work is excluded and preserved;
- metadata, relationships, lifecycle, discovery, and persistence agree;
- the immutable baseline and subject revision reconstruct deterministically;
- pre- and post-publication validation pass;
- evidence supports every gate and transition; and
- the Completion Report accurately certifies the observed outcome.

The procedure succeeds when a qualified executor can reproduce the workflow
across controlled document classes without undocumented knowledge or inferred
authority.

## 22. Adoption and Future Integration

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

Automation shall validate the actor and authority reference before accepting an
event. It shall not synthesize PASS, REJECTED, WITHDRAWN, lifecycle approval,
publication authority, or corrective authority from repository state.

## Revision History

| Version | Date | Description |
| --- | --- | --- |
| 1.0 | 2026-07-18 | Published the qualified reusable six-stage controlled-document publication workflow, separated authority and outcome domains, exact publication-boundary controls, evidence and validation models, proportional application, and informative automation transition appendix without authorizing automation or downstream implementation. |
| 1.1 | 2026-07-18 | Integrated Active PROC-0006 as an optional external qualification dependency while preserving PROC-0005 publication lifecycle, authorization, execution, outcome, and verification ownership. |
