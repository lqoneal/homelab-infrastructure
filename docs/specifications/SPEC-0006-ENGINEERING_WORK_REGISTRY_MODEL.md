---
document_id: SPEC-0006
title: Engineering Work Registry Model
version: 1.2
status: Active
owner: Engineering Management Platform
created: 2026-07-13
last_updated: 2026-07-13
phase: Engineering Management Platform Phase 1.3 Complete
domain: Engineering Management
classification: Engineering Specification
predecessor_revision: SPEC-0006@1.1
successor_revision: null
approval_status: Approved
approval_authority: Engineering Governance
approval_reference: Codex Handoff Procedure - Engineering Management Platform Phase 1.3 Operational Management Services
approval_date: 2026-07-13
persistence_status: Pending
source_of_truth: true
information_scope: EMP work-registry entities, management states, relationships, provenance, metrics inputs, and validation rules
declared_deferrals:
  - registry-migration
  - scheduling
  - automated-prioritization
  - metrics-calculation
relationships:
  - type: governed_by
    target: CHAR-0001
  - type: conforms_to
    target: POL-0001
  - type: conforms_to
    target: STD-0000
  - type: conforms_to
    target: SPEC-0001
  - type: implements
    target: EMP-0001
  - type: related_to
    target: SPEC-0004
  - type: related_to
    target: SPEC-0005
  - type: related_to
    target: SERVICE-0001
  - type: implemented_by
    target: SERVICE-0002
  - type: indexed_by
    target: DOC-0001
tags:
  - emp
  - work-registry
  - portfolio
  - management-state
  - dependencies
  - metrics
---

# Engineering Work Registry Model

## Purpose

This specification defines the implementation-independent model for the EMP Work Registry.

The registry is the authoritative source for EMP-owned operational coordination facts. It references, but does not duplicate, governance authority, project technical truth, repository observations, engineering evidence, or controlled-document content.

Phase 1.2 implements this model as a repository-controlled YAML registry. Serialization and storage do not change the authority boundaries defined by this specification.

Phase 1.3 adds controlled mutation and derived operational services over that same registry. It does not create another persistence owner or broaden registry authority.

---

# 1. Design Rules

The Work Registry shall:

- assign one stable identifier to each registry object;
- distinguish management state from document lifecycle, approval, persistence, and execution authority;
- preserve source-record provenance;
- represent hierarchy and dependencies explicitly;
- make deferral an attributable record rather than an undocumented omission;
- support deterministic status and metric derivation;
- preserve historical transitions without rewriting prior meaning; and
- remain independent of a database, command interface, dashboard, or scheduling engine.

Registry presence shall never imply authorization. Work requiring execution authority shall resolve to the applicable Active Engineering Work Order or other superior controlled authority.

---

# 2. Registry Object Envelope

Every registry object shall contain the following logical fields:

| Field | Requirement |
| --- | --- |
| `registry_id` | Permanent, unique EMP coordination identifier; never reused. |
| `object_type` | One registered entity type from this specification. |
| `title` | Human-readable label. |
| `management_state` | Current state from the entity-specific state set. |
| `owner` | Accountable management owner; does not imply Governance Authority. |
| `scope` | Portfolio or project coordination scope. |
| `authority_reference` | Required when the object represents work whose state depends on execution authorization or governance disposition. |
| `source_records` | One or more identifiers or stable locators for authoritative external facts used by the object. |
| `relationships` | Typed registry relationships to other registry objects or controlled records. |
| `created_at` | Attributable creation time. |
| `updated_at` | Attributable current-revision time. |
| `revision` | Monotonic registry-object revision. |
| `transition_history` | Ordered prior state transitions with time, actor, reason, and authority reference when applicable. |

Optional fields shall be defined by entity type and shall not obscure required provenance.

---

# 3. Entity Model

## 3.1 Portfolio

Owns the EMP coordination boundary and membership of registered projects.

Required additions: portfolio purpose, project memberships, portfolio owner, and status-derivation policy.

Management states: `planned`, `active`, `on_hold`, `completed`, `retired`.

## 3.2 Project

Represents a portfolio membership and reference to the project's authoritative Project State and repository records.

Required additions: canonical project-state reference, repository reference, portfolio priority when assigned, and portfolio membership.

Management states: `planned`, `active`, `on_hold`, `completed`, `retired`.

EMP does not own the project's technical state or repository health.

## 3.3 Mission

Represents a bounded engineering objective within a project.

Required additions: parent project, objective, applicable authority reference, entry criteria, completion criteria, and child phases.

Management states: `proposed`, `authorized`, `active`, `blocked`, `completed`, `cancelled`.

`authorized` is a projection that requires a resolving authority reference. It does not itself authorize execution.

## 3.4 Phase

Represents an ordered mission segment with entry, exit, and validation criteria.

Required additions: parent mission, sequence, entry criteria, exit criteria, validation references, and child sprints when used.

Management states: `planned`, `ready`, `active`, `blocked`, `completed`, `cancelled`.

## 3.5 Sprint

Represents an optional time-bounded or objective-bounded management interval within a phase.

Required additions: parent phase, objective, start and end constraints when applicable, capacity assumption when recorded, and included work items.

Management states: `planned`, `ready`, `active`, `blocked`, `completed`, `cancelled`.

A sprint is not an execution authority and need not exist for every phase.

## 3.6 Work Item

Represents a managed unit of engineering work.

Required additions: owning project, parent mission or phase when applicable, work type, priority, acceptance reference or completion criteria, authority reference when execution is authorized, and queue memberships.

Management states: `proposed`, `ready`, `active`, `blocked`, `completed`, `cancelled`, `deferred`.

Work-item completion records management outcome only. Governance acceptance and controlled-document lifecycle remain separately owned facts.

## 3.7 Work Queue

Represents an ordered or policy-grouped collection of work-item references.

Required additions: queue scope, selection policy, ordered membership or grouping rule, and owner.

Management states: `active`, `frozen`, `closed`.

Queue order is an EMP-owned coordination fact. Queue membership does not authorize execution, schedule work automatically, or change the referenced work item.

## 3.8 Milestone

Represents a management target and its evidence-backed attainment projection.

Required additions: target scope, success criteria, target date when applicable, supporting record references, and attainment observation.

Management states: `planned`, `achieved`, `withdrawn`.

`achieved` requires resolving evidence or a controlled milestone record. EMP does not approve the underlying result.

## 3.9 Deferral

Represents an explicit decision to postpone a work item or requirement.

Required additions: deferred object, reason, authority or decision reference, effective time, re-entry conditions, target horizon when known, and resolution reference.

Management states: `active`, `resolved`, `cancelled`.

An active deferral requires the referenced work item to have management state `deferred`. Removing a queue entry without a Deferral object is not a valid deferral.

## 3.10 Dependency

Represents a directed prerequisite relationship.

Required additions: prerequisite object, dependent object, dependency kind, satisfaction criteria, authority or source reference, and disposition when waived.

Management states: `proposed`, `active`, `satisfied`, `waived`, `cancelled`.

A dependency shall not target itself. Active dependency cycles are invalid unless a controlled exception explicitly defines the intended coupled unit.

## 3.11 Metric Definition

Represents a deterministic calculation contract, not a measured result.

Required additions: name, question answered, input fields, formula, scope, time basis, exclusions, and output unit.

Management states: `draft`, `active`, `retired`.

Metric results are derived views and shall carry generation time and source-registry revision.

---

# 4. Registry Relationships

The registry shall support these management relationships:

| Relationship | Meaning |
| --- | --- |
| `contains` / `contained_by` | Portfolio or work hierarchy. |
| `queued_in` / `queues` | Work-item membership in a queue. |
| `scheduled_in` / `schedules` | Work-item association with a sprint; no automated scheduling semantics. |
| `targets` / `targeted_by` | Milestone association with an object or scope. |
| `defers` / `deferred_by` | Deferral association with the postponed object. |
| `prerequisite_for` / `depends_on` | Directed dependency endpoints. |
| `evidenced_by` / `evidences` | Reference to supporting controlled evidence or milestone records. |
| `represented_by` / `represents` | Registry projection to an authoritative project or controlled record. |

These relationships are registry-domain relationships. When a relationship is persisted in a controlled-document metadata block, it shall use a relationship type recognized by SPEC-0001 or remain inside the registry payload rather than silently extending the controlled-document relationship vocabulary.

---

# 5. State Transition Rules

Every transition shall record previous state, new state, time, actor, reason, and authority reference when the transition reflects authorization, acceptance, waiver, or cancellation.

The following controls are mandatory:

- only one current management state exists per object;
- `active` work resolves to appropriate authority when authority is required;
- `blocked` identifies at least one active blocking dependency or recorded blocker;
- `completed` identifies completion evidence or an authoritative source-state reference;
- `deferred` identifies one active Deferral object;
- `achieved` milestones identify supporting evidence;
- `waived` dependencies identify the controlled waiver authority or decision; and
- transition history is append-only at the logical model level.

Phase 1.3 registry mutations shall additionally:

- lock the shared serialization boundary before reading the mutation base;
- validate the current registry before applying a change;
- increment the object revision for an object change and the registry revision once per committed transaction;
- attribute every committed transaction by action, actor, time, and reason;
- validate the complete candidate registry before persistence;
- replace the YAML serialization atomically only after validation succeeds;
- leave the prior serialization unchanged when any operation fails; and
- retain archived objects in the registry while excluding them from active management views.

Archive is not a lifecycle or management-state transition. An object may be archived only when no non-archived registry object refers to it. Archived objects remain available to lookup and history reconstruction.

Management transitions do not perform controlled-document lifecycle transitions.

---

# 6. Portfolio Status Model

Portfolio and project status shall be derived from registry objects and referenced authoritative records using declared rules.

Minimum status dimensions are:

- active and planned work counts;
- blocked work and blocking dependencies;
- milestone targets and attainment;
- active deferrals and re-entry conditions;
- queue depth and work age;
- mission and phase progress; and
- source currency and unresolved references.

No aggregate status may overwrite a source record. A status view shall disclose its registry revision, source snapshot time, scope, and authority boundary. Identical registry revisions and scopes shall produce identical categorized work identifiers.

Phase 1.3 operational status categorizes registry work as active, planned, deferred, blocked, or completed. Blocked work is the deterministic union of explicit `blocked` work items and dependents of active dependency records. Categories are derived views; overlap may be disclosed when, for example, deferred work remains dependency-blocked.

---

# 7. Engineering Metrics

The model permits, but does not implement, deterministic metrics including:

- throughput: completed work items per declared interval;
- cycle time: elapsed time from `active` to `completed`;
- work age: elapsed time since entry to the current actionable state;
- blocked count and blocked duration;
- queue depth by scope and priority;
- milestone attainment ratio;
- active dependency and dependency-satisfaction counts;
- active deferral count and deferral age; and
- planned-to-completed work ratio for a declared scope.

Every metric shall use an Active Metric Definition and shall remain a derived view. Metrics shall not evaluate engineer performance, establish priority, schedule work, or authorize execution in Phase 1.1.

---

# 8. Source and Repository Rules

Registry objects shall reference controlled records by permanent document identifier whenever one exists. Repository observations shall include repository identity and observed commit when currency matters.

The registry shall not embed copies of:

- Project State bodies;
- Engineering Work Orders;
- specifications, standards, or decisions;
- evidence packages or completion reports;
- repository-health output;
- checkpoint contents; or
- infrastructure and asset inventories.

The canonical registry is `engineering/registry/work-registry.yaml`. Its declarative schema is `engineering/registry/work-registry.schema.yaml`.

YAML is the canonical serialization because it is human-reviewable, produces useful Git diffs, supports the required nested entity model, and uses the repository's existing safe YAML validation dependency. The registry shall contain no executable YAML tags or aliases that transfer authority or obscure object identity.

Registry identifiers occupy the distinct `EMP-<ENTITY>-<STABLE-NAME>` namespace. Parent relationships use entity-specific stable identifiers. Sibling order uses positive integer `order` values; queue order uses unique contiguous `position` values beginning at one.

Any cache, database index, API response, report, or dashboard generated from the canonical YAML instance is a derived view unless separately established as a controlled record.

---

# 9. Validation Requirements

A registry implementation shall validate:

- unique identities and recognized entity types;
- required fields by entity type;
- recognized management states;
- resolving parent and endpoint relationships;
- hierarchy cardinality and containment consistency;
- authority references for authority-dependent states;
- evidence references for completed or achieved states;
- Deferral consistency;
- dependency direction, self-reference, and cycle rules;
- transition-history ordering and append-only preservation;
- source-record resolution and source currency; and
- deterministic metric definitions.

An operational mutation implementation shall also validate allowed transition graphs, attributable and chronological transition history, archive references, queue membership symmetry and contiguous ordering, milestone evidence qualification, dependency re-entry gates, and failed-transaction rollback.

Validation reports are derived views and use the existing EOS validation path.

---

# 10. Compliance

A Work Registry conforms to this specification when it preserves one authoritative owner for EMP coordination facts, maintains source provenance, distinguishes all relevant state types, supports deterministic validation and derivation, and introduces no competing governance, project, repository, checkpoint, or validation authority.

---

# Revision History

| Version | Date | Description |
| --- | --- | --- |
| 1.0 | 2026-07-13 | Established the Phase 1.1 work-registry entities, management states, relationships, provenance, portfolio status, metrics inputs, and validation rules. |
| 1.1 | 2026-07-13 | Selected the canonical repository YAML registry and schema, established the EMP identifier and ordering conventions, and activated the Phase 1.2 operational representation. |
| 1.2 | 2026-07-13 | Specified Phase 1.3 atomic mutations, transition controls, archival retention, deterministic status categorization, service validation, and rollback behavior. |
