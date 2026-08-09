---
document_id: PROC-0009
title: Roadmap and Planning Recording Procedure
version: 0.4
status: Draft
owner: Engineering Governance
created: 2026-08-06
last_updated: 2026-08-06
phase: Roadmap Procedure Maturity Corrective
domain: Engineering Governance
classification: Engineering Procedure
predecessor_revision: null
successor_revision: null
approval_status: Pending
approval_authority: Engineering Governance
approval_reference: null
approval_date: null
persistence_status: Pending
source_of_truth: false
information_scope: Roadmap and planning artifact classification, recording, reconciliation, publication preparation, verification, revision, supersession, and planning/execution boundary
declared_deferrals:
  - controlled-document-index-registration
  - roadmap-identifier-allocation
  - roadmap-mission-binding-schema
  - roadmap-eos-projection-contract
  - zeus-roadmap-automation
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
    target: SPEC-0001
  - type: related_to
    target: PROC-0001
  - type: related_to
    target: PROC-0005
  - type: related_to
    target: PROC-0006
  - type: related_to
    target: PROC-0007
  - type: indexed_by
    target: DOC-0001
tags:
  - roadmap
  - planning
  - reconciliation
  - traceability
  - verification-first
  - anti-duplication
---

# Roadmap and Planning Recording Procedure

## 1. Purpose and authority boundary

This procedure defines the repeatable method for classifying, recording,
reconciling, reviewing, publishing, verifying, revising, and superseding an
engineering roadmap or persistent planning record.

This procedure implements existing authority. It does not create, expand,
replace, or independently confer governance, planning, information, mission,
execution, approval, publication, synchronization, or other authority. A
Draft or Active state for this procedure, or for a roadmap, cannot itself
authorize repository mutation, WOP execution, provider invocation, mission
activation, controlled-document publication, EOS mutation, or lifecycle
advancement. Any unresolved authority is routed to its existing owner and
blocks the affected mutation or advancement.

Apply this procedure with the current valid revisions of CHAR-0001, POL-0001,
STD-0000, STD-0001, STD-0002, SPEC-0001, PROC-0001, PROC-0005, PROC-0006,
PROC-0007, the applicable Mission Contract, WOP, capability records, project
state, and EOS contract. A superior or class-specific authority controls when
this procedure is more restrictive. A missing, stale, conflicting, or
ambiguous authority is a stop condition.

### Governing Roadmap Management Invariant

Zeus must always be able to reconstruct both what was planned and what actually occurred, determine whether execution remains aligned with the authoritative plan, and derive the remaining plan to completion without rewriting engineering history or independently creating execution authority.

### Roadmap Approval Does Not Authorize Execution

Roadmap approval does not authorize execution.

Approval of an authoritative planning roadmap authorizes its use as the current planning and coordination reference only. It does not activate a mission, authorize a WOP, invoke a provider, permit repository mutation, authorize publication, or advance any execution lifecycle state.

All execution remains subject to the independently applicable mission, WOP, approval, provider, and execution authority contracts.

## 2. Scope and vocabulary

This procedure applies to a planning record intended to describe engineering
sequence, objectives, dependencies, milestones, planned capabilities, or
reconciliation targets. It applies to new records, revisions, adoption of a
roadmap after work has already occurred, and closeout reconciliation.

The procedural profile `AUTHORITATIVE_PLANNING_ROADMAP` means a planning
artifact whose declared scope and information authority have been resolved
through the applicable existing authority chain. It does not mean that the
roadmap grants execution authority.

The following dispositions reuse the controlled-document lifecycle and
existing authority vocabulary; they are not a second global lifecycle:

* **AUTHORITATIVE_PLANNING_ROADMAP** — current planning reference for its
  declared scope after authorized recording and publication.
* **IMPLEMENTATION_PLAN** — subordinate work-planning material bounded by an
  authoritative roadmap and the applicable mission/WOP authority. It may
  decompose or sequence authorized work but cannot modify, supersede, or
  authorize beyond the roadmap or its governing authority.
* **SUPERSEDED/HISTORICAL_ROADMAP** — preserved predecessor or historical
  record that no longer controls current planning.
* **INFORMATIONAL/EXPLORATORY_PLAN** — reference material that cannot direct
  work or represent authoritative planning facts.

Planning authority and execution authority are separate. Roadmap objectives
may be planned, reviewed, or verified without authorizing implementation.
Only the applicable existing mission, WOP, Engineering Work Order, and
governance records can authorize execution.

Classification is recorded with its rationale, scope, authority source,
review/lifecycle state, and relationship to the current planning reference.
Ambiguous classification is read-only inspectable but not recordable as an
authoritative planning artifact.

## 3. Roles and delegated ownership

| Concern | Existing owner consumed by this procedure |
| --- | --- |
| Governance and lifecycle authority | Engineering Governance; CHAR-0001, POL-0001, STD-0001 |
| Representation and relationships | SPEC-0001 |
| Persistence, discovery, and immutable history | STD-0002 and DOC-0001 |
| Work initiation and execution | PROC-0001 and the applicable Active WOP/EWO |
| Controlled publication mechanics | PROC-0005, when its authority is active and applicable |
| Qualification evidence and recommendation | PROC-0006 |
| Stabilization/reconciliation routing | PROC-0007, when applicable |
| Mission facts and eligibility | The applicable Mission Contract and mission knowledge owner |
| Capability facts | The applicable Capability Registry owner |
| EOS projection and synchronization | The applicable EOS authority and synchronization procedure |
| Runtime presentation or automation | Zeus as a consumer/derived view; Zeus does not qualify or create authority |

This procedure coordinates these owners. It does not copy their authoritative
facts into a competing roadmap-specific registry.

## 4. Entry and authority resolution

Before authoring or changing a roadmap, the operator shall record:

1. repository root, identity, branch, HEAD, published baseline, and working
   tree state;
2. active project, operation, mission, phase, execution, WOP/EWO, and
   authority records;
3. current revisions and lifecycle of this procedure and every directly
   applicable authority;
4. repository and EOS synchronization state and any declared baseline
   divergence;
5. the current authoritative roadmap, if one exists, and its digest,
   locator, revision, and predecessor/successor lineage;
6. the requested operation: author, adopt, revise, reconcile, publish,
   supersede, archive, or inspect; and
7. the exact intended scope and affected objectives.

If the active roadmap, scope, authority, identity, or lineage cannot be
resolved uniquely, permit read-only inspection and evidence collection but
block mutation or advancement. Record `BLOCKER`, `CAUSE`, `EVIDENCE`, and
`NEXT_AUTHORIZED_ACTION`.

## 5. Classification and identity resolution

Resolve classification before content is treated as authoritative. Record:

* classification and rationale;
* scope and operation/project binding;
* authority source and information owner;
* whether the record is controlled, a registered planning artifact, or
  informational material;
* lifecycle, approval, and persistence states separately; and
* the execution-authority boundary.

For a controlled roadmap, resolve the permanent `document_id`, version,
revision lineage, class, owner, lifecycle, approval and persistence metadata,
relationships, canonical locator, effective baseline, effective date,
supersession links, repository binding, applicable EOS projection/binding, and
content digest under SPEC-0001, STD-0001, STD-0002, and DOC-0001. A filename
is a locator, not a substitute for identity, and a digest is an integrity
binding, not a complete identity. If the applicable authority does not
allocate an identifier, stop and route identifier allocation to that
authority; do not invent one.

The minimum roadmap identity record is:

```text
roadmap_id
revision_or_version
classification
lifecycle_state
scope
operation_or_project_id
mission_id_when_applicable
authority_source
repository_locator
effective_baseline
effective_date
predecessor_revision
successor_revision
repository_binding
eos_projection_or_binding_when_applicable
content_digest
```

Lifecycle, authority, and persistence are separate dimensions. Use the
existing controlled-document vocabulary for draft/revision, review or
qualification, publication, active/current planning reference,
superseded, and historical/archive retention. `ACTIVE` means the current
planning reference for the resolved scope; it does not authorize execution.
An active revision cannot be selected when competing active roadmaps or
ambiguous supersession lineage exist.

Relationships shall use existing SPEC-0001 relationship mechanisms wherever
available. Unresolved relationships are recorded as unresolved and block the
affected transition; they are never fabricated.

## 6. Recording workflow

Perform the following ordered stages. A delegated procedure owns its stage;
this procedure records the handoff and consumes the result.

Before each stage, inspect authoritative state and determine whether the
intended condition is already satisfied. If it is satisfied, do not repeat a
mutation; resolve or record the existing evidence and continue from the
correct lifecycle point. Only an unmet, authorized condition may permit a
mutation. This verification-first rule applies on replay and after
interruption as well as on the initial operation.

1. **Authoring** — prepare the proposed roadmap or revision and preserve the
   prior record unchanged.
2. **Classification** — resolve the profile, scope, owner, and planning versus
   execution boundary.
3. **Identity** — resolve identifier, revision, lineage, locator, baseline,
   and digest.
4. **Authority and relationships** — resolve project/operation, mission,
   WOP/work, gate, evidence, capability, publication, and EOS relationships.
5. **Content validation** — validate required fields, deterministic objective
   identities, dependencies, completion criteria, traceability, blockers,
   and reconciliation state.
6. **Historical reconciliation** — compare the proposed plan with completed
   work and current capability evidence before recommending new work.
7. **Review and qualification** — obtain applicable PROC-0006 evidence and
   the required Engineering Governance review/approval. Qualification is a
   recommendation, not approval or publication authority.
8. **Publication** — invoke PROC-0005 for a controlled publication when its
   class and authority apply. Do not reimplement publication mechanics here.
9. **Synchronization** — invoke the applicable EOS boundary only after the
   repository publication boundary succeeds and preserve source identity and
   digest in the projection.
10. **Verification** — verify registration, binding, persistence, digest,
    publication, EOS state, and any required Zeus projection.
11. **Closeout** — require, where applicable, publication PASS, relationship
    and mission-binding reconciliation PASS, registration PASS, repository
    baseline PASS, EOS synchronization PASS, and Zeus roadmap verification
    PASS. If Zeus capability is not implemented, report
    `ZEUS_ROADMAP_VERIFICATION=NOT_READY`; never fabricate PASS.
12. **Activation as planning reference** — report the resulting active
    planning reference only when every applicable transition is proven.

No stage infers completion from the next stage or from a Markdown label.

## 7. Minimum roadmap content

An authoritative planning roadmap shall contain or reference, as applicable:

* identity, title, purpose, scope, owner, operation/project, and mission;
* governing authority and related controlled records;
* current phase and applicable baseline;
* stable objective/gate/milestone identifiers, sequence, dependencies, and
  prerequisites;
* intended capability progression and verification expectations;
* satisfaction criteria delegated to the governing mission/work contract;
* status, blockers, deferred work, and objective dispositions;
* absorbed, superseded, and historical objectives;
* roadmap-to-mission/WOP/gate/evidence/publication/EOS/Zeus references;
* reconciliation result and unresolved relationships;
* revision history, predecessor/successor references, and content digest; and
* explicit statement that planning content does not authorize execution.

Human-readable Markdown is permitted. Deterministic identity, relationship,
status, and evidence information must remain machine-resolvable through the
existing controlled-document and mission mechanisms. No new schema is created
by this procedure.

## 8. Stable objectives and traceability

Objective identity remains stable across revisions. Prefer existing roadmap,
mission, WOP/work, gate, evidence, publication, and Zeus identifiers. A
roadmap objective may map to multiple implementation gates; one gate may
satisfy multiple objectives; an objective may be absorbed by a broader
capability. Planning numbering and execution-gate numbering are distinct.

The intended trace is:

```text
roadmap objective -> mission -> WOP/work item -> implementation gate
  -> evidence -> published baseline -> EOS projection where applicable
  -> Zeus verification
```

If a link cannot yet be represented by an authoritative record, record the
unresolved link, block the affected advancement or implementation
recommendation, and route the gap to the existing authority. Do not create a
duplicate identifier or relationship registry.

## 9. Reconciliation and anti-duplication

Roadmap reconciliation is mandatory before recommending or authorizing work,
after interruption or material discovery, at work/mission closeout, and
before publishing a material revision. Compare planned capability with
authorized work, actual implementation, evidence, published result,
independent verification, and remaining gap.

An incomplete roadmap entry is not evidence that capability is absent. Inspect
published history, capability records, mission/WOP records, evidence,
baselines, EOS state, and Zeus verification where applicable. Each objective
shall receive an evidence-backed disposition from existing vocabulary:

* `SATISFIED` — required capability and applicable evidence are proven;
* `ABSORBED` — a broader or different authorized result satisfies the intent;
* `SUPERSEDED` — an authorized successor or changed requirement replaces it;
* `DEFERRED` — authority explicitly postpones it with rationale; or
* `REMAINS_REQUIRED` — reconciliation proves the capability is still absent
  and authorized work may be considered through normal admission.

Where the governing authority uses lifecycle state, preserve the distinction
between `PLANNED`, `AUTHORIZED`, `IN_PROGRESS`, `IMPLEMENTED`, `PUBLISHED`,
and `VERIFIED`; use `SUPERSEDED`, `ABSORBED`, and `DEFERRED` as dispositions
where applicable. A planning disposition never upgrades execution authority.
The roadmap procedure must not claim that an objective is missing solely
because prose is stale or because a gate number is absent from the roadmap.

The procedure shall preserve existing gate identities and evidence. It shall
never rename, renumber, invalidate, or reexecute published work solely to
make it conform to roadmap numbering.

## 10. Objective satisfaction

The applicable Mission Contract, WOP/EWO, qualification record, and
completion criteria determine whether an objective is satisfied. This
procedure does not invent a universal qualification authority. Depending on
scope, satisfaction may require implementation, evidence, publication,
authoritative-record reconciliation, EOS synchronization, and independent
Zeus verification. Record each applicable component and its authoritative
result separately.

`IMPLEMENTED` is not `VERIFIED`; `ROADMAP COMPLETE` is not `MISSION
AUTHORIZED`; and `ROADMAP NEXT` is not `EXECUTION AUTHORIZED`.

## 11. Revision, supersession, and history

Revise a roadmap only as a controlled transaction: resolve the current
published revision, reconcile current state, prepare the proposed revision,
perform change and impact analysis, resolve authority and review, publish
through the existing mechanism, reconcile affected relationships, synchronize
EOS where applicable, and verify the new active revision. The revision
package shall include changed objectives, dependencies, sequence,
constraints, assumptions, or dispositions; impact analysis; authority;
predecessor; proposed successor; and reason, including insertion, deletion,
resequencing, dependency change, satisfaction, absorption, supersession,
deferral, decomposition, consolidation, or external-constraint change.

Apply the existing controlled-document lifecycle and publication mechanics.
The successor preserves the permanent identity where the class requires it,
records its immediate predecessor, and does not rewrite the predecessor.
Only one active authoritative roadmap may control a declared scope unless a
superior authority explicitly permits otherwise. Ambiguous active revisions
fail closed. Historical roadmaps remain discoverable and retain their
objective dispositions, evidence, locators, and digests.

## 12. Mission, initiation, closeout, publication, and EOS integration

Mission binding is logical, source-bound traceability, not duplicated
authority. Resolve `roadmap -> mission` and, when the existing framework
supports it, the corresponding `mission -> roadmap` reference through the
existing generic relationship or mission artifact mechanism. Zeus must
eventually resolve this relationship without requiring an operator to know a
Markdown pathname. Do not edit mission records under this procedure unless
separately authorized by their owner.

At initiation, the consuming work procedure shall resolve the active roadmap,
revision, objective, intended contribution, dependencies, existing
capability, absorbed/satisfied disposition, conflicts, and required
reconciliation before admission. This procedure supplies the checks;
PROC-0001 remains the initiation/execution owner.

At closeout, the consuming work procedure shall record delivered capability,
objective mappings, partial satisfaction, absorption, changed assumptions,
sequence impact, remaining work, and whether a roadmap revision is required.
The completion record remains authoritative for implementation outcome; the
roadmap projection is reconciled from that record and does not become a
competing execution record.

Before invoking PROC-0005, verify classification, identity, authority,
content, lineage, relationships, reconciliation, and required review. PROC-0005
owns publication mechanics; PROC-0006 owns qualification evidence; neither is
replaced by this procedure.

The preferred projection boundary is:

```text
authoritative repository roadmap -> source-bound projection -> EOS
```

Synchronize only at the applicable existing EOS boundary. Preserve source
locator, revision, digest, and synchronization result. Repository/EOS
divergence or an unsupported projection blocks terminal acceptance and
remains inspectable read-only.

## 13. Verification, failure, idempotence, and recovery

Every terminal report shall expose, where supported:

```text
BLOCKER
CAUSE
EVIDENCE
NEXT_AUTHORIZED_ACTION
```

Mutation or advancement fails closed for ambiguous classification, identity,
authority, active revision, mission binding, supersession, provenance,
baseline, reconciliation, duplication risk, publication, EOS synchronization,
or verification. Inspection and evidence preservation remain available.

Re-running against unchanged authoritative state is idempotent. It shall not
create duplicate objectives, relationships, evidence, revisions, or
dispositions. Reuse existing evidence and report `ALREADY_SATISFIED` or the
equivalent canonical disposition where supported.

For an interrupted operation, resolve the roadmap, revision, authority,
source state, prior transaction/evidence, and completed stages before
resuming. Resume only unmet authorized stages; never restart blindly or
create a second transaction.

## 14. Operation Beta adoption contract

This procedure does not create or migrate the Operation Beta roadmap. When a
separately authorized future operation applies it, use this sequence:

1. publish and make this procedure effective through the existing lifecycle;
2. resolve the Beta roadmap identity, classification, and authority;
3. author the roadmap at the existing Beta locator;
4. inventory historical Beta implementation and publication evidence;
5. compare objectives with capabilities, not gate numbers alone;
6. map existing gates to objectives and record satisfied/absorbed items;
7. identify remaining objectives and establish mission relationships through
   existing authority;
8. validate, review, qualify, and publish the roadmap;
9. synchronize any applicable EOS projection;
10. verify the roadmap and expose it through authorized Zeus projections.

No existing Beta authority record is altered by this procedure. No published
Beta implementation is invalidated, renamed, renumbered, or reexecuted solely
to conform to a later roadmap.

## 15. Outputs and completion criteria

Retain the authoring package, classification decision, identity and
relationship resolution, reconciliation report, qualification evidence,
review/approval result, publication transaction, synchronization result,
verification result, and revision/supersession record according to the
applicable existing procedure.

The procedure operation is complete only when the requested transition is
proven at its applicable boundary, the authoritative record and projections
agree, all unresolved blockers are surfaced, and the next authorized action
is explicit. A report or Zeus view alone does not establish authority.

## 16. Zeus execution-progress tracking and reporting

An executable roadmap shall contain enough deterministic structure for a
future Zeus progress projection to resolve phase and gate position. This
section defines an integration requirement only; it does not implement Zeus,
EENS, a new event framework, or a competing progress authority.

### 16.1 Progress projection contract

When Zeus executes or monitors work associated with an authoritative roadmap,
the future projection shall be source-bound to the active roadmap revision,
mission state, WOP/gate state, execution records, and qualification or
verification state. It shall expose at minimum:

```text
ROADMAP_ID
ROADMAP_REVISION
MISSION_ID
EXECUTION_STATE
PHASE_CURRENT
PHASE_TOTAL
PHASE_ID
PHASE_NAME
PHASE_STATE
GATE_CURRENT
GATE_TOTAL
GATE_ID
GATE_NAME
GATE_STATE
COMPLETED_PHASES
COMPLETED_GATES
CURRENT_BLOCKERS
CURRENT_APPROVALS_REQUIRED
NEXT_AUTHORIZED_ACTION
LAST_PROGRESS_EVENT
LAST_PROGRESS_TIMESTAMP
SOURCE_ROADMAP
SOURCE_ROADMAP_DIGEST
PROJECTION_VERIFICATION
```

`PHASE_CURRENT/PHASE_TOTAL` and `GATE_CURRENT/GATE_TOTAL` are minimum
operator-orientation metrics. Totals shall be resolved from the applicable
roadmap revision, never hard-coded into Zeus. They are not completion
percentages. A percentage, if later displayed, requires a deterministic rule
defined by the applicable roadmap contract.

The compact operator projection should make the active mission, state,
phase position, gate position, current item, completed items, blockers, and
next authorized action discoverable without manually reading roadmap prose.
Machine-readable output shall support deterministic Zeus reasoning, EENS
notifications, dashboards, recovery, closeout, and portfolio reporting.

### 16.2 Derivation and verification

Roadmap structure defines intended progression. Authoritative execution and
verification records determine actual progression:

```text
roadmap structure
  + mission state
  + WOP/gate state
  + execution records
  + qualification/verification state
  = current progress projection
```

Manually edited prose is insufficient proof of progress. A future Zeus
projection shall independently verify, as applicable:

```text
ROADMAP_RESOLUTION=PASS
ROADMAP_REVISION=PASS
MISSION_BINDING=PASS
PHASE_RESOLUTION=PASS
PHASE_TOTAL_RESOLUTION=PASS
GATE_RESOLUTION=PASS
GATE_TOTAL_RESOLUTION=PASS
EXECUTION_STATE_BINDING=PASS
PROGRESS_SOURCE_PROVENANCE=PASS
PROGRESS_PROJECTION_CONSISTENCY=PASS
```

Conflicting authoritative sources fail closed. Zeus shall not select the
value that appears most advanced. Progress position does not itself prove
completion, and corrective work does not falsely advance the primary
roadmap.

### 16.3 State, events, and history

The projection shall preserve execution semantics including active, blocked,
paused, failed, awaiting approval, and corrective-execution states. A blocked
mission shall not appear advanced merely because corrective activity occurred.

Existing EENS contracts shall be reused for future significant progress
events where applicable, including:

```text
MISSION_STARTED
PHASE_STARTED
GATE_STARTED
GATE_PROGRESS_UPDATED
GATE_BLOCKED
GATE_AWAITING_APPROVAL
GATE_PAUSED
GATE_RESUMED
GATE_COMPLETED
PHASE_COMPLETED
EXECUTION_FAILED
EXECUTION_RECOVERED
MISSION_EXECUTION_COMPLETED
```

This procedure does not create an event framework. Each event must be
source-bound to the applicable roadmap revision and authoritative execution
record; an event cannot fabricate lifecycle advancement.

Progress reports shall be generated after material authoritative progress
transitions, on operator request, after interruption recovery or state
reconciliation, before applicable closeout verification, and when a new
active roadmap revision materially changes the projection. Historical
progress must remain interpretable against the roadmap revision that applied
at each transition, including phase/gate start, completion, blocked, and
resumed events. History shall derive from authoritative records/events rather
than become an independent source of truth.

Roadmap revision shall recalculate current totals deterministically while
preserving completed work and prior reports against their original revision.
Deferred, absorbed, superseded, conditional, corrective, recovery, parallel,
and dynamically discovered work shall be represented without assuming a
linear execution path. When multiple branches are active, resolve
`PHASE_CURRENT` and `GATE_CURRENT` deterministically from the applicable
roadmap revision and authoritative state: select the controlling active
branch defined by roadmap dependency/order; if no unique controlling branch
exists, report `PROGRESS_PROJECTION=AMBIGUOUS`, expose all active branches,
and fail closed for advancement. Ordinal position is distinct from qualified
completion; no unsupported percentage is implied.

### 16.4 Future Zeus interface target

Future Zeus interfaces should make progress discoverable through mission,
roadmap, and operation views, conceptually including:

```text
scripts/zeus mission progress <MISSION_ID>
scripts/zeus mission status <MISSION_ID>
scripts/zeus roadmap progress <ROADMAP_ID>
scripts/zeus operation progress operation-beta
```

These names are illustrative requirements, not an interface authorization.
The future projection shall remain source-bound and independently verifiable.

### 16.5 Roadmap readiness for progress projection

An executable roadmap is not architecturally ready for Zeus progress
projection until it exposes enough structure to resolve:

```text
TOTAL_PHASES
PHASE_ORDER
PHASE_IDENTITY
TOTAL_APPLICABLE_GATES
GATE_ORDER
GATE_IDENTITY
PHASE_TO_GATE_RELATIONSHIP
```

If any required structure cannot be resolved, report
`ZEUS_PROGRESS_PROJECTION=NOT_READY` and block the affected advancement while
leaving read-only inspection available.

The governing invariants are:

```text
ROADMAP_DEFINES_PLANNED_STRUCTURE
EXECUTION_RECORDS_DEFINE_ACTUAL_EXECUTION_STATE
VERIFICATION_DEFINES_QUALIFIED_PROGRESS
ZEUS_PROJECTS_AUTHORITATIVE_SOURCES
PROGRESS_REPORTING_DOES_NOT_CREATE_EXECUTION_AUTHORITY
PROGRESS_POSITION_DOES_NOT_PROVE_COMPLETION
ROADMAP_REVISION_DOES_NOT_ERASE_HISTORICAL_PROGRESS
CORRECTIVE_WORK_DOES_NOT_FALSELY_ADVANCE_PRIMARY_ROADMAP
```

## 17. Submission and Zeus management after submission

An approved roadmap enters Zeus management only through the applicable
submission boundary. Submission is a planning-management operation; it is
not mission admission, WOP admission, bootstrap, provider invocation, or
execution authorization.

The submission sequence is:

```text
author -> approve through the applicable planning authority
  -> submit to Zeus -> validate provenance and structure
  -> resolve identity and revision -> register planning state
  -> reconcile existing capabilities, missions, and WOPs
  -> derive the current plan-to-completion view
  -> manage revisions, relationships, progress, and closeout
```

The future Zeus controller shall make each step idempotent. Identical
submissions reuse the existing roadmap identity and revision. A material
change creates a new revision with predecessor lineage, impact analysis,
and preserved historical state; it never silently overwrites a published
revision. Missing, conflicting, or ambiguous identity or provenance is
read-only inspectable and blocks submission.

After valid submission, Zeus is the intended planning-management consumer
for registration, parsing, objective decomposition, capability
reconciliation, dependency and sequencing analysis, mission/WOP relationship
management, blocker and approval tracking, progress projection, drift
detection, absorption, satisfaction, revision coordination, and derivation of
the remaining plan to completion. Zeus must surface existing approval or
authority requirements and must not bypass them or manufacture authority.

## 18. Roadmap, mission, and WOP relationship model

Roadmap relationships are potentially many-to-many and must be represented
through existing relationship mechanisms:

```text
roadmap -> phase -> objective/gate -> mission -> WOP/work -> evidence
```

The model shall permit one objective to require several missions, one
mission to contribute to several objectives, several WOPs within a mission
where the applicable architecture permits it, one WOP to contribute to
several objectives, and corrective or recovery branches to contribute to an
existing objective. Existing capability may satisfy an objective without
new execution. Relationship direction does not change the authority of the
referenced mission or WOP.

For a roadmap-derived work proposal, future Zeus behavior shall resolve the
active revision, reconcile satisfied capability, determine eligible
objectives and dependencies, test duplication risk, choose appropriate
mission/WOP boundaries, attach derivation provenance, and submit the result
through the normal mission/WOP lifecycle. The roadmap states intended
outcomes; mission and WOP mechanisms determine whether execution is
authorized.

An unassigned mission remains valid unless a separate applicable authority
requires a roadmap relationship. Operator-submitted, bootstrap, corrective,
emergency, maintenance, exploratory, external, and pre-roadmap work may use
the neutral state:

```text
PLANNING_ORIGIN=UNASSIGNED
ROADMAP_BINDING=UNASSIGNED
ROADMAP_REQUIRED=NO
```

Roadmap analysis is additional to normal mission authority evaluation. The
absence of a roadmap binding alone cannot cause submission, admission,
bootstrap, or execution failure.

Future planning-origin values should distinguish `ROADMAP_DERIVED`,
`OPERATOR_SUBMITTED`, `SYSTEM_CORRECTIVE`, `EXTERNAL`, and `UNASSIGNED`.
Later reconciliation may classify an unassigned mission as contributing to
or satisfying an objective, a corrective branch, a new planning requirement,
operational maintenance, outside scope, or remaining unassigned. Such a
relationship preserves the original mission/WOP identity, authority,
timestamps, records, evidence, publication history, and completion history;
it must never rewrite origin provenance.

## 19. Planned state, actual state, and execution history

The roadmap definition and operational records shall preserve two distinct
domains:

```text
PLANNED_STATE          = intended structure, sequence, dependencies, and outcomes
ACTUAL_EXECUTION_STATE = authoritative mission, WOP, execution, evidence,
                         qualification, and publication facts
```

Zeus shall reconcile the domains rather than collapse one into the other.
Execution deviations become explicit relationships or dispositions, such as
`CORRECTIVE_BRANCH`, `RECOVERY`, `DEVIATION`, `ABSORBED`, `SUPERSEDED`, or
`REMAINING_GAP`. A roadmap revision must preserve the historical planned
state, actual execution state, and the relationship between them.

For each objective, the future operational record shall be able to resolve
planned intent, dependencies, derived and associated missions, WOPs,
execution attempts, corrective branches, blockers, approvals,
pause/resume/failure/recovery transitions, evidence, qualification,
publication, capability result, and final disposition. These are projections
of authoritative records, not a competing execution ledger.

## 20. Planning origin and execution-planning drift

Zeus shall eventually classify alignment between planned and actual work
without treating every unassigned mission as an error. The minimum
dispositions are:

```text
ALIGNED
UNASSIGNED_BUT_VALID
RECONCILIATION_REQUIRED
MATERIAL_PLAN_DEVIATION
UNAUTHORIZED_EXECUTION_DETECTED
```

Drift analysis shall consider unknown objectives, skipped dependencies,
unauthorized substitution, new work without roadmap reconciliation,
unsupported satisfaction, execution materially outside the plan, corrective
branches that change the completion path, published capability absent from
the roadmap, already-satisfied work still scheduled, invalid revision totals,
and mission/WOP relationships inconsistent with execution evidence.

Planning inconsistency and execution-authority failure are distinct. Only
the applicable authority model determines whether execution must stop. A
valid unassigned mission may require later reconciliation while remaining
valid under its own authority.

## 21. Plan-to-completion and execution coordination

After each material reconciliation, the future controller shall be able to
answer what remains necessary to reach the roadmap completion state. It shall
derive this from objective dispositions, dependencies, approvals, blockers,
parallel branches, corrective branches, supersession, absorption, and the
active roadmap revision, not by selecting the next number alone. Applicable
states include `PLANNED`, `ELIGIBLE`, `ACTIVE`, `BLOCKED`, `PAUSED`,
`DEFERRED`, `SATISFIED`, `ABSORBED`, `SUPERSEDED`, `FAILED`,
`CORRECTIVE_REQUIRED`, and `COMPLETED`, subject to canonical repository
vocabulary.

Planning coordination shall identify eligible work, critical blockers,
parallel work, duplication risk, efficient objective grouping, mission/WOP
boundaries, approval requirements, corrective prerequisites, and already
satisfied capability. Relationship semantics may include:

```text
depends_on, blocks, blocked_by, parallel_with, contributes_to,
satisfied_by, absorbs, supersedes, requires_approval,
requires_capability, produces_capability
```

These relationships plan and coordinate; none creates execution authority.

## 22. Operational record, storage, and reconciliation boundaries

The existing repository information architecture controls physical storage.
This procedure distinguishes, without creating a new directory hierarchy:

1. authoritative roadmap definition and published revisions;
2. a machine-readable representation where an existing contract supports it;
3. immutable historical revisions and lineage;
4. roadmap operational/reconciliation records;
5. progress projections; and
6. evidence and validation reports.

The repository roadmap remains authoritative. EOS consumes a source-bound
projection. Zeus consumes the roadmap and authoritative execution records;
neither operational records nor projections replace the source or create
authority.

Reconciliation is required at roadmap submission, revision, mission
creation/association/initiation, WOP creation/admission, objective or gate
start, material deviation, corrective-branch creation, blocker transition,
objective/gate completion, mission completion, qualification, publication,
closeout, resume, and applicable EOS synchronization. A boundary may produce
a projection or evidence record without editing the human-readable roadmap.

## 23. Revision, supersession, and historical integrity

Each revision must preserve both `WHAT_WAS_PLANNED_THEN` and
`WHAT_IS_PLANNED_NOW`. The revision package records additions, removals of
future work, supersession, dependency or sequencing changes, phase/gate
total changes, changed completion criteria, absorption, and corrective plan
changes. Historical progress denominators and reports remain bound to the
revision under which they were produced.

Roadmap management shall never rewrite mission or WOP provenance, renumber
historical missions/WOPs, delete corrective branches, claim external work
was roadmap-derived, replace execution records with planned state, silently
change historical totals, or mark an objective satisfied without evidence.
Published engineering history is preserved even when a later roadmap
absorbs, supersedes, or reinterprets its planning relationship.

## 24. Roadmap completion and closeout

Roadmap completion is a planning and reconciliation disposition, not
execution authority and not mission closure. The future controller may
report completion only when all required objectives have valid terminal
dispositions, required capabilities and relationships are evidenced,
material drift is resolved or explicitly dispositioned, required
publications are accounted for, operational history is internally
consistent, and the remaining plan is empty.

Where applicable, closeout must separately verify roadmap publication,
relationship/binding reconciliation, registration, repository baseline, EOS
synchronization, and Zeus verification. Until Zeus roadmap verification is
implemented and qualified, the result is `ZEUS_ROADMAP_MANAGEMENT=NOT_READY`,
not a fabricated success. Completion of a roadmap does not close a mission,
authorize publication, or authorize any subsequent work.

## 25. Future Zeus roadmap controller and interfaces

The intended future architecture is:

```text
roadmap definition -> roadmap controller -> reconciliation
  -> progress projection and plan-to-completion -> Zeus operator views
```

The controller consumes authority, missions, WOPs, execution records,
capability state, evidence, publication, and EOS projections. It must not
manufacture authority. Future interfaces may include `roadmap submit`,
`show`, `status`, `progress`, `history`, `verify`, `reconcile`, `plan`,
`next`, `missions`, and `wops`, plus mission-scoped roadmap resolution.
Names are targets only; no interface is implemented by this procedure.

Future verification must independently establish roadmap identity, revision,
provenance, registration, relationships, progress, historical execution,
objective satisfaction, drift, reconciliation, and remaining work. Until
that implementation is qualified, `ZEUS_ROADMAP_MANAGEMENT=NOT_READY` and
`EENS_ROADMAP_PROGRESS=NOT_READY` remain honest readiness states.

## 26. Interruption recovery and idempotence

Before resuming an interrupted submission, reconciliation, revision, or
closeout, resolve the current roadmap and revision, inspect prior transaction
and evidence records, verify source state and authority have not changed,
identify completed steps, and resume only unmet authorized steps. Never
restart blindly, create duplicate objectives/relationships, or create a
second revision for an already-satisfied condition.

## 27. Operation Beta migration and gate-history safety

This procedure does not create the Operation Beta roadmap, submit it to
Zeus, alter Beta authority, or derive missions/WOPs. After this procedure is
effective through its applicable authority chain, a separately authorized
migration shall resolve roadmap identity, author and submit the roadmap,
inventory historical implementation, map capabilities rather than gate
numbers, preserve published gates and evidence, record satisfied/absorbed/
remaining objectives, establish relationships through existing authority,
validate and publish, synchronize applicable EOS projection, and verify
readiness in Zeus.

No existing Beta implementation is renamed, renumbered, invalidated, or
reexecuted merely to conform to the later roadmap. No Beta authority record
is changed by this procedure.

## 28. Readiness and fail-closed terminal conditions

The procedure must report `BLOCKER`, `CAUSE`, `EVIDENCE`, and
`NEXT_AUTHORIZED_ACTION` for unresolved conditions. Mutation or advancement
is blocked when identity, revision, provenance, objective identity,
dependency, relationship, satisfaction, drift, reconciliation, publication,
EOS projection, or source-bound progress integrity cannot be established.

Read-only inspection, historical evidence collection, and recovery planning
remain available. An unassigned mission is not rejected merely because
roadmap association is unavailable. The procedure remains a Draft/Pending,
non-authoritative document until the existing governance, registration,
qualification, publication, and activation chain is completed.

## 29. Revision history

| Version | Date | Disposition |
| --- | --- | --- |
| 0.1 | 2026-08-06 | Drafted the bounded roadmap/planning recording, reconciliation, anti-duplication, publication, EOS, and verification contract without creating roadmap or execution authority. |
| 0.2 | 2026-08-06 | Added the future Zeus execution-progress projection contract, source-bound verification, revision/history semantics, EENS integration target, and minimum phase/gate structure without modifying Zeus or EENS. |
| 0.3 | 2026-08-06 | Integrated explicit authority and classification boundaries, identity/lifecycle fields, verification-first gating, revision closeout, mission traceability, material progress events/report triggers, deterministic non-linear progress handling, and Operation Beta migration safety. |
| 0.4 | 2026-08-06 | Added roadmap submission and post-submission Zeus management responsibilities, many-to-many mission/WOP relationships, unassigned-mission compatibility, planning-origin and drift semantics, execution-history preservation, plan-to-completion and coordination requirements, operational-record boundaries, historical-integrity protections, completion semantics, future controller targets, and migration safety without implementing Zeus or changing authority. |
