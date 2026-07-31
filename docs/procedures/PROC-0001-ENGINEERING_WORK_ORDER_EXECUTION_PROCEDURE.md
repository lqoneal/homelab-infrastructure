---
document_id: PROC-0001
title: Operational Alpha Work Initiation and Execution Procedure
version: 2.3
status: Active
owner: Engineering Governance
created: 2026-07-09
last_updated: 2026-07-31
phase: Engineering Execution Interface Standardization
domain: Engineering Governance
classification: Engineering Procedure
source_of_truth: true
predecessor_revision: PROC-0001@1.18
successor_revision: null
approval_status: Approved
approval_authority: Engineering Governance
approval_reference: EGR-000006
approval_date: 2026-07-18
persistence_status: Persisted
declared_deferrals: []
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
    target: PROC-0003
  - type: related_to
    target: PROC-0005
  - type: related_to
    target: PROC-0006
  - type: related_to
    target: PROC-0007
  - type: related_to
    target: SPEC-0004
  - type: related_to
    target: SPEC-0005
  - type: related_to
    target: EGR-000002
  - type: related_to
    target: EWO-000018
  - type: related_to
    target: EWO-000019
  - type: indexed_by
    target: DOC-0001
tags:
  - governance
  - procedure
  - work-order
  - execution
  - engineering-operating-system
mission_assurance_requirements:
  - id: MA-GATES-001
    language_version: '1.0'
    phase: preflight
    description: All required pre-execution review gates are approved.
    assertion:
      selector: state.review_gates
      operator: required_map_values_equal
      value: approved
      exclude:
        - operator_acceptance
  - id: MA-LIFECYCLE-001
    language_version: '1.0'
    phase: execution
    description: Mission lifecycle is eligible for execution.
    assertion:
      all:
        - selector: state.mission.status
          operator: equals
          value: ACTIVE
        - selector: state.lifecycle.state
          operator: equals
          value: active
        - selector: state.lifecycle.implementation_status
          operator: not_equals
          value: complete
  - id: MA-SOURCES-001
    language_version: '1.0'
    phase: synchronization
    description: All authoritative source records resolve.
    applicability: &post_implementation
      any:
        - selector: state.lifecycle.implementation_status
          operator: equals
          value: complete
        - selector: state.mission.status
          operator: equals
          value: COMPLETED
    assertion:
      selector: state.sources
      operator: all_paths_exist
  - id: MA-RECONCILIATION-001
    language_version: '1.0'
    phase: synchronization
    description: Mission Contract and Work Registry lifecycle agree.
    applicability: *post_implementation
    assertion:
      selector: state.blockers
      operator: not_contains
      value: MISSION_REGISTRY_LIFECYCLE_CONFLICT
  - id: MA-COMPLETION-EVIDENCE-001
    language_version: '1.0'
    phase: synchronization
    description: Completion report resolves after implementation.
    applicability: *post_implementation
    assertion:
      selector: state.lifecycle.completion_report
      operator: path_exists
  - id: MA-IMPLEMENTATION-001
    language_version: '1.0'
    phase: closeout
    description: Implementation is complete.
    applicability: *post_implementation
    assertion:
      selector: state.lifecycle.implementation_status
      operator: equals
      value: complete
  - id: MA-ACCEPTANCE-001
    language_version: '1.0'
    phase: closeout
    description: Required operator acceptance is recorded.
    applicability: *post_implementation
    assertion:
      selector: state.lifecycle.acceptance_status
      operator: one_of
      value:
        - approved
        - accepted
        - complete
  - id: MA-SYNCHRONIZATION-001
    language_version: '1.0'
    phase: closeout
    description: Post-mission synchronization requirements are satisfied.
    applicability: *post_implementation
    assertion:
      all:
        - selector: state.sources
          operator: all_paths_exist
        - selector: state.blockers
          operator: not_contains
          value: MISSION_REGISTRY_LIFECYCLE_CONFLICT
        - selector: state.lifecycle.completion_report
          operator: path_exists
  - id: MA-CLOSEOUT-001
    language_version: '1.0'
    phase: closeout
    description: Mission lifecycle records completion.
    applicability: *post_implementation
    assertion:
      all:
        - selector: state.mission.status
          operator: equals
          value: COMPLETED
        - selector: state.lifecycle.state
          operator: equals
          value: completed
---

# Operational Alpha Work Initiation and Execution Procedure

## Operational Alpha convergence migration

For Operational Alpha, this procedure is interpreted through SPEC-0014. The
former Work Registry Mission Contract and Active Engineering Work Order
admission path is superseded for new actions. Historical records remain
read-only evidence. The normal initiation authority chain is Governance
Decision → Authority Record → EMM → published Implementation WOP → resolution
receipt → preflight qualification. During the active manual-governance phase,
an explicitly submitted, EMM-resolved WOP may instead resolve its exact
allowlisted root actions under `MANUAL-GOVERNANCE-WOP-AUTHORITY-POLICY`; all
autonomous WOPs use the normal chain. No step in this procedure activates a
WOP by itself.

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
* STD-0003 — Engineering Work Order Standard;
* STD-0004 — Engineering State Freshness Standard;
* PROC-0005 — Controlled Document Publication Procedure, when the Work Order includes controlled publication; and
* PROC-0006 — Governance Qualification Procedure, when the Work Order includes Governance qualification; and
* PROC-0007 — Governance Stabilization Procedure, when the Work Order includes Governance subsystem reconciliation.

---

## Execution Principles

Operational Alpha implementation WOPs shall be executed:

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
Canonical Metadata Resolution
        ↓
Authority Record or Manual-Governance Root Verification
        ↓
Implementation WOP / Baseline Verification
        ↓
Preflight Qualification
        ↓
Authorized Capability Execution
        ↓
Evidence, Synchronization, and Reconciliation
        ↓
Completion Report and Qualification
```

## Repository-Authoritative Engineering Execution Interface

This procedure owns the canonical lifecycle:

```text
Governance Decision
        ↓
Authority Record
        ↓
EMM Resolution
        ↓
Implementation WOP
        ↓
Qualified Capability Execution
        ↓
Verification and Reconciliation
        ↓
Completion Report
        ↓
Resume
```

The machine-readable index at
`engineering/execution/execution-interface.yaml` binds each capability to its
existing semantic owner and is consumed through `engctl execution`. The index
is operational routing data; it does not replace controlled authority.

Every execution agent shall begin with repository discovery and a mission
snapshot. The snapshot resolves repository identity, current mission, phase,
authority reference, objectives, completion criteria, lifecycle state, next
action, blockers, and source records without prompt history. Conversational
context may identify the requested mission but shall not supply missing
procedure, authority, state, or completion semantics.

The normal resolved authority contract is the SPEC-0014 Authority Record, exact
EMM entity revisions, and the baseline-bound Implementation WOP. While the
manual-governance policy is active, an exact EMM-resolved WOP may instead be
the root authority for its own explicit allowlisted actions if its governance
submission and active delegation validate. The Work Registry and historical
EWOs may be consumed as traceability inputs but cannot grant, deny, or replace
either current contract for Operational Alpha.

Authority Records, Operational Gate Plans, and Activation Records are
constructed and published through `OPERATIONAL-ALPHA-CONTROLLED-ARTIFACT-
FRAMEWORK@1.0`. A generated candidate is not a controlled record and cannot
advance lifecycle until its source digest is registered in EMM and runtime
resolution validates the published source.

## Mission-Assurance Verification

The execution workflow and its lifecycle transitions remain owned by this
procedure and the controlled authorities it references. Zeus independently
verifies their operational results; Zeus does not perform, waive, approve, or
take ownership of those requirements.

Before execution, Zeus shall derive the applicable Mission Contract and
pre-mission requirements from the canonical Engineering Execution Interface.
Discovery cardinality is evidence: execution fails closed unless exactly one
Mission Contract resolves. Zeus shall verify repository identity,
mission-scoped authority, required review gates, WOP applicability, canonical
blockers, and lifecycle eligibility from authoritative operational state.

During execution, the same verification shall remain available so that a
regression makes continued execution ineligible. After implementation, Zeus
shall verify source-record resolution, Mission Contract and Work Registry
lifecycle agreement, and required Completion Report evidence before reporting
synchronization complete. Closeout eligibility additionally requires completed
implementation, recorded required acceptance, completed lifecycle state, and
successful synchronization.

Each assurance result shall identify the mission, phase, applicable
requirements, authoritative sources, observed values, unsatisfied requirement
identifiers, eligibility disposition, and a deterministic evidence digest.
An observation command does not create approval, acceptance, execution
authority, synchronization, or a lifecycle transition.

---

## Codex Launch Enforcement

Every repository-governed Codex engineering mission SHALL launch through:

```bash
engctl codex --ewo EWO-XXXXXX -- [codex arguments ...]
```

The wrapper establishes the notification lifecycle and an inherited execution
marker. `homelabctl resume`, `engctl resume`, and Engineering Work Initiation
qualification detect a Codex context without that marker, report a wrapper
bypass engineering condition, attempt a value-free bypass notification, and
stop with exit status 78. A bypass is not converted into authority by setting
environment variables manually.

An exception must be explicit in an approved Active EWO, identify why wrapper
launch is technically impossible, define equivalent notification and evidence
controls, and be reported in the Completion Report. EWO-000019 itself is the
one-time bootstrap exception needed to establish this enforcement.

Wrapper start, completion, failure, timeout, and interruption events are
operational metadata only. Prompts, output, diffs, repository content, private
configuration, topics, endpoints, tokens, and credentials shall not enter the
notification body.

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

For publication work, the initiation record shall also resolve PROC-0005 and
the repository–EOS synchronization procedure, then record the Initial
Validation, Publication, Synchronization, and Final Validation Boundaries
before execution. EOS comparison is read-only during initiation. Repository
content remains authoritative, EOS remains a derived projection, and a
repository commit does not automatically synchronize EOS.

If repository authority advanced inside an authorized publication sequence
before its declared Synchronization Boundary, classify an otherwise exact
repository-to-EOS mismatch as `EXPECTED_PUBLICATION_DRIFT`. Do not invoke an
auto-repairing resume or qualification path and do not synchronize. At the
declared boundary classify the condition as `SYNCHRONIZATION_REQUIRED`, pause
publication advancement, and require separately established synchronization
authority and prerequisites. Source, synchronization, and runtime failures
shall use `AUTHORITATIVE_SOURCE_FAILURE`, `SYNCHRONIZATION_FAILURE`, and
`RUNTIME_STATE_FAILURE` respectively.

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

Repository discovery shall include:

```bash
engctl repository discover homelab
engctl repository health homelab
engctl registry validate
engctl execution snapshot --mission <MISSION-ID>
```

A missing, ambiguous, stale, or conflicting SPEC-0014 resolution receipt, EMM
revision, or Implementation WOP blocks Operational Alpha implementation. A
missing Authority Record also blocks unless the exact WOP has a valid active
manual-governance submission and its requested action is explicitly
allowlisted. Legacy Mission Contract failures are traceability observations,
not authority-resolution inputs. Resolve a current failure as follows:

1. preserve the normal authority-resolution result;
2. evaluate every Governance Bootstrap Condition predicate defined by
   SPEC-0011;
3. when any predicate fails, execute the existing fail-closed STOP behavior;
4. when every predicate passes, suspend execution, produce a Bootstrap
   Detection Report, and request Engineering Governance guidance under
   PROC-0002.

Bootstrap detection does not create execution authority. During suspension an
execution agent shall not modify authoritative metadata, invent or expand
authority, implement a product or feature, complete or accept a gate, advance
a gate, reinterpret controlled documentation, or change repository content.
Resume is permitted only after the correcting successor fact is published and
SPEC-0014 resolution independently succeeds.

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

The report shall conform to STD-0003 and instantiate TPL-0002. Begin with the
exact required heading and complete the execution record before findings or
certification. Do not restate or redefine the standard section model in the
Engineering Work Order.

### Report Production Workflow

1. Record transaction identity, governing authority, executed scope, and
   execution agent.
2. Record repository start and end identity, branch, commit, working-tree and
   index state, plus runtime state where applicable.
3. Summarize relevant commands and activities without disclosing secrets or
   substituting raw transcript volume for attributable evidence.
4. Inventory controlled artifacts reviewed, repository and runtime changes,
   validation activities, and delivered artifacts.
5. For every validator, distinguish partial output from terminal completion.
   Capture the terminal exit status and do not claim a conclusion until the
   validator has completed. A pipeline or subsequent successful command shall
   not mask the validator status. When a governing procedure defines
   file-type-aware finding classification, record both the raw exit status and
   the governed classification; do not relabel, suppress, or silently repair
   the raw result.
6. Complete mission status, scope compliance, completion criteria, and the
   execution/results boundary required by STD-0003.
7. Present Findings, Analysis, Recommendations, Final Certification, and
   Follow-on Work in the standard order.
8. Complete the Governance Conformance Review. Mission completion shall not be
   reported before it is complete.

Use `Not Applicable` with rationale when a mandatory section does not apply.
Historical Completion Reports remain valid and shall not be rewritten solely
to adopt the current structure.

Authority Circumvention Assessment shall return exactly one allowed value from
STD-0003. A governance gap, exception, ambiguity, or circumvention condition
shall not be silently corrected or omitted. Record the affected authority,
impact, whether it pre-existed the mission, corrective recommendation, and
required follow-up authority.

Engineering Governance Notes remain blank.

Completion Reports record mission delta only: relevant starting state, actions
performed, changed artifacts, terminal verification results, reconciliation,
remaining work, and final status. They reference rather than restate reusable
procedures, standards, inventories, or unchanged repository history.

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

Resume regenerates the Mission Snapshot from repository records and continues
at the first incomplete lifecycle step. Prompt history and agent memory are
never resume inputs. Completed evidence remains complete unless its binding
regresses or the Mission Contract requires revalidation.

## Command Authority Integration

All operations shall be classified under SPEC-0005. Automatic and
mission-pre-authorized operations proceed without repeated confirmation when
their classification and scope match. Explicit-approval operations require a
separate recorded operator decision. Emergency-stop operations shall not
execute automatically. Ambiguity escalates to the more restrictive class and
fails closed when authority cannot be resolved.

---

## Controlled Document Publication Integration

When an Active Engineering Work Order includes controlled document publication,
execution shall consume PROC-0005 in addition to this procedure.

PROC-0001 remains the owner of Work Order execution, mission classification,
Engineering State verification, evidence collection, Completion Reports,
Commit Classification, and Commit Reconstruction Planning. PROC-0005 owns the
common publication gates, frozen publication content, exact publication
boundary, controlled publication transaction, and post-publication verification.

Execution-generated publication control artifacts shall be routed to the
active PROC-0005 transaction output ledger when their production event occurs.
Their creation does not modify the frozen publication-input manifest. PROC-0001
records the artifact identity, class, owner, generating event, and handoff to
the declared transaction output boundary. If immutable transaction
finalization has already occurred, PROC-0001 routes the artifact to a linked
corrective successor transaction instead of reopening or rewriting history.

The publication transaction may begin only after the applicable PROC-0005
authorization gate passes. Neither procedure supplies Governance approval,
lifecycle-transition authority, repository authority, or implementation
authority absent the governing Work Order or superior authorization. Milestone
publication retains the specialized dependency order defined below.

## Governance Qualification Integration

When an Active Engineering Work Order includes Governance qualification,
execution shall consume PROC-0006 in addition to this procedure. PROC-0001
remains the owner of bounded Work Order execution, evidence collection, and
Completion Report production. PROC-0006 owns the reusable qualification stages
and returns its result and routing recommendation to the caller; it supplies no
Governance decision, lifecycle, publication, baseline, or implementation
authority.

## Governance Stabilization Integration

When an Active Engineering Work Order includes Governance subsystem
reconciliation, execution shall consume PROC-0007 in addition to this
procedure. PROC-0001 remains the owner of bounded Work Order execution,
evidence collection, and Completion Report production. PROC-0007 coordinates
the authorized reconciliation and returns routing packages to its caller; it
does not execute changes, qualify results, decide Governance dispositions,
publish, designate baselines, or authorize implementation.

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

### Operational Alpha Admission and Activation

For Operational Alpha, this entire section is superseded by SPEC-0014's
Authority Record and WOP lifecycle. The historical terminology retained below
documents provenance only and shall not be evaluated by the runtime resolver.

Engineering Governance is the sole Mission Admission Authority until
controlled documentation explicitly establishes another model. A WOP manually
submitted by Engineering Governance is intentionally submitted and admitted.
Admission records Governance intent only and remains valid until explicitly
revoked by Engineering Governance.

Engineering Governance is separately the sole Mission Activation Authority.
Activation authorizes the system to begin execution qualification. It does not
guarantee successful execution. An execution agent shall never independently
admit, revoke, or activate a mission.

Repository identity, repository integrity, package integrity, Mission Contract
resolution, authority resolution, and execution verification shall determine
execution readiness independently of Mission Admission. Objective failure
shall set execution status to `BLOCKED` and preserve the admitted mission and
Governance activation record. Execution verification does not reinterpret,
reverse, or invalidate admission or activation.

The activation service shall lock the repository boundary, verify
that no conflicting active Mission Contract exists, and atomically reconcile
the Mission Contract, Work Registry, Project State, and activation evidence.
EOS is a derived projection and shall synchronize and validate before the
transaction is complete. Any failure shall restore repository before-images
and regenerate EOS from the restored records. Direct candidate-to-active
lifecycle mutation is prohibited.

After interruption, an incomplete activation journal shall be recovered before
new activation is attempted. A committed request is idempotent. A terminal
Mission Contract cannot reactivate. Operational execution shall begin only
when exactly one active Mission Contract resolves and resume and execution
snapshot interfaces report identical authority.

The canonical manual lifecycle is:

`Engineering Governance -> Manual WOP Submission -> Mission Admission ->
Repository Identity Verification -> Repository Integrity Verification ->
Package Integrity Verification -> Mission Activation -> Mission Contract
Resolution -> Execution Verification -> Mission Execution`.

Execution agents participate beginning with repository verification. Mission
intent originates with Engineering Governance.

### Independent Mission State

Governance state and execution state are separate dimensions:

| Governance state | Meaning |
| --- | --- |
| `Submitted` | Engineering Governance has submitted the mission for admission. |
| `Admitted` | Engineering Governance has intentionally accepted the mission into the Engineering Operating System. |
| `Activated` | Engineering Governance has authorized execution qualification to begin. |
| `Revoked` | Engineering Governance has explicitly withdrawn admission or activation. |
| `Completed` | Engineering Governance has closed the governance lifecycle. |

| Execution state | Meaning |
| --- | --- |
| `Pending Verification` | Execution qualification has not completed. |
| `Verification Failed` | An objective readiness check failed. |
| `Ready` | Every required execution-readiness check currently passes. |
| `Executing` | Authorized mission execution is in progress. |
| `Suspended` | Execution has paused without changing Governance state. |
| `Failed` | Execution terminated unsuccessfully without changing Governance state. |
| `Completed` | Execution completed; Governance closeout remains independent. |

Governance state changes only through Engineering Governance. Execution state
changes through objective execution events.

### Blocked Missions

A verification failure shall report:

```text
Mission Status: ADMITTED
Execution Status: BLOCKED
```

A blocked mission remains admitted, attributable, auditable, and awaiting
correction. After correction it may resume execution qualification from the
applicable verification boundary without a new Mission Admission. An execution
agent shall never reinterpret a blocked mission as not admitted.

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
| 2.0 | 2026-07-30 | Migrated Operational Alpha initiation, authority resolution, lifecycle, synchronization, qualification, and completion routing to SPEC-0014. |
| 2.1 | 2026-07-30 | Added the active manual-governance WOP root-authority exception for exact allowlisted actions, preserving normal Authority Record requirements for autonomous WOPs. |
| 2.3 | 2026-07-31 | Recognized the EMM-controlled immutable Implementation-WOP lifecycle-transition projection defined by SPEC-0014@1.4; transition publication and reconciliation precede any effective ACTIVE state. |
| 1.5 | 2026-07-15 | Established Commit Reconstruction Planning, approved reconstruction methods, execution gates, persistent planning artifacts, and proportional planning governance. |
| 1.6 | 2026-07-17 | Added the Mission Classification Gate, risk-proportional Category A/B/C initiation, exact Completion Report standard, and mandatory Governance Conformance Review under EGR-000002 and EWO-000018. |
| 1.7 | 2026-07-17 | Required repository-governed Codex missions to launch through `engctl codex`, added initiation-time bypass detection and exception controls, and defined the mandatory notification lifecycle under EWO-000019. |
| 1.8 | 2026-07-18 | Established the execution-first report production workflow, repository start/end capture, safe activity summaries, terminal validator-status requirements, partial-output handling, applicability treatment, and ordered results reporting. |
| 1.9 | 2026-07-18 | Integrated PROC-0005 for controlled publication missions while preserving PROC-0001 ownership of Work Order execution, evidence, Completion Reports, Commit Classification, Commit Reconstruction Planning, and milestone sequencing. |
| 1.10 | 2026-07-18 | Integrated Active PROC-0006 for Governance qualification missions while preserving PROC-0001 ownership of bounded Engineering Work Order execution, evidence, and Completion Reports. |
| 1.11 | 2026-07-18 | Integrated Active PROC-0007 for Governance stabilization missions while preserving PROC-0001 bounded-execution ownership and PROC-0007 orchestration-only responsibility. |
| 1.12 | 2026-07-28 | Standardized the repository-authoritative Engineering Execution Interface, Mission Snapshot, minimal handoff consumption, mission-delta reporting, repository-only resume, and command-authority integration. |
| 1.13 | 2026-07-28 | Candidate: routed canonical discovery, authority, snapshot, and handoff validation through the SPEC-0005 Engineering Execution Contract with mandatory framework review gates. |
| 1.14 | 2026-07-28 | Candidate: defined independent Zeus mission-assurance verification across preflight, execution, synchronization, and closeout while preserving this procedure's process ownership. |
| 1.15 candidate | 2026-07-28 | Added deterministic mission admission, activation-request, atomic reconciliation, rollback, interruption recovery, cardinality, and shared authority-reporting workflow. |
| 1.16 | 2026-07-29 | Added Governance Bootstrap consultation and normal-authority re-entry; defined independent Governance and execution state, Governance-only admission and activation, and resumable blocked missions. |
| 1.17 | 2026-07-29 | Corrected publication Work Initiation to declare four repository–EOS boundaries, preserve repository authority, classify expected publication drift, and require separate synchronization authority. |
| 1.18 | 2026-07-29 | Required validator evidence to preserve raw exit status while applying only explicitly governed file-type-aware finding classifications. |
| 1.19 | 2026-07-29 | Routed execution-generated publication control artifacts to the active PROC-0005 output ledger or, after immutable finalization, to a linked corrective successor transaction. |
