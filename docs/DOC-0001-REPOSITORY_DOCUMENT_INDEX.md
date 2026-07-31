---
document_id: DOC-0001
title: Repository Document Index
version: 2.78
status: Active
owner: Homelab Infrastructure
created: 2026-07-06
last_updated: 2026-07-31
phase: Zeus Operational Alpha
domain: Repository Governance
classification: Repository Document Index
predecessor_revision: DOC-0001@2.77
successor_revision: null
approval_status: Approved
approval_authority: Engineering Governance
approval_reference: Mission B - Authority Establishment and Portfolio Reconciliation
approval_date: 2026-07-25
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
    target: PROC-0004
  - type: indexes
    target: PROC-0005
  - type: indexes
    target: PROC-0006
  - type: indexes
    target: PROC-0007
  - type: indexes
    target: STD-0004
  - type: indexes
    target: STD-0005
  - type: indexes
    target: TPL-0004
  - type: indexes
    target: EGR-000001
  - type: related_to
    target: PROJ-0001
  - type: indexes
    target: PHASE-0001
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
    target: EWO-000015
  - type: related_to
    target: EWO-000016
  - type: related_to
    target: EWO-000017
  - type: indexes
    target: EWO-000017-COMPLETION
  - type: indexes
    target: EWO-000019
  - type: indexes
    target: EWO-000019-COMPLETION
  - type: related_to
    target: EGR-000002
  - type: indexes
    target: EGR-000003
  - type: indexes
    target: EWO-000020
  - type: indexes
    target: EGR-000004
  - type: indexes
    target: EGR-000005
  - type: indexes
    target: EGR-000006
  - type: indexes
    target: EWO-000021
  - type: indexes
    target: EWO-000021-AUTHORIZATION-EVIDENCE
  - type: indexes
    target: EWO-000021-AUTHORIZATION-COMPLETION
  - type: indexes
    target: SPEC-0007
  - type: indexes
    target: SPEC-0008
  - type: indexes
    target: SPEC-0009
  - type: indexes
    target: SPEC-0010
  - type: indexes
    target: SPEC-0011
  - type: indexes
    target: SPEC-0012
  - type: indexes
    target: SPEC-0013
  - type: indexes
    target: ARCH-0001
  - type: indexes
    target: ADR-0001
  - type: indexes
    target: SPEC-0002
  - type: indexes
    target: AQR-0001
  - type: indexes
    target: MILESTONE-0006
  - type: indexes
    target: EWO-000021-EVIDENCE
  - type: indexes
    target: EWO-000021-COMPLETION
  - type: indexes
    target: EWO-000022
  - type: indexes
    target: EWO-000022-EVIDENCE
  - type: indexes
    target: EWO-000022-COMPLETION
  - type: indexes
    target: EWO-000023
  - type: indexes
    target: EDR-0003
  - type: indexes
    target: EWO-000023-COMPLETION
  - type: indexes
    target: EWO-000023-HISTORICAL-EVIDENCE-PERSISTENCE
  - type: indexes
    target: MILESTONE-0007
  - type: indexes
    target: MILESTONE-0007-PUBLICATION-VERIFICATION
  - type: indexes
    target: MILESTONE-0008
  - type: indexes
    target: MILESTONE-0009
  - type: indexes
    target: MILESTONE-0010
  - type: related_to
    target: EWO-000018
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

Every engineering mission shall begin with the Mission Classification Gate in
PROC-0001. Apply the category-specific gates before using this repository
ritual. Category A performs the complete ritual. Category B or C performs the
repository-specific steps only when the mission consumes or affects repository
state; otherwise repository cleanliness is recorded as informational.

For Operational Alpha, an authorized WOP is the execution artifact. Its
authority is resolved through published controlled documentation, mission
eligibility, convergence authority, the EMM, and applicable runtime
verification. `engctl codex` may provide notification and optional WOP
provenance (`--wop WOP-ID`), but it neither grants execution authority nor
requires an EWO. An accepted WOP Admission Record remains the fail-closed
admission requirement when the published Operational Alpha lifecycle requires
one.

For Category A, review the repository in the following order.

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

An approved dirty-tree exception shall identify the governing authority,
pre-existing paths, isolation method, permitted shared-record overlap, and
validation required before commit. No mission classification or exception
creates engineering authority.

The active repository publications are the sole operational source for Work
Initiation, mission classification, mission lifecycle, Completion Report, and
Governance Conformance Review behavior. Handoffs shall reference these records
and shall not restate competing rules.

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

When a mission anticipates controlled document publication, Work Initiation
shall resolve PROC-0005 in addition to PROC-0001. PROC-0001 governs Work Order
execution and commit planning; PROC-0005 governs the common controlled
publication workflow, exact publication boundary, persistence transaction, and
post-publication verification. Neither procedure creates Governance approval,
lifecycle-transition authority, publication authority, or implementation
authority. Class-specific procedures remain additionally applicable.

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
| ARCH | Controlled engineering assessments recording evidence, findings, confidence, and nonbinding recommendations |
| ADR | Architecture-specific Decision Records operating within Engineering Decision Record responsibilities |
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
| PHASE-0001 | Zeus Operational Alpha Authority | Active | Homelab Infrastructure | `docs/project/PHASE-0001-ZEUS-OPERATIONAL-ALPHA-AUTHORITY.md` |
| INF-0001 | Engineering Infrastructure Baseline | Active | Homelab Infrastructure | `docs/infrastructure/INF-0001-INFRASTRUCTURE_BASELINE.md` |
| HW-0001 | Master Hardware Register | Active | Homelab Infrastructure | `docs/hardware/HW-0001-MASTER_HARDWARE_REGISTER.md` |
| EDR-0001 | Hardware Asset Record Architecture | Approved | Homelab Infrastructure | `docs/edr/EDR-0001-HARDWARE_ASSET_RECORD_ARCHITECTURE.md` |
| EDR-0002 | Engineering Authority Model | Draft | EOS Program | `docs/edr/EDR-0002-ENGINEERING_AUTHORITY_MODEL.md` |
| EDR-0003 | Governed Authorization Transaction Architecture | Approved | Engineering Governance | `docs/edr/EDR-0003-GOVERNED-AUTHORIZATION-TRANSACTION-ARCHITECTURE.md` |
| ARCH-0001 | Engineering Convergence Assessment | Draft | Homelab Infrastructure | `docs/architecture/ARCH-0001-ENGINEERING-CONVERGENCE-ASSESSMENT.md` |
| ADR-0001 | Zeus Canonical Architecture Decision | Draft | Homelab Infrastructure | `docs/architecture/ADR-0001-ZEUS-CANONICAL-ARCHITECTURE-DECISION.md` |
| AQR-0001 | Architecture Qualification Report | Draft | Homelab Infrastructure | `docs/architecture/AQR-0001-ARCHITECTURE-QUALIFICATION-REPORT.md` |
| EOS-0001 | Engineering Operating System Constitution | Draft | EOS Program | `docs/eos/EOS-0001-ENGINEERING_OPERATING_SYSTEM_CONSTITUTION.md` |
| EOS-0002 | Engineering Operating System Master Plan | Draft | EOS Program | `docs/eos/EOS-0002-ENGINEERING_OPERATING_SYSTEM_MASTER_PLAN.md` |
| EOS-0003 | EOS Operational Persistence Profile | Draft | Homelab Infrastructure | `docs/eos/EOS-0003-OPERATIONAL_PERSISTENCE_PROFILE.md` |
| EMP-0001 | Engineering Management Platform Architecture | Active | Engineering Management Platform | `docs/emp/EMP-0001-ENGINEERING_MANAGEMENT_PLATFORM_ARCHITECTURE.md` |
| SPEC-0001 | Controlled Document Model | Active | EOS Program | `docs/specifications/SPEC-0001-CONTROLLED_DOCUMENT_MODEL.md` |
| SPEC-0002 | Zeus Canonical Architecture Specification | Draft | Homelab Infrastructure | `docs/specifications/SPEC-0002-ZEUS-CANONICAL-ARCHITECTURE-SPECIFICATION.md` |
| SPEC-0004 | Engineering Context Reconstruction Service | Draft | EOS Program | `docs/specifications/SPEC-0004-ENGINEERING_CONTEXT_RECONSTRUCTION_SERVICE.md` |
| SPEC-0005 | Engineering Control Framework | Active | EOS Program | `docs/specifications/SPEC-0005-ENGINEERING_CONTROL_FRAMEWORK.md` |
| SPEC-0006 | Engineering Work Registry Model | Active | Engineering Management Platform | `docs/specifications/SPEC-0006-ENGINEERING_WORK_REGISTRY_MODEL.md` |
| SPEC-0007 | Engineering Platform Construction Specification | Active | Engineering Platform | `docs/specifications/SPEC-0007-ENGINEERING-PLATFORM-CONSTRUCTION-SPECIFICATION.md` |
| SPEC-0008 | Engineering Transaction Profile Specification | Draft | Engineering Governance | `docs/specifications/SPEC-0008-ENGINEERING_TRANSACTION_PROFILE_SPECIFICATION.md` |
| SPEC-0009 | Notification Service Specification | Active | Engineering Platform | `docs/specifications/SPEC-0009-NOTIFICATION_SERVICE_SPECIFICATION.md` |
| SPEC-0010 | Engineering Knowledge Repository Architecture | Active | Engineering Platform | `docs/specifications/SPEC-0010-ENGINEERING-KNOWLEDGE-REPOSITORY-ARCHITECTURE.md` |
| SPEC-0011 | Production Authority Restoration Specification | Active | Lawrence O'Neal | `docs/specifications/SPEC-0011-PRODUCTION-AUTHORITY-RESTORATION-SPECIFICATION.md` |
| SPEC-0012 | Production Execution Foundation | Active | Lawrence O'Neal | `docs/specifications/SPEC-0012-PRODUCTION-EXECUTION-FOUNDATION.md` |
| SPEC-0013 | Controlled Mission Assurance Language | Draft | EOS Program | `docs/specifications/SPEC-0013-CONTROLLED-MISSION-ASSURANCE-LANGUAGE.md` |
| SPEC-0014 | Operational Alpha Convergence Authority Model | Active | Homelab Infrastructure | `docs/specifications/SPEC-0014-OPERATIONAL-ALPHA-CONVERGENCE-AUTHORITY.md` |
| SERVICE-0001 | EOS Core Services Catalog | Draft | EOS Program | `docs/services/SERVICE-0001-EOS_CORE_SERVICES_CATALOG.md` |
| SERVICE-0002 | EMP Management Services Catalog | Active | Engineering Management Platform | `docs/services/SERVICE-0002-EMP_MANAGEMENT_SERVICES_CATALOG.md` |
| GEN-0001 | Engineering Operating System Genesis Record | Active | Engineering Governance | `docs/genesis/GEN-0001-GENESIS_GOVERNANCE_RECORD.md` |
| POL-0001 | Engineering Governance Policy | Active | Engineering Governance | `docs/policies/POL-0001-ENGINEERING_GOVERNANCE_POLICY.md` |
| STD-0000 | Engineering Governance Documentation Architecture | Active | Engineering Governance | `docs/standards/STD-0000-ENGINEERING_GOVERNANCE_DOCUMENTATION_ARCHITECTURE.md` |
| STD-0001 | Engineering Document Lifecycle Standard | Active | Engineering Governance | `docs/standards/STD-0001-ENGINEERING_DOCUMENT_LIFECYCLE_STANDARD.md` |
| STD-0002 | Engineering Document Persistence Standard | Active | Engineering Governance | `docs/standards/STD-0002-ENGINEERING_DOCUMENT_PERSISTENCE_STANDARD.md` |
| STD-0003 | Operational Alpha Work Authorization Standard | Active | Engineering Governance | `docs/standards/STD-0003-ENGINEERING_WORK_ORDER_STANDARD.md` |
| STD-0004 | Engineering State Freshness Standard | Active | Engineering Governance | `docs/standards/STD-0004-ENGINEERING_STATE_FRESHNESS_STANDARD.md` |
| STD-0005 | Engineering Hardware Lifecycle Standard | Active | Engineering Governance | `docs/standards/STD-0005-ENGINEERING_HARDWARE_LIFECYCLE_STANDARD.md` |
| PROC-0001 | Operational Alpha Work Initiation and Execution Procedure | Active | Engineering Governance | `docs/procedures/PROC-0001-ENGINEERING_WORK_ORDER_EXECUTION_PROCEDURE.md` |
| PROC-0002 | Engineering Governance Resolution Procedure | Active | Engineering Governance | `docs/procedures/PROC-0002-ENGINEERING_GOVERNANCE_RESOLUTION_PROCEDURE.md` |
| PROC-0003 | Engineering Recovery Runbook | Active | Engineering Governance | `docs/procedures/PROC-0003-ENGINEERING_RECOVERY_RUNBOOK.md` |
| PROC-0004 | Engineering Handoff Construction Procedure | Draft | Engineering Governance | `docs/procedures/PROC-0004-ENGINEERING_HANDOFF_CONSTRUCTION_PROCEDURE.md` |
| PROC-0005 | Controlled Document Publication Procedure | Draft | Engineering Governance | `docs/procedures/PROC-0005-CONTROLLED_DOCUMENT_PUBLICATION_PROCEDURE.md` |
| PROC-0006 | Governance Qualification Procedure | Active | Engineering Governance | `docs/procedures/PROC-0006-GOVERNANCE-QUALIFICATION-PROCEDURE.md` |
| PROC-0007 | Governance Stabilization Procedure | Active | Engineering Governance | `docs/procedures/PROC-0007-GOVERNANCE-STABILIZATION-PROCEDURE.md` |
| TPL-0001 | Operational Alpha Implementation WOP Template | Active | Engineering Governance | `docs/templates/TPL-0001-ENGINEERING_WORK_ORDER_TEMPLATE.md` |
| TPL-0002 | Completion Report Template | Active | Engineering Governance | `docs/templates/TPL-0002-ENGINEERING_COMPLETION_REPORT_TEMPLATE.md` |
| TPL-0003 | Engineering Evidence Package Template | Active | Engineering Governance | `docs/templates/TPL-0003-ENGINEERING_EVIDENCE_PACKAGE_TEMPLATE.md` |
| TPL-0004 | Engineering Governance Resolution Template | Active | Engineering Governance | `docs/templates/TPL-0004-ENGINEERING_GOVERNANCE_RESOLUTION_TEMPLATE.md` |
| EGR-000001 | Governance Foundation Qualification and Publication | Active | Engineering Governance | `docs/resolutions/EGR-000001-GOVERNANCE_FOUNDATION_QUALIFICATION_AND_PUBLICATION.md` |
| EGR-000002 | Governance Framework Modernization Authorization | Active | Engineering Governance | `docs/resolutions/EGR-000002-GOVERNANCE-FRAMEWORK-MODERNIZATION-AUTHORIZATION.md` |
| EGR-000003 | EWO-000020 Notification Service Authorization | Active | Engineering Governance | `docs/resolutions/EGR-000003-EWO-000020-NOTIFICATION-SERVICE-AUTHORIZATION.md` |
| EGR-000004 | Engineering Platform Repository Reconciliation Authorization | Active | Engineering Governance | `docs/resolutions/EGR-000004-ENGINEERING-PLATFORM-REPOSITORY-RECONCILIATION-AUTHORIZATION.md` |
| EGR-000005 | PROC-0006 Approval and Activation | Active | Engineering Governance | `docs/resolutions/EGR-000005-PROC-0006-APPROVAL-AND-ACTIVATION.md` |
| EGR-000006 | PROC-0007 Approval and Activation | Active | Engineering Governance | `docs/resolutions/EGR-000006-PROC-0007-APPROVAL-AND-ACTIVATION.md` |
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
| EWO-000015 | Governance Architecture Reconciliation | Active | Engineering Governance | `docs/work-orders/EWO-000015-GOVERNANCE-ARCHITECTURE-RECONCILIATION.md` |
| EWO-000016 | thaDuke Firmware Remediation | Active | Engineering Governance | `docs/work-orders/EWO-000016-THADUKE-FIRMWARE-REMEDIATION.md` |
| EWO-000017 | Codex Stage 1 Completion Notification Integration | Completed | Engineering Governance | `docs/work-orders/EWO-000017-CODEX-STAGE-1-COMPLETION-NOTIFICATION-INTEGRATION.md` |
| EWO-000017-COMPLETION | EWO-000017 Engineering Completion Report | Approved | Engineering Governance | `docs/work-orders/EWO-000017-ENGINEERING-COMPLETION-REPORT.md` |
| EWO-000018 | Governance Framework Modernization | Active | Engineering Governance | `docs/work-orders/EWO-000018-GOVERNANCE-FRAMEWORK-MODERNIZATION.md` |
| EWO-000019 | Codex Wrapper Enforcement and Notification Lifecycle Verification | Completed | Engineering Governance | `docs/work-orders/EWO-000019-CODEX-WRAPPER-ENFORCEMENT.md` |
| EWO-000019-COMPLETION | EWO-000019 Engineering Completion Report | Approved | Engineering Governance | `docs/work-orders/EWO-000019-ENGINEERING-COMPLETION-REPORT.md` |
| EWO-000020 | Engineering Notification Service Implementation | Superseded | Engineering Governance | `docs/work-orders/EWO-000020-ENGINEERING-NOTIFICATION-SERVICE-IMPLEMENTATION.md` |
| EWO-000021 | Engineering Platform Repository Reconciliation Mission (Handoff 1) | Active | Engineering Governance | `docs/work-orders/EWO-000021-ENGINEERING-PLATFORM-REPOSITORY-RECONCILIATION.md` |
| EWO-000021-AUTHORIZATION-EVIDENCE | EWO-000021 Authorization Evidence Package | Approved | Engineering Governance | `docs/work-orders/EWO-000021-AUTHORIZATION-EVIDENCE-PACKAGE.md` |
| EWO-000021-AUTHORIZATION-COMPLETION | EWO-000021 Authorization Completion Report | Approved | Engineering Governance | `docs/work-orders/EWO-000021-AUTHORIZATION-COMPLETION-REPORT.md` |
| EWO-000021-EVIDENCE | EWO-000021 Engineering Evidence Package | Approved | Engineering Governance | `docs/work-orders/EWO-000021-ENGINEERING-EVIDENCE-PACKAGE.md` |
| EWO-000021-COMPLETION | EWO-000021 Engineering Completion Report | Approved | Engineering Governance | `docs/work-orders/EWO-000021-ENGINEERING-COMPLETION-REPORT.md` |
| EWO-000022 | SPEC-0007 Revision 15 Controlled Publication | Superseded | Engineering Governance | `docs/work-orders/EWO-000022-SPEC-0007-REVISION-15-CONTROLLED-PUBLICATION.md` |
| EWO-000022-EVIDENCE | EWO-000022 Engineering Evidence Package | Approved | Engineering Governance | `docs/work-orders/EWO-000022-ENGINEERING-EVIDENCE-PACKAGE.md` |
| EWO-000022-COMPLETION | EWO-000022 Engineering Completion Report | Approved | Engineering Governance | `docs/work-orders/EWO-000022-ENGINEERING-COMPLETION-REPORT.md` |
| EWO-000023 | Governance Authority Architecture Investigation | Archived | Engineering Governance | `docs/work-orders/EWO-000023-GOVERNANCE-AUTHORITY-ARCHITECTURE-INVESTIGATION.md` |
| EWO-000023-COMPLETION | EWO-000023 Engineering Completion Report | Draft | Engineering Governance | `docs/work-orders/EWO-000023-ENGINEERING-COMPLETION-REPORT.md` |
| EWO-000023-PHASE-1-AUTHORITY-BOUNDARY | EWO-000023 Phase 1 Authority Boundary Analysis | Draft | Engineering Governance | `docs/work-orders/EWO-000023-PHASE-1-AUTHORITY-BOUNDARY-ANALYSIS.md` |
| EWO-000023-PHASE-1-EVIDENCE | EWO-000023 Phase 1 Engineering Evidence Package | Draft | Engineering Governance | `docs/work-orders/EWO-000023-PHASE-1-ENGINEERING-EVIDENCE-PACKAGE.md` |
| EWO-000023-PHASE-1-INVESTIGATION | EWO-000023 Phase 1 Authority-Gap Characterization | Draft | Engineering Governance | `docs/work-orders/EWO-000023-PHASE-1-INVESTIGATION-REPORT.md` |
| EWO-000023-PHASE-2-ALTERNATIVES | EWO-000023 Phase 2 Alternative Architecture Evaluation | Draft | Engineering Governance | `docs/work-orders/EWO-000023-PHASE-2-ALTERNATIVE-ARCHITECTURE-EVALUATION.md` |
| EWO-000023-PHASE-2-COMPARATIVE-ANALYSIS | EWO-000023 Phase 2 Comparative Architecture Analysis | Draft | Engineering Governance | `docs/work-orders/EWO-000023-PHASE-2-COMPARATIVE-ANALYSIS.md` |
| EWO-000023-PHASE-2-EVIDENCE | EWO-000023 Phase 2 Engineering Evidence Package | Draft | Engineering Governance | `docs/work-orders/EWO-000023-PHASE-2-ENGINEERING-EVIDENCE-PACKAGE.md` |
| EWO-000023-PHASE-2-OWNERSHIP | EWO-000023 Phase 2 Repository Ownership Analysis | Draft | Engineering Governance | `docs/work-orders/EWO-000023-PHASE-2-REPOSITORY-OWNERSHIP-ANALYSIS.md` |
| EWO-000023-PHASE-3-EVIDENCE | EWO-000023 Phase 3 Engineering Evidence Package | Draft | Engineering Governance | `docs/work-orders/EWO-000023-PHASE-3-ENGINEERING-EVIDENCE-PACKAGE.md` |
| EWO-000023-PHASE-3-RECOMMENDATION | EWO-000023 Phase 3 Governance Recommendation Package | Draft | Engineering Governance | `docs/work-orders/EWO-000023-PHASE-3-GOVERNANCE-RECOMMENDATION-PACKAGE.md` |
| EWO-000023-PHASE-3-ROADMAP | EWO-000023 Phase 3 Governed Authorization Transaction Implementation Roadmap | Draft | Engineering Governance | `docs/work-orders/EWO-000023-PHASE-3-IMPLEMENTATION-ROADMAP.md` |
| EWO-000023-PHASE-3-REPOSITORY-IMPACT | EWO-000023 Phase 3 Repository Impact Analysis | Draft | Engineering Governance | `docs/work-orders/EWO-000023-PHASE-3-REPOSITORY-IMPACT-ANALYSIS.md` |
| EWO-000023-PHASE-3-VALIDATION | EWO-000023 Phase 3 Validation Report | Draft | Engineering Governance | `docs/work-orders/EWO-000023-PHASE-3-VALIDATION-REPORT.md` |
| EWO-000023-HISTORICAL-EVIDENCE-PERSISTENCE | EWO-000023 Historical Evidence Persistence Report | Active | Engineering Governance | `docs/work-orders/EWO-000023-HISTORICAL-EVIDENCE-PERSISTENCE-REPORT.md` |
| FIN-0001 | Master Financial Ledger | Active | Homelab Infrastructure | `docs/finance/FIN-0001-MASTER_FINANCIAL_LEDGER.md` |
| FIN-0002 | Master Procurement Register | Active | Homelab Infrastructure | `docs/finance/FIN-0002-MASTER_PROCUREMENT_REGISTER.md` |
| PROC-000001 | Engineering Terminal 01 Procurement | Closed | Homelab Infrastructure | `docs/finance/procurements/PROC-000001.md` |
| PROC-000002 | Engineering Spare microSD Card 01 Procurement | Closed | Homelab Infrastructure | `docs/finance/procurements/PROC-000002.md` |
| TRX-000001 | Procurement Transaction - Engineering Terminal 01 | Posted | Homelab Infrastructure | `docs/finance/transactions/TRX-000001.md` |
| TRX-000002 | Procurement Transaction - Engineering Spare microSD Card 01 | Posted | Homelab Infrastructure | `docs/finance/transactions/TRX-000002.md` |
| AST-000009 | Engineering Spare microSD Card 01 | Available | Homelab Infrastructure | `docs/hardware/assets/AST-000009.md` |
| AST-000010 | WD 500 GB External HDD | Available | Homelab Infrastructure | `docs/hardware/assets/AST-000010.md` |
| MILESTONE-0001 | Hardware Domain Complete | Approved | Homelab Infrastructure | `docs/project/milestones/2026-07-06-hardware-domain-complete.md` |
| MILESTONE-0002 | Engineering Workstation Shared Services Complete | Approved | Homelab Infrastructure | `docs/project/milestones/2026-07-09-engineering-workstation-shared-services-complete.md` |
| MILESTONE-0003 | Engineering Platform Mission 0 Complete | Approved | Homelab Infrastructure | `docs/project/milestones/2026-07-13-engineering-platform-mission-0-complete.md` |
| MILESTONE-0004 | Engineering Management Platform Foundation 1.0 Operational | Approved | Engineering Management Platform | `docs/project/milestones/2026-07-13-engineering-management-platform-foundation-1.0-operational.md` |
| MILESTONE-0005 | Engineering Platform Foundation 1.0 — Foundation Complete | Approved | Homelab Infrastructure | `docs/project/milestones/2026-07-15-engineering-platform-foundation-1.0-foundation-complete.md` |
| MILESTONE-0006 | Engineering Platform Transition to Self-Implementation | Approved | Engineering Platform | `docs/project/milestones/2026-07-17-engineering-platform-transition-to-self-implementation.md` |
| MILESTONE-0007 | Governance Authority Transaction Architecture Qualified | Approved | Engineering Governance | `docs/project/milestones/2026-07-18-governance-authority-transaction-architecture-qualified.md` |
| MILESTONE-0007-PUBLICATION-VERIFICATION | MILESTONE-0007 Publication Verification Report | Active | Engineering Governance | `docs/project/milestones/MILESTONE-0007-PUBLICATION-VERIFICATION-REPORT.md` |
| MILESTONE-0008 | Engineering Governance Framework Version 1.0 Operationally Qualified | Approved | Engineering Governance | `docs/project/milestones/2026-07-18-engineering-governance-framework-1.0-operationally-qualified.md` |
| MILESTONE-0009 | Operational Alpha Governance Baseline 1.0 and Governance Freeze | Approved | Engineering Governance | `docs/project/milestones/2026-07-29-operational-alpha-governance-baseline-1.0.md` |
| MILESTONE-0010 | Operational Alpha Implementation Baseline 1.0 Adoption | Approved | Homelab Infrastructure | `docs/project/milestones/2026-07-30-operational-alpha-implementation-baseline-1.0.md` |
| MILESTONE-0011 | Operational Alpha Convergence Runtime Closeout and Transition | Approved | Homelab Infrastructure | `docs/project/milestones/2026-07-30-operational-alpha-convergence-runtime-closeout.md` |

This table shall be updated whenever a controlled document is created, superseded, or archived.

---

# Architecture Documentation Discovery

The canonical repository placement for controlled engineering assessments and
architecture-specific decision records is:

```text
docs/architecture/
```

`ARCH` is a registered domain-record subtype under the Domain and Project
Records responsibility in STD-0000. An ARCH record owns a bounded assessment:
evidence, method, findings, confidence, maturity, risk, and nonbinding
recommendations. It shall not establish an architecture decision, technical
requirement, lifecycle transition, or implementation authority.

`ADR` is the architecture-specific registered subtype of the Engineering
Decision Record responsibility defined by STD-0000. ADR and EDR do not form
competing decision hierarchies. ADR is used when the decision subject is a
system architecture; EDR remains the general engineering-decision class.

`AQR` is a registered domain-record subtype for an Architecture Qualification
Report. It owns architecture-specific qualification criteria, evidence
mapping, findings, readiness determinations, and promotion recommendations.
It does not own architecture decisions, the reusable qualification workflow,
controlled-document lifecycle transitions, publication, baseline activation,
or implementation authority. AQR records conform to PROC-0006 and return
recommendations to the applicable decision owner.

Permanent ARCH, ADR, and AQR identifiers use their class prefix followed by a
four-digit decimal sequence. Assignment begins with `ARCH-0001`, `ADR-0001`,
and `AQR-0001`, proceeds monotonically within each namespace, and accounts for
current, historical, staged, unstaged, untracked, and explicitly reserved
identifiers. Identifiers are never reused.

Architecture discovery begins with this index, then verifies:

1. identifier, title, status, owner, and canonical path;
2. YAML metadata, lifecycle, approval, persistence, and relationships;
3. source evidence and immutable provenance;
4. assessment-to-decision-to-specification traceability; and
5. the applicable exact revision before any downstream use.

The initial traceability chain is:

```text
ENGINEERING-CONVERGENCE-REVIEW-001 (historical evidence)
    -> ARCH-0001
    -> ADR-0001
    -> SPEC-0002
    -> AQR-0001 (qualification and recommendation only)
    -> MILESTONE-0010 (HF-012-qualified implementation-planning baseline)
    -> future bounded WOPs
```

The historical review archive remains evidence only. Draft ARCH, ADR, and SPEC
records possess no operational authority. Approval, activation, publication,
and future implementation remain separate controlled decisions.

No separate architecture, ADR, or specification index exists in this
repository. DOC-0001 is the authoritative controlled-document catalogue and
namespace coordination record. The EMP Work Registry owns operational
management state and is not a duplicate controlled-document registry.

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

EGR-000001 records Governance Foundation qualification and publication.
EGR-000002 authorizes Governance Framework Modernization and activates
EWO-000018 as the bounded implementation contract.

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
| AST-000005 | Seagate Backup Plus Ultra Touch | Available — enclosure SMART telemetry limitation | Homelab Infrastructure | `docs/hardware/assets/AST-000005.md` |
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

# Engineering Service Discovery

## EENS Operational Alpha

The Engineering Event and Notification System Operational Alpha is the
qualified notification-service implementation represented in this repository.

Its canonical repository source is:

```text
services/eens
```

The canonical engineering-workstation source location is:

```text
/data/engineering/repositories/homelab/services/eens
```

The qualified LOpi operational deployment is:

```text
/home/loneal/data/engineering/eens
```

`services/eens` is the authoritative version-controlled implementation source.
The LOpi path is the qualified runtime deployment produced from that source.
Runtime deployment state does not replace repository history or controlled
engineering records, and repository publication alone does not assert that a
deployment is running or qualified.

The Operational Alpha includes append-only event persistence, idempotent event
acceptance, ordered replay, independent durable consumer checkpoints,
engineering handoff and wrapped-command lifecycle event production, and
continuous notification delivery through ntfy.

SPEC-0009 remains the authoritative notification-service architecture.
INF-0001 owns the infrastructure and deployment baseline. PROJ-0001 owns
current project state. The Work Registry records operational management state.

Future HNS capabilities, including authenticated WebSocket transport,
workstation clients, subscription management, delivery-attempt evidence,
producer authorization, advanced routing and retry policy, Remote Approval,
and complete HNS qualification, remain future engineering work.

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

## Mission 0 Qualification Authority and Traceability

The following map establishes authoritative ownership for reusable Mission 0
qualification guidance. Future handoffs shall reference these authorities
instead of reproducing their procedures.

| Engineering concern | Authoritative document | Supporting relationship |
| --- | --- | --- |
| Asset lifecycle, qualification gates, appropriation, monitoring, and retirement | STD-0005 | HW-0001 and AST records own asset-specific state. |
| Qualification orchestration and report requirement | STD-0005 | A future platform-specific procedure references existing authorities; it does not duplicate them. |
| Qualification Report persistence and automation dependency | SPEC-0007 | STD-0004 owns state freshness; SPEC-0004 owns derived resume reconstruction. |
| Evidence identity, acquisition, preservation, recovery, restoration, execution-environment verification, and hardware isolation | PROC-0003 | PROC-0001 initiates bounded work; project records supply system-specific acceptance criteria. |
| Engineering host baseline, repository locations, storage capability, and host-versus-sandbox model | INF-0001 | Project infrastructure references this global baseline without duplicating it. |
| Controlled-document discovery, authority routing, and publication traceability | DOC-0001 | PROC-0005 governs controlled publication; STD-0001 and STD-0002 govern lifecycle and persistence. |

The lifecycle vocabulary is: Asset Discovery, Asset Identification,
Inventory, Evidence Acquisition, Qualification, Operational Assignment
(Appropriation), Monitoring, and Retirement. Recovery, Restoration, and
Operational Deployment are separate decisions and shall not be inferred from
acquisition, readability, backup status, or qualification alone.

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
* Verify evidence identity before investigation
* Preserve evidence before recovery or repair
* Qualify assets independently of project assignment
* Distinguish Engineering host state from execution-environment constraints
* Isolate one variable before permanent hardware disqualification

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
| 2.15 | 2026-07-16 | Registered AST-000010 as the qualified WD 500 GB External HDD under preservation hold without creating unsupported financial facts. |
| 2.16 | 2026-07-16 | Published and registered STD-0005 as the single Engineering Hardware Lifecycle authority and integrated deterministic discovery. |
| 2.17 | 2026-07-16 | Recorded AST-000005 enclosure-boundary failure isolation and qualification hold. |
| 2.18 | 2026-07-16 | Recorded owner-authorized AST-000005 secure reprovisioning disposition and pending-requalification lifecycle. |
| 2.19 | 2026-07-17 | Synchronized AST-000005 qualified Linux configuration and Available lifecycle state with its authoritative asset and hardware records. |
| 2.20 | 2026-07-17 | Registered EWO-000017 and reconciled the previously approved EWO-000015 registration while integrating shared Codex lifecycle notifications. |
| 2.21 | 2026-07-17 | Registered EGR-000002 and EWO-000018 as the authorization and bounded successor implementation contract for holistic governance-framework modernization. |
| 2.22 | 2026-07-17 | Reconciled repository Work Initiation with Category A/B/C gates and registered repository-governed Completion Report and Governance Conformance Review behavior under EWO-000018. |
| 2.23 | 2026-07-17 | Registered EWO-000017 completion, its Completion Report, and accepted Stage 1 notification capability. |
| 2.24 | 2026-07-17 | Registered and activated EWO-000019 for Codex wrapper enforcement and notification lifecycle verification. |
| 2.25 | 2026-07-17 | Integrated mandatory `engctl codex` launch and wrapper-bypass detection into repository Work Initiation under EWO-000019. |
| 2.26 | 2026-07-17 | Registered EWO-000019 completion, lifecycle acceptance, and its Engineering Completion Report. |
| 2.27 | 2026-07-17 | Registered EGR-000003 and approved Active EWO-000020 as the bounded Engineering Notification Service implementation authority. |
| 2.28 | 2026-07-17 | Registered EGR-000004, superseded unstarted EWO-000020, and registered Approved Active EWO-000021 plus authorization evidence and closeout records. |
| 2.29 | 2026-07-17 | Published SPEC-0007 Engineering Baseline 1.0, MILESTONE-0006, EWO-000021 execution evidence, and the Completion Report. |
| 2.30 | 2026-07-17 | Registered Approved Active EWO-000022 as the bounded authority for SPEC-0007 Revision 15 controlled publication. |
| 2.31 | 2026-07-17 | Published SPEC-0007 Version 1.1 from the authoritative Revision 15 manuscript and registered EWO-000022 publication evidence and Completion Report. |
| 2.32 | 2026-07-18 | Superseded completed EWO-000022 and registered approved Active EWO-000023 as the bounded governance-authority architecture investigation. |
| 2.33 | 2026-07-18 | Registered Approved EDR-0003 Version 0.3, the complete EWO-000023 historical evidence set, the Archived lifecycle transition, and the immutable-boundary verification record without publishing MILESTONE-0007. |
| 2.34 | 2026-07-18 | Published and registered MILESTONE-0007 as the historical summary of the immutable EWO-000023 qualification boundary and registered its publication verification without advancing EDR-0003 or authorizing implementation. |
| 2.35 | 2026-07-18 | Synchronized STD-0003 Version 1.3, PROC-0001 Version 1.8, TPL-0001 Version 1.3, and TPL-0002 Version 1.2 as the atomic Engineering Reporting Standard implementation without creating a new reporting class. |
| 2.36 | 2026-07-18 | Synchronized TPL-0001 Version 1.4 as the next-generation Engineering Handoff authorization-contract template without revising secondary controlled documents or the qualified governance architecture. |
| 2.37 | 2026-07-18 | Published and indexed PROC-0004 Version 1.0 as the authoritative Engineering Handoff construction procedure and synchronized TPL-0001 Version 1.5 as its structural template. |
| 2.38 | 2026-07-18 | Published and indexed SPEC-0008 Version 1.0 with one conservative baseline ETP, synchronized PROC-0004 Version 1.1 and TPL-0001 Version 1.6, and integrated fail-closed validation without creating a new document class or runtime service. |
| 2.39 | 2026-07-18 | Published and indexed SPEC-0009 Version 1.0 as the authoritative Notification Service architecture with deterministic lifecycle, ownership, identity, interface, compatibility, and Deferred Execution boundaries without authorizing implementation. |
| 2.40 | 2026-07-18 | Published and indexed PROC-0005 Version 1.0 as the single reusable operational controlled-document publication procedure with separated authority domains, exact publication-boundary controls, deterministic evidence, proportional application, and informative automation transitions without authorizing automation or implementation. |
| 2.41 | 2026-07-18 | Integrated PROC-0005 across the documentation architecture, lifecycle and persistence standards, Work Order execution, EGR processing, Handoff construction, and Work Initiation while preserving normative and specialized ownership. |
| 2.42 | 2026-07-18 | Corrected TPL-0001 to resolve PROC-0005 for common controlled publication while preserving PROC-0001 as the Engineering Work Order execution owner. |
| 2.43 | 2026-07-18 | Registered PROC-0006 Version 0.1 as the Draft Governance Qualification Procedure implementing the qualified nine-stage capability without granting operational authority or publishing it as Active. |
| 2.44 | 2026-07-18 | Registered qualified Draft PROC-0006 Version 0.2 after bounded stage-accounting and terminal-routing remediation; approval, activation, and controlled publication remain pending. |
| 2.45 | 2026-07-18 | Approved, activated, published, and integrated PROC-0006 Version 1.0 under EGR-000005, with reference-only revisions to PROC-0001, PROC-0002, PROC-0004, and PROC-0005. |
| 2.46 | 2026-07-18 | Registered PROC-0007 Version 0.1 as the Draft Governance Stabilization Procedure implementing the qualified twelve-stage orchestration model with Active PROC-0006 as its external qualification dependency. |
| 2.47 | 2026-07-18 | Approved, activated, published, and integrated PROC-0007 Version 1.0 under EGR-000006, with reference-only revisions to PROC-0001, PROC-0002, PROC-0004, PROC-0005, and PROC-0006. |
| 2.48 | 2026-07-18 | Registered MILESTONE-0008 as the Approved Engineering Governance Framework Version 1.0 operational-qualification boundary completing Governance Phase I without changing procedures or introducing implementation authority. |
| 2.49 | 2026-07-19 | Reconciled STD-0005, PROC-0003, and INF-0001 authority for the Mission 0 qualification lifecycle; added host-versus-sandbox, evidence-identity, preservation, hardware-isolation, storage-qualification, and appropriation traceability without duplicating operational procedures. |
| 2.50 | 2026-07-19 | Published and registered SPEC-0010 as the Engineering Knowledge Repository architecture and synchronized STD-0000/STD-0002 knowledge-object, persistence, EOS-boundary, and historical-discovery authority. |
| 2.51 | 2026-07-19 | Synchronized STD-0005 Version 1.2, SPEC-0007 Version 1.2, and SPEC-0004 Version 1.3 for reference-oriented Raspberry Pi qualification orchestration, standardized Qualification Reports, persistent Engineering State consumption, resume integration, and authoritative-procedure dependency without implementation. |
| 2.52 | 2026-07-21 | Registered EENS Operational Alpha service discovery, canonical repository source, qualified LOpi deployment, source-versus-deployment boundary, implemented capabilities, and deferred HNS expansion under Mission 7 repository convergence. |
| 2.53 | 2026-07-24 | Removed the invalid non-controlled `discovers` relationship to the unresolved `EENS-OPERATIONAL-ALPHA` service label while preserving indexed SPEC-0009 authority and the EENS service-discovery record. |
| 2.54 | 2026-07-25 | Indexed PHASE-0001 and reconciled repository discovery to the Zeus Operational Alpha authority baseline while preserving completed EENS history. |
| 2.55 | 2026-07-26 | Published and indexed SPEC-0011 and reconciled the production authority hierarchy, controlled-document execution authority, Zeus CLI semantics, and Authority Restoration Principle. |
| 2.56 | 2026-07-26 | Registered SPEC-0012 and the production execution foundation while preserving dispatcher activation, agent registration, baseline publication, and first operational execution qualification as separate controls. |
| 2.57 | 2026-07-28 | Registered SPEC-0013 Version 1.0 as the Draft Controlled Mission Assurance Language candidate and bound Zeus assurance interpretation to its exact revision; approval, activation, and controlled publication remain separate decisions. |
| 2.58 | 2026-07-29 | Registered MILESTONE-0009 as the Operational Alpha constitutional baseline and governance-freeze transition, including mandatory synchronized documentation, qualification, and verification change control. |
| 2.59 | 2026-07-29 | Reconciled PROC-0001 Version 1.17, PROC-0005 Version 1.5, STD-0004 Version 1.4, and EOS-0003 Version 1.4 with the repository-authoritative EOS publication contract and explicit synchronization boundaries. |
| 2.60 | 2026-07-29 | Registered SPEC-0012 Version 1.1 as the frozen canonical Progressive authority-primitives, decision-authority, compatibility, and lifecycle-projection implementation baseline. |
| 2.61 | 2026-07-29 | Registered SPEC-0012 Version 1.2 as the exactly three-layer, architecturally frozen Progressive Runtime Layer baseline. |
| 2.62 | 2026-07-29 | Registered SPEC-0012 Version 1.3 as the enforced downward-only Progressive Runtime Layer dependency contract and compatibility-isolation baseline. |
| 2.63 | 2026-07-29 | Registered SPEC-0012 Version 1.4 as the governed Runtime Extension Rule and fail-closed runtime-classification baseline. |
| 2.64 | 2026-07-29 | Registered SPEC-0012 Version 1.5 as the Runtime Registration Rule and fail-closed runtime-consumer registry synchronization baseline. |
| 2.65 | 2026-07-29 | Registered SPEC-0012 Version 1.6 as the Runtime Capability Rule and fail-closed runtime-capability traceability baseline. |
| 2.66 | 2026-07-29 | Registered SPEC-0012 Version 1.7 as the Runtime Policy Rule and fail-closed runtime-policy governance baseline. |
| 2.67 | 2026-07-29 | Registered SPEC-0012 Version 1.8 as the Runtime State Rule and fail-closed runtime-state governance baseline. |
| 2.68 | 2026-07-29 | Registered SPEC-0012 Version 1.9 as the Runtime Transition Rule and fail-closed runtime-transition governance baseline. |
| 2.69 | 2026-07-29 | Registered SPEC-0012 Version 1.10 as the Runtime Execution Contract Rule and fail-closed runtime-execution-contract governance baseline. |
| 2.70 | 2026-07-29 | Registered SPEC-0012 Version 1.11 as the Runtime Outcome Rule and fail-closed runtime-outcome governance baseline. |
| 2.71 | 2026-07-29 | Registered SPEC-0012 Version 1.12 and the consolidated Progressive Runtime Governance Baseline v1.0, preserving the accepted three-layer architecture and unchanged runtime behavior. |
| 2.72 | 2026-07-30 | Registered Draft ARCH-0001, ADR-0001, and SPEC-0002; established ARCH and ADR discovery and numbering; and recorded historical-assessment-to-decision-to-specification traceability without approval, activation, publication, or implementation authority. |
| 2.73 | 2026-07-30 | Registered Draft AQR-0001 as the architecture-specific qualification criteria, evidence, readiness, and promotion-recommendation record; established AQR discovery and numbering while preserving PROC-0006 qualification, STD-0001 lifecycle, Engineering Governance disposition, and PROC-0005 publication authority. |
| 2.74 | 2026-07-30 | Reconciled registration for SPEC-0002 Draft 1.3 and AQR-0001 Draft 1.1, including complete ADR component, invariant, interface, and Future Implementation traceability plus observational Repository Convergence Qualification; no architecture decision, repository convergence, lifecycle transition, publication, synchronization, or promotion authority was introduced. |
| 2.75 | 2026-07-30 | Registered MILESTONE-0010 and the `OA-IMPLEMENTATION-BASELINE-1.0` adoption trace. The entry establishes an implementation-planning baseline from HF-012 without activating Draft architecture records or authorizing implementation. |
| 2.76 | 2026-07-30 | Registered SPEC-0014 and synchronized the controlled Operational Alpha authority migration across STD-0003, PROC-0001, SPEC-0005, PROC-0006, TPL-0001, and TPL-0002. |
| 2.77 | 2026-07-30 | Registered MILESTONE-0011 and the certified `ZEUS-CONVERGENCE-RUNTIME-BASELINE-1.0` registry trace; Operational Alpha remains blocked at OA-01 until its separately controlled execution prerequisites exist. |
| 2.78 | 2026-07-31 | Reconciled Operational Alpha initiation to the published WOP and convergence-authority model; historical EWOs no longer gate repository-governed Operational Alpha execution. |
