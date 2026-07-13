---
document_id: SERVICE-0002
title: EMP Management Services Catalog
version: 1.2
status: Active
owner: Engineering Management Platform
created: 2026-07-13
last_updated: 2026-07-13
phase: Engineering Management Platform Phase 1.3 Complete
domain: Engineering Management
classification: Engineering Service Catalog
predecessor_revision: SERVICE-0002@1.1
successor_revision: null
approval_status: Approved
approval_authority: Engineering Governance
approval_reference: Codex Handoff Procedure - Engineering Management Platform Phase 1.3 Operational Management Services
approval_date: 2026-07-13
persistence_status: Pending
source_of_truth: true
information_scope: Logical EMP management-service responsibilities, inputs, outputs, boundaries, and EOS dependencies
declared_deferrals:
  - scheduling
  - automation
  - dashboards
  - notifications
  - metrics-calculation
  - analytics
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
  - type: implements
    target: SPEC-0006
  - type: related_to
    target: SERVICE-0001
  - type: related_to
    target: SPEC-0004
  - type: related_to
    target: SPEC-0005
  - type: related_to
    target: EOS-0003
  - type: indexed_by
    target: DOC-0001
tags:
  - emp
  - services
  - engineering-management
  - portfolio
  - work-registry
---

# EMP Management Services Catalog

## Purpose

This catalog defines the logical management services required by EMP and assigns one responsibility to each service.

The Phase 1.3 core services are operational over the single Work Registry persistence boundary. All consume the existing Engineering Platform and EOS services cataloged by SERVICE-0001 and operationalized during Mission 0.

---

# 1. Service Principles

Every EMP Management Service shall:

- consume the Work Registry model in SPEC-0006;
- preserve controlled-record and project-repository ownership;
- expose no independent Governance Authority;
- use existing EOS control, context, checkpoint, repository, validation, documentation, inventory, publishing, and journal responsibilities;
- produce deterministic results for identical inputs;
- remain implementation-independent; and
- avoid implementing another EMP or EOS service's responsibility.

---

# 2. Management Services

## 2.1 Work Registry Service

Purpose: Maintain the canonical EMP coordination objects, relationships, management states, source references, and transition history.

Inputs:

- authorized management changes;
- controlled-record identifiers and stable source locators;
- project and portfolio relationships; and
- registry validation results.

Outputs:

- current registry revision;
- traceable registry-object history; and
- registry change results.

Operations: validated create, update, archive, lookup, and state transition with atomic persistence, registry and object revisions, and attributable mutation history.

Boundary: Does not create Governance Authority, manage controlled-document lifecycle, discover repositories, capture checkpoints, or render dashboards.

## 2.2 Portfolio Service

Purpose: Maintain portfolio membership and derive cross-project coordination status.

Inputs:

- portfolio and project registry objects;
- milestones, deferrals, dependencies, and queues; and
- referenced authoritative project state.

Outputs:

- portfolio membership;
- cross-project coordination state; and
- derived portfolio-status data.

Operations: portfolio summary, project registration, project activation and suspension, and deterministic project ordering.

Boundary: Does not own project technical state, project execution, repository inventory, or acceptance decisions.

## 2.3 Work Queue Service

Purpose: Maintain queue definitions, policy, ordered membership, and queue-scoped management views.

Inputs:

- work-item references;
- authorized priority and membership changes; and
- queue policy.

Outputs:

- current queue membership and order; and
- derived queue depth and aging data.

Operations: enqueue, dequeue, reprioritize, reorder, and queue validation. Positions are unique and contiguous from one, and work-item queue references remain symmetric.

Boundary: Does not schedule work, execute backlogs, activate Engineering Work Orders, or change project records.

## 2.4 Dependency Service

Purpose: Maintain directed work dependencies and determine their management effect.

Inputs:

- dependency objects;
- endpoint state and source references; and
- satisfaction or waiver evidence.

Outputs:

- dependency status;
- blocker projections; and
- cycle and consistency findings.

Operations: dependency discovery, graph validation, prerequisite qualification, explicit satisfaction, and blocked-work reporting.

Boundary: Does not perform engineering impact analysis, waive dependencies, or resolve technical prerequisites.

## 2.5 Milestone Service

Purpose: Maintain milestone targets and derive evidence-backed attainment state.

Inputs:

- milestone criteria;
- target relationships; and
- authoritative evidence or milestone records.

Outputs:

- target status; and
- attainment projection with evidence references.

Operations: milestone lookup and status, evidence qualification, and completion projection. Completion requires evidence and an authority reference but does not accept the underlying result.

Boundary: Does not accept engineering outcomes, fabricate historical milestones, or replace controlled milestone records.

## 2.6 Deferral Service

Purpose: Preserve explicit deferred-work decisions and validate controlled re-entry.

Inputs:

- work-item state;
- attributable reason and authority reference;
- re-entry conditions; and
- dependency state.

Outputs:

- active or resolved Deferral records;
- append-only transition history; and
- deterministic re-entry findings.

Operations: defer, resume, history lookup, and re-entry validation. Resume fails while an active dependency remains.

Boundary: Does not authorize resumed execution, discard prior deferral records, or infer that a dependency is waived.

## 2.7 Portfolio Status Service

Purpose: Generate deterministic management status from one validated registry revision.

Inputs:

- work-item management states;
- active dependency records; and
- an optional registered project scope.

Outputs:

- active, planned, deferred, blocked, and completed work identifiers; and
- source registry revision, snapshot time, scope, and authority note.

Boundary: Does not inspect or overwrite controlled-document state, calculate analytics, schedule work, or grant execution authority.

## 2.8 Engineering Metrics Service

Purpose: Evaluate Active metric definitions against versioned registry inputs.

Inputs:

- Active Metric Definitions;
- a specified registry revision; and
- declared scope and time basis.

Outputs:

- reproducible metric results carrying source revision and generation time.

Boundary: Does not own source facts, rank engineers, assign priority, schedule work, or turn metrics into governance decisions. Metric calculation remains a separately authorized enhancement because analytics are outside Phase 1.3.

---

# 3. Existing EOS Services Consumed

| Existing EOS responsibility | EMP service use |
| --- | --- |
| Engineering Control Service | Routes operational management commands through the existing global entry point. |
| Engineering Context Reconstruction Service | Incorporates registry context into deterministic resume and status views. |
| Documentation Service | Supports controlled registry publications and metadata relationships. |
| Validation Service | Runs registry, relationship, lifecycle-boundary, and source-resolution validation. |
| Checkpoint Service | Provides optional checkpoint references for resumability without becoming work state. |
| Inventory Service | Supplies repository, document, asset, and service inventory references. |
| Publishing Service | Produces future reports and dashboards as derived views. |
| Journal Service | Provides chronological activity references without owning management state. |
| Repository operational services | Supply discovery, health, synchronization, and publication-readiness observations. |

EMP shall extend these services through registered inputs and rules where appropriate; it shall not fork, wrap with independent business logic, or replace them.

---

# 4. Service Interaction

```text
Existing Engineering Control Service
                  |
                  v
        Work Registry Service
          /       |       \
         v        v        v
   Portfolio   Work Queue  Dependency
      |           |           |
      +-----------+-----------+
             |         |
             v         v
        Milestone   Deferral
             \         /
              v       v
          Portfolio Status
                  |
                  v
 Existing context, validation, publishing,
 inventory, repository, checkpoint, and journal services
```

The Work Registry Service is the sole management-state persistence boundary. Other management services request changes through it and produce derived evaluations from versioned registry inputs.

---

# 5. Implementation Status

Phase 1.2 implemented:

- canonical YAML registry loading;
- schema, identity, hierarchy, state, ordering, deferral, dependency, serialization, and authority-boundary validation;
- registry object discovery and lookup;
- read-only `engctl registry` routing;
- aggregate Engineering Platform validation integration; and
- Engineering Context Reconstruction contribution.

Phase 1.3 implements:

- validated atomic registry create, update, archive, lookup, and transition operations;
- portfolio and project registration, lifecycle projection, ordering, summary, and status;
- deterministic queue mutation and validation;
- dependency discovery, validation, qualification, satisfaction, and blocker reporting;
- milestone lookup, evidence qualification, and completion projection;
- deferral creation, resolution, history preservation, and re-entry validation;
- `engctl` management routing and expanded Engineering Context contribution; and
- operational regression and aggregate Engineering Platform validation.

Scheduling, automation, notifications, dashboards, analytics, metric calculation, AI planning, optimization, autonomous management, and product implementation remain outside the completed EMP core. They require separate enhancement or product authority.

---

# 6. Compliance

An implementation conforms to this catalog when each management responsibility has one authoritative implementation, all shared engineering capabilities remain delegated to EOS, all outputs remain traceable, and no service acquires governance or project information ownership outside its defined scope.

---

# Revision History

| Version | Date | Description |
| --- | --- | --- |
| 1.0 | 2026-07-13 | Established the Phase 1.1 EMP logical management-service catalog and EOS service boundaries. |
| 1.1 | 2026-07-13 | Recorded the operational Work Registry loader, validator, discovery, controller, aggregate validation, and Engineering Context integration delivered by Phase 1.2. |
| 1.2 | 2026-07-13 | Recorded the Phase 1.3 transactional registry, portfolio, queue, dependency, milestone, deferral, status, controller, context, and validation services and qualified the EMP core as operationally complete. |
