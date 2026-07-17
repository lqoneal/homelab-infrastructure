---
document_id: PROC-0001
title: Engineering Work Order Execution Procedure
version: 1.6
status: Active
owner: Engineering Governance
created: 2026-07-09
last_updated: 2026-07-17
phase: Governance Framework Modernization
domain: Engineering Governance
classification: Engineering Procedure
source_of_truth: true
related_documents:
  - GEN-0001
  - STD-0000
  - STD-0001
  - STD-0002
  - STD-0003
  - STD-0004
  - POL-0001
  - EWO-000012
  - PROC-0003
  - EGR-000002
  - EWO-000018
tags:
  - governance
  - procedure
  - work-order
  - execution
  - engineering-operating-system
---

# Engineering Work Order Execution Procedure

## Purpose

This procedure defines the approved method for executing an Engineering Work Order within the Engineering Operating System.

It translates the requirements established by the Engineering Governance Policy and Engineering Work Order Standard into a repeatable operational workflow.

This procedure defines how an implementation agent executes an Active Engineering Work Order.

---

## Scope

This procedure applies to every Engineering Work Order executed under the Engineering Operating System.

---

## References

Execution shall conform to:

* POL-0001 — Engineering Governance Policy;
* STD-0000 — Engineering Governance Documentation Architecture;
* STD-0001 — Engineering Document Lifecycle Standard;
* STD-0002 — Engineering Document Persistence Standard;
* STD-0003 — Engineering Work Order Standard.

---

## Execution Principles

Engineering Work Orders shall be executed:

* deterministically;
* within approved scope;
* within granted authority;
* using engineering evidence;
* without assumptions;
* without unauthorized process modification.

---

## Execution Workflow

Every Engineering Work Order shall execute according to the following workflow:

```text
Mission Classification Gate
        ↓
Engineering Document Verification
        ↓
Operational Inventory
        ↓
Operational Preparation
        ↓
Baseline Verification
        ↓
Engineering Phase Execution
        ↓
Engineering Evidence Collection
        ↓
Completion Report
        ↓
Engineering Governance Review
```

---

## Step 1 — Mission Classification Gate

Classify the mission before applying initiation gates. Classification selects
risk-proportional controls; it does not grant authority, waive an EWO, or
override a mission-specific stop condition.

### Category A — Repository Engineering Work

Examples include repository changes, controlled documents, EOS publications,
and version-controlled engineering artifacts.

Required gates:

* full Engineering Platform qualification;
* authority and governance verification;
* repository identity and integrity;
* current Engineering State and EOS synchronization;
* active checkpoint and repository inventory;
* infrastructure, Project State, DOC-0001, and applicable controlled records;
* clean working tree unless an explicit controlled exception identifies the
  pre-existing paths, isolation method, and permitted overlap; and
* no active conflicting Git or lifecycle operation.

### Category B — Local Engineering Environment Work

Examples include `~/.config`, SSH configuration, notification configuration,
workstation-local engineering settings, and local secrets.

Required gates:

* execution environment qualification;
* explicit authority verification;
* applicable governance verification;
* trust-boundary validation;
* secret-handling validation; and
* mission-specific local ownership, permission, and destination controls.

Repository cleanliness shall be recorded but shall not automatically block the
mission unless the mission reads, writes, validates, derives configuration
from, or otherwise interacts with the repository.

### Category C — Operational / Diagnostic Work

Examples include inventory, read-only qualification, diagnostics, monitoring,
hardware inspection, and health assessment.

Required gates:

* execution environment qualification;
* authority and scope verification;
* operational trust-boundary and external-effect verification; and
* mission-specific safety controls.

Repository cleanliness is informational unless repository interaction is
required. Diagnostics do not authorize remediation.

### Mixed or Ambiguous Missions

Use the most restrictive applicable category unless the Active EWO separates
the work into independently authorized and gated phases. If classification is
ambiguous or would materially change the applicable controls, stop and obtain
Engineering Governance disposition. Record classification and gate results in
the Completion Report.

---

## Step 2 — Engineering Document Verification

Purpose:

Verify the execution contract.

Verify:

* Engineering Work Order identifier;
* revision;
* approval status;
* Active lifecycle state;
* no newer Active revision supersedes the current revision.

If verification fails:

STOP.

Engineering Governance authorization is required.

---

## Step 3 — Operational Inventory

Purpose:

Establish the operational environment before execution.

Inventory, as applicable:

* host;
* user;
* repository;
* repositories;
* storage;
* connected media;
* required services;
* runtime environment;
* project state.

When the mission includes recovery acquisition, verification, cleanup,
restoration, or recovery evidence, also review and execute PROC-0003 —
Engineering Recovery Runbook. Work initiation and baseline verification do not
authorize a recovery action that the Work Order does not explicitly permit.

Compare observed state with expected state.

Report differences.

Qualify Engineering State freshness under STD-0004 before implementation:

1. locate authoritative Project State and Sprint State;
2. identify the latest completed milestone and last reconciled boundary;
3. determine the unreconciled milestone count;
4. compare current mission, baseline, investigations, next action, EOS state,
   active checkpoint, and resume output; and
5. report `CURRENT`, `WITHIN THRESHOLD`, or `RECONCILIATION REQUIRED`.

If state cannot be proven current enough, a mandatory trigger remains, or
resume would present obsolete work, perform the separately authorized
Engineering State Reconciliation before additional implementation.

Do not modify the environment.

---

## Step 4 — Operational Preparation

Purpose:

Confirm operational readiness.

Verify required:

* tools;
* utilities;
* repository access;
* permissions;
* dependencies.

Do not perform remediation unless explicitly authorized.

If preparation cannot be completed:

STOP.

Report evidence.

---

## Step 5 — Baseline Verification

Purpose:

Verify engineering integrity before work begins.

For Category A, examples include:

* repository integrity;
* repository identity;
* current branch;
* current HEAD;
* remote configuration;
* working tree state.

Verify all mission-specific baseline requirements defined by the Engineering Work Order.

For Categories B and C, apply the classification-specific gates above and all
mission-specific baseline requirements. Repository cleanliness is not promoted
from informational evidence to a blocker unless repository interaction or an
explicit Work Order condition requires it.

If an applicable baseline verification fails:

STOP.

Engineering Governance authorization is required.

---

## Step 6 — Engineering Phase Execution

Execute only the engineering activities authorized by the Engineering Work Order.

Do not:

* exceed scope;
* infer authority;
* redesign governance;
* modify prohibited engineering assets.

Execute phases sequentially unless the Engineering Work Order explicitly authorizes another execution model.

---

## Step 7 — Engineering Evidence Collection

Collect sufficient engineering evidence to support Engineering Governance review.

Evidence shall be:

* objective;
* reproducible;
* attributable;
* traceable.

Evidence shall correspond to the Engineering Work Order objectives.

---

## Step 8 — Completion Report

Produce the Completion Report required by the Engineering Work Order.

The report shall summarize:

* execution performed;
* engineering evidence;
* mission status;
* execution status;
* scope compliance;
* engineering findings;
* operational observations;
* recommended next Engineering Work Order.

The report title shall be exactly `Completion Report` and shall conform to
TPL-0002. Every Codex engineering mission shall include a completed Governance
Conformance Review containing Authority Verification, Mission Scope
Compliance, Trust Boundary Verification, Controlled Document Compliance,
Authority Circumvention Assessment, Governance Gap Assessment, Documentation
Requirement, and Overall Governance Status.

Authority Circumvention Assessment shall return exactly one allowed value from
STD-0003. A governance gap, exception, ambiguity, or circumvention condition
shall not be silently corrected or omitted. Record the affected authority,
impact, whether it pre-existed the mission, corrective recommendation, and
required follow-up authority.

Mission completion shall not be reported until the Governance Conformance
Review is complete.

Engineering Governance Notes remain blank.

---

## Resume After Interruption

Upon resumption:

1. Repeat the Mission Classification Gate and verify the Active Engineering Work Order.

2. Reapply the classification-specific initiation gates.

3. Perform Operational Inventory and Operational Preparation.

4. Perform the applicable Baseline Verification.

5. Resume at the first incomplete engineering phase.

Before Step 5, repeat the STD-0004 freshness qualification. Authoritative
reconciled Project State and current mission records take precedence over an
older checkpoint. A checkpoint conflict or obsolete resume objective blocks
implementation pending reconciliation.

Completed phases remain complete unless Engineering Governance authorizes repetition.

---

## Engineering Commit Classification

### Purpose and Requirement

Commit Classification ensures that Git history accurately represents
engineering history. Every outstanding repository change shall be classified
before any engineering commit is created. No engineering work, automation,
milestone publication, or repository workflow may bypass classification.

Classification occurs after required Engineering State Reconciliation and
operates on that reconciled state. STD-0004 governs when reconciliation is
required; this procedure governs how repository changes are organized. A
classification mission does not itself authorize staging, committing, tagging,
pushing, milestone publication, or implementation.

### Classification Model

Each change shall receive one or more applicable classifications from this
governed model:

- Governance;
- Standards;
- Procedures;
- Engineering Platform;
- Infrastructure;
- Tooling;
- Recovery;
- Implementation;
- Documentation;
- Engineering Evidence;
- Bug Fix;
- Refactor; and
- Milestone.

Engineering Governance may add classifications when a distinct engineering
domain requires one. Expansion shall preserve existing meanings and shall not
create a duplicate authority or obscure an engineering objective.

### Classification Procedure

Before commit execution, the responsible engineer shall:

1. verify repository identity, branch, HEAD, integrity, upstream state, and
   active Git operations;
2. inventory every modified, added, deleted, renamed, copied, and untracked
   path in every repository within mission scope;
3. preserve and identify pre-existing work without assuming its ownership or
   purpose;
4. associate every change or separable hunk with its engineering objective,
   mission, classification, authoritative records, validation evidence, and
   dependencies;
5. establish commit boundaries so each proposed commit contains one logical
   engineering change set serving one engineering objective;
6. separate unrelated work and retain tightly coupled implementation,
   validation, and directly governing documentation together when their
   independence would be false;
7. order commits so no commit depends on work that appears later in history;
8. identify cross-repository dependencies while preserving one commit per
   repository boundary;
9. identify milestone prerequisites and isolate milestone publication from
   all prerequisite engineering work; and
10. produce a proposed commit plan for review before any commit is created.

When one file contains changes from multiple objectives, classification shall
operate at hunk or reconstructed-revision granularity. Whole-file staging shall
not be used to conceal mixed objectives.

### Commit Principles and Traceability

Every proposed commit shall satisfy all of the following:

- one engineering objective per commit;
- one logical engineering change set per commit;
- no unrelated work in the same commit;
- no artificial separation of changes that are mutually required to validate;
- dependency-aware ordering; and
- sufficient engineering traceability to reconstruct why the change entered
  repository history.

Each commit plan shall identify its engineering objective, repository,
affected files or hunks, classification, dependency position, recommended
title, validation evidence, and rationale. It shall be traceable to controlled
documentation and repository history and, where applicable, to the Engineering
Work Order, Project State, Engineering State, milestone, and completion or
evidence records.

### Pre-Execution Validation

Classification is not complete until all of the following pass:

- every outstanding path and separable change is classified;
- commit boundaries are complete and unambiguous;
- dependency order is established and acyclic;
- repository integrity and the applicable validation suite pass;
- Engineering State is reconciled as required by STD-0004;
- authoritative records, EOS, resume context, and the proposed history do not
  conflict; and
- any milestone prerequisites are explicitly identified and satisfied.

Failure or indeterminate evidence blocks reconstruction planning and commit
execution. Classification approval authorizes only the reviewed classification
unless separate authority explicitly authorizes later lifecycle stages.

### Commit Classification Report

When persistent planning is required, classification shall produce a Commit
Classification Report identifying:

- engineering objectives;
- affected repositories and files or separable hunks;
- engineering classifications;
- dependency relationships;
- proposed commit boundaries; and
- the proposed commit sequence.

The Commit Classification Report answers: **What Engineering History should
exist?**

---

## Commit Reconstruction Planning

### Purpose and Requirement

Commit Reconstruction Planning is a distinct governed engineering activity
between Commit Classification and Commit Execution. It determines the safest
method for faithfully transforming the approved logical change sets into
repository history without losing work, combining objectives, falsifying
revision sequence, or violating dependencies.

Every proposed commit shall have an approved reconstruction plan before Commit
Execution. Planning shall preserve the approved classification; it shall not
silently change objectives, boundaries, order, or scope.

### Required Plan Content

For every proposed commit, determine and document:

- engineering objective;
- repository;
- affected files or hunks;
- dependency ordering;
- selected reconstruction method and its safety rationale;
- validation requirements before and after creation;
- proposed commit title;
- proposed commit message; and
- expected repository, index, working-tree, and validation state after the
  commit.

The Commit Reconstruction Plan answers: **How will the approved Engineering
History be safely created?** Commit Execution shall implement the approved plan
and stop when observed state differs materially from its expected state.

### Acceptable Reconstruction Methods

Acceptable methods include:

- whole-file staging when every selected file belongs entirely to one change
  set;
- interactive hunk staging for independently selectable changes within files;
- temporary index reconstruction when an exact intermediate tree must be built
  without altering the primary working tree;
- a temporary worktree when isolation and full-tree validation are safer than
  index-only reconstruction;
- branch sequencing when dependency boundaries require independently
  reviewable repository history; and
- cherry-pick workflow when already isolated commits must be assembled in an
  approved dependency sequence.

This list is not a mandated preference order. The responsible engineer shall
select the safest method that preserves all existing work, exact logical
boundaries, dependency ordering, validation capability, and traceability.
Destructive reset, loss of untracked work, fabricated historical state, or
unreviewed boundary changes are not acceptable reconstruction techniques.

### Execution Gate

Commit Execution may begin only after successful completion of Engineering
State Reconciliation, Commit Classification, and Commit Reconstruction
Planning. Verify immediately before execution that:

- every modified, deleted, renamed, copied, added, and untracked file is
  classified;
- every proposed commit has an approved reconstruction plan;
- dependency ordering is approved and acyclic;
- applicable repository validation passes;
- Engineering State remains reconciled under STD-0004;
- milestone prerequisites are satisfied or explicitly assigned to earlier
  planned commits; and
- the repository and working tree still match the planning baseline.

Any mismatch, new unclassified change, failed validation, or obsolete
Engineering State blocks execution and returns the workflow to the applicable
prior stage.

### Engineering Planning Artifact Governance

Routine work containing one logical objective in one repository may use
ephemeral classification and reconstruction planning when its boundaries,
dependencies, validation, and expected state are unambiguous. The rigor and
execution gates of this procedure still apply.

Persistent Commit Classification Reports and Commit Reconstruction Plans are
mandatory for work involving any of the following:

- multiple engineering objectives;
- multiple repositories;
- milestone publication;
- repository-wide reconciliation;
- governance, standards, or procedure reconciliation;
- Engineering Platform modification;
- complex dependency ordering; or
- commit reconstruction planning beyond an unambiguous whole-file commit.

For milestone, governance, standards, procedure, Engineering Platform,
repository-wide, and complex multi-objective work, both artifacts shall be
retained as controlled engineering planning records or within the designated
engineering planning location at `engineering/planning/` in the governing
repository. Their storage authority, identifier, review,
approval, revision, retention, and relationships shall follow the existing
documentation architecture of that repository. They shall reference one
another and the applicable Project State, Engineering State, Work Order,
milestone, and validation evidence when those records exist.

Persistent planning records support review and reconstruction; they do not
become a second Project State, authorize commits, or replace repository history.
Engineering rigor shall remain proportional to complexity.

### Milestone Rule

A milestone commit shall never be a catch-all commit. Before milestone
publication, engineering work shall proceed in this order:

1. classify all outstanding work;
2. prepare and approve Commit Reconstruction Plans;
3. review and approve both planning artifacts;
4. execute prerequisite commits in dependency order under commit authority;
5. validate the resulting repository state;
6. qualify the milestone against its authoritative prerequisites;
7. publish the milestone in its own logical commit; and
8. create the milestone tag only under explicit tag authority after the
   milestone commit succeeds.

Unrelated cleanup, implementation, evidence, governance, or documentation
shall not be absorbed into milestone publication.

---

## Communication Requirements

Implementation agents shall communicate:

* observations;
* evidence;
* mission impact;
* recommendations.

Implementation agents shall not:

* infer governance intent;
* conceal uncertainty;
* continue after encountering approved stop conditions.

---

## Stop Conditions

Execution shall stop immediately when:

* granted authority is exceeded;
* Engineering Governance authorization is required;
* deterministic execution cannot be maintained;
* baseline integrity fails;
* approved stop conditions are encountered.

The implementation agent shall report:

* observation;
* evidence;
* mission impact;
* recommendation.

No further engineering work shall occur until authorized.

---

## Completion Criteria

Execution is complete when:

* all Engineering Work Order objectives have been addressed;
* required engineering evidence has been collected;
* the Completion Report has been produced;
* execution has stopped at the authorized endpoint.

Engineering Governance determines mission acceptance.

---

## Compliance

Implementation agents shall comply with:

* Engineering Governance Policy;
* Engineering Work Order Standard;
* Engineering Work Order;
* applicable Engineering standards;
* applicable Engineering procedures.

Authority not explicitly granted remains prohibited.

---

## Success Criteria

This procedure is complete when every implementation agent can execute an Active Engineering Work Order deterministically, consistently, and within the approved governance framework from document verification through completion reporting.

---

## Revision History

| Version | Date | Description |
| ------- | ---- | ----------- |
| 1.0 | 2026-07-09 | Initial Engineering Work Order Execution Procedure established. |
| 1.1 | 2026-07-10 | Replaced Issued verification with Active execution-authority verification under EWO-000012. |
| 1.2 | 2026-07-15 | Required recovery work initiated under this procedure to consume PROC-0003 without expanding mission authority. |
| 1.3 | 2026-07-15 | Integrated STD-0004 freshness qualification and reconciliation gating into Work Initiation and resume after interruption. |
| 1.4 | 2026-07-15 | Established mandatory Commit Classification, traceability, validation, dependency ordering, commit boundaries, and milestone publication controls after Engineering State Reconciliation. |
| 1.5 | 2026-07-15 | Established Commit Reconstruction Planning, approved reconstruction methods, execution gates, persistent planning artifacts, and proportional planning governance. |
| 1.6 | 2026-07-17 | Added the Mission Classification Gate, risk-proportional Category A/B/C initiation, exact Completion Report standard, and mandatory Governance Conformance Review under EGR-000002 and EWO-000018. |
