# Architecture Decision Record — Engineering Platform Host & Topology Architecture

**Status:** Planning — Pre-Specification
**Decision Domain:** Engineering Platform Host and Topology Architecture
**Current Workstream:** Workstream 1 — Capability Architecture
**Current Gate:** Gate 1.3 — Capability Hierarchy and Dependencies
**Normative Authority:** None

---

# 1. Purpose

This Architecture Decision Record preserves the major decisions, alternatives, rationale, consequences, and supersessions arising during development of the Engineering Platform Host & Topology Architecture.

This document is non-normative.

It records architectural reasoning so that future controlled specifications can be drafted without losing the evidence, alternatives, and intent behind the design.

The ADR must preserve prior decisions even when later gates refine or supersede them.

---

# 2. Decision Scope

This ADR records decisions concerning:

* Engineering Host abstraction;
* Host identity;
* Host capabilities;
* capability categories;
* capability dependencies;
* Capability Qualification;
* Platform Services;
* Service Instances;
* Service requirements;
* Service Placement;
* Platform relationships;
* derived topology;
* lifecycle separation;
* ownership boundaries;
* future distributed operation.

It does not authorize implementation or modify existing controlled-document authority.

---

# 3. Decision Method

Each decision records:

* question;
* evidence;
* alternatives considered;
* decision;
* rationale;
* consequences;
* supersession status;
* deferred work.

The architecture sequence is organized as:

```text
Foundation Gates
        ↓
Planning Gate
        ↓
Architecture Workstreams
        ↓
Integration Review
        ↓
Controlled Specification Readiness
```

---

# 4. Decision Status Vocabulary

The following status terms are used in this ADR:

## Accepted for Planning

The decision governs continued architecture development but is not yet a controlled requirement.

## Provisional

The decision is adopted temporarily and requires validation in a later gate.

## Refined

The original decision remains valid but its interpretation has been narrowed or clarified.

## Superseded

A later decision replaces part or all of the earlier decision.

The original rationale remains preserved.

## Deferred

The topic is intentionally postponed.

---

# 5. Foundation Gate F1 — Dedicated Host Architecture

## Question

Should Engineering Host concepts remain embedded across individual Service and Infrastructure documents, or should they be developed as a shared Platform architecture?

## Evidence

Repository archaeology identified Host assumptions across:

* Engineering Platform architecture;
* Infrastructure Baselines;
* Service deployment;
* Notification Service planning;
* repository access;
* EOS participation;
* checkpoint access;
* distributed execution;
* future Engineering Management Platform services.

These assumptions were not governed by one coherent architectural model.

## Alternatives Considered

### Alternative A — Leave Host concepts distributed

Each Service or Infrastructure document would define the Host behavior it required.

### Alternative B — Add Host details only to the Infrastructure Baseline

The Infrastructure Baseline would describe Hosts as part of deployed infrastructure.

### Alternative C — Establish a shared Host & Topology Architecture

A reusable architecture would define Host identity, capabilities, placement, and relationships for all Platform Services.

## Decision

Establish a dedicated Engineering Platform Host & Topology Architecture.

## Rationale

A shared architecture:

* prevents Service-specific redefinition;
* separates deployed configuration from architectural semantics;
* supports future distributed operation;
* preserves common terminology;
* enables consistent qualification and placement;
* reduces document coupling.

## Consequences

* Future Platform Services may depend on the shared architecture.
* Infrastructure Baselines remain records of actual deployment.
* A future controlled Host specification may be required.
* Existing documents will eventually require dependency review.

## Status

Accepted for Planning.

---

# 6. Foundation Gate F2 — Engineering Host Abstraction

## Question

What term should describe an execution environment participating in the Engineering Platform?

## Alternatives Considered

### Node

Advantages:

* common in distributed systems;
* concise;
* familiar in clustering contexts.

Disadvantages:

* may imply cluster membership;
* may be confused with graph nodes;
* may introduce premature orchestration assumptions.

### Device

Advantages:

* intuitive for physical equipment.

Disadvantages:

* inadequate for virtual machines, containers, and bounded software environments;
* overlaps with Asset terminology.

### Machine

Advantages:

* familiar;
* simple.

Disadvantages:

* strongly implies physical hardware;
* inadequate for virtual or nested environments.

### Engineering Host

Advantages:

* describes an execution environment;
* supports physical and virtual forms;
* aligns with Service-hosting language;
* avoids premature cluster semantics.

## Decision

Use **Engineering Host** as the canonical architectural term.

## Definition

An Engineering Host is a bounded execution environment capable of participating in the Engineering Platform.

## Rationale

The abstraction supports:

* workstations;
* Raspberry Pis;
* servers;
* virtual machines;
* container hosts;
* appliances;
* future cloud execution environments.

It separates the execution environment from the physical Asset providing it.

## Consequences

* Host identity must be independent of Asset identity.
* One Asset may provide multiple Hosts.
* Host architecture must reference rather than duplicate Asset records.
* Existing uses of node, device, or machine require contextual interpretation.

## Status

Accepted for Planning.

---

# 7. Foundation Gate F3 — Capability-Based Architecture

## Question

Should Engineering Hosts be defined primarily through named roles or through reusable capabilities?

## Alternatives Considered

### Alternative A — Fixed Host Roles

Examples:

* engineering workstation;
* notification server;
* repository server;
* AI server.

Disadvantages:

* roles combine unrelated properties;
* Services become tied to specific machines;
* role proliferation is likely;
* requirements remain implicit.

### Alternative B — Hardware-Class Assignment

Services would be assigned according to hardware type.

Disadvantages:

* hardware type does not establish fitness;
* qualification remains implicit;
* heterogeneous systems are difficult to support;
* replacement hardware may unnecessarily change architecture.

### Alternative C — Capability-Based Placement

Hosts advertise qualified capabilities.

Services declare required capabilities.

Placement matches Service requirements to Host qualifications.

## Decision

Adopt a capability-based Host architecture.

## Rationale

Capability-based design:

* separates Service requirements from deployment;
* supports heterogeneous hardware;
* permits one Host to provide many functions;
* supports migration and replacement;
* enables evidence-based qualification;
* avoids role proliferation;
* supports deterministic Placement.

## Consequences

* A canonical capability vocabulary is required.
* Capabilities require qualification evidence.
* Services must eventually declare capability requirements.
* Placement must evaluate capability satisfaction.
* Role labels may remain informal summaries only.

## Status

Accepted for Planning.

---

# 8. Foundation Gate F4 — Ownership Boundaries

## Question

Which engineering facts should the Host & Topology Architecture own?

## Alternatives Considered

### Alternative A — Centralized Platform Ownership

The Host Architecture would own hardware, Service deployment, operational state, topology, and qualification.

Disadvantages:

* duplicates existing authority;
* creates a monolithic specification;
* conflicts with Hardware, Infrastructure, EOS, Services, and Governance.

### Alternative B — Minimal Host Naming Standard

The architecture would define only Host identifiers.

Disadvantages:

* insufficient for qualification;
* insufficient for Service Placement;
* relationships remain ambiguous.

### Alternative C — Bounded Shared Architecture

The architecture owns common Host, capability, Placement, and relationship semantics while referencing external authorities.

## Decision

The future Host & Topology Architecture owns:

* Host abstraction;
* Host identity semantics;
* shared capability identities and contracts;
* capability dependency semantics;
* Capability Qualification semantics;
* Service Placement semantics;
* shared relationship semantics;
* derived-topology rules.

It does not own:

* physical Asset lifecycle;
* Platform Service behavior;
* deployed infrastructure truth;
* global operational state;
* engineering work authorization;
* governance authority;
* Service-specific information authority.

## Rationale

This division creates a reusable Platform layer without displacing established ownership.

## Consequences

Cross-document relationships must be explicit.

## Status

Accepted for Planning.

---

# 9. Foundation Gate F5 — Independent Lifecycle Domains

## Question

Should Hosts, capabilities, Service Instances, and Placements share one lifecycle?

## Alternatives Considered

### Alternative A — Unified Platform Lifecycle

All related objects would inherit one shared state.

Disadvantages:

* a Host may remain qualified while one Service fails;
* a capability may expire while the Host remains online;
* a Placement may migrate without retiring the Service;
* operational health becomes confused with engineering lifecycle.

### Alternative B — Independent Lifecycles

Each architectural subject owns a separate lifecycle.

## Decision

Maintain independent lifecycles for:

* Engineering Host;
* Capability Qualification;
* Service Instance;
* Service Placement.

Operational condition remains independent.

## Rationale

The objects change for different reasons and on different schedules.

Example:

```text
Host lifecycle: Qualified
Operational condition: Online
Capability state: Restricted
Service-instance state: Running
Placement state: Suspended
```

## Consequences

* State models must not be collapsed.
* Services must distinguish Host health from Service health.
* Qualification status must remain distinct from online status.
* Placement activation remains distinct from Placement Qualification.

## Status

Accepted for Planning.

---

# 10. Foundation Gate F6 — Stable Identity Model

## Question

How should persistent Platform subjects be identified?

## Alternatives Considered

### Hostname as Identity

Disadvantages:

* hostnames are mutable;
* aliases differ by client;
* names may be reused;
* network changes would disrupt continuity.

### Hardware Identifier as Host Identity

Examples:

* serial number;
* MAC address;
* disk UUID.

Disadvantages:

* virtual Hosts may lack stable hardware identity;
* hardware may be replaced while execution identity continues;
* nested environments are not represented cleanly.

### Stable Platform Identifier

Each persistent engineering subject receives a Platform-scoped identity.

## Decision

Use separate stable identifiers for:

```text
asset_id
host_id
service_id
instance_id
placement_id
```

Hostnames, addresses, aliases, hardware identifiers, and runtime identifiers are attributes or bindings.

## Rationale

Stable identifiers support:

* replacement;
* migration;
* reconstruction;
* historical traceability;
* relationship persistence;
* topology derivation;
* distributed operation.

## Consequences

* Host identity must be registered.
* Historical names should remain discoverable.
* Identifiers must not be reused.
* Identity continuity rules require future refinement.

## Status

Accepted for Planning.

---

# 11. Planning Gate P1 — Architecture Planning Package

## Question

How should pre-specification architecture work be recorded?

## Alternatives Considered

### One Large Planning Document

Disadvantages:

* difficult to navigate;
* decision history and conceptual model become mixed;
* different content types mature at different rates.

### Numerous Topic Notes

Disadvantages:

* document sprawl;
* unclear purpose;
* fragmented architecture.

### Cohesive Planning Package

A small set of complementary living documents divides responsibility.

## Decision

Maintain:

```text
README.md
ADR-Host-Architecture.md
Conceptual-Host-Architecture.md
Host-Architecture-Glossary.md
Host-Specification-Planning.md
Architecture-Roadmap.md
Architecture-Development-Standard.md
```

## Rationale

The package separates:

* package orientation;
* decision history;
* conceptual architecture;
* terminology;
* specification planning;
* workstream planning;
* architecture-development method.

## Consequences

* New planning documents require clear justification.
* Existing documents should be revised holistically.
* Controlled promotion remains a later activity.

## Status

Accepted for Planning.

---

# 12. Workstream 1 — Capability Architecture

## Objective

Define the shared Engineering Platform capability model used to describe Host fitness and Service requirements.

Current gate sequence:

```text
Gate 1.1 — Canonical Capability Taxonomy
Gate 1.2 — Service Requirement Validation
Gate 1.3 — Capability Hierarchy and Dependencies
Gate 1.4 — Capability Constraints and Profiles
Gate 1.5 — Capability Matching
Gate 1.6 — Capability Lifecycle Integration
Gate 1.7 — Capability Architecture Review
```

---

# 13. Workstream 1, Gate 1.1 — Canonical Capability Taxonomy

## Question

What initial capability taxonomy should the Engineering Platform use?

## Decision

Adopt seven conceptual categories:

1. Interaction
2. Execution
3. Service Hosting
4. Persistence
5. Connectivity
6. Platform Integration
7. Specialized Compute

Individual machine-readable capabilities remain the units used for:

* declaration;
* qualification;
* Service requirements;
* Host matching;
* Placement Qualification.

## Initial Vocabulary

### Interaction

```text
interactive-operation
local-user-interface
remote-interactive-access
mobile-operator-endpoint
```

### Execution

```text
authorized-command-execution
engineering-workload-execution
isolated-execution
scheduled-execution
long-running-execution
```

### Service Hosting

```text
persistent-service-hosting
host-native-supervision
always-on-operation
service-isolation
service-health-reporting
```

### Persistence

```text
durable-local-storage
qualified-authoritative-storage
backup-capable-storage
recoverable-storage
removable-storage-support
```

### Connectivity

```text
authenticated-network-listener
authenticated-network-client
local-network-participation
outbound-network-access
internet-service-access
notification-delivery
time-synchronization
```

### Platform Integration

```text
repository-access
repository-working-copy
eos-participation
checkpoint-access
checkpoint-publication
engineering-event-publication
platform-observation
platform-synchronization
```

### Specialized Compute

```text
high-memory-compute
parallel-cpu-compute
gpu-compute
ai-inference
ai-training
hardware-diagnostics
storage-qualification
```

## Rationale

The categorized taxonomy provides:

* a manageable initial vocabulary;
* separation between reusable capabilities and Service-specific requirements;
* a basis for validation;
* a foundation for qualification and matching;
* support for heterogeneous Hosts.

## Consequences

* Existing Services must be reviewed.
* Names may be removed, merged, generalized, or narrowed.
* Quantitative properties require a separate constraint model.
* The taxonomy remains provisional.

## Status

Refined by Gates 1.2 and 1.3.

---

# 14. Workstream 1, Gate 1.2 — Service Requirement Validation

## Question

Can known Engineering Platform Services express their Host requirements through the provisional capability vocabulary without relying on fixed Host roles?

## Services Reviewed

The planning validation considered:

* Engineering Control;
* EOS and checkpoint functions;
* repository functions;
* Notification Service;
* Engineering Knowledge Repository;
* print and supporting infrastructure;
* future AI Services.

## Decision

Capability composition remains the preferred Service requirement model.

Known Service classes can generally express Host requirements through combinations of reusable capabilities.

## Findings

### Capability categories remain useful

The seven categories support organization and review.

They are not themselves qualification or matching units.

### Quantitative constraints are required

Examples include:

* memory;
* storage capacity;
* latency;
* throughput;
* GPU memory;
* availability;
* power continuity;
* recovery objectives.

### Negative requirements are required

Examples include:

* no Internet egress;
* no external model API;
* no removable storage;
* no unencrypted authoritative data;
* no placement outside an approved trust domain.

### Trust and authority remain separate

Capabilities must not encode:

* authentication;
* authorization;
* publication authority;
* information ownership;
* Service admission.

### Relationships may affect Placement

Examples include:

* Host administers Printer Asset;
* Host accesses Storage Asset;
* Host synchronizes with Host;
* Host belongs to Trust Domain.

## Naming Findings

The following terms required review:

```text
authorized-command-execution
eos-participation
checkpoint-access
checkpoint-publication
engineering-event-publication
notification-delivery
```

A missing shared concept was also identified:

```text
peripheral-device-access
```

## Decision

Proceed to dependency and hierarchy analysis before stabilizing the vocabulary.

## Status

Complete for conceptual planning.

---

# 15. Workstream 1, Gate 1.3 — Capability Hierarchy and Dependencies

## Question

How should capabilities relate to one another without creating rigid inheritance, hidden roles, ambiguous qualification, or non-deterministic matching?

## Evidence

Gate 1.2 showed that:

* some capabilities depend on lower-level capabilities;
* some implementations can satisfy the same semantic capability;
* some capability names were Service-specific;
* quantitative and negative requirements should remain separate;
* a simple flat capability list is insufficient;
* traditional inheritance could hide scope and evidence differences.

## Alternatives Considered

### Alternative A — Flat Independent Capability List

Every capability would be unrelated to every other capability.

Advantages:

* simple storage;
* simple naming.

Disadvantages:

* repeated requirements;
* hidden prerequisites;
* no impact propagation;
* poor explanation of matching failures;
* inconsistent qualification.

### Alternative B — General Capability Inheritance

Capabilities would form a class hierarchy where specialized capabilities automatically inherit all parent properties.

Advantages:

* familiar model;
* concise conceptual hierarchy.

Disadvantages:

* scope differences may be hidden;
* qualification evidence may not transfer;
* lifecycle differences become ambiguous;
* parent and child contracts may evolve independently;
* matching behavior may become implicit.

### Alternative C — Directed Dependency Graph

Capabilities remain independently defined and qualified.

Explicit typed relationships connect them.

## Decision

Use a directed acyclic capability graph.

Capabilities remain independent semantic contracts.

Relationships are explicit and typed.

## Relationship Types

The graph supports:

```text
requires
implies
alternative
conflicts_with
```

Each relationship has distinct semantics.

---

# 16. Gate 1.3 Decision — `requires`

## Definition

Capability A `requires` Capability B when A cannot be qualified unless B is also qualified within a compatible scope.

Example:

```text
persistent-service-hosting
    requires long-running-execution
```

## Decision

Use `requires` as the preferred dependency relationship.

## Consequences

* qualification of A depends on B;
* revocation or expiration of B may affect A;
* Service requirement A expands to include B;
* B remains independently qualified;
* compatible scope must be evaluated.

## Status

Accepted for Planning.

---

# 17. Gate 1.3 Decision — `implies`

## Definition

Capability A `implies` Capability B when qualification of A necessarily demonstrates B without requiring an independent qualification for matching.

## Decision

Permit `implies` only under strict conditions.

It may be used only when:

* B is inherent in A;
* evidence for A necessarily proves B;
* qualification scopes are compatible;
* independent lifecycle management is unnecessary;
* no ambiguity is created.

## Rationale

Overuse of implication would conceal evidence and scope differences.

## Consequences

The initial architecture should prefer `requires`.

## Status

Accepted for Planning with restrictive use.

---

# 18. Gate 1.3 Decision — `alternative`

## Definition

An alternative relationship identifies multiple capability qualifications or implementation forms that may satisfy the same semantic requirement.

## Decision

Equivalent technologies should normally qualify one common capability.

Example implementations:

```text
systemd
OpenRC
Windows Service Control Manager
appliance supervisor
```

may qualify:

```text
service-supervision
```

Technology belongs in evidence and qualification attributes.

Service requirement expressions may also define `any_of` groups.

## Consequences

* implementation details do not become unnecessary capability identities;
* Services can remain implementation-independent;
* alternative groups require formal evaluation in Gate 1.4.

## Status

Accepted for Planning.

---

# 19. Gate 1.3 Decision — `conflicts_with`

## Definition

Capability A `conflicts_with` Capability B when the two qualifications cannot safely coexist within the same Host or overlapping scope.

## Decision

Use `conflicts_with` only for intrinsic or qualification-scope incompatibility.

Service-specific exclusions belong in Placement constraints.

## Example

A Service prohibiting Internet egress does not mean:

```text
isolated-execution conflicts_with internet-service-access
```

The Host may possess both capabilities while a particular Placement prohibits use of Internet access.

## Consequences

Intrinsic capability conflicts and Placement prohibitions remain separate.

## Status

Accepted for Planning.

---

# 20. Gate 1.3 Decision — Reject General Inheritance

## Question

Should capabilities inherit properties and qualification automatically from broader capabilities?

## Decision

Reject general object-oriented capability inheritance.

Use:

```text
independent capabilities
        +
explicit dependencies
        +
constraints
```

## Rationale

This preserves:

* independent evidence;
* explicit scope;
* independent lifecycle;
* explainable matching;
* controlled semantic evolution.

## Consequences

Specialization does not automatically transfer qualifications.

## Status

Accepted for Planning.

---

# 21. Gate 1.3 Decision — Capability Categories and Namespaces

## Question

Should category names become prefixes in canonical capability identifiers?

## Alternatives Considered

### Category-Prefixed Identifier

Example:

```text
service-hosting.persistent-service-hosting
```

### Platform-Wide Unique Slug

Example:

```text
persistent-service-hosting
```

with separate category metadata.

## Decision

Use Platform-wide unique capability slugs.

Store category separately.

Example:

```yaml
capability_id: persistent-service-hosting
category: service-hosting
```

## Rationale

This avoids:

* identifier disruption when categories change;
* rigid hierarchy;
* duplicated metadata;
* unnecessary identifier length.

## Consequences

* capability IDs must be collision-free Platform-wide;
* future federation may require a Platform namespace;
* category changes need not change capability identity.

## Status

Accepted for Planning.

---

# 22. Gate 1.3 Decision — Dependency Cycles

## Question

May capability dependencies contain cycles?

## Decision

No.

The capability dependency graph must remain acyclic.

Invalid:

```text
A requires B
B requires C
C requires A
```

## Rationale

Cycles create:

* impossible qualification ordering;
* recursive matching;
* ambiguous revocation;
* non-deterministic explanations.

## Consequences

The future capability registry must validate graph acyclicity before publication.

## Status

Accepted for Planning.

---

# 23. Gate 1.3 Decision — Capability Contract Versioning

## Question

How should capabilities evolve without breaking Host qualifications or Service requirements silently?

## Decision

A capability identifier represents a stable semantic contract.

Contract version is represented separately.

Example:

```yaml
capability_id: persistent-service-hosting
contract_version: 1
```

Do not embed versions in the slug.

Avoid:

```text
persistent-service-hosting-v1
```

## Compatible Changes

The same contract version may retain:

* wording clarification;
* non-breaking examples;
* evidence clarification;
* compatible metadata expansion.

## Breaking Changes

A new contract version is required when a change affects:

* qualification requirements;
* dependencies;
* scope interpretation;
* matching outcomes;
* lifecycle behavior;
* trust assumptions.

## Consequences

Breaking changes require:

1. publication of a new contract;
2. identification of affected qualifications;
3. identification of affected Service requirements;
4. requalification;
5. Placement reevaluation;
6. controlled retirement of the earlier contract.

## Status

Accepted for Planning.

---

# 24. Gate 1.3 Decision — Dependency State Propagation

## Question

What happens when a required capability expires, is restricted, or is revoked?

## Decision

Dependent qualifications must be reevaluated.

Example:

```text
service-supervision: Revoked
        ↓
persistent-service-hosting: Requalification Required
        ↓
affected Placements: Requalification Required
```

A dependent capability need not be immediately revoked in every case.

Possible interim states include:

```text
Restricted
Suspended
Evidence Pending
Requalification Required
```

## Consequences

Detailed propagation rules remain part of Gate 1.6.

## Status

Accepted for Planning; lifecycle behavior deferred.

---

# 25. Gate 1.3 Supersession — Command Execution

## Earlier Term

```text
authorized-command-execution
```

## Problem

The name implied that execution authority had already been granted.

Capability should describe Host fitness, not authorization of a particular actor or action.

## Superseding Term

```text
controlled-command-execution
```

## Decision

Replace `authorized-command-execution` with `controlled-command-execution`.

## Rationale

The new term describes a qualified controlled execution mechanism while preserving external authorization boundaries.

## Consequences

Future requirement mappings and planning documents should use the new term.

Historical references remain understandable through this ADR.

## Status

Superseded.

---

# 26. Gate 1.3 Supersession — Platform State Capabilities

## Earlier Term

```text
eos-participation
```

## Problem

The term encoded a specific Platform implementation rather than reusable Host behavior.

## Superseding Terms

```text
platform-state-consumption
platform-state-publication
```

## Decision

Replace `eos-participation` with separate consumption and publication capabilities.

## Rationale

The generalized terms:

* distinguish read and write behavior;
* support future state Services;
* preserve EOS as the current operational-state authority;
* avoid implementation-specific Host contracts.

## Consequences

EOS-specific semantics remain in EOS authority.

## Status

Superseded.

---

# 27. Gate 1.3 Supersession — Engineering Record Capabilities

## Earlier Terms

```text
checkpoint-access
checkpoint-publication
engineering-event-publication
```

## Problem

The terms mixed common Host fitness with particular record and Service semantics.

## Superseding Terms

```text
engineering-record-consumption
engineering-record-publication
```

## Decision

Use generalized engineering-record capabilities.

Checkpoint and event semantics remain with their applicable Service or procedure.

## Rationale

This creates a reusable contract for consuming and publishing qualified engineering records.

## Consequences

Service requirements must provide the record type, authority, and interface as constraints or Service-specific semantics.

## Status

Superseded.

---

# 28. Gate 1.3 Supersession — External Delivery

## Earlier Term

```text
notification-delivery
```

## Problem

The term was tightly associated with one Platform Service.

## Superseding Term

```text
external-message-delivery
```

## Decision

Use `external-message-delivery` as the shared Host capability.

## Rationale

The capability may support:

* mobile push;
* email;
* SMS;
* webhook delivery;
* other approved external endpoints.

Notification routing and delivery policy remain owned by the Notification Service.

## Consequences

The applicable delivery provider and endpoint class must be recorded in qualification scope.

## Status

Superseded.

---

# 29. Gate 1.3 Addition — Peripheral Device Access

## Question

How should the architecture represent qualified access to printers, scanners, diagnostic interfaces, storage devices, and similar peripherals?

## Alternatives Considered

### Technology-Specific Capabilities

Examples:

```text
usb-device-access
serial-device-access
printer-access
scanner-access
```

Disadvantages:

* likely capability proliferation;
* implementation-specific naming;
* difficult reuse.

### General Peripheral Capability

Use one shared capability with device and protocol expressed through scope and constraints.

## Decision

Add:

```text
peripheral-device-access
```

## Rationale

The capability describes reusable Host fitness without encoding a specific peripheral technology.

## Consequences

Qualification scope should identify:

* device identity or class;
* access method;
* protocol;
* permissions;
* exclusivity;
* operational limits.

## Status

Accepted for Planning.

---

# 30. Gate 1.3 Addition — General Service Supervision

## Earlier Model

```text
persistent-service-hosting
    requires host-native-supervision
```

## Problem

The model required the supervision mechanism to be native to the Host operating system.

Persistent Service hosting may instead rely on:

* container supervision;
* appliance-native supervision;
* virtual-machine orchestration;
* another qualified supervision environment.

## Alternatives Considered

### Retain `host-native-supervision` as Universal Requirement

Disadvantages:

* implementation-specific;
* excludes valid supervision mechanisms;
* reduces portability.

### Remove Supervision Requirement

Disadvantages:

* persistent hosting would lack an explicit recovery and lifecycle prerequisite.

### Introduce General `service-supervision`

A general semantic capability would be satisfied by qualified supervision mechanisms.

## Decision

Add:

```text
service-supervision
```

Revise the dependency to:

```text
persistent-service-hosting
    requires long-running-execution
    requires service-supervision
```

Retain:

```text
host-native-supervision
```

as one possible supervision form.

## Rationale

This preserves the behavioral requirement while remaining implementation-independent.

## Consequences

* `host-native-supervision` is no longer a universal prerequisite.
* Other supervision forms may later be added.
* Gate 1.4 must define alternative satisfaction and profiles.
* Qualification evidence must identify the actual mechanism.

## Status

Accepted for Planning.

---

# 31. Gate 1.3 Refinement — Recoverable Storage

## Earlier Model

```text
recoverable-storage
    requires backup-capable-storage
```

## Problem

Recoverability may be provided through:

* backup;
* replication;
* snapshots;
* immutable reconstruction;
* redundant storage;
* Service-specific regeneration.

Backup is not the only valid recovery mechanism.

## Decision

Replace the universal backup dependency with an alternative recovery-mechanism requirement.

Conceptually:

```text
recoverable-storage
    requires one qualified recovery mechanism
```

## Consequences

Gate 1.4 must define:

* alternative groups;
* recovery profiles;
* mechanism constraints;
* evidence expectations.

## Status

Refined.

---

# 32. Candidate Dependency Graph After Gate 1.3

```text
remote-interactive-access
    requires authenticated-network-listener

controlled-command-execution
    requires engineering-workload-execution

scheduled-execution
    requires engineering-workload-execution
    requires time-synchronization

long-running-execution
    requires engineering-workload-execution

persistent-service-hosting
    requires long-running-execution
    requires service-supervision

always-on-operation
    requires persistent-service-hosting

service-health-reporting
    requires platform-observation

qualified-authoritative-storage
    requires durable-local-storage
    requires recoverable-storage

recoverable-storage
    requires one qualified recovery mechanism

repository-working-copy
    requires repository-access
    requires durable-local-storage

platform-state-publication
    requires authenticated-network-client
    requires time-synchronization

engineering-record-publication
    requires authenticated-network-client
    requires time-synchronization

platform-synchronization
    requires authenticated-network-client
    requires authenticated-network-listener
    requires time-synchronization

ai-inference
    requires engineering-workload-execution

ai-training
    requires engineering-workload-execution

hardware-diagnostics
    requires controlled-command-execution

storage-qualification
    requires hardware-diagnostics
```

This remains provisional pending Gate 1.4.

---

# 33. Revised Capability Vocabulary

## Interaction

```text
interactive-operation
local-user-interface
remote-interactive-access
mobile-operator-endpoint
```

## Execution

```text
controlled-command-execution
engineering-workload-execution
isolated-execution
scheduled-execution
long-running-execution
```

## Service Hosting

```text
persistent-service-hosting
service-supervision
host-native-supervision
always-on-operation
service-isolation
service-health-reporting
```

## Persistence

```text
durable-local-storage
qualified-authoritative-storage
backup-capable-storage
recoverable-storage
removable-storage-support
```

## Connectivity

```text
authenticated-network-listener
authenticated-network-client
local-network-participation
outbound-network-access
internet-service-access
external-message-delivery
time-synchronization
```

## Platform Integration

```text
repository-access
repository-working-copy
platform-state-consumption
platform-state-publication
engineering-record-consumption
engineering-record-publication
platform-observation
platform-synchronization
peripheral-device-access
```

## Specialized Compute

```text
high-memory-compute
parallel-cpu-compute
gpu-compute
ai-inference
ai-training
hardware-diagnostics
storage-qualification
```

---

# 34. Gate 1.3 Decision Summary

Gate 1.3 establishes:

1. capabilities form a directed acyclic dependency graph;
2. capabilities remain independently defined and qualified;
3. general inheritance is rejected;
4. explicit dependency composition is preferred;
5. `requires`, `implies`, `alternative`, and `conflicts_with` are distinct;
6. `implies` is restricted;
7. equivalent technologies should qualify common semantic capabilities;
8. Service-specific negative requirements remain Placement constraints;
9. intrinsic incompatibilities may use `conflicts_with`;
10. category is metadata rather than identifier namespace;
11. capability identifiers are Platform-wide unique slugs;
12. contract versions are separate metadata;
13. breaking changes require requalification and Placement reevaluation;
14. dependency cycles are prohibited;
15. dependency-state changes trigger reevaluation;
16. `authorized-command-execution` is superseded;
17. EOS-specific capability naming is superseded;
18. checkpoint- and event-specific capability naming is superseded;
19. Notification-specific delivery naming is generalized;
20. `peripheral-device-access` is added;
21. `service-supervision` is added;
22. persistent Service hosting no longer universally requires host-native supervision;
23. recoverability supports alternative qualified mechanisms.

---

# 35. Current Decision Register

| Decision                                        | Status                                    |
| ----------------------------------------------- | ----------------------------------------- |
| Dedicated Host & Topology Architecture          | Accepted for Planning                     |
| Canonical term is Engineering Host              | Accepted for Planning                     |
| Capability-based architecture                   | Accepted for Planning                     |
| Bounded ownership model                         | Accepted for Planning                     |
| Independent lifecycle domains                   | Accepted for Planning                     |
| Stable subject identities                       | Accepted for Planning                     |
| Cohesive planning package                       | Accepted for Planning                     |
| Seven-category capability taxonomy              | Refined                                   |
| Capability composition for Service requirements | Accepted for Planning                     |
| Directed acyclic capability graph               | Accepted for Planning                     |
| General capability inheritance rejected         | Accepted for Planning                     |
| Explicit dependency semantics                   | Accepted for Planning                     |
| Platform-wide capability slugs                  | Accepted for Planning                     |
| Separate capability contract versions           | Accepted for Planning                     |
| `controlled-command-execution`                  | Supersedes prior term                     |
| General Platform-state capabilities             | Supersede EOS-specific term               |
| General engineering-record capabilities         | Supersede checkpoint/event-specific terms |
| `external-message-delivery`                     | Supersedes Notification-specific term     |
| `peripheral-device-access`                      | Accepted for Planning                     |
| `service-supervision`                           | Accepted for Planning                     |
| Alternative recovery mechanisms                 | Accepted for Planning                     |

---

# 36. Deferred Decisions

The following remain open:

* canonical constraint schema;
* unit system;
* comparison operators;
* capability scope representation;
* alternative requirement syntax;
* capability profile semantics;
* profile composition;
* profile versioning;
* recovery profile definitions;
* missing-value behavior;
* restricted-qualification matching;
* conflict evaluation;
* trust-domain references;
* relationship constraints;
* automatic Placement suspension rules;
* capability registry implementation;
* final Host identifier format;
* Host registration authority;
* federation namespace.

---

# 37. Known Risks

## Hidden Inheritance

Dependencies may be interpreted as inheritance.

Mitigation:

* retain independent qualification records;
* require explicit dependency relationships;
* evaluate scope compatibility.

## Dependency Proliferation

Too many dependencies may create a brittle graph.

Mitigation:

* require semantic necessity;
* avoid encoding implementation details;
* validate dependency closure against actual Services.

## False Equivalence

Different implementations may be grouped under one capability even when their semantics differ.

Mitigation:

* define the common behavioral contract precisely;
* record mechanism-specific constraints;
* require compatible evidence.

## Capability Version Fragmentation

Frequent breaking versions may make matching and migration difficult.

Mitigation:

* keep capability contracts narrow and stable;
* distinguish clarification from semantic change;
* require explicit migration plans.

## Service Leakage

Service-specific semantics may remain hidden in generalized names.

Mitigation:

* require Service specifications to declare record types, interfaces, authorities, and constraints.

---

# 38. Next Gate

Proceed to:

```text
Workstream 1
Gate 1.4 — Capability Constraints and Profiles
```

Gate 1.4 must define:

* common constraint types;
* units;
* comparison operators;
* qualification scope;
* required, optional, and preferred requirements;
* prohibited conditions;
* alternative requirement groups;
* reusable capability profiles;
* profile composition;
* profile versioning;
* recovery-mechanism profiles;
* missing-value behavior;
* explainable evaluation.

The gate must ensure that capability profiles do not become fixed Host roles.

---

# 39. ADR Maintenance Rule

When a future gate changes an earlier decision:

1. preserve the original decision;
2. identify the superseding or refining decision;
3. explain the problem with the earlier model;
4. record the new rationale;
5. record consequences and migration impacts;
6. revise affected planning documents holistically.

Prior reasoning must not be silently deleted.

