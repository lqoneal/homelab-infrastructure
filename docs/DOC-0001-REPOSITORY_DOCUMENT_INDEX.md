---

document_id: DOC-0001
title: Repository Document Index
version: 1.0
status: Active
owner: Homelab Infrastructure
created: 2026-07-06
last_updated: 2026-07-06
phase: Mission 0 / Phase 0.1
domain: Repository Governance
classification: Repository Document Index
source_of_truth: true
related_documents:

* PROJ-0001
* INF-0001
  tags:
* repository
* governance
* documentation
* index
* source-of-truth

---

# Repository Document Index

## Purpose

This document is the authoritative index for all controlled engineering documents contained within the Homelab repository.

It serves as the primary navigation document for engineers, automation, and future Engineering Management Platform tooling.

All controlled engineering documents shall be registered in this document.

---

# Repository Purpose

The Homelab repository is the authoritative source for the engineering environment supporting the entire portfolio.

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
6. Review the active Phase document.
7. Review task-specific controlled documents.
8. Review Git branch, commit, and working tree.
9. Resume implementation.

---

# Controlled Document Classification

| Prefix  | Description                          |
| ------- | ------------------------------------ |
| DOC     | Repository governance and navigation |
| PROJ    | Project state and execution          |
| PHASE   | Mission and phase execution plans    |
| INF     | Infrastructure documentation         |
| HW      | Hardware documentation               |
| FIN     | Financial documentation              |
| SPEC    | Technical specifications             |
| STD     | Engineering standards                |
| ADR     | Architecture Decision Records        |
| EDR     | Engineering Decision Records         |
| JOURNAL | Engineering history and milestones   |

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

| Document ID | Title                     | Status  | Owner                  |
| ----------- | ------------------------- | ------- | ---------------------- |
| DOC-0001    | Repository Document Index | Active  | Homelab Infrastructure |
| PROJ-0001   | Project State             | Active  | Homelab Infrastructure |
| INF-0001    | Infrastructure Baseline   | Planned | Homelab Infrastructure |
| HW-0001     | Master Hardware Register  | Planned | Homelab Infrastructure |
| FIN-0001    | Financial Ledger          | Planned | Homelab Infrastructure |
| FIN-0002    | Procurement Log           | Planned | Homelab Infrastructure |

This table shall be updated whenever a controlled document is created, superseded, or archived.

---

# Source of Truth

Each engineering artifact shall have one authoritative owner.

Examples:

* Engineering workstation → Homelab
* Repository governance → DOC documents
* Project execution → PROJ documents
* Mission planning → PHASE documents
* Hardware inventory → HW documents
* Financial records → FIN documents

Duplication of controlled engineering information is prohibited.

---

# Engineering Principles

The Homelab repository follows the Engineering Constitution approved for the portfolio.

The governing principles include:

* Single Source of Truth
* Separation of Responsibilities
* Standards Before Automation
* Reproducibility
* Traceability
* Layered Architecture
* Controlled Documentation
* Automation as an Engineer
* Human Authority
* Foundation Before Features

---

# Relationship to the Engineering Portfolio

Homelab provides the engineering environment for the portfolio.

It supplies the global infrastructure baseline consumed by product repositories.

The future Engineering Management Platform will govern engineering standards while Homelab remains the authoritative source for the engineering environment.

---

# Revision History

| Version | Date       | Description                              |
| ------- | ---------- | ---------------------------------------- |
| 1.0     | 2026-07-06 | Initial controlled document established. |

