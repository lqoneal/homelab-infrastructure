---
document_id: STD-0005
title: Engineering Hardware Lifecycle Standard
version: 1.0
status: Active
owner: Engineering Governance
created: 2026-07-16
last_updated: 2026-07-16
phase: Engineering Hardware Lifecycle Standard Publication
domain: Engineering Hardware
classification: Engineering Standard
predecessor_revision: null
successor_revision: null
approval_status: Approved
approval_authority: Engineering Governance
approval_reference: Codex Handoff Procedure - WD 500 GB Inventory and Engineering Hardware Lifecycle Standard
approval_date: 2026-07-16
persistence_status: Pending
source_of_truth: true
declared_deferrals:
  - hardware-lifecycle-automation
relationships:
  - type: governed_by
    target: CHAR-0001
  - type: conforms_to
    target: POL-0001
  - type: conforms_to
    target: STD-0000
  - type: related_to
    target: STD-0001
  - type: related_to
    target: STD-0002
  - type: related_to
    target: STD-0004
  - type: required_by
    target: HW-0001
  - type: related_to
    target: PROC-0001
  - type: related_to
    target: PROC-0003
  - type: related_to
    target: INF-0001
  - type: indexed_by
    target: DOC-0001
tags:
  - hardware
  - lifecycle
  - onboarding
  - qualification
  - preservation
  - asset-management
---

# Engineering Hardware Lifecycle Standard

## Purpose

This standard is the single governing authority for onboarding, assigning,
operating, managing, retiring, and disposing of engineering hardware. It
generalizes the evidence-backed workflow proven by storage qualification and
AST-000010 registration without duplicating the technical procedures owned by
PROC-0001, PROC-0003, or other asset-class authorities.

## Scope

This standard applies to current and future engineering assets, including:

- HDDs, SSDs, microSD cards, and USB storage;
- Raspberry Pi and other embedded hardware;
- laptops, workstations, tablets, and phones;
- networking equipment, printers, and peripherals; and
- any future physical asset accepted into the engineering portfolio.

It governs lifecycle gates and required evidence. It does not authorize a
purchase, data access, repair, destructive test, data movement, role
assignment, retirement, disposal, or financial assertion. Each execution
requires its own bounded authority.

## Authority and Information Ownership

Engineering Governance owns this standard. Information remains owned once:

- HW-0001 owns asset identifiers, register membership, portfolio summaries,
  ownership, assignment summaries, and lifecycle-state reporting;
- each AST record owns detailed identity, qualification, role, condition,
  limitations, history, and disposition for its asset;
- finance records own supported procurement and transaction facts;
- infrastructure and project records own operational integration and assigned
  role baselines;
- PROC-0003 owns storage diagnostics, protected inspection, recovery, and
  storage evidence procedures;
- PROC-0001 owns Work Initiation, Commit Classification, Commit Reconstruction
  Planning, and governed execution; and
- STD-0004 owns Engineering State freshness and reconciliation.

No checklist, inventory view, resume output, or asset record may establish a
second hardware-lifecycle authority.

## Governing Principles

### Preservation First

Unknown or pre-existing data, configuration, credentials, licenses, evidence,
or device state shall be treated as potentially valuable until assessed.
Repurposing, repair, reset, formatting, firmware modification, secure erase,
retirement, or disposal shall not precede the applicable preservation gate.

### Evidence First

Lifecycle decisions shall be supported by observed identity, condition,
content or configuration state where authorized, qualification results,
limitations, provenance, and attributable decision evidence. Absence of
purchase information shall be recorded as unknown rather than invented.

### Read-Only Qualification by Default

Storage and data-bearing hardware shall be discovered and assessed without
writes by default. Read-write access, modifying diagnostics, firmware changes,
repair, and destructive testing require explicit authority and protected
evidence. Non-storage hardware shall use the least-mutating diagnostic method
capable of supporting the required conclusion.

### Role Follows Qualification

Ownership may be established at registration, but operational role and project
assignment shall follow identity, health, preservation, compatibility, and
risk qualification. A healthy device with unresolved valuable data may be
registered as available and unassigned under preservation hold.

## Required Lifecycle

```text
Hardware Discovery
        ↓
Identity Verification
        ↓
Health Qualification
        ↓
Content Inventory
        ↓
Preservation Assessment
        ↓
Asset Registration
        ↓
Financial Reconciliation
        ↓
Role Assignment
        ↓
Operational Integration
        ↓
Lifecycle Management
        ↓
Retirement / Disposal
```

No downstream gate implies permission to bypass an incomplete upstream gate.
A non-data-bearing asset may record Content Inventory and Preservation
Assessment as not applicable with evidence and rationale; those gates are not
silently omitted.

## Gate Requirements

### 1. Hardware Discovery

Execute Engineering Work Initiation under PROC-0001. Record authority, host,
operator, UTC time, repository and Engineering State, discovery method,
physical context, and pre-existing condition. Isolate one candidate when
practical and avoid actions that could change its state.

### 2. Identity Verification

Establish the strongest available identity before testing. Evidence may
include manufacturer, model, model number, serial, WWN, MAC address, service
tag, capacity, hardware revision, firmware, physical labels, bus topology, and
cryptographically verified management identity. Volatile device paths and
network addresses are observations, not identities.

Stop on identity ambiguity, mismatch, duplicate serial, unexpected capacity,
or inability to distinguish the candidate from a protected asset.

### 3. Health Qualification

Use asset-appropriate, non-destructive diagnostics and record tool versions,
commands, output, exit status, condition, errors, limitations, power and
thermal observations, interface evidence, and qualification decision. Storage
uses PROC-0003 and the Engineering Storage Qualification Capability. A vendor
summary alone does not override error evidence.

### 4. Content Inventory

For data-bearing assets, inventory only within explicit access authority.
Default to protected read-only access and collect the minimum information
needed to classify content: utilization, top-level structure, major sizes,
largest objects when required, dominant categories, configuration, and likely
ownership. Do not copy, open private content unnecessarily, repair, index into
an uncontrolled service, or alter access timestamps when avoidable.

### 5. Preservation Assessment

Classify data, configuration, licenses, evidence, and recoverability as
preserve, archive, migrate, review, repurpose-after-migration, or quarantine.
Identify unique material, existing backups, retention constraints, privacy,
security, legal, and operational dependencies. Preserve first; uncertainty
defaults to review or quarantine, not deletion.

### 6. Asset Registration

After identity and health qualification succeed, allocate the next permanent
AST identifier, prove uniqueness across current and historical records, create
the AST record, update HW-0001, and register discovery in DOC-0001 when
required by repository architecture. Record owner, assignment, status,
location, evidence, limitations, preservation state, and lifecycle history.
Identifiers are never reused.

Registration records an asset; it does not certify a future role, authorize
data disposition, or imply financial provenance.

### 7. Financial Reconciliation

Link existing procurement, transaction, warranty, ownership, and valuation
evidence when available and required by finance policy. Do not infer vendor,
price, purchase date, tax, warranty, depreciation, or funding source. Record
unknown facts explicitly and leave finance records unchanged when no supported
financial event exists.

### 8. Role Assignment

Assign an engineering role only after qualification and preservation gates
support it. Record role, project assignment, criticality, suitability,
capacity, security, performance, compatibility, redundancy, recovery, and
maintenance expectations. Ownership and assignment remain independent.

### 9. Operational Integration

Integrate through the owning infrastructure or project baseline. Validate
connectivity, power, firmware and software compatibility, security controls,
monitoring, backup or recovery requirements, configuration persistence,
service behavior, and rollback. Do not place an asset into production merely
because it passed standalone health checks.

### 10. Lifecycle Management

Maintain condition, location, ownership, assignment, maintenance, incidents,
configuration, firmware, capacity, warranty, preservation holds, dependencies,
and periodic requalification proportionate to risk. Every material change
shall update the owning AST record and affected register, infrastructure,
project, finance, and Engineering State owners.

### 11. Retirement and Disposal

Retirement removes an asset from operational service but preserves its
identifier and history. Before disposal, verify replacement and dependency
closure, preserve required data and configuration, obtain explicit data-
sanitization and disposal authority, use an asset-appropriate verified method,
record evidence and chain of custody, reconcile financial disposition when
supported, update lifecycle state, and retain the AST record permanently.

Failure to verify sanitization or physical disposition blocks a disposal
claim. A retired asset is not automatically safe to discard or reuse.

## Lifecycle Decisions and Stop Conditions

At every gate, select and record one supported disposition: proceed, preserve,
archive, migrate, review, repurpose after migration, quarantine, retire, or
dispose. Stop and preserve evidence when:

- authority, identity, ownership, or asset boundaries are ambiguous;
- diagnostics indicate hardware, interface, power, thermal, firmware,
  filesystem, or data-integrity risk;
- protected, private, unique, regulated, or unknown content may be endangered;
- a required tool, administrator context, backup, recovery path, or evidence
  destination is unavailable;
- registration would duplicate an identifier or unsupported fact;
- role assignment would precede qualification or preservation;
- retirement or disposal would strand a dependency or lack verified data
  disposition; or
- repository, controlled-document, Engineering State, or validation integrity
  fails.

## Documentation and Engineering State Reconciliation

Each lifecycle execution updates only affected information owners. At minimum,
reconcile the AST record and HW-0001; update DOC-0001, finance, infrastructure,
project, milestone, or recovery records only when their owned facts change.
Do not create a new procedure when an existing authority applies.

Before commit, execute Engineering State Reconciliation under STD-0004 and
Commit Classification and Commit Reconstruction Planning under PROC-0001.
Separate unrelated hardware registration, standard publication, operational
integration, milestone, and finance objectives into governed commit
boundaries. After authorized commits, refresh EOS state, create the applicable
checkpoint, and verify resume accuracy.

## Minimum Evidence

Preserve mission authority, operator, host, UTC timing, repository state,
identity, physical observations, tools and versions, diagnostic commands and
results, content and preservation classification when authorized, limitations,
stop decisions, registration and financial reconciliation, role and
integration evidence, lifecycle decision, validation results, committed paths,
commit identifiers, and Engineering State reconciliation.

Evidence shall avoid unnecessary secrets and personal content while remaining
sufficient to reconstruct the decision.

## Revision History

| Version | Date | Description |
| --- | --- | --- |
| 1.0 | 2026-07-16 | Established the preservation-first, evidence-first engineering hardware onboarding, operation, lifecycle-management, retirement, and disposal authority. |
