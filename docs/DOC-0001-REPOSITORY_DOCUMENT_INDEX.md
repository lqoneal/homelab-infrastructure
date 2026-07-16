---
document_id: DOC-0001
title: Repository Document Index
version: 2.14
status: Active
owner: Homelab Infrastructure
created: 2026-07-06
last_updated: 2026-07-16
phase: Engineering Storage Qualification Capability
domain: Repository Governance
classification: Repository Document Index
predecessor_revision: DOC-0001@2.13
successor_revision: null
approval_status: Approved
approval_authority: Engineering Governance
approval_reference: Codex Handoff Procedure - Engineering Storage Qualification Capability Implementation
approval_date: 2026-07-16
persistence_status: Pending
source_of_truth: true
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
    target: SPEC-0001
  - type: indexes
    target: PROC-0002
  - type: indexes
    target: PROC-0003
  - type: indexes
    target: STD-0004
  - type: indexes
    target: TPL-0004
  - type: indexes
    target: EGR-000001
  - type: related_to
    target: PROJ-0001
  - type: related_to
    target: INF-0001
  - type: related_to
    target: EOS-0001
  - type: indexes
    target: EOS-0003
  - type: indexes
    target: MILESTONE-0003
  - type: indexes
    target: MILESTONE-0004
  - type: indexes
    target: MILESTONE-0005
  - type: indexes
    target: EMP-0001
  - type: indexes
    target: SPEC-0006
  - type: indexes
    target: SERVICE-0002
  - type: related_to
    target: EDR-0002
  - type: related_to
    target: GEN-0001
  - type: related_to
    target: EWO-000011
  - type: related_to
    target: EWO-000012
  - type: related_to
    target: EWO-000013
  - type: related_to
    target: EWO-000014
  - type: related_to
    target: EWO-000016
tags:
  - repository
  - governance
  - documentation
  - index
  - source-of-truth
---

# Repository Document Index

## Purpose

This document is the authoritative index for controlled engineering records contained within the Homelab repository.

It serves as the primary navigation document for engineers, automation, and future Engineering Management Platform tooling.

All controlled engineering documents shall be registered in this document or explicitly identified as legacy published documents pending migration or archival.

---

# Repository Purpose

The Homelab repository is the controlled publication for the engineering environment supporting the portfolio.

It owns the global engineering infrastructure, including:

* Engineering workstations
* Servers
* Storage architecture
* Network architecture
* Development environment
* Backup and recovery
* Shared engineering services

Project-specific repositories reference Homelab where appropriate instead of duplicating global infrastructure documentation.

The implemented Engineering Storage Qualification Capability is owned by
INF-0001 and operationally governed by PROC-0003. Package presence is recorded
in `inventory/software.md`; no duplicate storage-qualification authority is
created by that inventory view.

---

# Repository Work Initiation Ritual

Every engineering session shall begin by reviewing the repository in the following order.

1. Verify repository root.
2. Inventory repository structure.
3. Review this document.
4. Review applicable infrastructure baseline documents.
5. Review the Project State document.
6. Review the active sprint or work order.
7. Review task-specific controlled documents.
8. Review Git branch, commit, and working tree.
9. Qualify Engineering State freshness under STD-0004, including the latest
   completed milestone, last reconciled boundary, EOS state, active checkpoint,
   and resume accuracy.
10. If reconciliation is required, complete it before implementation.
11. Resume implementation only from reconciled authoritative state.

---

# Repository Commit Workflow

STD-0004 governs the operational lifecycle and requires Engineering State
Reconciliation before Commit Classification. PROC-0001 is the single
authoritative procedure for Commit Classification and Commit Reconstruction
Planning. Before any repository commit, inventory and classify every
outstanding change, establish one-objective logical commit boundaries, validate
dependency order and repository integrity, and approve the reconstruction
method, validation, commit message, and expected state for every commit.

Persistent Commit Classification Reports and Commit Reconstruction Plans are
required for milestone, multi-objective, multi-repository, governance,
standards, procedure, Engineering Platform, repository-wide, or complex
reconstruction work. Their designated repository location is
`engineering/planning/`. Routine unambiguous single-objective work may use
ephemeral planning under PROC-0001.

Commit execution, milestone publication, tagging, and pushing each require
their applicable authority. Milestone publication shall remain separate from
its prerequisite commits and shall never serve as a catch-all change set.

---

# Controlled Document Classification

| Prefix | Description |
| ------ | ----------- |
| DOC | Repository governance and navigation |
| PROJ | Project state and execution |
| PHASE | Mission and phase execution plans |
| EOS | Engineering Operating System governance |
| EMP | Engineering Management Platform architecture |
| GEN | Genesis governance records |
| POL | Engineering governance policies |
| INF | Infrastructure documentation |
| HW | Hardware documentation |
| AST | Engineering hardware asset records |
| FIN | Financial documentation |
| PROC | Engineering procedures and procurement records |
| TRX | Financial transaction records |
| SPEC | Technical specifications |
| SERVICE | Engineering service catalogs |
| STD | Engineering standards |
| TPL | Engineering document templates |
| EWO | Engineering Work Orders authorizing mission-specific execution |
| EGR | Engineering Governance Resolutions recording governance decisions |
| ADR | Architecture Decision Records |
| EDR | Engineering Decision Records |
| MILESTONE | Engineering milestone records |
| JOURNAL | Engineering history and milestones |

---

# Infrastructure Ownership

Infrastructure documentation is divided into two categories.

## Global Infrastructure

Owned by Homelab.

Examples include:

* Engineering workstation
* Shared storage
* Network
* Backup systems
* Shared engineering services
* Repository locations

## Project Infrastructure

Owned by the individual project.

Examples include:

* SprinterOS vehicle hardware
* AI Assistant compute infrastructure
* Future project-specific hardware

Project infrastructure may reference Homelab infrastructure documents but shall not duplicate their contents.

---

# Controlled Documents

| Document ID | Title | Status | Owner | Path |
| ----------- | ----- | ------ | ----- | ---- |
| DOC-0001 | Repository Document Index | Active | Homelab Infrastructure | `docs/DOC-0001-REPOSITORY_DOCUMENT_INDEX.md` |
| PROJ-0001 | Project State | Active | Homelab Infrastructure | `docs/project/PROJ-0001-PROJECT_STATE.md` |
| INF-0001 | Engineering Infrastructure Baseline | Active | Homelab Infrastructure | `docs/infrastructure/INF-0001-INFRASTRUCTURE_BASELINE.md` |
| HW-0001 | Master Hardware Register | Active | Homelab Infrastructure | `docs/hardware/HW-0001-MASTER_HARDWARE_REGISTER.md` |
| EDR-0001 | Hardware Asset Record Architecture | Approved | Homelab Infrastructure | `docs/edr/EDR-0001-HARDWARE_ASSET_RECORD_ARCHITECTURE.md` |
| EDR-0002 | Engineering Authority Model | Draft | EOS Program | `docs/edr/EDR-0002-ENGINEERING_AUTHORITY_MODEL.md` |
| EOS-0001 | Engineering Operating System Constitution | Draft | EOS Program | `docs/eos/EOS-0001-ENGINEERING_OPERATING_SYSTEM_CONSTITUTION.md` |
| EOS-0002 | Engineering Operating System Master Plan | Draft | EOS Program | `docs/eos/EOS-0002-ENGINEERING_OPERATING_SYSTEM_MASTER_PLAN.md` |
| EOS-0003 | EOS Operational Persistence Profile | Active | Homelab Infrastructure | `docs/eos/EOS-0003-OPERATIONAL_PERSISTENCE_PROFILE.md` |
| EMP-0001 | Engineering Management Platform Architecture | Active | Engineering Management Platform | `docs/emp/EMP-0001-ENGINEERING_MANAGEMENT_PLATFORM_ARCHITECTURE.md` |
| SPEC-0001 | Controlled Document Model | Active | EOS Program | `docs/specifications/SPEC-0001-CONTROLLED_DOCUMENT_MODEL.md` |
| SPEC-0004 | Engineering Context Reconstruction Service | Draft | EOS Program | `docs/specifications/SPEC-0004-ENGINEERING_CONTEXT_RECONSTRUCTION_SERVICE.md` |
| SPEC-0005 | Engineering Control Framework | Draft | EOS Program | `docs/specifications/SPEC-0005-ENGINEERING_CONTROL_FRAMEWORK.md` |
| SPEC-0006 | Engineering Work Registry Model | Active | Engineering Management Platform | `docs/specifications/SPEC-0006-ENGINEERING_WORK_REGISTRY_MODEL.md` |
| SERVICE-0001 | EOS Core Services Catalog | Draft | EOS Program | `docs/services/SERVICE-0001-EOS_CORE_SERVICES_CATALOG.md` |
| SERVICE-0002 | EMP Management Services Catalog | Active | Engineering Management Platform | `docs/services/SERVICE-0002-EMP_MANAGEMENT_SERVICES_CATALOG.md` |
| GEN-0001 | Engineering Operating System Genesis Record | Active | Engineering Governance | `docs/genesis/GEN-0001-GENESIS_GOVERNANCE_RECORD.md` |
| POL-0001 | Engineering Governance Policy | Active | Engineering Governance | `docs/policies/POL-0001-ENGINEERING_GOVERNANCE_POLICY.md` |
| STD-0000 | Engineering Governance Documentation Architecture | Active | Engineering Governance | `docs/standards/STD-0000-ENGINEERING_GOVERNANCE_DOCUMENTATION_ARCHITECTURE.md` |
| STD-0001 | Engineering Document Lifecycle Standard | Active | Engineering Governance | `docs/standards/STD-0001-ENGINEERING_DOCUMENT_LIFECYCLE_STANDARD.md` |
| STD-0002 | Engineering Document Persistence Standard | Active | Engineering Governance | `docs/standards/STD-0002-ENGINEERING_DOCUMENT_PERSISTENCE_STANDARD.md` |
| STD-0003 | Engineering Work Order Standard | Active | Engineering Governance | `docs/standards/STD-0003-ENGINEERING_WORK_ORDER_STANDARD.md` |
| STD-0004 | Engineering State Freshness Standard | Active | Engineering Governance | `docs/standards/STD-0004-ENGINEERING_STATE_FRESHNESS_STANDARD.md` |
| PROC-0001 | Engineering Work Order Execution Procedure | Active | Engineering Governance | `docs/procedures/PROC-0001-ENGINEERING_WORK_ORDER_EXECUTION_PROCEDURE.md` |
| PROC-0002 | Engineering Governance Resolution Procedure | Active | Engineering Governance | `docs/procedures/PROC-0002-ENGINEERING_GOVERNANCE_RESOLUTION_PROCEDURE.md` |
| PROC-0003 | Engineering Recovery Runbook | Active | Engineering Governance | `docs/procedures/PROC-0003-ENGINEERING_RECOVERY_RUNBOOK.md` |
| TPL-0001 | Engineering Work Order Template | Active | Engineering Governance | `docs/templates/TPL-0001-ENGINEERING_WORK_ORDER_TEMPLATE.md` |
| TPL-0002 | Engineering Completion Report Template | Active | Engineering Governance | `docs/templates/TPL-0002-ENGINEERING_COMPLETION_REPORT_TEMPLATE.md` |
| TPL-0003 | Engineering Evidence Package Template | Active | Engineering Governance | `docs/templates/TPL-0003-ENGINEERING_EVIDENCE_PACKAGE_TEMPLATE.md` |
| TPL-0004 | Engineering Governance Resolution Template | Active | Engineering Governance | `docs/templates/TPL-0004-ENGINEERING_GOVERNANCE_RESOLUTION_TEMPLATE.md` |
| EGR-000001 | Governance Foundation Qualification and Publication | Active | Engineering Governance | `docs/resolutions/EGR-000001-GOVERNANCE_FOUNDATION_QUALIFICATION_AND_PUBLICATION.md` |
| EWO-000010 | Governance Baseline 1.0 Qualification | Active | Engineering Governance | `docs/work-orders/EWO-000010-GOVERNANCE_BASELINE_1.0_QUALIFICATION.md` |
| EWO-000010-EVIDENCE | EWO-000010 Qualification Evidence Package | Draft | Engineering Governance | `docs/work-orders/EWO-000010-QUALIFICATION-EVIDENCE-PACKAGE.md` |
| EWO-000010-COMPLETION | EWO-000010 Qualification Completion Report | Draft | Engineering Governance | `docs/work-orders/EWO-000010-QUALIFICATION-COMPLETION-REPORT.md` |
| EWO-000011 | Controlled Document Model Revision 1.1 | Active | Engineering Governance | `docs/work-orders/EWO-000011-CONTROLLED_DOCUMENT_MODEL_REVISION_1.1.md` |
| EWO-000011-EVIDENCE | EWO-000011 Engineering Evidence Package | Draft | Engineering Governance | `docs/work-orders/EWO-000011-ENGINEERING-EVIDENCE-PACKAGE.md` |
| EWO-000011-COMPLETION | EWO-000011 Engineering Completion Report | Draft | Engineering Governance | `docs/work-orders/EWO-000011-ENGINEERING-COMPLETION-REPORT.md` |
| EWO-000012 | Lifecycle Authority Reconciliation | Active | Engineering Governance | `docs/work-orders/EWO-000012-LIFECYCLE_AUTHORITY_RECONCILIATION.md` |
| EWO-000012-EVIDENCE | EWO-000012 Engineering Evidence Package | Draft | Engineering Governance | `docs/work-orders/EWO-000012-ENGINEERING-EVIDENCE-PACKAGE.md` |
| EWO-000012-COMPLETION | EWO-000012 Engineering Completion Report | Draft | Engineering Governance | `docs/work-orders/EWO-000012-ENGINEERING-COMPLETION-REPORT.md` |
| EWO-000013 | Execution Record Traceability Conformance | Active | Engineering Governance | `docs/work-orders/EWO-000013-EXECUTION_RECORD_TRACEABILITY_CONFORMANCE.md` |
| EWO-000013-EVIDENCE | EWO-000013 Engineering Evidence Package | Draft | Engineering Governance | `docs/work-orders/EWO-000013-ENGINEERING-EVIDENCE-PACKAGE.md` |
| EWO-000013-COMPLETION | EWO-000013 Engineering Completion Report | Draft | Engineering Governance | `docs/work-orders/EWO-000013-ENGINEERING-COMPLETION-REPORT.md` |
| EWO-000014 | SPEC-0001 Lifecycle Promotion | Active | Engineering Governance | `docs/work-orders/EWO-000014-SPEC-0001-LIFECYCLE-PROMOTION.md` |
| EWO-000014-EVIDENCE | EWO-000014 Engineering Evidence Package | Draft | Engineering Governance | `docs/work-orders/EWO-000014-ENGINEERING-EVIDENCE-PACKAGE.md` |
| EWO-000014-COMPLETION | EWO-000014 Engineering Completion Report | Draft | Engineering Governance | `docs/work-orders/EWO-000014-ENGINEERING-COMPLETION-REPORT.md` |
| EWO-000016 | thaDuke Firmware Remediation | Active | Engineering Governance | `docs/work-orders/EWO-000016-THADUKE-FIRMWARE-REMEDIATION.md` |
| FIN-0001 | Master Financial Ledger | Active | Homelab Infrastructure | `docs/finance/FIN-0001-MASTER_FINANCIAL_LEDGER.md` |
| FIN-0002 | Master Procurement Register | Active | Homelab Infrastructure | `docs/finance/FIN-0002-MASTER_PROCUREMENT_REGISTER.md` |
| PROC-000001 | Engineering Terminal 01 Procurement | Closed | Homelab Infrastructure | `docs/finance/procurements/PROC-000001.md` |
| PROC-000002 | Engineering Spare microSD Card 01 Procurement | Closed | Homelab Infrastructure | `docs/finance/procurements/PROC-000002.md` |
| TRX-000001 | Procurement Transaction - Engineering Terminal 01 | Posted | Homelab Infrastructure | `docs/finance/transactions/TRX-000001.md` |
| TRX-000002 | Procurement Transaction - Engineering Spare microSD Card 01 | Posted | Homelab Infrastructure | `docs/finance/transactions/TRX-000002.md` |
| AST-000009 | Engineering Spare microSD Card 01 | Available | Homelab Infrastructure | `docs/hardware/assets/AST-000009.md` |
| MILESTONE-0001 | Hardware Domain Complete | Approved | Homelab Infrastructure | `docs/project/milestones/2026-07-06-hardware-domain-complete.md` |
| MILESTONE-0002 | Engineering Workstation Shared Services Complete | Approved | Homelab Infrastructure | `docs/project/milestones/2026-07-09-engineering-workstation-shared-services-complete.md` |
| MILESTONE-0003 | Engineering Platform Mission 0 Complete | Approved | Homelab Infrastructure | `docs/project/milestones/2026-07-13-engineering-platform-mission-0-complete.md` |
| MILESTONE-0004 | Engineering Management Platform Foundation 1.0 Operational | Approved | Engineering Management Platform | `docs/project/milestones/2026-07-13-engineering-management-platform-foundation-1.0-operational.md` |
| MILESTONE-0005 | Engineering Platform Foundation 1.0 — Foundation Complete | Approved | Homelab Infrastructure | `docs/project/milestones/2026-07-15-engineering-platform-foundation-1.0-foundation-complete.md` |

This table shall be updated whenever a controlled document is created, superseded, or archived.

---

# Operational Work Registry Discovery

The canonical Engineering Management Platform Work Registry is:

```text
engineering/registry/work-registry.yaml
```

Its canonical declarative schema is:

```text
engineering/registry/work-registry.schema.yaml
```

The registry uses YAML serialization and owns operational management state only. It is not a controlled document, Governance Authority, execution authority, or replacement for project-controlled engineering truth.

Deterministic discovery and validation are available through:

```text
engctl registry path
engctl registry list [entity]
engctl registry get <registry-id>
engctl registry context [project]
engctl registry validate
engctl registry create <entity> <record> <reason>
engctl registry update <registry-id> <field> <yaml-value> <reason>
engctl registry archive <registry-id> <reason>
engctl registry transition <registry-id> <state> <reason>
```

Operational management discovery is routed through `engctl portfolio`, `engctl project`, `engctl queue`, `engctl dependency`, `engctl milestone`, `engctl defer`, and `engctl status`. Registry-derived context and categorized management status are merged into Engineering Context Reconstruction while retaining explicit source-record references and the registry authority boundary.

---

# Engineering Governance Resolution Discovery

Engineering Governance Resolutions are first-class controlled governance-decision records.

The authoritative repository placement for current and future Homelab EGR records is:

```text
docs/resolutions/
```

Permanent EGR identifiers shall use `EGR-` followed by a six-digit decimal sequence. Assignment begins with `EGR-000001`, proceeds monotonically within this repository, and shall account for current, historical, staged, unstaged, untracked, and reserved identifiers. An identifier shall not be reused.

Each authoritative EGR filename shall begin with its permanent identifier followed by a descriptive title. Its current revision shall be registered in the Controlled Documents table after the record is created. The absence of an EGR instance is valid before operational issuance and shall not cause framework validation to fail.

To discover an EGR or determine approval-reference readiness:

1. begin with this index;
2. locate the EGR entry in the Controlled Documents table;
3. verify that its identifier, filename, metadata, and canonical path agree;
4. verify the exact revision, lifecycle state, approval metadata, disposition, decision scope, persistence state, and relationships in the EGR;
5. follow its references to the governing authority, Finding or proposal, applicable EWO, Completion Report, Evidence Package, and affected controlled revisions; and
6. verify that required validation and registration evidence exists before treating the EGR as an operational approval reference.

The EGR framework is implemented by:

* STD-0000 — Engineering Documentation Standard;
* PROC-0002 — Engineering Governance Resolution Procedure; and
* TPL-0004 — Engineering Governance Resolution Template.

DOC-0001 provides EGR discovery and identifier coordination. It does not select a governance disposition, approve a Resolution, activate a lifecycle transition, or replace the authoritative EGR record.

EGR-000001 is the first registered Engineering Governance Resolution and records Governance Foundation qualification and publication.

---

# Engineering Work Order Discovery

Engineering Work Orders are first-class controlled engineering records.

The authoritative repository placement for current and future Homelab Engineering Work Orders is:

```text
docs/work-orders/
```

Each authoritative Work Order filename shall begin with its permanent `EWO-` identifier, and its current revision shall be registered in the Controlled Documents table.

To discover the governing Work Order for repository activity:

1. begin with this index;
2. locate the applicable `EWO` entry in the Controlled Documents table;
3. verify the identifier, controlled revision, Active lifecycle state, mission, and phase in the Work Order;
4. follow its references to the governing baseline;
5. follow its record relationships to the associated Evidence Package and Completion Report when produced.

For every Engineering Work Order that enters execution, the Repository Document Index shall register:

- the governing Engineering Work Order;
- its Engineering Evidence Package;
- its Engineering Completion Report.

These three records constitute the authoritative execution record and shall support deterministic repository reconstruction.

Historical Work Orders and earlier repository placements remain controlled records. They shall remain discoverable and shall not be moved or rewritten solely to conform to the current placement convention.

The existing `engineering/work-orders/` location is a legacy Work Order location pending separately authorized reconciliation. Records in that location retain their existing meaning and history but do not replace the indexed authoritative Work Order under `docs/work-orders/` when both exist for the same identifier.

Mission 0.1 confirmed that `engineering/work-orders/EWO-000010.md` was an untracked, zero-byte duplicate with no controlled content. It was removed under the Mission 0.1 reconciliation authority. The authoritative EWO-000010 publication remains `docs/work-orders/EWO-000010-GOVERNANCE_BASELINE_1.0_QUALIFICATION.md`; no authoritative record or history was removed.

---

# Controlled Asset Records

The following hardware asset records are controlled engineering records governed by `HW-0001`.

They currently use `asset_id` metadata rather than `document_id` metadata and are classified as legacy-format controlled records pending migration or explicit exemption.

| Asset ID | Title | Status | Owner | Path |
| -------- | ----- | ------ | ----- | ---- |
| AST-000001 | Engineering Workstation | Operational | Homelab Infrastructure | `docs/hardware/assets/AST-000001.md` |
| AST-000002 | Primary Internal NVMe SSD | Operational | Homelab Infrastructure | `docs/hardware/assets/AST-000002.md` |
| AST-000003 | Secondary Intel RST Device | Operational | Homelab Infrastructure | `docs/hardware/assets/AST-000003.md` |
| AST-000004 | WD My Passport Backup Drive | Operational | Homelab Infrastructure | `docs/hardware/assets/AST-000004.md` |
| AST-000005 | BUP Ult Secure Drive | Operational | Homelab Infrastructure | `docs/hardware/assets/AST-000005.md` |
| AST-000006 | SanDisk Recovery USB | Operational | Homelab Infrastructure | `docs/hardware/assets/AST-000006.md` |
| AST-000007 | Raspberry Pi 5 | Operational | Homelab Infrastructure | `docs/hardware/assets/AST-000007.md` |
| AST-000008 | Engineering Terminal 01 | Operational | Homelab Infrastructure | `docs/hardware/assets/AST-000008.md` |

---

# Legacy Published Documents

The following repository documents predate the current controlled document model.

They remain useful published references but require migration, replacement, or archival during the Governance Codification Sprint.

| Path | Current Role | Reconciliation Classification |
| ---- | ------------ | ----------------------------- |
| `docs/architecture.md` | Legacy architecture publication | Legacy Artifact |
| `docs/roadmap.md` | Legacy roadmap publication | Legacy Artifact |

---

# Source of Truth

Engineering knowledge is governed by Authoritative Engineering Records.

The repository is a controlled, versioned publication of those records and the supporting implementation artifacts.

Examples:

* Engineering workstation baseline -> INF documents
* Repository governance -> DOC documents
* Project execution -> PROJ documents
* EOS governance -> EOS documents
* Engineering authority -> EDR documents
* Hardware inventory -> HW and AST records
* Financial records -> FIN, PROC, and TRX records

Duplication of controlled engineering information is prohibited.

---

# Engineering Principles

The Homelab repository follows the Engineering Operating System governance records approved for the portfolio.

The governing principles include:

* One authoritative source
* Capture once, publish many
* Views are not records
* Inventory before design
* Architecture before implementation
* Validation before publication
* Resumability by design
* Traceability
* Relationships are first-class

---

# Relationship to the Engineering Portfolio

Homelab provides the engineering environment for the portfolio.

It supplies the global infrastructure baseline consumed by product repositories.

The Engineering Management Platform manages portfolio coordination and engineering work within existing Engineering Governance. It consumes EOS services and project-controlled records without governing engineering standards, replacing the Engineering Platform, or changing Homelab's authority for the engineering environment.

---

# Revision History

| Version | Date | Description |
| ------- | ---- | ----------- |
| 1.0 | 2026-07-06 | Initial controlled document established. |
| 1.1 | 2026-07-08 | Reconciled controlled document inventory for Architecture Baseline 2.1. |
| 1.2 | 2026-07-09 | Registered Engineering Workstation shared services milestone. |
| 1.3 | 2026-07-09 | Published and registered Governance Baseline 1.0 genesis governance records. |
| 1.4 | 2026-07-09 | Registered Engineering Work Orders as first-class controlled records, indexed EWO-000010 and EWO-000011, and defined deterministic Work Order placement, discovery, precedence, and legacy compatibility under EWO-000011. |
| 1.5 | 2026-07-10 | Registered EWO-000012 and its execution records and established Active lifecycle verification for Engineering Work Order discovery. |
| 1.6 | 2026-07-10 | Registered EWO-000010 Qualification Evidence Package and Completion Report and completed deterministic execution-record registration for Governance Baseline qualification. |
| 1.7 | 2026-07-10 | Registered EWO-000013 and its Evidence Package and Completion Report and completed EWO-000010 bidirectional execution-record conformance under EWO-000013. |
| 1.8 | 2026-07-10 | Published and registered EWO-000014 and its execution records to authorize SPEC-0001 Version 1.3 lifecycle promotion. |
| 1.9 | 2026-07-10 | Synchronized the indexed SPEC-0001 Version 1.3 lifecycle state to Active following the EWO-000014 controlled promotion. |
| 2.0 | 2026-07-13 | Registered the EGR controlled document class, PROC-0002, TPL-0004, canonical EGR identifier and placement rules, and deterministic EGR discovery without issuing an EGR instance. |
| 2.1 | 2026-07-13 | Registered EGR-000001 as the first Engineering Governance Resolution and completed Governance Foundation discovery integration. |
| 2.2 | 2026-07-13 | Registered and preserved Active EWO-000016 under Mission 0.1 reconciliation authority and recorded removal of the obsolete zero-byte legacy EWO-000010 duplicate. |
| 2.3 | 2026-07-13 | Registered EOS-0003 operational persistence treatment and MILESTONE-0003 Mission 0 Engineering Platform closeout under Mission 0.4 authority. |
| 2.4 | 2026-07-13 | Registered the EMP Phase 1.1 platform architecture, work-registry model, and management-services catalog and clarified the EMP relationship to Governance, EOS, and Homelab. |
| 2.5 | 2026-07-13 | Registered deterministic discovery for the Phase 1.2 operational YAML Work Registry, schema, validation, controller routing, and authority boundary. |
| 2.6 | 2026-07-13 | Registered the Phase 1.3 controlled mutation interfaces, operational management command groups, deterministic status, and Engineering Context contribution. |
| 2.7 | 2026-07-13 | Registered MILESTONE-0004, EMP Foundation 1.0 operational qualification, the publication baseline, and controlled portfolio transition to SprinterOS product development. |
| 2.8 | 2026-07-15 | Published and registered PROC-0003 as the authoritative Engineering Recovery Runbook and reconciled its governing references. |
| 2.9 | 2026-07-15 | Published and registered STD-0004 and integrated Engineering State freshness qualification into repository Work Initiation. |
| 2.10 | 2026-07-15 | Registered PROC-0001 as the authoritative repository Commit Classification workflow and linked it to the reconciled STD-0004 operational lifecycle. |
| 2.11 | 2026-07-15 | Registered Commit Reconstruction Planning and proportional persistent planning-artifact governance within the PROC-0001 repository workflow. |
| 2.12 | 2026-07-15 | Registered MILESTONE-0005 as the Engineering Platform Foundation 1.0 operational-transition boundary. |
| 2.13 | 2026-07-15 | Registered AST-000009, PROC-000002, and TRX-000002 for the engineering spare microSD acquisition. |
| 2.14 | 2026-07-16 | Registered the implemented Engineering Storage Qualification Capability under existing INF-0001 infrastructure authority and PROC-0003 operational procedure authority. |
