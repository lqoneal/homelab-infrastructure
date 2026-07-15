---
document_id: EMP-0001
title: Engineering Management Platform Architecture
version: 1.3
status: Active
owner: Engineering Management Platform
created: 2026-07-13
last_updated: 2026-07-15
phase: Engineering Management Platform Phase 1.3 Complete
domain: Engineering Management
classification: Platform Architecture
predecessor_revision: EMP-0001@1.2
successor_revision: null
approval_status: Approved
approval_authority: Engineering Governance
approval_reference: Codex Handoff Procedure - Engineering State Freshness Standard Implementation
approval_date: 2026-07-15
persistence_status: Pending
source_of_truth: true
information_scope: EMP responsibilities, layers, portfolio model, service boundaries, EOS integrations, and repository ownership
declared_deferrals:
  - dashboards
  - scheduling
  - automation
  - ai-planning
  - backlog-execution
  - portfolio-execution
  - notifications
  - analytics
relationships:
  - type: governed_by
    target: CHAR-0001
  - type: conforms_to
    target: POL-0001
  - type: conforms_to
    target: STD-0000
  - type: conforms_to
    target: STD-0004
  - type: conforms_to
    target: SPEC-0001
  - type: implemented_by
    target: SPEC-0006
  - type: implemented_by
    target: SERVICE-0002
  - type: related_to
    target: EOS-0001
  - type: related_to
    target: EOS-0002
  - type: related_to
    target: EOS-0003
  - type: related_to
    target: SPEC-0004
  - type: related_to
    target: SPEC-0005
  - type: related_to
    target: SERVICE-0001
  - type: indexed_by
    target: DOC-0001
  - type: related_to
    target: PROJ-0001
tags:
  - emp
  - architecture
  - engineering-management
  - portfolio
  - work-registry
---

# Engineering Management Platform Architecture

## Purpose

This document defines the minimum architecture for the Engineering Management Platform (EMP).

EMP is the engineering-management layer built on the operational Engineering Platform. It coordinates engineering work across the portfolio by consuming authoritative repository records and existing Engineering Operating System (EOS) services.

EMP does not originate governance authority, replace authoritative records, or redesign the Engineering Platform.

---

# 1. Architectural Position

```text
Engineering Governance and controlled authority
                       |
                       v
Engineering Management Platform
  portfolio, work registry, management services
                       |
                       v
Mission 0 Engineering Platform and EOS services
  control, context, checkpoints, repositories, validation,
  documentation, inventory, publishing, and journals
                       |
                       v
Project repositories and authoritative engineering records
```

The layers cooperate without transferring authority:

- Engineering Governance establishes governance, activates Engineering Work Orders, and accepts outcomes.
- EMP owns portfolio coordination and work-management information within the scope defined here.
- EOS owns reusable operational engineering services and derived engineering views.
- Project and domain records own project-specific engineering facts, execution authority, evidence, and outcomes.

EMP management state never expands an Engineering Work Order, performs a governance transition, or makes a project record authoritative.

---

# 2. Management Responsibilities

EMP is responsible for managing:

- portfolio membership and portfolio coordination;
- project, mission, phase, and sprint relationships;
- work queues and queue membership;
- work-item state and management ownership;
- milestone targets and observed attainment references;
- explicit deferred-work records and re-entry conditions;
- intra-project and cross-project dependencies;
- deterministic engineering metrics; and
- portfolio status derived from the work registry and authoritative source records.

EMP is not responsible for:

- constitutional, policy, standard, or lifecycle authority;
- authorizing engineering execution;
- project-specific technical truth;
- controlled-document lifecycle implementation;
- repository discovery or repository health;
- checkpoint creation, selection, retention, or restoration;
- engineering-context reconstruction;
- validation framework ownership;
- publishing or dashboard rendering;
- chronological engineering journals; or
- product planning or execution for SprinterOS, AI Assistant, or any other downstream product.

---

# 3. Work Registry

The EMP Work Registry is the authoritative management record for EMP-owned coordination facts. Its representation, entities, states, relationships, and validation rules are defined by SPEC-0006.

The registry records references to authoritative project, governance, evidence, repository, and milestone records. It does not copy their controlled content.

The registry distinguishes:

- controlled-document lifecycle state;
- execution authority;
- EMP management state;
- observed technical or repository state; and
- derived status and metrics.

Only EMP management state is owned by the registry. Every externally owned fact remains a reference to its authoritative record or an explicitly identified derived observation.

Phase 1.2 implements the first operational registry instance at `engineering/registry/work-registry.yaml`. The registry is authoritative only for the operational management state represented by that instance.

---

# 4. Portfolio Model

The portfolio is an EMP coordination scope containing registered projects and cross-project management relationships.

The structural model is:

```text
Portfolio
  +-- Projects
        +-- Missions
              +-- Phases
                    +-- Sprints
                          +-- Work Items

Portfolio and project scopes also contain:
  +-- Work Queues
  +-- Milestones
  +-- Deferrals
  +-- Dependencies
  +-- Metric Definitions
```

Containment describes management organization, not governance precedence. A project may exist in one or more reporting views, but one registered portfolio entry owns its EMP coordination identity. Project technical state remains owned by that project's controlled records.

Cross-project dependencies and portfolio priority are EMP-owned facts because no individual project can authoritatively own a portfolio-wide relationship. Each dependency shall reference the authoritative project records that describe its endpoints.

---

# 5. Management-Service Architecture

SERVICE-0002 defines the EMP Management Services and their boundaries.

The core operational services are:

- Work Registry Service;
- Portfolio Service;
- Work Queue Service;
- Dependency Service;
- Milestone Service; and
- Deferral Service; and
- Portfolio Status Service.

Phase 1.3 operates these services over the single Work Registry persistence boundary through the existing Engineering Control Service. Engineering Metrics remains a model-defined enhancement because Phase 1.3 expressly excludes analytics and metric calculation. EMP completion adds no daemon, database server, API, scheduler, or background automation.

Additional interfaces may be introduced only through separately authorized enhancements and shall use the existing Engineering Control Service pattern rather than introduce a competing global controller.

---

# 6. EOS Integration

EMP consumes existing EOS responsibilities as follows:

| EOS responsibility | EMP use | Boundary |
| --- | --- | --- |
| Engineering Control Service / `engctl` | EMP management commands route through the existing global control entry point. | EMP shall not create a second global controller or duplicate project-wrapper logic. |
| Engineering Context Reconstruction Service | EMP supplies registered management context for resume and status views. | ECRS owns reconstruction and its outputs remain derived views. |
| Checkpoint Service | EMP links work state to checkpoint references when useful. | Checkpoints remain append-only operational evidence and are not work-registry entries. |
| Repository Service | EMP references discovered repositories and readiness observations. | Repository discovery, health, synchronization, and publication readiness remain EOS responsibilities. |
| Validation Service | EMP contributes registry-specific rules to the existing validation path. | EMP shall not create a competing validation framework. |
| Documentation Service | EMP records use the controlled-document model and publication lifecycle. | Document creation, metadata, relationships, and publication support remain EOS responsibilities. |
| Inventory Service | EMP references repository, document, hardware, and service inventory facts. | EMP portfolio membership and priority do not replace infrastructure or asset inventories. |
| Publishing Service | Future reports and dashboards consume EMP records. | Published status remains a derived view; dashboards are deferred. |
| Journal Service | EMP may link chronological activity to work items. | Journal chronology does not replace management state or execution evidence. |
| EOS persistence profile | EMP runtime views, if later implemented, shall follow the source/derived separation. | Phase 1.1 changes no EOS runtime, pointer, checkpoint, or retention behavior. |

STD-0004 governs freshness across these integrations. EMP shall provide its
current owned management facts for reconciliation but shall not treat registry
state as a replacement for Project State, current mission authority, or EOS
context. Resume and status views shall consume reconciled owners and shall not
promote stale registry objectives merely because they remain registered.

---

# 7. Repository Relationships

The Homelab repository is the canonical publication location for the Phase 1.1 EMP architecture, Phase 1.2 registry foundation, and Phase 1.3 operational management layer. It continues to own the Engineering Platform implementation and global infrastructure baseline.

Repository responsibilities are:

- this repository publishes EMP architecture, registry-model, and service-boundary records under `docs/emp/`, `docs/specifications/`, and `docs/services/`;
- DOC-0001 provides authoritative discovery for these records;
- each project repository continues to own its project-specific state, plans, technical records, work authority, evidence, and outcomes;
- EOS runtime directories contain operational state and derived views, not EMP authoritative portfolio records; and
- the operational registry is repository-controlled at `engineering/registry/work-registry.yaml`, with its schema at `engineering/registry/work-registry.schema.yaml`.

Phase 1.2 selects YAML because the repository already uses human-reviewable YAML for machine-readable engineering metadata and the existing validation environment provides safe YAML parsing. The repository-controlled location provides Git history and deterministic discovery without placing authoritative management state in the regenerable EOS runtime cache.

---

# 8. Information Ownership

| Information | Authoritative owner |
| --- | --- |
| Governance rules and execution authority | Existing Governance Foundation records and Active Engineering Work Orders |
| EMP architecture and layer boundaries | EMP-0001 |
| Work-registry representation and management-state semantics | SPEC-0006 |
| EMP logical service responsibilities | SERVICE-0002 |
| Project-specific technical and execution state | Applicable project-controlled records |
| Portfolio membership, portfolio priority, and cross-project coordination | `engineering/registry/work-registry.yaml` |
| Repository presence, health, synchronization, and readiness | Existing EOS Repository Service observations and INF records within their scopes |
| Checkpoint history and active pointer | Existing EOS Checkpoint Service and EOS persistence records |
| Reports, dashboards, context summaries, and metrics output | Derived views traceable to the records above |

No fact shall acquire a second information owner merely because EMP consumes or displays it.

---

# 9. Phase Boundaries

## Phase 1.1 Establishes

- the EMP management layer;
- the work-registry model;
- the portfolio coordination model;
- management-service boundaries;
- EOS integration contracts;
- repository and information-ownership relationships; and
- controlled publications needed to authorize later implementation design.

## Phase 1.1 Does Not Establish

- an operational registry;
- an EMP runtime or command group;
- data storage technology;
- dashboards or reports;
- scheduling or automated prioritization;
- backlog or portfolio execution;
- AI planning or recommendations;
- SprinterOS functionality; or
- AI Assistant functionality.

## Phase 1.2 Establishes

- the canonical repository-controlled YAML registry and declarative schema;
- stable EMP registry identifiers, hierarchy, ordering, and management states;
- initial portfolio, project, roadmap, queue, milestone, deferral, and dependency registration;
- registry loading, validation, discovery, and controller routing; and
- registry contribution to Engineering Context Reconstruction.

Phase 1.2 does not implement scheduling, dashboards, automation, AI planning, backlog optimization, portfolio execution, notifications, metrics calculations, or autonomous task management.

## Phase 1.3 Establishes

- atomic, validated registry create, update, archive, lookup, and state-transition operations;
- operational portfolio, project, queue, dependency, milestone, and deferral services;
- deterministic portfolio-status generation from registry state;
- management command routing through the existing `engctl` controller;
- expanded management contribution to Engineering Context Reconstruction; and
- regression and aggregate validation for the complete operational management layer.

Phase 1.3 completes the EMP core defined by its authorization. Dashboards, scheduling, automation, notifications, AI planning, optimization, analytics, metric calculation, autonomous task management, and product implementation remain separately authorized enhancements or downstream work.

---

# 10. Compliance

An EMP implementation conforms to this architecture only when it:

- consumes rather than replaces EOS services;
- preserves Governance Foundation authority;
- maintains one information owner for each fact;
- persists management facts through the controlled registry model;
- treats all generated status and metrics as derived views;
- preserves project-repository ownership;
- routes shared control, context, validation, repository, and checkpoint needs through existing Engineering Platform services; and
- consumes STD-0004 reconciliation and freshness results without creating a
  competing Engineering State owner; and
- remains within an Active, bounded implementation authority.

---

# Revision History

| Version | Date | Description |
| --- | --- | --- |
| 1.0 | 2026-07-13 | Established the Phase 1.1 EMP management layer, portfolio model, service boundaries, EOS integrations, and repository ownership architecture. |
| 1.1 | 2026-07-13 | Recorded the Phase 1.2 operational YAML Work Registry, canonical repository location, ECRS contribution, controller routing, and preserved authority boundaries. |
| 1.2 | 2026-07-13 | Recorded the Phase 1.3 transactional management services, deterministic status, controller expansion, context contribution, and EMP core completion boundary. |
| 1.3 | 2026-07-15 | Integrated STD-0004 freshness and reconciliation boundaries into EMP-to-EOS context and resume responsibilities. |
