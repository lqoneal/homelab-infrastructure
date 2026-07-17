---
document_id: STD-0004
title: Engineering State Freshness Standard
version: 1.3
status: Active
owner: Engineering Governance
created: 2026-07-15
last_updated: 2026-07-17
phase: Governance Framework Modernization
domain: Engineering Governance
classification: Engineering Standard
predecessor_revision: STD-0004@1.2
successor_revision: null
approval_status: Approved
approval_authority: Engineering Governance
approval_reference: EGR-000002
approval_date: 2026-07-15
persistence_status: Pending
source_of_truth: true
declared_deferrals:
  - engineering-state-reconciliation
relationships:
  - type: governed_by
    target: CHAR-0001
  - type: conforms_to
    target: POL-0001
  - type: conforms_to
    target: STD-0000
  - type: related_to
    target: STD-0001
  - type: related_to
    target: STD-0002
  - type: required_by
    target: PROC-0001
  - type: constrains
    target: SPEC-0004
  - type: constrains
    target: EOS-0003
  - type: related_to
    target: EMP-0001
  - type: related_to
    target: PROJ-0001
  - type: indexed_by
    target: DOC-0001
tags:
  - engineering-state
  - freshness
  - reconciliation
  - resume
  - lifecycle
  - eos
---

# Engineering State Freshness Standard

## Purpose

This standard establishes the mandatory freshness threshold and reconciliation
controls for authoritative Engineering State. It ensures that Engineering
State, Engineering Operating System (EOS) operational state, and every resume
mechanism remain aligned with actual engineering progress without creating
unnecessary documentation churn.

## Scope

This standard applies to Homelab, EOS, the Engineering Management Platform,
and every portfolio project that uses Engineering Platform initiation,
checkpoint, state, context, handoff, or resume services. It governs the
freshness of operational engineering state; STD-0001 continues to govern the
lifecycle states of controlled documents.

This standard does not authorize implementation, lifecycle transition,
checkpoint creation, or state mutation. Each reconciliation executes within
its applicable mission authority.

## Authority and Information Ownership

Engineering Governance owns this standard and its freshness requirements.
Authoritative information ownership remains distributed by scope:

- Project State owns the current project resume point and next approved action;
- project sprint records own current sprint state;
- project and infrastructure records own the current engineering baseline;
- active mission records own mission-specific authority and objectives;
- EOS owns operational state, checkpoint selection, and context reconstruction;
- EMP owns its registered portfolio and work-management state; and
- derived resume output owns no authoritative state.

Reconciliation synchronizes these owners. It does not copy their facts into a
second authoritative source or permit an EOS checkpoint, runtime cache,
dashboard, conversation, or generated summary to override them.

## Definitions

**Engineering State** is the coordinated authoritative set required to resume
engineering work: Project State, Sprint State, EOS operational state, resume
context, Engineering Platform operational status, current engineering
baseline, active investigations, current mission, and next recommended
mission.

**Completed engineering milestone** is a milestone whose completion is
supported by accepted or mission-authorized evidence, regardless of whether a
subsequent reconciliation has yet updated every Engineering State owner.

**Unreconciled milestone** is a completed engineering milestone whose effect on
one or more required Engineering State owners has not been synchronized and
validated.

**Engineering State Reconciliation** is the governed activity that identifies
the latest supported engineering reality, synchronizes the required
authoritative owners and operational state, validates relationships, and makes
resume context accurate.

**Freshness threshold** is the permitted maximum of two completed engineering
milestones that remain unreconciled.

An engineering phase, sprint, session, or pause may include many implementation
events. Only supported completed milestones count against the numeric
threshold, but the mandatory event triggers below apply independently of that
count.

## Engineering Requirement

Authoritative Engineering State shall never intentionally lag actual
engineering progress by more than two completed engineering milestones.

Whenever a milestone completes, its effect on Engineering State shall be
evaluated. Completion that would produce a third unreconciled milestone makes
Engineering State Reconciliation mandatory before any additional
implementation work proceeds. Work may stop safely, preserve evidence, and
perform the reconciliation; it shall not continue implementation through the
breach.

The threshold limits lag. It is not a target, a permission to preserve known
obsolete objectives, or a reason to defer a mandatory event-triggered
reconciliation.

## Mandatory Reconciliation Triggers

Engineering State Reconciliation is mandatory when any of the following
occurs:

1. more than two completed milestones would remain unreconciled;
2. a project phase completes;
3. a sprint completes;
4. a checkpoint is to be created;
5. an extended engineering pause begins;
6. an engineering handoff occurs;
7. an engineering session terminates; or
8. Engineering Work Initiation would otherwise resume from obsolete state.

The responsible engineer shall treat a pause as extended when its anticipated
duration or loss of active context could prevent deterministic resume. When
that cannot be known, reconcile before relinquishing the session or handing
off work.

Checkpoint creation is downstream of reconciliation. A checkpoint captures a
reconciled resume boundary; it shall not be used to preserve known stale state.
Emergency interruption may prevent pre-interruption reconciliation, but the
first resumed activity shall reconcile before implementation continues.

## Required Reconciliation Scope

Reconciliation shall synchronize, at minimum:

- Project State, including actual progress, current resume point, and next
  approved action;
- Sprint State, including completion, active work, blockers, and next boundary;
- EOS operational state and active checkpoint selection;
- resume context and its source-record references;
- Engineering Platform operational status relevant to the mission;
- the current qualified engineering baseline;
- active investigations, known faults, blockers, and unresolved findings;
- current mission, authority, phase, and status; and
- the next recommended mission without representing it as automatically
  authorized.

When EMP management state or another project source is affected, its owning
record shall also be synchronized. Reconciliation shall preserve completed
history and existing evidence rather than rewrite earlier records to appear
continuously current.

## Reconciliation Procedure Requirements

A reconciliation shall:

1. identify its authority, scope, operator, repository state, and UTC time;
2. inventory completed and unreconciled milestones since the last reconciled
   boundary;
3. compare authoritative records, EOS state, checkpoint state, observed
   repository facts, and accepted evidence;
4. resolve each current-state fact to its single authoritative owner;
5. update only affected owners and their required relationships;
6. regenerate or refresh derived context only after authoritative records are
   current;
7. validate repository integrity, documents, relationships, lifecycle
   consistency, EOS synchronization, and resume accuracy; and
8. record the reconciled-through milestone or equivalent current boundary,
   remaining unreconciled count, limitations, and next recommended mission.

Instrumentation or automation may assist evaluation, but it shall not invent
milestone completion, infer authority, or make a derived view authoritative.

## Engineering Lifecycle Integration

The operational Engineering Lifecycle is:

```text
Resume
  ↓
Qualification
  ↓
Implementation
  ↓
Validation
  ↓
Documentation Updates
  ↓
Engineering State Reconciliation
  ↓
Commit Classification
  ↓
Commit Reconstruction Planning
  ↓
Commit Execution
  ↓
Milestone Qualification
  ↓
Checkpoint
  ↓
Resume Ready
```

The stages serve these purposes:

1. **Resume** reconstructs context from reconciled authoritative records.
2. **Qualification** verifies authority, scope, baseline, tools, repository
   integrity, and freshness before work begins.
3. **Implementation** performs only the authorized engineering change.
4. **Validation** proves the change satisfies its technical and governance
   requirements.
5. **Documentation Updates** reconcile affected controlled knowledge and
   evidence with the validated result.
6. **Engineering State Reconciliation** synchronizes Project State, Sprint
   State, EOS, resume context, baselines, investigations, and next work under
   this standard.
7. **Commit Classification** inventories every outstanding repository change,
   assigns each change to one engineering objective, establishes logical
   commit boundaries, and orders dependencies under PROC-0001.
8. **Commit Reconstruction Planning** selects and documents the safest method
   for transforming each approved logical change set into repository history,
   including validation and expected-state controls under PROC-0001.
9. **Commit Execution** implements only the approved reconstruction plans in
   dependency order and performs no implicit milestone publication.
10. **Milestone Qualification** verifies that prerequisite commits and
   validation are complete before a milestone publication and tag are
   separately authorized.
11. **Checkpoint** captures the reconciled, committed, and qualified resume
    boundary.
12. **Resume Ready** confirms that authoritative records and derived resume
    mechanisms identify the same current engineering state.

Engineering State Reconciliation precedes Commit Classification so commit
planning operates on current authoritative state. Commit Classification defines
what engineering history should exist; Commit Reconstruction Planning defines
how that approved history will be created safely. This standard governs when
reconciliation occurs and what state it synchronizes. PROC-0001 governs both
classification and reconstruction planning. None of these activities transfers
authority to another or independently authorizes commit execution.

Engineering State Reconciliation may be omitted at an intermediate lifecycle
pass only when Engineering State remains within the two-milestone threshold,
no mandatory trigger has occurred, and resume output is not known to be
obsolete. Omission shall never bypass reconciliation before checkpoint
creation, session termination, handoff, sprint completion, or phase completion.

This operational lifecycle does not replace the controlled-document lifecycle
defined by STD-0001. Document revisions created during reconciliation remain
subject to their normal lifecycle, approval, representation, and persistence
requirements.

## Work Initiation Requirements

Engineering Work Initiation shall qualify freshness before implementation:

1. locate authoritative Project State and Sprint State;
2. identify the latest supported completed milestone and the last reconciled
   boundary;
3. count unreconciled completed milestones;
4. compare current mission, baseline, investigations, next action, EOS state,
   active checkpoint, and resume output;
5. report whether state is `CURRENT`, `WITHIN THRESHOLD`, or
   `RECONCILIATION REQUIRED`; and
6. stop implementation and reconcile when the threshold would be breached or
   resume would otherwise consume obsolete objectives.

`WITHIN THRESHOLD` is acceptable only when no event trigger requires immediate
reconciliation and no known obsolete objective would be presented as current.
An inability to determine freshness is `RECONCILIATION REQUIRED`, not an
assumption of currency.

## Resume Accuracy Requirements

All Engineering Resume mechanisms shall derive context from reconciled
authoritative Engineering State. Resume generation shall resolve Project State,
Sprint State, current mission, baseline, active investigations, and next action
before considering a checkpoint.

A checkpoint is historical operational evidence and a resume-boundary aid. If
it conflicts with a newer authoritative state record, the newer supported
authoritative record prevails, the conflict shall be reported, and
reconciliation is required. Resume shall not intentionally present an
objective, investigation, phase, sprint, or mission as current when the
authoritative evidence records it as completed, superseded, closed, or
otherwise no longer active.

EOS runtime views and resume summaries remain derived views. They shall expose
their source records and freshness result and shall be regenerated after
reconciliation. A stale checkpoint shall never silently displace current
Project State.

## Project State Requirements

Each active project shall maintain a deterministically discoverable Project
State publication as its primary project resume point. It shall identify:

- current mission, phase, sprint, implementation boundary, and baseline;
- current active investigations and blockers;
- last reconciled milestone or equivalent boundary;
- count or explicit disposition of later completed milestones;
- current resume instruction; and
- next recommended mission, clearly separated from execution authority.

Project State shall be updated during reconciliation when any of these facts
changes. Cosmetic restatement and duplication of unchanged evidence are not
required.

## Checkpoint and EOS Requirements

EOS operational state shall reference the authoritative records from which its
current context derives. A new checkpoint shall be created only after required
reconciliation and shall identify the reconciled boundary and source Project
State. Checkpoint selection, filesystem ordering, or creation time shall not
establish current engineering truth by itself.

After authoritative state changes, EOS derived operational state and resume
context shall be refreshed and validated. If EOS cannot resolve its source
records, reports a checkpoint/state conflict, or cannot determine freshness,
resume is not qualified for implementation.

## Design Objective and Churn Control

Engineering documentation shall remain operationally current without
unnecessary churn. Reconcile facts only in their authoritative owner; other
records shall reference that owner. Derived views shall regenerate from the
reconciled sources. Historical evidence, detailed logs, and conversations need
not be copied into Project State when an attributable controlled reference is
sufficient.

Engineering sessions shall be resumable from authoritative documentation
without reconstructing engineering history from prior conversations.

## Validation and Acceptance

Freshness validation passes only when:

- the latest completed milestone and last reconciliation boundary are
  discoverable;
- no more than two completed milestones remain unreconciled;
- no mandatory trigger remains undispositioned;
- required Engineering State owners agree on current mission, phase, sprint,
  baseline, investigations, and next action within their scopes;
- EOS state and resume context resolve to those authoritative owners;
- any checkpoint conflict is absent or explicitly blocks resume;
- resume contains no known completed objective as current; and
- repository, document, relationship, lifecycle, and index validation pass.

## Stop Conditions

Stop implementation and require reconciliation or Governance review when:

- a third unreconciled milestone would be created;
- a mandatory trigger occurs and reconciliation is incomplete;
- the latest completed milestone or last reconciled boundary cannot be
  determined;
- authoritative owners conflict or a duplicate information owner would be
  created;
- Project State, Sprint State, EOS state, checkpoint, or resume disagree about
  current work in a way that could alter execution;
- resume presents or would present a known obsolete objective;
- source evidence, repository integrity, document relationships, lifecycle
  consistency, or required validation fails; or
- reconciliation would require authority beyond the active mission.

Safe evidence preservation and governance reporting may continue. Additional
implementation shall not.

## Policy Statement

Authoritative Engineering State shall never intentionally drift beyond two
completed engineering milestones behind actual implementation.

Work Initiation shall apply freshness as a risk-proportional gate after mission
classification under PROC-0001. Category A requires full repository and EOS
freshness qualification. Categories B and C require freshness only for the
authoritative state they consume or affect; unrelated repository dirtiness is
informational. No classification waives explicit authority, trust-boundary, or
mission-specific freshness requirements.

## Revision History

| Version | Date | Description |
| ------- | ---- | ----------- |
| 1.0 | 2026-07-15 | Established the Engineering State freshness threshold, reconciliation triggers and scope, operational lifecycle integration, and resume-accuracy requirements. |
| 1.1 | 2026-07-15 | Reconciled the operational lifecycle to place Commit Classification, Commit Execution, and Milestone Qualification after Engineering State Reconciliation and defined their authority boundaries. |
| 1.2 | 2026-07-15 | Added Commit Reconstruction Planning between classification and execution and distinguished the governed what, how, and execution authority boundaries. |
| 1.3 | 2026-07-17 | Integrated mission-classification-driven freshness gates and preserved authority and trust-boundary controls under EGR-000002 and EWO-000018. |
