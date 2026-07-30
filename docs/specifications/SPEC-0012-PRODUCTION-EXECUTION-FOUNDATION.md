---
document_id: SPEC-0012
title: Production Execution Foundation
document_type: Engineering Specification
version: 1.12
status: Active
effective_date: 2026-07-26
last_updated: 2026-07-29
owner: Lawrence O'Neal
authority_domain: Execution Authority
approval_authority: Lawrence O'Neal
approval_reference: ZEUS-P2-019
source_of_truth: true
persistence_status: Pending
predecessor: SPEC-0012@1.11
successor: null
declared_deferrals:
  - first-operational-wop-execution-qualification
  - automatic-authority-restoration-coordination
  - repository-baseline-closeout-publication-lifecycle
relations:
  governed_by: [CHAR-0001]
  conforms_to: [SPEC-0011, POL-0001, STD-0001, STD-0002]
  related_to: [EMP-0001, EOS-0001, PROC-0001, PROC-0008]
  indexed_by: [DOC-0001]
---

# Production Execution Foundation

## 1. Authority and scope

Lawrence O'Neal is the ultimate human authority and `loneal` is the
authenticated production principal. The Zeus CLI is the authoritative
instruction interface. Controlled documentation is the normal operational
source of execution authority. The dispatcher resolves and enforces that
authority; it cannot create, broaden, or repair authority by itself.

This specification provides a commissionable implementation foundation. It
does not commission a dispatcher, qualify a production agent, dispatch an
operational WOP, or prove operational WOP execution capability.

## 2. First-qualification authority model

First-time capability development uses an explicit lifecycle:

```text
PLANNED
  -> AUTHORIZED_FOR_IMPLEMENTATION
  -> IMPLEMENTED
  -> AUTHORIZED_FOR_QUALIFICATION
  -> QUALIFIED
  -> AUTHORIZED_FOR_COMMISSIONING
  -> COMMISSIONED
  -> OPERATIONALLY_ELIGIBLE
```

Implementation, qualification, commissioning, and operational execution are
distinct authority purposes. Each transition is sequential, provenance-bound,
digest-protected, and supported by its named authorization and evidence.
Qualification authorization permits bounded qualification using production
implementations and contracts, but it does not assert that qualification
succeeded. Operational authority resolution accepts only
`OPERATIONALLY_ELIGIBLE`; it shall not treat an earlier state as operational.

Insufficient authority produces an actionable safe-stop record identifying the
blocking record, required transition, and operational impact. Restoration
follows SPEC-0011 and never permits execution outside restored controlled
documentation.

## 3. Dispatcher policy and activation

The authoritative policy is
`engineering/dispatch/dispatcher-policy.yaml`. Dispatch defaults to denial and
requires valid authority, admission, immutable WOP, matching published
repository baseline, active dispatcher activation, a matching active qualified
agent, authenticated EENS, cryptographic evidence verification, and live
reconciliation dependencies.

Activation records are authenticated by a detached `loneal` SSH signature and
bind dispatcher identity, implementation and policy
versions, repository identity and baseline, activating authority and time,
supported mission and agent classes, EENS/evidence/reconciliation
configurations, and suspension/revocation state. Missing, prepared, stale,
invalid, suspended, revoked, or baseline-mismatched activation prohibits
dispatch.

Assignment selection is deterministic among eligible agents. The initial
policy permits no automatic retry. Interruption produces a resume token;
resumption revalidates authority, activation, agent trust, WOP integrity, and
idempotency. Timeout, cancellation, invocation rejection, terminal failure,
missing heartbeat, or unavailable control dependency stops safely and records
an actionable reason.

## 4. Production execution-agent registry

The version-2 registry is authenticated by a detached `loneal` SSH signature.
Its schema records stable identity, agent and host type,
service identity, mission and tool capabilities, repository scope,
constraints, qualification status and evidence, activation, last validation,
trust, EENS and evidence-signing identities, resume capability, and concurrency
limit. Fixture agents are prohibited from production selection. Assignment
requires a current qualification, valid trust binding, capability and access
match, EENS availability, and evidence-signing capability.

## 5. Invocation and supervision

An immutable assignment binds authority decision, WOP digest, repository
baseline, selected agent, evidence obligations, and idempotency identity. The
local authenticated transport implements the same contract intended for a
future remote transport: authenticate target, bind the invocation token to the
assignment, transmit the authoritative WOP, obtain acceptance, record
execution identity, establish EENS correlation and monitoring, return terminal
state and evidence locators, and return an identical result for a repeated
assignment.

EENS producers use detached SSH signatures, stable event identifiers,
mission/assignment correlation, append-only durable files, replay, and durable
consumer checkpoints. The normative lifecycle vocabulary is:
`mission.selected`, `authority.resolved`, `wop.resolved`,
`admission.accepted`, `dispatch.authorized`, `assignment.created`,
`agent.selected`, `agent.invocation.requested`,
`agent.invocation.accepted`, `execution.started`, `progress.reported`,
`approval.required`, `approval.resolved`, `execution.interrupted`,
`execution.resumed`, `execution.completed`, `execution.failed`,
`evidence.submitted`, `evidence.qualified`, `reconciliation.started`,
`reconciliation.completed`, and `mission.closed`. Events apply when their
corresponding lifecycle condition occurs; failure and approval branches are
not fabricated during a successful execution.

## 6. Evidence and independent qualification

Production evidence binds WOP, mission, assignment, agent, repository,
baseline, gate, action, timestamps, output locator and digest, and validation
result. The agent signs canonical evidence bytes under the production evidence
namespace. An independent qualifier—never the executing identity—verifies
signature, digest, identity, scope, gate, output, repository state, tests,
completeness, and contradiction absence. Fixture signatures and fixture
evidence cannot qualify production execution.

## 7. Live reconciliation and closeout

Scoped adapters cover mission, work item, WOP, assignment, execution, evidence,
approval, project, work registry, completion registry, operational resume,
controlled documentation, and EENS checkpoints. Every update is
optimistic-lock protected, idempotent, restartable, auditable, scoped,
validated, and interruption-safe. Mission closeout is prohibited until every
required adapter succeeds and the resulting records validate.

## 8. Progressive implementation architecture

The repository's canonical Progressive implementation architecture is the
Progressive Runtime Layer. It consists of exactly three implementation layers.

### 8.1 Progressive Authority Primitives

`scripts.lib.emp.progressive_gate` is the exclusive Progressive implementation
authority for:

- verification;
- receipt validation;
- predecessor resolution; and
- gate-state queries.

Future Progressive implementation units shall consume these capabilities
exclusively through the canonical Progressive interface. No new verification
implementation may be introduced elsewhere. Gate-specific verifiers remain
implementations selected by the canonical verification interface; callers
shall not create competing verification dispatch or validation paths.

### 8.2 Progressive Decision Authority

`ProgressiveGateService` is the canonical implementation façade and the
exclusive Progressive implementation authority for:

- approval and rejection;
- decision persistence;
- acceptance recording;
- replay;
- receipt generation; and
- supersedence.

Projection and compatibility code may observe or delegate to this façade. It
shall not originate, validate, persist, replay, supersede, or advance a
Progressive decision independently.

### 8.3 Progressive Lifecycle Projection

Progressive Lifecycle Projection is the exclusive Progressive implementation
authority for read-only lifecycle projection, compatibility lifecycle
rendering, and lifecycle projection snapshots. It shall never verify evidence,
validate receipts, own decisions, advance lifecycle state, or supersede
authority. Invalid, stale, conflicting, or replay-inconsistent canonical state
produces no projection and fails closed.

### 8.4 Compatibility policy

`scripts.lib.emp.progressive_oa` is a compatibility boundary. Existing public
interfaces remain supported. New Progressive functionality shall not
introduce additional decision implementations inside compatibility modules.
Compatibility modules may delegate but shall not own Progressive authority.

Future implementation units shall consume canonical authority primitives and
canonical decision authority, avoid direct implementation of duplicated
authority logic, and reduce compatibility surfaces over time rather than
expand them.

### 8.5 Dependency contract

The Progressive Runtime Layer has strict one-way dependencies:

```text
Layer 3 — Progressive Lifecycle Projection
        |
        v
Layer 2 — Progressive Decision Authority
        |
        v
Layer 1 — Progressive Authority Primitives
```

Dependencies are permitted only downward.

Layer 1 may depend only on foundational shared utilities. It shall not depend
on Progressive Decision Authority, Progressive Lifecycle Projection, or
compatibility adapters.

Layer 2 may consume Layer 1. It shall not depend on Layer 3 or compatibility
adapters.

Layer 3 may consume Layer 2 and Layer 1. It shall never own authority, advance
lifecycle state, verify evidence, validate receipts, or persist decisions.

Compatibility adapters may consume the Progressive Runtime Layer, shall never
be consumed by a runtime layer, and remain temporary migration boundaries. No
runtime implementation shall depend on a compatibility module.

Repository qualification shall validate this dependency graph, reject upward
or circular runtime dependencies, reject compatibility dependency leakage, and
reject duplicate authority ownership. Validation fails closed when its
architectural inputs are absent or invalid.

### 8.6 Runtime extension rule

The Progressive Runtime Layer consists of exactly the three runtime layers
defined in Sections 8.1 through 8.3. Future implementation units may extend,
refine, or consume an existing runtime layer. They shall not introduce a
fourth runtime layer, redefine runtime-layer responsibilities, split or merge
runtime layers, or bypass the dependency contract.

Any modification to the runtime-layer model requires an approved architectural
decision before implementation.

### 8.7 Runtime classification rule

Foundational shared utilities support runtime implementation and may be
consumed by runtime layers. They are implementation infrastructure only and
shall never be classified as runtime layers.

Compatibility adapters support migration, consume runtime layers, and preserve
legacy interfaces. They shall never be classified as runtime layers.

Validation tools, qualification suites, architectural validators, and
enforcement utilities are qualification infrastructure. They support the
runtime, are not runtime layers, and shall not alter runtime authority
ownership.

The repository's machine-readable runtime classification shall identify all
three runtime layers and these non-runtime categories. Architectural validation
shall fail closed when the classification is absent, invalid, expanded, or
inconsistent with this specification.

### 8.8 Runtime registration rule

Every Progressive Runtime consumer shall declare the canonical runtime layers
it consumes. A consumer may declare Layer 1, Layer 2, and Layer 3 as applicable
and shall identify only those canonical layers. A consumer shall not declare a
nonexistent runtime layer, compatibility adapter, foundational shared utility,
or qualification infrastructure as a runtime layer.

The repository shall maintain a deterministic, machine-readable Runtime
Consumer Registry that identifies every registered consumer, the canonical
layers consumed, the registered interfaces used, and whether the consumer is
production or compatibility code. The registry is an implementation artifact,
not a controlled document.

Architectural validation shall discover runtime consumption deterministically
and prove that every consumer is registered, every declaration references only
canonical layers, consumption occurs only through the interfaces registered
for that consumer, and the registry matches repository implementation.
Validation shall reject unregistered consumers, nonexistent layers, duplicate
registrations, interface bypass, invalid or stale entries, and missing
runtime-registration input. Validation fails closed.

### 8.9 Runtime capability rule

Every registered runtime consumer shall declare the canonical runtime
capability or capabilities it consumes. Runtime capabilities are architectural
contracts. They are distinct from runtime layers, runtime interfaces, and
implementation modules. A capability may be implemented by one or more
runtime layers, and a consumer may consume one or more capabilities.

The repository shall maintain a deterministic, machine-readable Runtime
Capability Registry identifying every canonical runtime capability, the
runtime layers implementing it, its canonical runtime interfaces, and its
registered consumers. The registry is an implementation artifact, not a
controlled document.

Architectural validation shall prove capability ownership and bidirectional
traceability through canonical runtime layers, canonical runtime interfaces,
and registered runtime consumers. It shall reject undefined or duplicate
capabilities, orphaned capabilities without a runtime owner, references to
nonexistent capabilities, declarations inconsistent with registered runtime
layers, capability/interface mismatches, stale registrations, and missing
runtime-capability input. Validation fails closed.

The required traceability chain is:

```text
Runtime Capability
        |
        v
Canonical Runtime Layer(s)
        |
        v
Canonical Runtime Interface(s)
        |
        v
Registered Runtime Consumer(s)
```

Every element shall be traceable in both directions.

### 8.10 Runtime policy rule

Every canonical runtime capability shall reference exactly one canonical
Runtime Policy. Runtime Policies govern operational behavior. They are
distinct from runtime capabilities, runtime layers, runtime interfaces, and
implementation modules. Policies describe execution governance rather than
implementation.

The repository shall maintain a deterministic, machine-readable Runtime Policy
Registry. Each policy shall define its policy identifier, governed capability,
required authority level, approval requirements, execution constraints,
lifecycle state, eligibility requirements, and failure behavior. The registry
is an implementation artifact, not a controlled document.

Architectural validation shall prove exactly-one policy ownership for every
capability, validate policy authority, approval, lifecycle, eligibility, and
failure rules, and keep policy metadata synchronized with repository
architecture. It shall reject undefined or duplicate policies, capabilities
without governing policies, policies referencing nonexistent capabilities,
conflicting assignments, invalid approval requirements or lifecycle states,
stale registrations, and missing runtime-policy input. Validation fails
closed.

The required traceability chain is:

```text
Runtime Policy
        |
        v
Runtime Capability
        |
        v
Canonical Runtime Layer(s)
        |
        v
Canonical Runtime Interface(s)
        |
        v
Registered Runtime Consumer(s)
```

Every relationship shall be traceable in both directions.

### 8.11 Runtime state rule

Every Runtime Policy shall reference one or more canonical Runtime States
under which execution is permitted. Runtime States define the operational
conditions under which governed runtime capabilities are authorized to
execute. Runtime States are distinct from runtime policies, runtime
capabilities, runtime layers, runtime interfaces, and implementation modules.

The repository shall maintain a deterministic, machine-readable Runtime State
Registry. Each state shall define its state identifier, permitted predecessor
states, permitted successor states, entry conditions, exit conditions,
required invariants, and permitted Runtime Policies. The registry is an
implementation artifact, not a controlled document.

Architectural validation shall prove that every policy references one or more
canonical states, every state is reachable from the canonical initial state,
every transition is reciprocal and valid, transition graphs are acyclic,
state invariants are complete, and policy-to-state permissions agree in both
directions. It shall reject undefined or duplicate states, invalid predecessor
or successor references, unreachable states, illegal transition cycles,
policies referencing nonexistent states, execution outside authorized states,
stale runtime-state metadata, and missing runtime-state input. Validation
fails closed.

The required traceability chain is:

```text
Runtime State
        |
        v
Runtime Policy
        |
        v
Runtime Capability
        |
        v
Canonical Runtime Layer(s)
        |
        v
Canonical Runtime Interface(s)
        |
        v
Registered Runtime Consumer(s)
```

Every relationship shall be traceable in both directions.

### 8.12 Runtime transition rule

Every Runtime State transition shall be represented by exactly one canonical
Runtime Transition. Runtime Transitions define the authorized movement between
runtime states. They are distinct from runtime states, runtime policies,
runtime capabilities, runtime layers, runtime interfaces, and implementation
modules.

The repository shall maintain a deterministic, machine-readable Runtime
Transition Registry. Each transition shall define its transition identifier,
source Runtime State, destination Runtime State, governing Runtime Policy or
Policies, transition guard conditions, required evidence, approval
requirements, rollback behavior, and transition invariants. The registry is an
implementation artifact, not a controlled document.

Architectural validation shall prove exactly-one transition ownership for
every Runtime State graph edge, valid source and destination states, complete
guards, evidence, approvals, rollback behavior, transition invariants, and
metadata freshness. It shall reject undefined transitions, duplicate
transition identifiers, transitions referencing nonexistent Runtime States,
transitions violating the Runtime State graph, missing guard conditions,
missing approval requirements, missing required evidence, missing rollback
definitions, transition invariant violations, stale Runtime Transition
metadata, and missing Runtime Transition Registry. Validation fails closed.

The required traceability chain is:

```text
Runtime Transition
        |
        v
Runtime State
        |
        v
Runtime Policy
        |
        v
Runtime Capability
        |
        v
Canonical Runtime Layer(s)
        |
        v
Canonical Runtime Interface(s)
        |
        v
Registered Runtime Consumer(s)
```

Every relationship shall be traceable in both directions.

### 8.13 Runtime execution contract rule

Every canonical Runtime Transition shall reference exactly one canonical
Runtime Execution Contract. Runtime Execution Contracts define the required
execution semantics for an authorized transition. They are distinct from
Runtime Transitions, Runtime States, Runtime Policies, Runtime Capabilities,
Runtime Layers, Runtime Interfaces, and implementation modules.

The repository shall maintain a deterministic, machine-readable Runtime
Execution Contract Registry. Each contract shall define its execution contract
identifier, owning Runtime Transition, canonical ordered execution phases,
execution preconditions, ordered execution checkpoints, required evidence,
interruption behavior, resume behavior, completion criteria, failure criteria,
and rollback triggers. Checkpoints shall have unique deterministic identifiers
and order and shall identify their required evidence. Interruption metadata
shall identify interruptible phases, restart phase, resume prerequisites, and
interruption evidence. Rollback metadata shall identify its trigger, rollback
checkpoint, and rollback completion criteria. The registry is an
implementation artifact, not a controlled document.

Architectural validation shall reject undefined execution contracts, duplicate
contract identifiers, transitions without exactly one contract, contracts
referencing nonexistent transitions, missing or noncanonical execution phases,
missing or invalid checkpoints, missing required evidence, missing
interruption handling, missing resume behavior, missing completion criteria,
missing failure criteria, missing rollback triggers, stale execution-contract
metadata, and a missing Runtime Execution Contract Registry. Validation fails
closed.

The required traceability chain is:

```text
Runtime Execution Contract
        |
        v
Runtime Transition
        |
        v
Runtime State
        |
        v
Runtime Policy
        |
        v
Runtime Capability
        |
        v
Canonical Runtime Layer(s)
        |
        v
Canonical Runtime Interface(s)
        |
        v
Registered Runtime Consumer(s)
```

Every relationship shall be traceable in both directions. Runtime Execution
Contracts are architecture metadata only and shall not modify runtime
execution, orchestration, scheduling, or business logic.

### 8.14 Runtime outcome rule

Every Runtime Execution Contract shall reference one or more canonical Runtime
Outcomes. Every Runtime Outcome defines the authoritative completion result of
exactly one owning contract. Runtime Outcomes are distinct from Runtime
Execution Contracts, Runtime Transitions, Runtime States, Runtime Policies,
Runtime Capabilities, Runtime Layers, Runtime Interfaces, and implementation
modules.

The repository shall maintain a deterministic, machine-readable Runtime
Outcome Registry. Each outcome shall define its outcome identifier, owning
Runtime Execution Contract, canonical classification (`SUCCESS`, `FAILURE`,
`PARTIAL`, or `CANCELLED`), exactly one resulting Runtime State, deterministic
ordered nonempty required evidence, deterministic ordered nonempty completion
criteria, deterministic ordered nonempty invariant requirements, downstream
authorization effect (`ELIGIBLE`, `BLOCKED`, or `TERMINAL`), and lifecycle
projection effect. The registry is an implementation artifact, not a
controlled document.

Architectural validation shall reject undefined Runtime Outcomes, duplicate
outcome identifiers, contracts without outcomes, outcomes referencing
nonexistent execution contracts, invalid classifications, missing or invalid
resulting Runtime States, missing required evidence, missing completion
criteria, missing invariant definitions, invalid downstream authorization or
lifecycle projection effects, stale Runtime Outcome metadata, and a missing
Runtime Outcome Registry. Validation fails closed.

The required traceability chain is:

```text
Runtime Outcome
        |
        v
Runtime Execution Contract
        |
        v
Runtime Transition
        |
        v
Runtime State
        |
        v
Runtime Policy
        |
        v
Runtime Capability
        |
        v
Canonical Runtime Layer(s)
        |
        v
Canonical Runtime Interface(s)
        |
        v
Registered Runtime Consumer(s)
```

Every relationship shall be traceable in both directions. Runtime Outcomes are
architecture metadata only and shall not modify runtime execution,
orchestration, scheduling, business logic, or production behavior.

### 8.15 Architectural status

The accepted Runtime Outcome, Runtime Execution Contract, Runtime Transition,
Runtime State, Runtime Policy, Runtime Capability, Runtime Layer, Runtime
Interface, and Registered Runtime Consumer governance artifacts collectively
form the **Progressive Runtime Governance Baseline v1.0**. Consolidated
qualification shall validate every registry through the existing fail-closed
validators, prove every relationship in both directions, verify synchronized
registry digests, enforce deterministic ordering, and reconcile this
specification with DOC-0001.

Runtime Outcomes are architecture metadata only. No runtime execution,
scheduling, orchestration, business logic, or production behavior is changed
by this baseline. The consolidation validator and its evidence are
qualification infrastructure: they do not constitute another Runtime layer,
interface, capability, policy, state, transition, execution contract, or
outcome.

The three layers defined in Sections 8.1 through 8.3 collectively form the
sole canonical Progressive Runtime Layer. Its status is:

```text
PROGRESSIVE RUNTIME LAYER

ARCHITECTURALLY FROZEN

DEPENDENCY CONTRACT ENFORCED

RUNTIME EXTENSION GOVERNED

RUNTIME CONSUMERS REGISTERED

RUNTIME CAPABILITIES GOVERNED

RUNTIME POLICIES GOVERNED

RUNTIME STATES GOVERNED

RUNTIME TRANSITIONS GOVERNED

RUNTIME EXECUTION CONTRACTS GOVERNED

RUNTIME OUTCOMES GOVERNED

PROGRESSIVE RUNTIME GOVERNANCE BASELINE V1.0 QUALIFIED
```

Future implementation units consume the runtime, extend it where authorized,
and shall do so only through these dependency rules. They shall not create
competing runtime implementations. Compatibility adapters remain temporary
migration boundaries and shall decrease over time.

## 9. Commissioning boundary

P2-019 checks in a `PREPARED` activation record and an empty production agent
registry. After this implementation commit, normal operational dispatch
remains denied until the commit is published as the active repository
baseline, authentic activation and registration artifacts are signed, the
dispatcher is activated, and a production agent is independently qualified.
The first operational WOP execution qualification is separate deferred work.

## Revision history

| Version | Date | Description |
| --- | --- | --- |
| 1.0 | 2026-07-26 | Established the Production Execution Foundation. |
| 1.1 | 2026-07-29 | Froze the canonical Progressive authority primitives and decision façade, compatibility policy, and lifecycle-projection boundary. |
| 1.2 | 2026-07-29 | Established the exactly three-layer Progressive Runtime Layer and extended the architectural freeze across authority primitives, decision authority, and lifecycle projection. |
| 1.3 | 2026-07-29 | Established and enforced strict downward-only Progressive Runtime Layer dependencies, the foundational-utility boundary, compatibility isolation, and fail-closed dependency qualification. |
| 1.4 | 2026-07-29 | Established the governed Runtime Extension Rule, explicit non-runtime classifications, and fail-closed runtime-classification validation. |
| 1.5 | 2026-07-29 | Established the Runtime Registration Rule, deterministic Runtime Consumer Registry requirements, registered-interface enforcement, and fail-closed consumer synchronization validation. |
| 1.6 | 2026-07-29 | Established the Runtime Capability Rule, deterministic Runtime Capability Registry, bidirectional semantic traceability, and fail-closed capability governance validation. |
| 1.7 | 2026-07-29 | Established the Runtime Policy Rule, deterministic Runtime Policy Registry, exactly-one capability ownership, behavioral governance validation, and full bidirectional policy traceability. |
| 1.8 | 2026-07-29 | Established the Runtime State Rule, deterministic Runtime State Registry, operational-eligibility and transition validation, invariant enforcement, and full bidirectional state traceability. |
| 1.9 | 2026-07-29 | Established the Runtime Transition Rule, deterministic Runtime Transition Registry, exactly-one state-edge ownership, guard, evidence, approval, rollback, and invariant validation, and full bidirectional transition traceability. |
| 1.10 | 2026-07-29 | Established the Runtime Execution Contract Rule, deterministic Runtime Execution Contract Registry, canonical phase, checkpoint, evidence, interruption, resume, completion, failure, and rollback validation, and full bidirectional execution-contract traceability. |
| 1.11 | 2026-07-29 | Established the Runtime Outcome Rule, deterministic Runtime Outcome Registry, canonical classification, state, evidence, criteria, invariant, authorization, and lifecycle-effect validation, and full bidirectional outcome traceability. |
| 1.12 | 2026-07-29 | Consolidated and qualified the accepted Runtime governance registries as Progressive Runtime Governance Baseline v1.0, with deterministic cross-registry validation, controlled-document reconciliation, and an unchanged runtime-behavior boundary. |
