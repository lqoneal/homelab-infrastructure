---
document_id: SPEC-0005
title: Engineering Control Framework
version: 2.2
status: Active
owner: EOS Program
created: 2026-07-08
last_updated: 2026-07-30
governed_by: EOS-0001
implements:
  - EDR-0002
depends_on:
  - SPEC-0001
  - SPEC-0004
mission_assurance_requirements:
  - id: MA-CONTRACT-001
    language_version: '1.0'
    phase: preflight
    description: Exactly one Mission Contract resolves.
    assertion:
      selector: discovery.mission_contract_count
      operator: equals
      value: 1
  - id: MA-REPOSITORY-001
    language_version: '1.0'
    phase: preflight
    description: Repository identity matches the contract.
    assertion:
      selector: state.repository.identity
      operator: equals_selector
      value_selector: root
  - id: MA-AUTHORITY-001
    language_version: '1.0'
    phase: preflight
    description: Mission-scoped authority is bound and non-reusable.
    assertion:
      all:
        - selector: state.authority.applies_to
          operator: equals_selector
          value_selector: mission_id
        - selector: state.authority.reusable_for_other_missions
          operator: equals
          value: false
  - id: MA-BLOCKERS-001
    language_version: '1.0'
    phase: execution
    description: Canonical execution blockers are absent.
    assertion:
      selector: state.blockers
      operator: empty
---

# Engineering Control Framework

## Operational Alpha convergence migration

SPEC-0014 is the controlled authority owner for Operational Alpha. This
framework consumes its resolver result; it does not recreate a legacy
Work-Registry/EWO authority chain. `zeus mission snapshot`, `zeus mission
qualify`, and `zeus execution resolve` must use the exact version-pinned EMM
resolution receipt and fail closed on every non-`RESOLVED` outcome.

---

# 1. Purpose

The Engineering Control Framework defines the control architecture through which engineers, automation, and future intelligent systems interact with EOS-managed engineering capabilities.

Its purpose is to provide a single global entry point for engineering operations while preserving modular service boundaries.

---

# 2. Scope

This specification governs:

- global engineering control;
- project-specific controller wrappers;
- command routing;
- service invocation;
- control interfaces;
- future automation interfaces.

---

# 3. Design Objectives

The Engineering Control Framework SHALL:

- provide a global engineering control entry point;
- expose EOS Core Services through consistent commands;
- delegate execution to one authoritative implementation per capability;
- support project-specific wrappers without duplicating implementation logic;
- support future non-command-line interfaces.

---

# 4. Controller Model

EOS SHALL provide a global engineering controller.

Project-specific controllers MAY exist as convenience wrappers.

Project-specific controllers SHALL NOT implement independent business logic when a global EOS service exists.

---

# 5. Command Authority

Commands SHALL invoke services.

Commands SHALL NOT become authoritative records.

Command output SHALL be considered a derived engineering view.

## 5.1 Command Authority Standard

For Operational Alpha, the authority owner is the SPEC-0014 Authority Record
and its resolved baseline-bound Implementation WOP. Classification determines
whether recorded authority is sufficient; it never creates authority.

### Automatic

Repository inspection and discovery, controlled-document reads, patch
generation, syntax verification, unit tests, evidence and Completion Report
generation, checksum calculation, and documentation reconciliation execute
without operator confirmation.

Audit evidence records the capability, relevant inputs, terminal result, and
generated evidence locator.

### Pre-Authorized Mission Operations

In-scope file edits, patch application, non-destructive refactoring, runtime
reconciliation, and registry reconciliation execute without repeated operator
confirmation when the Mission Contract authorizes the affected scope.

Audit evidence records changed paths, material before/after state, and
verification results.

### Explicit Operator Approval

Authority publication, dispatch authorization, operator acceptance,
destructive operations, history rewriting, and Governance decisions require a
separate explicit operator decision applicable to the resolved operation and
target. Readiness is not approval.

Audit evidence records decision identity, scope, target, timestamp, integrity
binding, and resulting state.

### Emergency Stop

Credential disclosure, authority circumvention, unbounded destructive action,
unauthorized dispatch, and unauthorized Governance transition never execute
automatically. The agent stops, preserves state, records the refusal and
reason, and escalates.

## 5.2 Escalation Rules

An operation takes the most restrictive applicable classification. Unknown
classification, unresolved target, scope expansion, unexpected external
effect, missing audit capability, or conflicting authority fails closed.
Repeated safe operations within one mission and classification shall not
trigger repeated confirmation.

## 5.3 Engineering Execution Contract

This specification owns the Engineering Execution Contract. The operational
manifest binds callers to this owner and SHALL NOT reproduce these semantics.

The operator supplies mission decisions, reviews framework-changing proposals,
approves or rejects required gates, and separately decides acceptance,
publication, and dispatch. The orchestration agent resolves repository state,
maintains the Mission Contract and Snapshot, enforces gates, coordinates
verification and reconciliation, and stops on ambiguity. An execution agent
implements only the resolved scope, records commands and evidence, preserves
unrelated work, and may report implementation completion but SHALL NOT
self-accept it. The repository framework discovers controlled capabilities,
validates identities and revisions, derives blockers and next action, and
fails closed. Zeus consumes the resolved contract for its own qualified
lifecycle and SHALL NOT infer dispatch authority from implementation state.

The resolved Operational Alpha contract binds repository identity and baseline,
Authority Record, exact EMM revisions, Implementation WOP, scope, objective,
lifecycle position, capability, evidence, reconciliation obligations, and next
authorized action. A WOP is a bounded execution package only after Authority
Record resolution; neither a WOP nor workspace permission creates an
engineering decision.

Required inputs are the repository identity and HEAD, exact controlled-owner
identities and revisions, the unique Mission Contract and registry record,
applicable WOP and decision records, working-tree state, gate state, and
evidence. Required outputs are one repository-complete Mission Snapshot,
validation results, reconciled authoritative and operational candidates, and
a mission-delta Completion Report.

Command permission and engineering decision authority are independent.
Automatic or mission-scoped commands may execute only inside resolved scope.
Architecture selection, framework activation, implementation completion,
operator acceptance, controlled-document activation or publication, and
dispatch are engineering decisions and require the applicable recorded gate;
they are never implied by command class, filesystem permission, prior mission
authority, readiness, or a successful test.

Framework-changing work requires operator review of the proposed assessment
and corrective plan before implementation approval. The implementation
approval MUST name the same mission and is non-reusable. Controlled-document
activation, operator acceptance, publication, and dispatch remain later,
separate gates. No agent may approve a gate that governs its own work.

Execution stops on missing, duplicate, conflicting, stale, unavailable, or
wrong-revision semantic owners; unresolved repository or authority identity;
invalid or unresolved WOP applicability; an unapproved mandatory review gate;
out-of-scope effects; blockers; or an unauthorized next action. Evidence SHALL
bind inputs, changed paths, tests, failures, preserved unrelated state, and
resulting state. Reconciliation SHALL update every affected owner, consumer,
registry, project/resume surface, and report without erasing historical
defects.

Resume regenerates the Mission Snapshot through the same canonical discovery,
authority, and validation pipeline used for handoff. Implementation completion
means the agent has satisfied the criteria and produced evidence. It does not
mean operator acceptance. Publication and dispatch are independent of both
implementation completion and acceptance and require their own decisions.

---

# 6. Service Routing

The Engineering Control Framework SHALL route requests to the appropriate EOS Core Service.

Examples of service categories include:

- context reconstruction;
- checkpointing;
- validation;
- inventory;
- documentation;
- publishing;
- project operations.

---

# 7. Project Context

The framework SHALL support project-scoped execution.

Project context MAY be:

- explicit;
- inferred from current working directory;
- inferred from active EOS state;
- provided by configuration.

---

# 8. Resume Integration

The global engineering controller SHALL expose the Engineering Context Reconstruction Service through a resume interface.

The resume interface SHALL produce a derived engineering view and SHALL NOT own engineering state.

The controller SHALL expose `engctl execution inventory`, `snapshot`, and
`validate-handoff`. These surfaces consume the operational interface manifest
and existing semantic owners; they establish no additional authority.

Zeus SHALL consume the same canonical resolver through `zeus mission snapshot`,
`zeus mission qualify`, and `zeus execution resolve`. Mission qualification
SHALL fail closed unless exactly one requested Mission Contract resolves and
the lifecycle, implementation, acceptance, blockers, approvals, and next
authorized action are all present. Qualification output SHALL be deterministic
for an unchanged operational state.

Mission assurance requirements SHALL be declared as structured metadata by
the controlled specification, standard, procedure, or template that owns each
requirement. The Engineering Execution Interface SHALL resolve the exact
controlled-owner revisions and expose their declarations. Zeus SHALL evaluate
those declarations generically against the canonical Mission Snapshot and
mission identity; it SHALL NOT maintain an independent list of requirement
identifiers, descriptions, applicability rules, or expected values.

Missing requirement phases, duplicate requirement identifiers, unresolved
selectors, unsupported operators, conflicting owners, and unavailable owner
revisions SHALL fail closed. Updating a bound controlled-owner revision or its
requirement declarations SHALL affect subsequent assurance evaluation without
an assurance-logic change. Assurance evaluation remains read-only and SHALL
NOT execute PROC-0001 or mutate any source record.

---

# 9. Wrapper Rules

Project wrappers SHALL:

- provide project context;
- delegate to the global controller;
- avoid duplicating service logic;
- remain replaceable.

---

# 10. Validation

## 10.1 Mission Activation Service Candidate

The Mission Activation Service SHALL implement this ordered pipeline:

`Engineering Governance -> Manual WOP Submission -> Mission Admission ->
Repository Identity Verification -> Repository Integrity Verification ->
Package Integrity Verification -> Mission Activation -> Mission Contract
Resolution -> Execution Verification -> Mission Execution`.

For Operational Alpha, admission and activation are SPEC-0014 lifecycle
operations. Governance produces the Authority Record, the Metadata Engine
resolves it with the exact baseline-bound WOP, and qualification determines
whether the requested capability is eligible. A `READY` WOP is not activated
and authorization cannot be inferred from admission, a command, or prior work.

Admission SHALL NOT imply repository readiness, package validity, execution
authority, activation, Mission Contract resolution, authority resolution, or
execution readiness. Execution agents SHALL NOT admit, revoke, or reinterpret
mission intent.

Mission Activation SHALL be an attributable Engineering Governance decision
authorizing the system to begin execution qualification. It SHALL NOT guarantee
successful execution. Execution agents SHALL NOT activate missions
independently.

Repository identity, repository integrity, package integrity, Mission Contract
resolution, authority resolution, and execution verification SHALL determine
execution readiness only. Objective failure SHALL set execution status to
`BLOCKED` without reversing or invalidating admission.

Governance state SHALL be `Submitted`, `Admitted`, `Activated`, `Revoked`, or
`Completed` and SHALL change only through Engineering Governance. Execution
state SHALL be `Pending Verification`, `Verification Failed`, `Ready`,
`Executing`, `Suspended`, `Failed`, or `Completed` and SHALL change through
objective execution events.

A blocked mission SHALL remain admitted, attributable, auditable, and eligible
to resume execution qualification after correction without a new Mission
Admission. Execution agents SHALL NOT reinterpret `BLOCKED` as not admitted.

Activation processing SHALL use a correlation id, idempotency key,
expected-state comparison, one resolved Authority Record/WOP cardinality,
durable before-images, atomic authoritative-record update, post-write
resolution, and a transaction journal. Canonical records are the Authority
Record, EMM publication index, Implementation WOP, lifecycle receipt, and
Project State. EOS is derived and must synchronize through a receipt after the
authoritative transaction. Failure or interruption restores before-images and
rebuilds derived projections. Partial activation and direct lifecycle
activation are prohibited.

The resolver output is the single operational authorization result consumed by
both `engctl resume` and execution snapshots.

The Engineering Control Framework is compliant when:

- one global controller can invoke core EOS services;
- project wrappers delegate to global service implementations;
- command output is traceable to Authoritative Engineering Records;
- no project wrapper owns unique engineering logic that belongs to EOS.

---

# Compliance

All future EOS controllers SHALL conform to this specification.

---

# Revision History

| Version | Date | Description |
| --- | --- | --- |
| 1.0 | 2026-07-08 | Initial Engineering Control Framework draft. |
| 1.1 | 2026-07-28 | Activated the Command Authority Standard and standardized engctl Engineering Execution Interface routing. |
| 1.2 | 2026-07-28 | Candidate: defined the Engineering Execution Contract, separated command permission from decision authority, and required non-reusable framework review and approval gates. |
| 1.2 candidate reconciliation | 2026-07-28 | Added controlled-owner mission-assurance declarations and required generic, fail-closed Zeus evaluation through the canonical execution resolver. |
| 1.3 candidate | 2026-07-28 | Added the Mission Activation Service, admission qualifications, atomic transaction boundary, reconciliation, rollback, recovery, and resolver cardinality requirements. |
| 1.4 candidate | 2026-07-29 | Reconciled Governance-only admission and activation, independent Governance and execution state, execution-readiness blockers, and resumable blocked missions without adding runtime behavior. |
| 2.0 | 2026-07-30 | Migrated Operational Alpha command authority, resolver consumption, lifecycle activation, synchronization, and recovery to SPEC-0014. |
| 2.2 | 2026-07-31 | Registered the active controlled document revision required by the published execution-interface semantic-owner binding; no architecture or roadmap behavior changed. |
