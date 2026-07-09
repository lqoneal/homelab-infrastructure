---
document_id: DOC-0001
title: Repository Document Index
version: 1.3
status: Active
owner: Homelab Infrastructure
created: 2026-07-06
last_updated: 2026-07-09
phase: Governance Bootstrap
domain: Repository Governance
classification: Repository Document Index
source_of_truth: true
related_documents:
  - PROJ-0001
  - INF-0001
  - EOS-0001
  - EDR-0002
  - GEN-0001
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
9. Resume implementation.

---

# Controlled Document Classification

| Prefix | Description |
| ------ | ----------- |
| DOC | Repository governance and navigation |
| PROJ | Project state and execution |
| PHASE | Mission and phase execution plans |
| EOS | Engineering Operating System governance |
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
| SPEC-0001 | Controlled Document Model | Draft | EOS Program | `docs/specifications/SPEC-0001-CONTROLLED_DOCUMENT_MODEL.md` |
| SPEC-0004 | Engineering Context Reconstruction Service | Draft | EOS Program | `docs/specifications/SPEC-0004-ENGINEERING_CONTEXT_RECONSTRUCTION_SERVICE.md` |
| SPEC-0005 | Engineering Control Framework | Draft | EOS Program | `docs/specifications/SPEC-0005-ENGINEERING_CONTROL_FRAMEWORK.md` |
| SERVICE-0001 | EOS Core Services Catalog | Draft | EOS Program | `docs/services/SERVICE-0001-EOS_CORE_SERVICES_CATALOG.md` |
| GEN-0001 | Engineering Operating System Genesis Record | Active | Engineering Governance | `docs/genesis/GEN-0001-GENESIS_GOVERNANCE_RECORD.md` |
| POL-0001 | Engineering Governance Policy | Active | Engineering Governance | `docs/policies/POL-0001-ENGINEERING_GOVERNANCE_POLICY.md` |
| STD-0000 | Engineering Governance Documentation Architecture | Active | Engineering Governance | `docs/standards/STD-0000-ENGINEERING_GOVERNANCE_DOCUMENTATION_ARCHITECTURE.md` |
| STD-0001 | Engineering Document Lifecycle Standard | Active | Engineering Governance | `docs/standards/STD-0001-ENGINEERING_DOCUMENT_LIFECYCLE_STANDARD.md` |
| STD-0002 | Engineering Document Persistence Standard | Active | Engineering Governance | `docs/standards/STD-0002-ENGINEERING_DOCUMENT_PERSISTENCE_STANDARD.md` |
| STD-0003 | Engineering Work Order Standard | Active | Engineering Governance | `docs/standards/STD-0003-ENGINEERING_WORK_ORDER_STANDARD.md` |
| PROC-0001 | Engineering Work Order Execution Procedure | Active | Engineering Governance | `docs/procedures/PROC-0001-ENGINEERING_WORK_ORDER_EXECUTION_PROCEDURE.md` |
| TPL-0001 | Engineering Work Order Template | Active | Engineering Governance | `docs/templates/TPL-0001-ENGINEERING_WORK_ORDER_TEMPLATE.md` |
| TPL-0002 | Engineering Completion Report Template | Active | Engineering Governance | `docs/templates/TPL-0002-ENGINEERING_COMPLETION_REPORT_TEMPLATE.md` |
| TPL-0003 | Engineering Evidence Package Template | Active | Engineering Governance | `docs/templates/TPL-0003-ENGINEERING_EVIDENCE_PACKAGE_TEMPLATE.md` |
| FIN-0001 | Master Financial Ledger | Active | Homelab Infrastructure | `docs/finance/FIN-0001-MASTER_FINANCIAL_LEDGER.md` |
| FIN-0002 | Master Procurement Register | Active | Homelab Infrastructure | `docs/finance/FIN-0002-MASTER_PROCUREMENT_REGISTER.md` |
| PROC-000001 | Engineering Terminal 01 Procurement | Closed | Homelab Infrastructure | `docs/finance/procurements/PROC-000001.md` |
| TRX-000001 | Procurement Transaction - Engineering Terminal 01 | Posted | Homelab Infrastructure | `docs/finance/transactions/TRX-000001.md` |
| MILESTONE-0001 | Hardware Domain Complete | Approved | Homelab Infrastructure | `docs/project/milestones/2026-07-06-hardware-domain-complete.md` |
| MILESTONE-0002 | Engineering Workstation Shared Services Complete | Approved | Homelab Infrastructure | `docs/project/milestones/2026-07-09-engineering-workstation-shared-services-complete.md` |

This table shall be updated whenever a controlled document is created, superseded, or archived.

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

The future Engineering Management Platform will govern engineering standards while Homelab remains the authoritative source for the engineering environment.

---

# Revision History

| Version | Date | Description |
| ------- | ---- | ----------- |
| 1.0 | 2026-07-06 | Initial controlled document established. |
| 1.1 | 2026-07-08 | Reconciled controlled document inventory for Architecture Baseline 2.1. |
| 1.2 | 2026-07-09 | Registered Engineering Workstation shared services milestone. |
| 1.3 | 2026-07-09 | Published and registered Governance Baseline 1.0 genesis governance records. |
