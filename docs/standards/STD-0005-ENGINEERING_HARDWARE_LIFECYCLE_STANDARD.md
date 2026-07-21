---
document_id: STD-0005
title: Engineering Hardware Lifecycle Standard
version: 1.2
status: Active
owner: Engineering Governance
created: 2026-07-16
last_updated: 2026-07-19
phase: Raspberry Pi Qualification Architecture Recommendation Persistence
domain: Engineering Hardware
classification: Engineering Standard
predecessor_revision: STD-0005@1.1
successor_revision: null
approval_status: Approved
approval_authority: Engineering Governance
approval_reference: Codex Handoff - Persist Raspberry Pi Qualification Architecture Recommendations
approval_date: 2026-07-19
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
  - type: related_to
    target: SPEC-0007
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

Positive evidence identity is a prerequisite to technical investigation.
Before qualification, recovery, repair, restoration, or forensic analysis,
establish that the evidence and asset under observation are the intended
subjects and preserve the identity basis. An accessible device path, readable
filesystem, matching capacity, backup, or successful command is not positive
identity by itself.

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

### Qualification Is Asset-Oriented

Mission 0 qualifies infrastructure assets independently of any project or
future assignment. A qualified asset becomes a reusable engineering resource;
qualification does not appropriate it to a project. Operational Assignment,
also called Appropriation, is a later explicit lifecycle decision.

An independently identifiable Homelab infrastructure asset discovered during
an authorized investigation shall be recorded as an incidental discovery and
qualified through its own bounded evidence set when scope permits. Such a
discovery is an engineering opportunity, not a reason to merge identities,
broaden destructive authority, or interrupt the original evidence chain.

### Qualification Is Evidence-Based

Qualification is a supported engineering decision, not a synonym for
availability. Backups, successful reads, mounts, self-test summaries, or prior
operation contribute evidence but do not independently establish
qualification. Conflicting, incomplete, or unisolated evidence may support a
temporary disqualification, quarantine, or pending-qualification state. Those
are acceptable controlled states and shall not be weakened for convenience.

### Isolate Before Permanent Disqualification

Before permanently disqualifying hardware, isolate one variable at a time
whenever safe and practical. Candidate variables include media, readers,
controllers, interfaces, hosts, power delivery, adapters, cables, firmware,
and software layers. Preserve the original symptom, change only the selected
variable, repeat the relevant observation, and record what the comparison can
and cannot prove.

## Required Qualification Lifecycle

```text
Asset Discovery
        ↓
Asset Identification
        ↓
Inventory
        ↓
Evidence Acquisition
        ↓
Qualification
        ↓
Asset Registration
        ↓
Financial Reconciliation
        ↓
Operational Assignment (Appropriation)
        ↓
Operational Integration
        ↓
Monitoring
        ↓
Retirement / Disposal
```

No downstream gate implies permission to bypass an incomplete upstream gate.
A non-data-bearing asset may record content-specific evidence acquisition and
preservation controls as not applicable with evidence and rationale; lifecycle
stages are not silently omitted. Evidence Acquisition, Qualification,
Recovery, Restoration, and Operational Deployment are separate stages with
separate acceptance decisions. Completion of one does not imply completion or
authority for another.

## Future Qualification Procedure and Report Architecture

A future Raspberry Pi Engineering Qualification Procedure shall primarily
orchestrate this lifecycle and the applicable authoritative standards,
procedures, specifications, asset records, and infrastructure baselines. It
shall reference those owners rather than reproduce their qualification,
recovery, state, or platform requirements. The procedure may add only the
Raspberry Pi-specific sequence, entry and exit gates, required references,
evidence assembly, and sign-off behavior needed to make the lifecycle
repeatable.

Completed engineering qualification shall produce a standardized
Qualification Report. The report shall identify the asset, procedure and
governing revisions, evidence, environment, results, limitations, disposition,
and sign-off. SPEC-0007 owns the deferred platform architecture for persisting
that report into Engineering State and making it consumable by resume and
future automation. This standard does not create the procedure, report schema,
state implementation, or automation.

## Gate Requirements

### 1. Asset Discovery

Execute Engineering Work Initiation under PROC-0001. Record authority, host,
operator, UTC time, repository and Engineering State, discovery method,
physical context, and pre-existing condition. Isolate one candidate when
practical and avoid actions that could change its state.

### 2. Asset Identification

Establish the strongest available identity before testing. Evidence may
include manufacturer, model, model number, serial, WWN, MAC address, service
tag, capacity, hardware revision, firmware, physical labels, bus topology, and
cryptographically verified management identity. Volatile device paths and
network addresses are observations, not identities.

Stop on identity ambiguity, mismatch, duplicate serial, unexpected capacity,
or inability to distinguish the candidate from a protected asset.

### 3. Inventory

Record the identified asset's interfaces, components, capacity, configuration,
observed contents when authorized, dependencies, current role, provenance,
physical context, and applicable controlled records. Inventory describes what
is present; it does not establish qualification.

### 4. Evidence Acquisition

Acquire the minimum non-mutating evidence needed for qualification under the
applicable procedure. Preserve original observations, commands, logs, errors,
and identity linkage before corrective action. Evidence acquisition gathers
facts; it does not repair the asset or decide fitness.

### 5. Qualification

Use asset-appropriate, non-destructive diagnostics and record tool versions,
commands, output, exit status, condition, errors, limitations, power and
thermal observations, interface evidence, and qualification decision. Storage
uses PROC-0003 and the Engineering Storage Qualification Capability. A vendor
summary alone does not override error evidence.

Qualification shall precede recovery whenever practical. Recovery or repair
shall not overwrite the only evidence of the original condition. When urgent
preservation requires acquisition before full qualification, record the
exception, minimize mutation, and qualify the acquired evidence separately.

### 6. Preservation Assessment

For data-bearing assets, inventory only within explicit access authority.
Default to protected read-only access and collect the minimum information
needed to classify content: utilization, top-level structure, major sizes,
largest objects when required, dominant categories, configuration, and likely
ownership. Do not copy, open private content unnecessarily, repair, index into
an uncontrolled service, or alter access timestamps when avoidable.

Classify data, configuration, licenses, evidence, and recoverability as
preserve, archive, migrate, review, repurpose-after-migration, or quarantine.
Identify unique material, existing backups, retention constraints, privacy,
security, legal, and operational dependencies. Preserve first; uncertainty
defaults to review or quarantine, not deletion.

### 7. Asset Registration

After identity and health qualification succeed, allocate the next permanent
AST identifier, prove uniqueness across current and historical records, create
the AST record, update HW-0001, and register discovery in DOC-0001 when
required by repository architecture. Record owner, assignment, status,
location, evidence, limitations, preservation state, and lifecycle history.
Identifiers are never reused.

Registration records an asset; it does not certify a future role, authorize
data disposition, or imply financial provenance.

### 8. Financial Reconciliation

Link existing procurement, transaction, warranty, ownership, and valuation
evidence when available and required by finance policy. Do not infer vendor,
price, purchase date, tax, warranty, depreciation, or funding source. Record
unknown facts explicitly and leave finance records unchanged when no supported
financial event exists.

### 9. Operational Assignment (Appropriation)

Assign an engineering role only after qualification and preservation gates
support it. Record role, project assignment, criticality, suitability,
capacity, security, performance, compatibility, redundancy, recovery, and
maintenance expectations. Ownership and assignment remain independent.

### 10. Operational Integration

Integrate through the owning infrastructure or project baseline. Validate
connectivity, power, firmware and software compatibility, security controls,
monitoring, backup or recovery requirements, configuration persistence,
service behavior, and rollback. Do not place an asset into production merely
because it passed standalone health checks.

### 11. Monitoring and Lifecycle Management

Maintain condition, location, ownership, assignment, maintenance, incidents,
configuration, firmware, capacity, warranty, preservation holds, dependencies,
and periodic requalification proportionate to risk. Every material change
shall update the owning AST record and affected register, infrastructure,
project, finance, and Engineering State owners.

### 12. Retirement and Disposal

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
| 1.1 | 2026-07-19 | Reconciled the asset-oriented qualification lifecycle; required positive evidence identity, preservation before recovery, evidence-based storage qualification, incidental-asset treatment, variable isolation, explicit appropriation, and separate acquisition, qualification, recovery, restoration, deployment, monitoring, and retirement decisions. |
| 1.2 | 2026-07-19 | Established the future Raspberry Pi qualification procedure as a reference-oriented lifecycle orchestrator and required a standardized Qualification Report while deferring report schema, state persistence, resume consumption, and automation to their authoritative platform owners. |
