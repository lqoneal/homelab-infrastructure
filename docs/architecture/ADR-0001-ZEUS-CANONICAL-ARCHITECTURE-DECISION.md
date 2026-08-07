---
document_id: ADR-0001
title: Zeus Canonical Architecture Decision
version: 1.3
status: Draft
owner: Homelab Infrastructure
created: 2026-07-30
last_updated: 2026-07-30
phase: Zeus Operational Alpha
domain: Engineering Architecture
classification: Architecture Decision Record
predecessor_revision: ADR-0001@1.2
successor_revision: null
approval_status: Pending
approval_authority: null
approval_reference: null
approval_date: null
persistence_status: Pending
source_of_truth: true
information_scope: Canonical Homelab Engineering Platform architecture, decision-request resolutions, subsystem and information ownership, authority and lifecycle boundaries, interactions, invariants, migration, compatibility, and implementation constraints
declared_deferrals:
  - generalized-authority-topology-registry
  - multi-project-mission-contract-federation
  - distributed-dispatch-implementation-topology
  - advanced-notification-routing
  - exceptional-delayed-execution-authorization
  - authority-record-persistence-location
relationships:
  - type: governed_by
    target: CHAR-0001
  - type: conforms_to
    target: STD-0000
  - type: conforms_to
    target: STD-0001
  - type: conforms_to
    target: STD-0002
  - type: conforms_to
    target: SPEC-0001
  - type: depends_on
    target: ARCH-0001
  - type: implemented_by
    target: SPEC-0002
  - type: related_to
    target: EDR-0002
  - type: related_to
    target: EDR-0003
  - type: related_to
    target: SPEC-0011
  - type: related_to
    target: SPEC-0012
  - type: related_to
    target: PHASE-0001
  - type: indexed_by
    target: DOC-0001
tags:
  - architecture
  - decision
  - zeus
  - authority
  - operational-alpha
---

# Zeus Canonical Architecture Decision

## 1. Decision status and authority boundary

This is Draft Version 1.3 of the Zeus Canonical Architecture Decision. It is
the content-complete architecture candidate derived from `ARCH-0001` Draft
1.6 and resolves `ARCH-DR-001` through `ARCH-DR-020`.

While Draft:

- the selections in this document are proposed, not operational;
- no implementation, migration, retirement, publication, or lifecycle
  transition is authorized;
- existing Active controlled records retain their assigned authority;
- existing runtime behavior remains unchanged; and
- `SPEC-0002` is a Draft implementation reference only.

If an applicable controlled lifecycle decision approves and activates this
record, it becomes the single authoritative engineering architecture decision
for the Homelab Engineering Platform within its stated scope. A downstream
specification may elaborate these decisions but shall not select a competing
owner, authority path, lifecycle, or interaction. Approval shall not by itself
execute migration or activate production dispatch.

## 2. Context

The repository contains mature implementations for portfolio management,
operator interaction, Mission Contracts, WOPs, authority publication and
resolution, admission, supervised execution, evidence, qualification,
reconciliation, and notification. It also contains successive architecture
generations that independently solve parts of the same mission and authority
problem.

`ARCH-0001` Draft 1.6 identifies four convergence conditions:

1. the repository-owned Progressive OA path is the current ordered gate path;
2. execution authority is evaluated through multiple overlapping components;
3. mission description and operational state are represented in more than one
   editable location; and
4. much of the newest behavior is not yet a clean, published, reproducible
   baseline.

The architecture decision must preserve qualified capabilities while ensuring
that only one composition can reach a terminal execution decision.

## 3. Problem statement

Zeus requires an unambiguous architecture that answers:

- where a Governance Decision becomes an authoritative grant;
- how a Mission Contract derives from that grant without becoming authority;
- which records own mission identity, objective, scope, and dependencies;
- how a WOP becomes an immutable admitted execution package;
- how owner-specific authority facts are resolved;
- which component may narrow gate eligibility;
- which component emits the only terminal initiation decision;
- how execution, evidence, qualification, reconciliation, and notification
  compose without acquiring authority they do not own;
- how authoritative state differs from derived projections; and
- how resource conflicts are evaluated without repository-specific
  architecture;
- how Governance, EMP, Zeus, WOP, EENS, and EOS remain within their assigned
  responsibilities;
- how lifecycle states remain small and orthogonal; and
- how interruption recovery and future distribution preserve authority,
  identity, effect safety, and deterministic outcomes; and
- how legacy and compatibility paths are removed without losing history.

The current repository cannot safely treat each existing resolver or lifecycle
service as independently authoritative. A decision must define one path and
bound all other roles.

## 4. Decision drivers

### 4.1 Architectural assumptions

The decisions rely on the following bounded assumptions:

1. Operational Alpha initially operates against one explicitly bound
   repository and publication baseline, even though the resource model is not
   repository-specific.
2. Governance can issue attributable Governance Decisions and immutable
   Authority Record revisions with integrity-verifiable lineage.
3. Canonical serialization, cryptographic digests, stable identifiers, and
   deterministic reason codes are available to every control-plane handoff.
4. A WOP can be frozen, admitted, and qualified before execution without
   changing its content.
5. Existing consumers can be inventoried and migrated while dispatch remains
   disabled or bounded by the currently qualified path.
6. External-effect providers either expose an idempotency or fencing
   mechanism, or the effect is treated as non-repeatable and requires
   reconciliation after an uncertain outcome.
7. Controlled-document lifecycle, approval, and persistence continue to be
   governed by their existing superior records; this ADR does not replace
   those governance rules.

If an assumption is false, execution fails closed and the affected
architecture decision returns for controlled revision. An implementation
shall not compensate by creating an undeclared authority object, another
terminal decision path, or an overlapping lifecycle.

### 4.2 Decision drivers

The selected architecture shall:

1. fail closed on missing, ambiguous, stale, or conflicting inputs;
2. preserve one information owner for every governed fact;
3. separate authority resolution, eligibility narrowing, and terminal
   initiation;
4. retain immutable inputs and append-only decisions;
5. preserve the locked Progressive OA ordering;
6. reuse qualified implementation rather than create another adapter layer;
7. make authoritative state and projections distinguishable;
8. separate repository publication from EOS synchronization;
9. allow deterministic recovery and replay;
10. preserve historical evidence and compatibility obligations; and
11. support clean-checkout qualification and publication;
12. keep Governance limited to policy, approval, authority, and audit;
13. represent governed-resource conflicts through an extensible common model;
14. omit a second execution grant from the standard path;
15. minimize lifecycle states by separating Governance, execution, and
    synchronization domains;
16. recover deterministically from interruption without repeating an
    unproven external effect; and
17. allow autonomous selection and horizontal scale without replicating
    authority or permitting split-brain execution.

## 5. Alternatives considered

### Alternative A — Continue the plural architecture

Each existing authority, approval, lifecycle, and execution component retains
its current decision behavior.

**Advantages**

- minimal immediate code movement;
- preserves existing callers; and
- avoids a near-term migration.

**Disadvantages**

- competing decisions remain possible;
- current and legacy paths remain difficult to distinguish;
- Mission Contract and state drift persist; and
- gate qualification cannot prove one terminal route.

**Disposition:** Rejected.

### Alternative B — Replace existing services with one monolithic Zeus runtime

One new service owns mission intent, authority, eligibility, initiation,
execution, evidence, and state.

**Advantages**

- simple conceptual entry point; and
- centralized debugging.

**Disadvantages**

- destroys established information ownership;
- conflates governance, authority, execution, evidence, and projection;
- duplicates mature services;
- creates a high-risk cutover; and
- weakens independent qualification.

**Disposition:** Rejected.

### Alternative C — Federate existing decisions through another compatibility adapter

A new adapter accepts every existing decision format and selects or merges an
outcome.

**Advantages**

- provides a gradual caller migration; and
- retains every existing interface.

**Disadvantages**

- creates another decision point;
- preserves ambiguity permanently;
- selection rules can hide conflicting authority; and
- adapter output cannot repair invalid upstream ownership.

**Disposition:** Rejected as a canonical design. A bounded migration adapter
may translate syntax only if it cannot decide or widen authority.

### Alternative D — Separate Governance authority from typed orchestration owners

A Governance Decision produces an Authority Record. A Mission Contract is
derived from that authority. EMP plans, WOP packages the work, Zeus resolves
readiness and orchestrates execution, Progressive authority may only narrow
eligibility, EENS observes and notifies, and EOS synchronizes and reconciles.
Engineering Work Initiation emits the only terminal initiation decision.

**Advantages**

- preserves established services and ownership;
- prevents the Mission Contract from becoming a second governance owner;
- avoids a routine second execution grant;
- makes each decision boundary testable;
- supports fail-closed conflict handling;
- supports deterministic replay and resumable execution without treating
  recovery state as authority;
- allows compatibility logic to be isolated; and
- aligns with the observed Progressive architecture.

**Disadvantages**

- requires consumer migration and retirement evidence;
- temporarily increases explicit translation and comparison work; and
- demands precise state and interface contracts.

**Disposition:** Selected, subject to approval and activation.

## 6. Selected architecture

The selected architecture is:

```text
Operator Intent / Mission Proposal
      |
      v
Governance Decision
      |
      v
Immutable Authority Record
      |
      v
EMP deterministic contract derivation
      |
      v
Derived Mission Contract
      |
      v
Qualified WOP
      |
      +<----- EMP immutable prioritized-candidate snapshot
      |
      v
Zeus deterministic selection and orchestration
      |
      +------------------+
                         |
                         v
Owner Publications + Repository / Environment Observation
                         |
                         v
Authority Resolution Service
  -> Resolved Execution and Authority Context
                         |
                         v
Progressive Mission Authority, when applicable
  -> narrow-only eligibility result
                         |
                         v
Zeus Engineering Work Initiation
  -> sole terminal ALLOW / DENY / STOP decision
                         |
                         v
Atomic Reservation -> Supervision -> Execution Agent
                         |
                         v
Evidence -> Independent Qualification -> Reconciliation
                         |
             +-----------+-----------+
             |                       |
             v                       v
EENS events/notifications       EOS synchronization/reconciliation
```

No skipped edge is permitted. A downstream component shall not reconstruct a
broader authority from raw sources after a narrower upstream decision.
No Execution Grant exists in this standard path.
EMP materializes the Mission Contract and supplies a prioritized
eligible-candidate snapshot beside the authority chain; Zeus selects one
exact candidate only after binding it to the chain.
Planning priority and eligibility never substitute for authority.

The architecture separates five kinds of ownership:

- Governance owns policy, approval, Authority Record issuance, revocation, and
  audit.
- EMP owns planning facts and deterministic materialization of derived
  mission representations.
- Zeus owns selection, orchestration, the terminal initiation decision,
  execution progress, recovery, and completion.
- independent owners retain publication, admission, evidence, qualification,
  notification, and synchronization decisions; and
- controlled records and immutable artifacts own durable facts, while Runtime
  services own only the decisions explicitly assigned to them.

## 7. Decisions

### ADR-D-001 — Authority Record owns mission authority; Mission Contract is derived

The authoritative governance chain is:

```text
Governance Decision
  -> immutable Authority Record
  -> derived Mission Contract
```

The Authority Record is the sole mission-level governance authority. Every
Authority Record revision identifies:

- its permanent record and mission identities, schema version, and immutable
  revision;
- its exact Governance Decision, approving principal, approval role, policy
  revision, approval basis, and decision time;
- its bounded objective, scope, exclusions, constraints, dependencies,
  resource claims, validity boundary, and permitted effect classes;
- its predecessor, change reason, Governance event-chain locator, and
  supersession/revocation policy;
- its canonical content digest and integrity mechanism;
- its required qualification profile and exact result;
- its audit and evidence locators; and
- its source owner plus permitted EOS projection and synchronization
  direction.

An Authority Record revision is never edited in place. Correction,
supersession, renewal, or scope change creates a successor revision from a new
Governance Decision, and the successor points to its predecessor. Revocation
or supersession appends an attributable Governance event against the exact
revision; it does not add a future reference to the immutable predecessor or
rewrite prior execution or evidence.
Authority effectiveness is a fail-closed determination over integrity,
approval lineage, applicability, validity, qualification, supersession, and
revocation. It is not a second grant or independently writable lifecycle.
Qualification verifies the frozen Authority Record against its declared
profile; it does not approve, issue, renew, or revoke authority.

The EMP Mission Contract Deriver generates the Mission Contract
deterministically from exactly one Authority Record revision. Derivation
inputs are the Authority Record canonical bytes, the declared Mission Contract
schema revision, the derivation mapping revision, and any explicitly declared
immutable lookup artifact. An authority-bearing field shall derive only from
the Authority Record. The derivation shall use canonical serialization and
shall not depend on an uncaptured clock, random value, directory order,
environment value, remote response, or mutable projection.

The result carries source and derivation identities and digests, mission
identity, objective, scope, constraints, dependencies, resource claims, and
the authorized WOP requirement or locator for execution-facing consumers.
Repeating derivation with the same exact inputs reproduces byte-identical
output. A mapping or source change creates an immutable successor contract
revision; regeneration never mutates or silently replaces an existing
revision. EMP owns materialization, discovery, and regeneration of the
derived artifact. Governance retains ownership of every authority-bearing
source fact. Publication makes the derived artifact discoverable and
integrity-verifiable but does not authorize it. The Mission Contract cannot
grant, revoke, supersede, or parent authority. Other mission descriptions are
projections, compatibility inputs, fixtures, or historical records.

### ADR-D-002 — The qualified WOP is immutable execution input

A WOP becomes eligible for execution only after schema validation, exact
content identification, required publication/admission checks, and independent
qualification.

The qualified package, typed admission receipts, and qualification evidence
are immutable inputs. WOP admission, mission Runtime admission, and Stage 1
package admission remain separate decisions over distinct subjects; their
receipts are not interchangeable.
Execution outputs, decisions, evidence, and reconciliation records are
append-only or successor records. They shall not rewrite the admitted input.

### ADR-D-003 — Owner publications remain authoritative for their facts

Repository identity, repository baseline, Governance Decision, Authority
Record, work-item authority, approval authority, phase authority, governing
baseline, and operational configuration remain owned by their designated
publication or controlled-record owners.

No resolver acquires ownership of those facts. Resolution verifies,
normalizes, binds, and reports them.

### ADR-D-004 — Authority Resolution produces one resolved context

The Authority Resolution Service is the only production component that
combines authoritative owner facts, Authority Record identity, derived Mission
Contract identity, qualified WOP identity, Admission Record where applicable,
repository observation, operator identity, and applicable policy inputs into
the canonical Resolved Execution and Authority Context.

The result contains facts and determinations with provenance. It is not a
terminal execution authorization.

An Authorization Bundle, when consumed, is an immutable authenticated carrier
for exact owner publications. It is selected by declared publication family,
generation, applicability, source revision, validity, and revocation facts.
It is neither an Authority Record nor a terminal authorization. Missing,
expired, revoked, superseded, or multiply applicable bundles cause `STOP`;
recency is never a tie-breaker.

Offline Authority Graph and compatibility evaluators may validate topology or
translate legacy representations. They shall not emit a production allow
decision or widen the resolved context.

### ADR-D-005 — Progressive Mission Authority is narrow-only

Progressive Mission Authority evaluates gate order, prerequisite acceptance,
current package state, evidence bindings, and gate-specific eligibility.

It may:

- preserve an existing authorization ceiling;
- narrow an eligible action;
- block, defer, or deny gate progression; or
- require additional evidence.

It shall not:

- create mission or execution authority;
- replace owner publications;
- widen scope, actions, repositories, agents, or time bounds;
- bypass a failed resolution; or
- initiate execution.

### ADR-D-006 — Zeus Engineering Work Initiation owns the terminal decision

Engineering Work Initiation is a Zeus orchestration boundary and the sole
component permitted to emit the terminal initiation result consumed by
reservation and execution. It is not a Governance component.

It composes:

- the Resolved Execution and Authority Context;
- the narrow-only Progressive result when applicable;
- repository and environment observations;
- admission, agent, policy, freshness, and conflict checks; and
- mission-specific execution preconditions.

Its outcome is one of:

- `ALLOW` — all required inputs are valid and execution may proceed within the
  exact decision envelope;
- `DENY` — a stable policy or authority condition prohibits initiation; or
- `STOP` — required evidence is missing, ambiguous, stale, conflicting, or
  operationally unsafe.

No downstream service may reinterpret `DENY` or `STOP` as eligible.

### ADR-D-007 — Execution services consume, never originate, authority

Reservation, dispatcher, oversight, execution-agent selection, and agent
runtime consume the terminal initiation decision and exact WOP.

They may enforce stricter operational safety. They may not:

- expand the allowed action;
- substitute a different mission, repository, package, agent, or baseline;
- infer authority from management state; or
- retry outside the decision envelope.

EMP owns the mission inventory, priority, dependency graph, planning
eligibility, and Governance proposal/status interaction. EMP produces a
deterministic prioritized candidate snapshot, not an execution decision.
Zeus owns selection of one candidate from that snapshot, execution-readiness
resolution, bounded adaptation, dispatch, supervision, interruption recovery,
evidence-production orchestration, qualification orchestration, and execution
completion. Independent qualification still owns the qualification
determination. Zeus may adapt only within the Authority Record, derived
Mission Contract, qualified WOP, EWI envelope, and resource leases; a change
outside those bounds returns to EMP and Governance instead of widening at
runtime.

### ADR-D-008 — One owner for each state; projections are read-only

Each state field has one information owner. Other stores are typed projections
or evidence.

Projections:

- name their source and source revision;
- cannot be reverse-synchronized by inference;
- fail closed when stale or inconsistent;
- do not become authoritative because they are newer; and
- are regenerated or reconciled only through the designated direction.

Derived predicates, including Authority Record effectiveness, mission
planning eligibility, readiness, freshness, and synchronization condition,
name their producer, exact inputs, evaluation revision, reason code, and
invalidation rule. A predicate may narrow a decision only at its assigned
boundary and never becomes an independently writable lifecycle.

### ADR-D-009 — Evidence and qualification remain independent

Execution produces evidence. Evidence sealing verifies integrity.
Qualification evaluates evidence against criteria. Qualification does not
rewrite evidence or execution state. Acceptance and lifecycle transitions
consume qualification only through their designated decision mechanisms.

### ADR-D-010 — Publication and synchronization are separate

Repository publication owns exact source persistence, commit and tag identity,
reproduction, and publication metadata. EOS synchronization consumes an
explicit repository boundary and produces a derived operational projection.

A repository commit does not automatically authorize or perform EOS
synchronization. EOS drift shall not be repaired by rewriting repository
authority from a projection.

### ADR-D-011 — EENS owns durable engineering events, not decisions

EENS accepts and persists typed engineering events, delivers notification
projections, and supports replay and consumer checkpoints.

Notification delivery, acknowledgement, or failure shall not create approval,
authority, qualification, lifecycle, or execution outcomes.

### ADR-D-012 — Compatibility is isolated and retired by evidence

Legacy authority, gate approval, OA-02 lifecycle, external WOP, PMCT, and
mission-description paths shall be classified as:

- offline validator;
- syntax-only migration adapter;
- generated projection;
- fixture;
- historical record; or
- retired implementation.

No compatibility component remains on the canonical production decision path.
Removal requires consumer inventory, regression evidence, recovery analysis,
and preservation of historical evidence.

### ADR-D-013 — The standard lifecycle has no Execution Grant

Normal execution follows:

```text
Governance Decision
  -> Authority Record
  -> derived Mission Contract
  -> qualified WOP
  -> Zeus execution
```

Review, dual control, timing, destructive-effect restrictions, and
external-effect restrictions are conditions of the Authority Record and WOP
qualification. Zeus revalidates them before dispatch. A routine Execution
Grant would duplicate authorization and is not part of the selected
architecture.

If delayed authorization after WOP qualification becomes a demonstrable
requirement, it requires a separately controlled exceptional extension. That
extension shall not change the standard lifecycle by inference.

### ADR-D-014 — Resource conflicts use one generalized model

Conflict evaluation uses typed resource claims containing namespace, type,
identity, access mode, effect class, scope, lease policy, and containment
rules. The same model applies to repositories, infrastructure, services,
hardware, environments, controlled documents, publication units, credential
boundaries, and future resource types.

New resource types register identity and containment semantics without an
architectural change. Governance authorizes claims, WOP declares required
claims, EMP plans against them, and Zeus acquires operational leases. A lease
is not authority.

### ADR-D-015 — Governance, orchestration, and lifecycle domains are orthogonal

Subsystem responsibility is:

| Subsystem | Required responsibility | Prohibited responsibility |
|---|---|---|
| Governance | policy, approval, Authority Record issuance/revocation, audit | planning, prioritization, selection, orchestration, execution, synchronization |
| EMP | mission inventory, prioritization, dependency management, planning eligibility, Governance interaction | approval, authority issuance, runtime selection, dispatch |
| Zeus | deterministic mission selection, orchestration, bounded adaptation, execution, recovery, evidence and qualification orchestration, completion | Governance decisions, EMP source planning, qualification determination, notification transport, synchronization authority |
| WOP | immutable qualified execution package and completion criteria | authority, planning, selection, orchestration |
| EENS | observation, durable events, notification, replay to consumers | authority, execution decisions, synchronization |
| EOS | directional synchronization and reconciliation of owner facts and projections | authority, approval, planning, selection, orchestration |

The orthogonal state dimensions are:

- Governance: `Proposed`, `Authorized`, `Revoked`;
- Authority: a derived `effective` or `not effective` determination over one
  immutable Authority Record revision, not a mutable lifecycle;
- mission planning: EMP-owned inventory, priority, dependency-satisfaction,
  and planning-eligibility facts, not aliases for execution state;
- execution: `Planned`, `Ready`, `Running`, `Blocked`, `Complete`, `Failed`;
  and
- synchronization: `Dirty`, `Pending`, `Reconciled`.

Additional detail is expressed through reason codes, conditions, evidence, or
successor records. Mission selection creates an execution attempt; it does not
change Governance or Authority state. Execution completion does not revoke
authority, and synchronization condition cannot change any owner fact. A new
lifecycle state requires evidence that the existing states cannot represent a
necessary engineering distinction without ambiguity.

### ADR-D-016 — Recovery and scale preserve identity, authority, and effect safety

Each execution attempt binds one Authority Record revision, derived Mission
Contract revision, qualified WOP, candidate-snapshot digest, EWI decision,
resource-lease set, agent identity, and idempotency key. Checkpoints and
external-effect intents are append-only and identify the last proven safe
boundary.

After reboot, interruption, power loss, lease loss, or partial execution,
Zeus shall reconstruct from declared owners, revalidate authority and
freshness, reacquire fenced resource leases, and resume only from a checkpoint
whose identity and effects are proven. An uncertain non-idempotent effect
stops for reconciliation; it is never repeated because completion was not
observed. Duplicate dispatch is rejected by attempt identity, idempotency
keys, durable effect records, and fencing tokens.

Autonomous selection uses an immutable EMP candidate snapshot and a declared
deterministic selection-policy revision with stable tie-breaking. Distributed
or horizontally scaled Zeus workers may compete for work only through an
atomic reservation and fenced lease. Network partition, stale replica,
conflicting checkpoint, or lost quorum fails closed; no worker or EOS
projection becomes authority. Replay uses captured inputs and is
non-side-effecting unless the exact operation is explicitly idempotent.

EOS retries synchronization idempotently from the authoritative source
boundary. A partial, stale, or newer EOS projection cannot repair, revoke, or
supersede an Authority Record or other owner fact. These invariants permit a
future distributed implementation without selecting its transport, storage,
consensus, or deployment topology.

## 8. Canonical ownership

An owner is the only component or controlled-record class permitted to create
or transition the named fact. A producer of a derived artifact owns its
correct derivation, not the authority of its inputs.

| Information or decision | Canonical owner and permitted writer | Derived consumers or projections | Invalid competing owner |
|---|---|---|---|
| Governance policy and approval decision | Governance | Authority Record issuance and audit views | EMP, Zeus, WOP, EOS, EENS |
| Mission authority, authorized mission identity, objective, scope, exclusions, constraints, dependencies, effect classes, and validity | exact immutable Authority Record revision issued by Governance | Mission Contract, resolver, audit | Mission Contract, Work Registry, WOP, Runtime state |
| Authority supersession and revocation events | Governance event chain | effectiveness evaluation and audit | artifact mutation, EOS projection, Runtime state |
| Authority effectiveness | Authority Resolution Service as a derived predicate over Governance-owned inputs | REAC and EWI | mutable lifecycle field or Mission Contract flag |
| Derived Mission Contract bytes and derivation provenance | EMP Mission Contract Deriver | WOP, resolver, candidate view | manually edited duplicate mission store |
| Mission inventory, priority, planning dependencies, and planning eligibility | EMP Work Registry | immutable candidate snapshot and operator view | Zeus execution state or Project State copy |
| Candidate snapshot | EMP candidate-snapshot producer | Zeus selector and audit | mutable queue consumed without digest |
| Mission selection | Zeus deterministic selector | reservation and EMP outcome projection | Governance or EMP priority alone |
| Qualified execution package | WOP publisher plus immutable qualification binding | resolver, EWI, execution, evidence | Runtime-mutated WOP or external unbound path |
| WOP package admission | WOP Admission boundary in ADR-C-005 | mission Runtime admission and resolver | Stage 1 or Runtime receipt substituted by type |
| Mission Runtime admission | Zeus mission Runtime Admission boundary in ADR-C-008 | EWI | WOP or Stage 1 receipt substituted by type |
| Stage 1 execution-package admission | Zeus Stage 1 Admission boundary in ADR-C-008 | EWI and dispatcher | WOP or Runtime receipt substituted by type |
| Repository identity and observed baseline | repository identity and baseline publication owner | resolver and EWI observation | EOS or working-directory recency |
| Authority publications and Authorization Bundles | each designated fact owner; bundle producer owns only the carrier | resolver | resolver, adapter, or newest-file selection |
| Resolved Execution and Authority Context | Authority Resolution Service | PMA and EWI | PMA, EWI, graph, or compatibility resolver |
| Progressive gate eligibility | Progressive Mission Authority | EWI and operator projection | terminal execution consumer |
| Terminal initiation | Zeus Engineering Work Initiation | resource coordinator, reservation, execution supervisor | dispatcher, agent, PMA, legacy approval |
| Resource-claim authorization | Authority Record | WOP declaration and resolver | lease service |
| Operational resource lease and fencing token | Zeus resource coordinator | EWI, dispatcher, execution agent, recovery | Governance or EOS |
| Reservation and assignment | Zeus execution supervisor/dispatcher | agent and oversight | EMP queue |
| Execution attempt, checkpoint, bounded adaptation, effect record, and result | Zeus execution runtime | evidence pipeline, recovery, EMP outcome projection | EOS, EENS, or agent-local unsealed state |
| Evidence bytes and identity | originating evidence producer and sealed evidence record | qualification and audit | qualification service |
| Qualification determination | independent qualification service | acceptance, EWI, and lifecycle consumers | Zeus orchestration or evidence producer |
| Controlled-document lifecycle | applicable controlled-document owner and authorized lifecycle mechanism | index, publication, and operator views | repository commit or EOS projection |
| Project state | `PROJ-0001` information owner | EMP, EOS, and resume projections | Work Registry or Runtime inference |
| Repository publication identity and transaction result | controlled publication transaction and Git publication boundary | EOS synchronization | lifecycle status or working tree |
| Synchronization transaction, checkpoint, and reconciliation result | EOS | resume and operator views | source-record mutation |
| Durable engineering event and delivery checkpoint | EENS | consumers and notification transports | source lifecycle or execution decision |
| Read-only projections | named projection producer under the source owner's direction | presentation and discovery consumers | reverse-synchronization into source facts |

## 9. Authority boundaries

### 9.1 Authority is not inferred

The following do not independently authorize execution:

- a queue or management state;
- a Mission Contract filename;
- Mission Contract content without its exact effective Authority Record;
- a WOP path;
- a passing unit test;
- a gate implementation marker;
- an evidence file;
- an operator notification;
- a repository commit;
- an EOS projection; or
- this Draft ADR.

EOS reconciliation success, freshness, or recency cannot make an Authority
Record effective and cannot substitute for its Governance Decision,
qualification result, or source-owner integrity.

### 9.2 Narrowing is monotonic

For any downstream decision envelope `D(n+1)` and its upstream envelope
`D(n)`:

```text
scope(D(n+1)) is a subset of scope(D(n))
actions(D(n+1)) is a subset of actions(D(n))
resources(D(n+1)) is a subset of resources(D(n))
time(D(n+1)) does not exceed time(D(n))
```

If a component cannot prove monotonic narrowing, it returns `STOP`.

### 9.3 Fail-closed conflict behavior

Conflicting identity, digest, scope, lifecycle, authority, repository,
baseline, admission, agent, evidence, or policy facts result in `STOP`.
Precedence shall be resolved by the applicable information owner or superior
controlled authority, not by runtime recency or adapter preference.

## 10. Migration strategy

Migration is dependency ordered and requires separately authorized work.

### Stage 0 — Freeze and inventory

- record the exact candidate boundary;
- inventory every authority and mission consumer;
- identify current live, test, fixture, external, and historical paths; and
- inventory all three admission-receipt consumers and every Authorization
  Bundle generation;
- preserve historical evidence and checksums.

### Stage 1 — Establish contracts

- establish `SPEC-0002`;
- define Governance Decision, Authority Record, and Mission Contract derivation
  contracts;
- define the Resolved Execution and Authority Context;
- define narrow-only and terminal-decision interfaces;
- define state ownership and projection declarations; and
- define generalized resource claims, stable error codes, and stop codes; and
- define typed WOP, mission Runtime, Stage 1, resolution, initiation,
  reservation, qualification, publication, and synchronization receipts;
- define deterministic selection, attempt, checkpoint, effect-fencing,
  synchronization-recovery, and distributed-safety contracts.

### Stage 2 — Establish authority and converge Mission Contracts

- establish the Authority Record as the sole mission-level authority;
- select the canonical Authority Record and derived Mission Contract stores;
- map fields from execution mission descriptions;
- convert `engineering/execution/missions/` to a generated discovery
  projection during consumer migration;
- convert dependent views to generated projections; and
- reject independently edited duplicate facts.

### Stage 3 — Converge authority resolution

- route owner publications and repository observation through one resolver;
- compare existing resolver results during bounded qualification;
- select exact Authorization Bundle family and generation by declared
  applicability rather than recency;
- prevent offline and compatibility components from emitting production
  authorization; and
- bind Progressive evaluation to the resolved context.

### Stage 4 — Converge initiation and execution

- make EWI the only terminal decision;
- remove Execution Grant from the standard path;
- require reservation and dispatch to consume the exact decision identity;
- replace repository-specific conflicts with generalized resource claims and
  leases;
- bind deterministic selection, attempts, checkpoints, effect intents, resume,
  and completion to exact identities;
- prove no alternate route reaches an agent; and
- retain dispatch-disabled behavior until qualification.

### Stage 5 — Retire compatibility

- remove production consumers;
- retire the standalone PMCT executable after its predicates have moved behind
  canonical interfaces and consumer-complete evidence exists;
- preserve fixtures and historical evidence where required;
- remove dead code only after import, routing, recovery, and test inventories
  pass; and
- document residual compatibility support explicitly.

### Stage 6 — Publish and qualify

- publish dependency-ordered units;
- reproduce from a clean checkout;
- run aggregate and gate qualification;
- verify unchanged accepted fingerprints where applicable; and
- reconcile projections only through separately authorized synchronization.

## 11. Consequences

### Positive

- exactly one path reaches execution;
- Governance no longer embeds orchestration;
- Mission Contract consumers cannot mistake contract data for authority;
- routine execution requires no duplicate grant;
- resource conflicts extend without architecture changes;
- lifecycle state has fewer cross-domain aliases;
- deterministic candidate selection and fenced attempts support autonomous
  operation and future horizontal scale;
- interruption recovery does not infer success or repeat uncertain effects;
- authority and state ownership become testable;
- existing mature services are reused;
- Progressive gate ordering is preserved;
- compatibility can be retired incrementally;
- publication and clean-checkout qualification become explicit; and
- evidence and notification remain independent.

### Negative

- callers must migrate to typed interfaces;
- temporary comparison evidence and adapters are required;
- duplicate state must be classified before removal;
- operational commissioning remains blocked until end-to-end qualification;
  and
- ownership errors become visible stop conditions rather than silently merged
  data.

### Neutral

- this decision does not determine implementation language, process topology,
  database technology, transport provider, user-interface layout, or
  deployment host;
- existing controlled records retain their authority unless separately
  revised; and
- historical evidence remains historical.

## 12. Bounded future-scope and implementation deferrals

The authority, ownership, lifecycle, interaction, recovery, compatibility, and
Operational Alpha decisions are complete. The following entries defer only a
technology selection or a future scope extension inside the invariants already
decided by this record. None is required to interpret or implement the
Operational Alpha architecture.

| Deferred implementation or future-scope subject | Reason | Revisit trigger |
|---|---|---|
| General topology registry | not required for one repository path | multiple independently deployed owner graphs |
| Cross-project Mission Contract federation | current OA is repository bounded | second project enters shared execution |
| Distributed dispatcher implementation topology | identity, fencing, replay, and fail-closed distribution invariants are decided; transport and consensus technology are not required for local OA | qualified multi-host execution requirement |
| Remote approval transport | authority model must converge first | authenticated approval capability mission |
| Advanced EENS routing | outside OA authority path | HNS expansion mission |
| Evidence catalogue technology | ownership contract precedes tooling | publication candidate contains stable evidence taxonomy |
| Long-term repository relocation | cosmetic reorganization adds risk | post-OA information-architecture mission |
| Exceptional delayed-execution authorization | no demonstrated requirement remains after Authority Record conditions and WOP qualification | concrete need to withhold authorization after qualification |
| Authority Record persistence location | logical owner and schema precede filesystem placement | synchronized controlled-document and schema design |

## 13. Acceptance criteria

This decision is eligible for controlled approval when:

1. every `ARCH-0001` decision question has an explicit disposition;
2. every selected decision is explicit enough for `SPEC-0002` reconciliation
   without another architectural interpretation;
3. existing Active controlled records have been checked for ownership conflict;
4. the Governance Decision, Authority Record, derived Mission Contract,
   qualified WOP, resolved context, PMA, and EWI boundaries are internally
   consistent;
5. state ownership and projection direction are complete;
6. migration preserves historical evidence and accepted gate lineage;
7. compatibility components cannot originate production authority;
8. publication and synchronization remain separate;
9. cross-references and document identifiers validate; and
10. approval and activation occur only through applicable lifecycle controls;
11. generalized resource-conflict behavior fails closed for unknown types and
    incompatible claims;
12. Governance, EMP, Zeus, WOP, EENS, and EOS remain within their assigned
    responsibilities; and
13. the minimal Governance, execution, and synchronization states are
    internally consistent;
14. Authority Record identity, version, approval lineage, qualification,
    supersession, revocation, audit, and EOS projection boundaries are
    complete;
15. Mission Contract derivation is byte-reproducible and immutable from
    declared inputs; and
16. restart, partial execution, duplicate dispatch, stale state,
    synchronization failure, and distributed recovery preserve identity,
    effect safety, and fail-closed authority.

Implementation acceptance is separate and requires future WOP evidence.

## 14. Decision Request resolution and traceability

Every Decision Request has one resolution record in Section 14.1 through
Section 14.20. Decision identifiers remain stable from Draft 1.2; a resolution
record composes one or more decisions into the complete answer requested by
`ARCH-0001`.

| Decision Request | Resolution section | Decisions | Canonical components | Future implementation |
|---|---|---|---|---|
| ARCH-DR-001 | 14.1 | ADR-D-001, ADR-D-008, ADR-D-015 | ADR-C-001 through ADR-C-004 | ADR-FI-001 |
| ARCH-DR-002 | 14.2 | ADR-D-003, ADR-D-004 | ADR-C-002, ADR-C-006 | ADR-FI-003 |
| ARCH-DR-003 | 14.3 | ADR-D-006 | ADR-C-008 | ADR-FI-005 |
| ARCH-DR-004 | 14.4 | ADR-D-005 | ADR-C-007, ADR-C-008 | ADR-FI-004 |
| ARCH-DR-005 | 14.5 | ADR-D-012 | ADR-C-014 | ADR-FI-011, ADR-FI-015 |
| ARCH-DR-006 | 14.6 | ADR-D-008, ADR-D-015 | ADR-C-001, ADR-C-003, ADR-C-008, ADR-C-011 | ADR-FI-006 |
| ARCH-DR-007 | 14.7 | ADR-D-010 | ADR-C-011, ADR-C-013 | ADR-FI-007 |
| ARCH-DR-008 | 14.8 | ADR-D-001, ADR-D-012 | ADR-C-003, ADR-C-004, ADR-C-014 | ADR-FI-008 |
| ARCH-DR-009 | 14.9 | ADR-D-003, ADR-D-004, ADR-D-006 | ADR-C-006, ADR-C-008, ADR-C-013 | ADR-FI-009, ADR-FI-015 |
| ARCH-DR-010 | 14.10 | ADR-D-003, ADR-D-004, ADR-D-012 | ADR-C-006, ADR-C-014 | ADR-FI-003 |
| ARCH-DR-011 | 14.11 | ADR-D-002, ADR-D-009 | ADR-C-005, ADR-C-006, ADR-C-008, ADR-C-010 | ADR-FI-002, ADR-FI-010 |
| ARCH-DR-012 | 14.12 | ADR-D-005, ADR-D-012 | ADR-C-007, ADR-C-014 | ADR-FI-011 |
| ARCH-DR-013 | 14.13 | ADR-D-011 | ADR-C-012 | ADR-FI-012 |
| ARCH-DR-014 | 14.14 | ADR-D-003, ADR-D-004, ADR-D-012 | ADR-C-006, ADR-C-014 | ADR-FI-003 |
| ARCH-DR-015 | 14.15 | ADR-D-012; Section 10 | ADR-C-008, ADR-C-014 | ADR-FI-015 |
| ARCH-DR-016 | 14.16 | ADR-D-002, ADR-D-004, ADR-D-006 | ADR-C-005, ADR-C-006, ADR-C-008 | ADR-FI-010 |
| ARCH-DR-017 | 14.17 | ADR-D-013 | ADR-C-001, ADR-C-008 | ADR-FI-005 |
| ARCH-DR-018 | 14.18 | ADR-D-014 | ADR-C-009 | ADR-FI-013 |
| ARCH-DR-019 | 14.19 | ADR-D-006, ADR-D-007, ADR-D-011, ADR-D-015 | ADR-C-001 through ADR-C-014 | ADR-FI-016 |
| ARCH-DR-020 | 14.20 | ADR-D-007, ADR-D-008, ADR-D-016 | ADR-C-008, ADR-C-009, ADR-C-011 | ADR-FI-014 |

Architecture Review Incorporation rationale:

| Accepted recommendation | ADR disposition | Rationale |
|---|---|---|
| Mission Contract is not authority | ADR-D-001 | A separate Authority Record preserves one governance owner while allowing the Mission Contract to remain a stable execution-facing representation. |
| Remove Execution Grant | ADR-D-013 | A routine second grant duplicates authorization; Authority Record conditions, WOP qualification, and immediate revalidation preserve the necessary controls. |
| Generalize conflicts | ADR-D-014 | Typed resource claims and containment rules cover present and future governed resources without resource-specific control flow. |
| Separate Governance and orchestration | ADR-D-006, ADR-D-011, ADR-D-015 | Explicit subsystem ownership prevents policy and authority services from accumulating planning, runtime, observation, or synchronization behavior. |
| Minimize lifecycle states | ADR-D-015 | Orthogonal states prevent Governance, execution, and synchronization facts from being collapsed into one ambiguous composite lifecycle. |

Operational Alpha readiness refinement rationale:

| Review subject | ADR disposition | Rationale |
|---|---|---|
| Authority Record completeness | ADR-D-001 | Immutable revision lineage plus a derived effectiveness test makes approval, qualification, revocation, and audit deterministic without a new authority object. |
| Mission Contract reproducibility | ADR-D-001 | Declared inputs, canonical serialization, byte-identical regeneration, successor revisions, and non-authoritative publication prevent contract drift. |
| EMP and Zeus overlap | ADR-D-007 and ADR-D-015 | EMP supplies prioritized planning candidates; Zeus selects and executes one exact candidate while independent qualification retains determination ownership. |
| EOS boundary | ADR-D-010, ADR-D-015, and ADR-D-016 | EOS remains directional synchronization/reconciliation infrastructure and cannot infer authority from projection state. |
| Failure recovery and scale | ADR-D-016 | Stable attempt identity, checkpoints, idempotency, fencing, revalidation, and source-directed reconciliation support recovery and scale without lifecycle expansion. |
| Orthogonal state | ADR-D-015 | Authority effectiveness and mission eligibility are derived facts; they do not require additional mutable lifecycle states. |

`SPEC-0002` shall trace every normative requirement to one or more decision
identifiers in this record.

### 14.1 ARCH-DR-001 — Governance authority and Mission Contract derivation

| Attribute | Resolution |
|---|---|
| Architectural decision | Governance owns the immutable Authority Record as the sole mission-level authority. EMP owns deterministic materialization of one immutable Mission Contract revision from one Authority Record revision. The contract represents authority but never grants it. |
| Rationale | Separating the governance grant from its execution-facing representation prevents circular authority and editable mission-description drift. |
| Alternatives considered | Mission Contract as authority; Work Registry as authority; independently editable contract plus authority record; one derived contract per Authority Record revision. |
| Rejected alternatives | Contract-as-authority and registry-as-authority conflate representation or planning with approval. Independent editing creates two owners. |
| Affected subsystems | Governance, Authority Record, EMP, Mission Contract, WOP, Authority Resolution, EOS. |
| Authoritative owners | Governance owns the Decision, Authority Record, supersession, and revocation. EMP owns derivation execution and derived artifact discovery. |
| Lifecycle impacts | Authority Record revisions are immutable successors; effectiveness is derived. Mission Contract revisions are immutable derivations and have no independent authority lifecycle. |
| Implementation constraints | Canonical serialization; exact input and mapping digests; byte-identical regeneration; no uncaptured clock, randomness, environment, remote lookup, or mutable projection; authority-bearing fields derive only from the Authority Record. |
| Backward compatibility | Existing Mission Contract stores become generated projections, syntax-only inputs, fixtures, historical records, or are retired after consumer migration. |
| Future implementation | ADR-FI-001. |

### 14.2 ARCH-DR-002 — Resolved execution-authority context

| Attribute | Resolution |
|---|---|
| Architectural decision | The Authority Resolution Service produces the only canonical Resolved Execution and Authority Context (REAC). |
| Rationale | One provenance-preserving normalization boundary removes plural resolver outcomes without transferring fact ownership to the resolver. |
| Alternatives considered | Every consumer resolves independently; Authority Graph owns production resolution; a compatibility adapter chooses among outcomes; one canonical resolver. |
| Rejected alternatives | Independent resolution and outcome selection preserve disagreement. An offline graph cannot become a terminal production authority. |
| Affected subsystems | Authority Record, owner publications, repository observation, WOP admission, Authority Resolution, PMA, Zeus EWI. |
| Authoritative owners | Source owners retain facts; Authority Resolution owns the immutable REAC artifact and derived effectiveness determinations. |
| Lifecycle impacts | REAC is an immutable evaluation result bound to exact inputs and evaluation revision, not a mutable lifecycle or execution grant. |
| Implementation constraints | Complete provenance, canonical digest, stable reason codes, ambiguity rejection, no raw-source re-resolution downstream. |
| Backward compatibility | Existing resolvers may run offline for comparison or syntax translation but cannot emit production allow. |
| Future implementation | ADR-FI-003. |

### 14.3 ARCH-DR-003 — Terminal initiation decision

| Attribute | Resolution |
|---|---|
| Architectural decision | Zeus Engineering Work Initiation (EWI) is the sole terminal initiation owner and emits exactly `ALLOW`, `DENY`, or `STOP`. |
| Rationale | A single final composition point makes execution reachability, denial, and fail-closed behavior testable. |
| Alternatives considered | PMA terminal decision; dispatcher decision; agent-local decision; plural decisions; one Zeus EWI decision. |
| Rejected alternatives | PMA would conflate gate narrowing with execution. Dispatcher or agent ownership permits bypass. Plural decisions reintroduce ambiguity. |
| Affected subsystems | Zeus, Authority Resolution, PMA, admission services, resource coordinator, dispatcher, execution agent. |
| Authoritative owners | Zeus EWI owns terminal initiation; upstream owners retain their source decisions. |
| Lifecycle impacts | EWI emits an immutable decision receipt bound to one attempt envelope; it does not alter Governance or Authority lifecycle. |
| Implementation constraints | No downstream reinterpretation of `DENY` or `STOP`; exact input digests; one reachable production entry; append-only receipt. |
| Backward compatibility | Legacy approval, next-action, and dispatcher allow paths are disabled, translated to non-authoritative predicates, or retired. |
| Future implementation | ADR-FI-005. |

### 14.4 ARCH-DR-004 — Progressive Mission Authority monotonicity

| Attribute | Resolution |
|---|---|
| Architectural decision | Progressive Mission Authority (PMA) may only preserve or narrow the REAC envelope and may never broaden authority or initiate execution. |
| Rationale | Progressive gates own ordering and eligibility, not governance authority or terminal execution. |
| Alternatives considered | PMA broadens authority; PMA independently authorizes; PMA is removed; PMA remains narrow-only. |
| Rejected alternatives | Broadening and independent authorization violate the authority chain. Removal discards qualified gate-order behavior. |
| Affected subsystems | PMA, Authority Resolution, Zeus EWI, Progressive gate records. |
| Authoritative owners | PMA owns only the immutable Progressive eligibility result; EWI owns initiation. |
| Lifecycle impacts | PMA consumes gate facts and emits a derived result; it does not add lifecycle states. |
| Implementation constraints | Set-containment proof for scope, actions, resources, and time; inability to prove monotonicity returns `STOP`. |
| Backward compatibility | Existing broad or terminal PMA behaviors are prohibited; narrow predicate logic may be retained behind the canonical interface. |
| Future implementation | ADR-FI-004. |

### 14.5 ARCH-DR-005 — Legacy and compatibility roles

| Attribute | Resolution |
|---|---|
| Architectural decision | Authority Graph is offline validation only; WOP compatibility is syntax-only; legacy approval and OA-02 lifecycle paths are fixtures or historical; PMCT predicates may be retained only behind canonical interfaces; no compatibility component is production-authoritative. |
| Rationale | Qualified logic can be reused without preserving competing owners or terminal paths. |
| Alternatives considered | Keep all live; delete immediately; choose legacy as canonical; isolate by explicit compatibility class. |
| Rejected alternatives | Keeping live preserves plural authority. Immediate deletion lacks consumer and recovery evidence. Legacy selection contradicts the assessed current path. |
| Affected subsystems | Authority Graph, WOP compatibility, legacy approval, OA-02 lifecycle, PMCT, test suites, Zeus. |
| Authoritative owners | Canonical components in Section 15 own production behavior; ADR-C-014 owns compatibility classification and migration evidence only. |
| Lifecycle impacts | Each compatibility item has `observed`, `bounded`, `consumer-free`, and `retired` evidence milestones, not an operational mission lifecycle. |
| Implementation constraints | No production `ALLOW`; no widening; explicit caller inventory; negative reachability tests; preserved historical fixtures. |
| Backward compatibility | Translation may preserve syntax and read compatibility until all named consumers move; semantic or authority fallback is forbidden. |
| Future implementation | ADR-FI-011 and ADR-FI-015. |

### 14.6 ARCH-DR-006 — Orthogonal state and lifecycle ownership

| Attribute | Resolution |
|---|---|
| Architectural decision | Governance, Authority effectiveness, EMP planning, Zeus execution, controlled-document lifecycle, publication, and EOS synchronization are separate owner domains. Copies are typed read-only projections. |
| Rationale | Orthogonality prevents repeated facts from becoming reverse-synchronized composite state. |
| Alternatives considered | One global mission state; mirrored writable state; newest-write wins; small owner-specific models plus derived predicates. |
| Rejected alternatives | Global state couples unrelated transitions. Writable mirrors and recency rules destroy ownership and deterministic recovery. |
| Affected subsystems | Governance, EMP, Zeus, controlled documents, publication, EOS, operator views. |
| Authoritative owners | The owner matrix in Section 8 and lifecycle matrix in Section 18 are exhaustive for this scope. |
| Lifecycle impacts | Governance uses `Proposed`, `Authorized`, `Revoked`; execution uses `Planned`, `Ready`, `Running`, `Blocked`, `Complete`, `Failed`; synchronization uses `Dirty`, `Pending`, `Reconciled`; other conditions are derived predicates or governed by existing document lifecycle. |
| Implementation constraints | One writer per fact; source revision and invalidation on projections; no inference across domains; reason codes instead of new composite states. |
| Backward compatibility | Duplicate state fields become projections, evidence, or are removed after consumer-complete migration. |
| Future implementation | ADR-FI-006. |

### 14.7 ARCH-DR-007 — Publication and EOS synchronization

| Attribute | Resolution |
|---|---|
| Architectural decision | Controlled publication first establishes the exact repository baseline. EOS later performs a separate, directional, idempotent synchronization from that frozen boundary and records reconciliation. |
| Rationale | Persistence and operational projection have different owners, failure modes, replay rules, and authority consequences. |
| Alternatives considered | Commit implies sync; EOS publishes; bidirectional newest-write reconciliation; separate ordered transactions. |
| Rejected alternatives | Implicit or EOS-owned publication conflates responsibilities. Bidirectional recency can overwrite authority. |
| Affected subsystems | Controlled-document framework, Git publication, publication registry, EOS, source owners. |
| Authoritative owners | Publication transaction and Git own publication identity; EOS owns synchronization transaction and projection checkpoint. |
| Lifecycle impacts | Publication and synchronization advance independently; neither changes controlled-document lifecycle without its authorized mechanism. |
| Implementation constraints | Exact-path manifest and digests; source-to-projection direction; idempotency key; partial-write detection; retry from source; immutable receipts. |
| Backward compatibility | Existing combined publish/sync commands must split internally or expose separate receipts without changing source ownership. |
| Future implementation | ADR-FI-007. |

### 14.8 ARCH-DR-008 — `engineering/execution/missions/` disposition

| Attribute | Resolution |
|---|---|
| Architectural decision | `engineering/execution/missions/` is a generated EMP discovery projection during migration and is retired when no consumer requires it. It is never an independently editable mission source. |
| Rationale | A generated projection preserves current discovery consumers while removing duplicate ownership. |
| Alternatives considered | Canonical store; second editable store; immediate deletion; generated projection then retirement. |
| Rejected alternatives | Canonical or editable retention competes with Authority Record and Mission Contract ownership. Immediate deletion lacks consumer evidence. |
| Affected subsystems | EMP, Mission Contract derivation, mission discovery, compatibility consumers, tests. |
| Authoritative owners | EMP owns generation; Authority Record owns authorized mission facts; EMP Work Registry owns planning facts. |
| Lifecycle impacts | Projection freshness is derived from source and generator revisions; it has no mission lifecycle. |
| Implementation constraints | Deterministic generation, source digest, read-only enforcement, drift detection, no reverse import after cutover. |
| Backward compatibility | Path and read schema may remain temporarily; writes fail and consumers migrate to canonical interfaces. |
| Future implementation | ADR-FI-008. |

### 14.9 ARCH-DR-009 — Repository cleanliness and remote freshness

| Attribute | Resolution |
|---|---|
| Architectural decision | Repository policy is phase-specific and deterministic: assessment/planning may use a dirty tree only with a complete inventory; admission/qualification bind an exact included boundary and prove unrelated dirt excluded; publication/cutover require clean-checkout reproduction of an exact commit; remote operations require authenticated remote identity and a captured fetch/freshness result. |
| Rationale | One universal “clean” predicate is either too weak for publication or unnecessarily blocks bounded review. |
| Alternatives considered | Always-clean rule; dirty-tree prohibition everywhere; operator judgment; phase-specific exact-boundary policy. |
| Rejected alternatives | Universal rules ignore phase risk. Operator judgment is not replayable. |
| Affected subsystems | Repository observation, EMP, WOP admission, Authority Resolution, EWI, qualification, publication. |
| Authoritative owners | Repository observation owns captured facts; the applicable Authority Record and phase policy own the required threshold; EWI enforces it. |
| Lifecycle impacts | Cleanliness and remote freshness are immutable observations with validity bounds, not lifecycle states. |
| Implementation constraints | Capture root, remote URL, branch, HEAD, upstream relation, status inventory, included paths, excluded dirt, observation time source, fetch result, and policy revision; unavailable required remote verification returns `STOP`. |
| Backward compatibility | Legacy boolean-clean checks may remain as derived display fields but cannot replace the full observation. |
| Future implementation | ADR-FI-009 and ADR-FI-015. |

### 14.10 ARCH-DR-010 — Authorization Bundle lifecycle

| Attribute | Resolution |
|---|---|
| Architectural decision | An Authorization Bundle is an immutable authenticated carrier of owner publications, produced by the designated publication assembler and selected by exact family, generation, applicability, subject, source revisions, validity, supersession, and revocation. It is not an authority object. |
| Rationale | A typed carrier supports existing publication generations without creating a second authority owner. |
| Alternatives considered | Bundle as execution grant; newest bundle wins; merge all bundles; exact applicable bundle with ambiguity failure. |
| Rejected alternatives | Grant semantics violate ADR-D-001 and ADR-D-013. Recency and merge rules can combine incompatible authority. |
| Affected subsystems | Authority publishers, bundle assembler, Authority Resolution, compatibility adapters. |
| Authoritative owners | Each source owner owns its fact; bundle assembler owns carrier integrity; Authority Resolution owns selection determination. |
| Lifecycle impacts | Bundle identity is immutable. Expiry, source revocation, or supersession make it inapplicable through evaluation; the bundle is not rewritten. |
| Implementation constraints | Signed or integrity-bound manifest, exact subject and purpose, closed input list, generation policy, no fallback on ambiguity. |
| Backward compatibility | Earlier bundle generations require explicit adapters and applicability rules; cross-generation field synthesis is forbidden. |
| Future implementation | ADR-FI-003. |

### 14.11 ARCH-DR-011 — Receipt taxonomy and substitution

| Attribute | Resolution |
|---|---|
| Architectural decision | The canonical receipt types are WOP Admission, mission Runtime Admission, Stage 1 Package Admission, Authority Resolution, EWI Initiation, Resource Reservation, Execution Completion, Qualification, Publication, and EOS Synchronization receipts. Each has a distinct schema, issuer, subject, purpose, input digest set, decision or result, and integrity field. |
| Rationale | Typed receipts preserve decision boundaries and prevent a successful result at one layer from satisfying another. |
| Alternatives considered | One generic receipt; filename-based inference; optional type fields; closed typed taxonomy with versioned extensions. |
| Rejected alternatives | Generic or inferred types permit cross-type substitution and obscure ownership. |
| Affected subsystems | WOP, mission Runtime, Stage 1, Authority Resolution, Zeus, resource coordinator, qualification, publication, EOS. |
| Authoritative owners | The service that makes the named decision owns its receipt; no receipt consumer may reissue it under another type. |
| Lifecycle impacts | Receipts are immutable outcomes. Correction creates a successor or a new attempt; no receipt transitions in place. |
| Implementation constraints | Type discriminator first; schema and issuer verification; exact subject/purpose binding; integrity before semantic evaluation; wrong type fails before content reuse. |
| Backward compatibility | Untyped legacy receipts require bounded type-specific adapters and cannot enter production if type or purpose is ambiguous. |
| Future implementation | ADR-FI-002 and ADR-FI-010. |

### 14.12 ARCH-DR-012 — PMCT operational role

| Attribute | Resolution |
|---|---|
| Architectural decision | PMCT has no standalone operational decision role. Reusable PMCT predicates may become pure libraries invoked behind PMA, Authority Resolution, or EWI contracts; the standalone executable is retired after consumer-complete evidence. |
| Rationale | Retaining tested predicates avoids waste while removing an overlapping decision owner. |
| Alternatives considered | Keep standalone PMCT; make PMCT terminal; delete all logic; retain pure predicates only. |
| Rejected alternatives | Standalone or terminal PMCT preserves plural authority. Immediate deletion discards potentially qualified logic without analysis. |
| Affected subsystems | PMCT, PMA, Authority Resolution, EWI, tests, compatibility boundary. |
| Authoritative owners | Calling canonical component owns the decision; PMCT-derived library code owns no decision or state. |
| Lifecycle impacts | The executable follows compatibility retirement evidence, not mission lifecycle. |
| Implementation constraints | Pure deterministic functions; typed inputs and outputs; no owner-source reads; no persistence; no `ALLOW`. |
| Backward compatibility | CLI may remain offline during migration with explicit non-production labeling and negative reachability tests. |
| Future implementation | ADR-FI-011. |

### 14.13 ARCH-DR-013 — EENS and future HNS boundary

| Attribute | Resolution |
|---|---|
| Architectural decision | EENS owns durable typed engineering events, ordered replay, consumer checkpoints, notification projection, and delivery status. Correlation policy, human workflow, broad routing, and future HNS behavior remain outside EENS Operational Alpha scope. |
| Rationale | Observation and notification are mature bounded capabilities but must not accumulate governance or orchestration. |
| Alternatives considered | EENS decides outcomes; fold EENS into Zeus; implement HNS now; retain bounded event/notification service. |
| Rejected alternatives | Decision ownership violates subsystem boundaries. Folding reduces independent durability. HNS expansion is not required for OA architecture. |
| Affected subsystems | EENS, Zeus, EMP, EOS, notification transports, future HNS. |
| Authoritative owners | Source systems own event facts; EENS owns durable event copies, ordering, checkpoints, and delivery status. |
| Lifecycle impacts | Event and delivery status do not transition mission, execution, authority, or synchronization state. |
| Implementation constraints | Idempotent event identity, ordered replay per declared stream, consumer checkpoints, secret isolation, no command or approval semantics. |
| Backward compatibility | Existing notification integrations remain if they consume EENS events; advanced routes are explicit deferrals. |
| Future implementation | ADR-FI-012. |

### 14.14 ARCH-DR-014 — Authority-publication generation applicability

| Attribute | Resolution |
|---|---|
| Architectural decision | Authority Resolution selects publications by declared authority family, schema generation, governed subject, scope, source owner, validity, freshness, supersession, and revocation. Exactly one applicable generation is required for each fact class. |
| Rationale | Explicit applicability prevents silent fallback or mixing across architecture generations. |
| Alternatives considered | Latest timestamp; preferred filesystem path; merge generations; exact rule-driven selection. |
| Rejected alternatives | Recency and paths are not authority. Merging can synthesize a grant no owner issued. |
| Affected subsystems | Authority publications, Authorization Bundles, Authority Resolution, compatibility adapters. |
| Authoritative owners | Source owner declares publication generation and applicability; Authority Resolution evaluates selection. |
| Lifecycle impacts | Applicability is evaluated from immutable publications and owner events; it is not a mutable selector state. |
| Implementation constraints | Closed generation registry for the active baseline, exact subject binding, ambiguity and unknown generation return `STOP`, selected-source provenance in REAC. |
| Backward compatibility | Legacy generations may be translated individually; no field-level cross-generation merge. |
| Future implementation | ADR-FI-003. |

### 14.15 ARCH-DR-015 — Architecture cutover evidence and rollback

| Attribute | Resolution |
|---|---|
| Architectural decision | Cutover requires consumer inventory, production call-graph proof, negative alternate-path tests, clean-checkout qualification, typed-interface conformance, deterministic replay, recovery tests, and evidence that compatibility paths cannot emit or widen authorization. |
| Rationale | Architectural intent is insufficient unless reachability and effect behavior prove one production path. |
| Alternatives considered | Declare cutover from documentation; feature flag without proof; immediate deletion; evidence-gated staged cutover. |
| Rejected alternatives | Documentation and flags do not prove reachability. Immediate deletion lacks recovery and consumer evidence. |
| Affected subsystems | All canonical and compatibility components, tests, publication, qualification. |
| Authoritative owners | Independent qualification owns cutover determination; Zeus owns dispatch-disabled enforcement until acceptance. |
| Lifecycle impacts | Cutover acceptance is separate from implementation, publication, commissioning, and declaration. |
| Implementation constraints | Exact candidate digest; preserved accepted lineage; zero alternate production entry points; rollback only before an unambiguously irreversible effect and only to a still-qualified, still-authorized baseline; afterward use forward recovery and reconciliation. |
| Backward compatibility | Compatibility remains non-authoritative until consumer-free evidence permits retirement; rollback cannot reactivate an authority path rejected by this ADR. |
| Future implementation | ADR-FI-015. |

### 14.16 ARCH-DR-016 — Admission-layer responsibilities

| Attribute | Resolution |
|---|---|
| Architectural decision | WOP Admission validates the immutable work package and qualification prerequisites; mission Runtime Admission validates mission, authority, repository, and Runtime binding; Stage 1 Admission validates the exact dispatch envelope, agent, environment, and reservation prerequisites. |
| Rationale | Layer-specific subjects prevent duplicated validation from becoming interchangeable authorization. |
| Alternatives considered | One admission service for all subjects; repeat every check at every layer; trust upstream filenames; typed layered decisions with shared pure validators. |
| Rejected alternatives | One service conflates owners. Repetition drifts. Filenames are not integrity or authority. |
| Affected subsystems | WOP, Authority Resolution, mission Runtime, Stage 1, EWI, dispatcher. |
| Authoritative owners | ADR-C-005 owns WOP Admission. ADR-C-008 owns distinct mission Runtime Admission and Stage 1 Admission boundaries. Shared validators own no admission outcome. |
| Lifecycle impacts | Admission receipts are immutable inputs to later decisions; failure does not mutate Authority or execution lifecycle. |
| Implementation constraints | Subject-specific schemas; exact upstream receipt bindings; common checks factored into pure versioned validators; no downstream substitution. |
| Backward compatibility | Legacy single admission outputs require explicit decomposition or fail closed if the layer cannot be proven. |
| Future implementation | ADR-FI-010. |

### 14.17 ARCH-DR-017 — No standard post-WOP authority object

| Attribute | Resolution |
|---|---|
| Architectural decision | For the current Zeus submission path, the standard chain ends with the identity-bound submitted WOP as work authority; admission, provider qualification, baseline, lifecycle, and explicit in-WOP gates lead directly to Zeus execution checks. There is no generic corrective, implementation, or Execution Grant. |
| Rationale | A routine second grant duplicates governance authority and creates another revocation, identity, and reconciliation problem. |
| Alternatives considered | Mandatory Execution Grant; optional implicit grant; WOP qualification as grant; no post-WOP authority object. |
| Rejected alternatives | Both grant variants create or hide a second authority object. Qualification evaluates conformity and is not approval. |
| Affected subsystems | Governance, WOP, Zeus EWI, admission, compatibility. |
| Authoritative owners | The operator-submitted WOP owns work scope; named control owners own validation predicates; EWI owns initiation only after those predicates pass. |
| Lifecycle impacts | No additional lifecycle state or transition is introduced. |
| Implementation constraints | Pre-dispatch revalidation of WOP identity, scope, conditions, receipts, freshness, claims, and environment; no delayed generic authorization artifact may be introduced without demonstrated need. |
| Backward compatibility | Existing Execution Grant representations become compatibility evidence or are ignored after explicit migration; they cannot be required by the canonical path. |
| Future implementation | ADR-FI-005. |

### 14.18 ARCH-DR-018 — Generalized resource claims and conflicts

| Attribute | Resolution |
|---|---|
| Architectural decision | Governed resources use typed claims with namespace, type, identity, access mode, effect class, scope, containment relation, and lease policy. Governance authorizes claims, WOP declares needs, EMP plans conflicts, and Zeus acquires fenced operational leases. |
| Rationale | A uniform identity and containment model covers repositories, infrastructure, services, hardware, environments, documentation, and future types without resource-specific control flow. |
| Alternatives considered | Repository-only keys; string tags; service-specific locks; extensible typed resource model. |
| Rejected alternatives | Repository-only and string models cannot express containment or future types. Per-service locks duplicate conflict semantics. |
| Affected subsystems | Governance, EMP, WOP, Zeus resource coordinator, EWI, recovery. |
| Authoritative owners | Authority Record owns permitted claim ceiling; WOP owns required declaration; Zeus resource coordinator owns leases and fencing. |
| Lifecycle impacts | Claim authorization is immutable; lease acquire/renew/release is operational state and never authority. |
| Implementation constraints | Unknown type or containment fails closed; deterministic conflict matrix; atomic acquisition for the declared set; fencing token on each effect. |
| Backward compatibility | Repository conflict keys map to typed repository claims during migration and are then removed from decision interfaces. |
| Future implementation | ADR-FI-013. |

### 14.19 ARCH-DR-019 — Subsystem responsibility boundaries

| Attribute | Resolution |
|---|---|
| Architectural decision | Governance owns policy, approval, authority, and audit; EMP owns mission planning; Zeus owns selection and execution orchestration; WOP owns immutable work packaging; independent qualification owns determinations; EENS owns events and notification; EOS owns synchronization and reconciliation. |
| Rationale | Explicit handoffs prevent Governance from orchestrating and prevent operational services from becoming authority. |
| Alternatives considered | Governance-orchestrated platform; monolithic Zeus; EMP dispatch; distributed ownership with typed handoffs. |
| Rejected alternatives | The first three conflate governance, planning, or orchestration and recreate duplicate ownership. |
| Affected subsystems | Every component in Section 15. |
| Authoritative owners | Section 8 owns the information matrix; Section 15 owns component responsibilities and prohibitions. |
| Lifecycle impacts | Each subsystem transitions only its domain; no completion, notification, or synchronization event implies another domain transition. |
| Implementation constraints | Typed interfaces, one producer per decision, no raw-source bypass, independent qualification, one terminal initiation path, conformance tests for prohibited responsibilities. |
| Backward compatibility | Existing overlapping functions are moved behind the owning interface, bounded as compatibility, or retired with evidence. |
| Future implementation | ADR-FI-016. |

### 14.20 ARCH-DR-020 — Recovery, replay, and horizontal scale

| Attribute | Resolution |
|---|---|
| Architectural decision | Every attempt binds exact authority, contract, WOP, candidate, EWI, lease, agent, policy, and idempotency identities. Recovery revalidates owners, resumes only from proven checkpoints, fences effects, stops on uncertainty, and uses atomic reservation plus quorum-safe leases for distributed workers. |
| Rationale | Durable identity and effect proof prevent duplicate effects, stale-authority resume, split brain, and projection drift without making recovery state authoritative. |
| Alternatives considered | Restart from latest local state; at-least-once blind retry; active-active without fencing; deterministic replay with revalidation and effect safety. |
| Rejected alternatives | Local recency, blind retry, and unfenced concurrency can repeat effects or continue without valid authority. |
| Affected subsystems | Zeus selector, EWI, resource coordinator, dispatcher, agent, evidence, qualification, EOS. |
| Authoritative owners | Zeus owns attempts and checkpoints; resource coordinator owns leases; effect provider or sealed effect record owns effect completion proof; EOS owns synchronization recovery only. |
| Lifecycle impacts | Resume continues the same attempt only when identities and checkpoint remain valid; otherwise a new attempt is created. `Complete` is not reopened. |
| Implementation constraints | Stable tie-breaking; atomic reservation; lease fencing; append-only intents/results; non-side-effecting replay by default; authority/freshness revalidation; quorum or fail closed; source-directed EOS retry. |
| Backward compatibility | Unfenced executors are limited to offline or read-only work until qualified; legacy checkpoints require exact identity migration or cannot resume. |
| Future implementation | ADR-FI-014. |

## 15. Canonical subsystem architecture

| ID | Subsystem or architectural component | Required responsibilities and owned outputs | Required inputs | Prohibited responsibilities |
|---|---|---|---|---|
| ADR-C-001 | Governance | policy; proposal disposition; Governance Decision; Authority Record issuance, supersession, revocation; audit lineage | proposal, policy, review and qualification evidence | planning, prioritization, mission selection, orchestration, execution, qualification determination, notification, synchronization |
| ADR-C-002 | Authority Record and effectiveness model | immutable mission authority; authorized scope and claims; lineage; derived effectiveness contract | Governance Decision and exact owner events | planning or execution state; contract derivation; Runtime mutation; projection-based repair |
| ADR-C-003 | EMP | mission inventory, priority, dependency graph, planning eligibility, Governance interaction, immutable candidate snapshot | Authority Record status, Work Registry, planning policy, outcomes | approval, authority issuance, terminal selection, dispatch, execution |
| ADR-C-004 | Mission Contract Deriver and Registry | deterministic materialization, immutable derived-contract identity, discovery, regeneration | exact Authority Record revision, schema and mapping revisions, declared immutable lookup artifacts | grant, revoke, widen, or independently edit authority-bearing mission facts |
| ADR-C-005 | WOP and Admission | immutable work package, completion criteria, WOP admission, qualification binding, typed package receipt | derived Mission Contract, work content, schemas, qualification criteria | mission authority, prioritization, Runtime selection, orchestration, evidence evaluation |
| ADR-C-006 | Authority Resolution Service | owner-publication selection, Authority Record effectiveness evaluation, canonical REAC and resolution receipt | exact owner publications, bundle, repository observation, contract, WOP and admission identities, policy | terminal initiation, fact ownership, authority widening, source mutation |
| ADR-C-007 | Progressive Mission Authority | gate ordering, prerequisite and evidence evaluation, monotonic eligibility result | REAC, gate state, accepted predecessors, evidence bindings | authority creation, broadening, terminal initiation, dispatch |
| ADR-C-008 | Zeus | deterministic candidate selection, mission Runtime and Stage 1 admission, EWI, bounded adaptation, reservation, dispatch, supervision, attempt/checkpoint/effect state, recovery, completion, evidence and qualification orchestration | EMP snapshot, contract, qualified WOP, REAC, PMA result, observations, leases | Governance decision, source planning mutation, qualification determination, notification transport, EOS synchronization |
| ADR-C-009 | Resource Coordination | deterministic conflict evaluation, atomic reservation, lease ownership, fencing tokens | authorized claims, WOP requirements, environment observation, attempt identity | authority issuance, mission selection, successful-effect inference |
| ADR-C-010 | Evidence and Independent Qualification | evidence identity and sealing; criterion evaluation; immutable qualification determination | execution evidence, exact criteria, candidate and policy identities | evidence rewriting, execution orchestration, authority issuance, automatic lifecycle transition |
| ADR-C-011 | EOS | directional synchronization, projection checkpoint, drift classification, idempotent reconciliation and receipt | frozen source boundary, synchronization policy, prior checkpoint | authority, approval, planning, selection, source publication, reverse inference from projection |
| ADR-C-012 | EENS | durable typed events, ordered replay, consumer checkpoints, notification projections and delivery status | source events and transport configuration | approval, authority, lifecycle, execution, qualification, synchronization decisions |
| ADR-C-013 | Controlled-document and Publication Framework | document identity/lifecycle under existing governance; exact-path inventory; commit/tag/publication identity; publication receipts and metadata | controlled content, applicable approval and publication authority, qualification evidence | runtime authority inference, EOS synchronization, implementation execution |
| ADR-C-014 | Compatibility Boundary | syntax translation, offline comparison, fixtures, historical preservation, consumer and retirement evidence | explicitly classified legacy input | production allow/deny ownership, authority widening, newest-result selection, hidden fallback |

The architecture intentionally treats Mission Contracts and Authority Records
as governed artifacts with producers, not autonomous decision services. It
treats the Engineering lifecycle as the composition of owner-specific
lifecycles in Section 18, not as another subsystem or global state machine.

## 16. Architectural invariants

Every conforming specification and implementation shall preserve these
invariants. Failure to prove an invariant at a decision boundary produces
`STOP` or prevents lifecycle advancement.

| ID | Family | Invariant |
|---|---|---|
| ADR-INV-AUTH-001 | Authority | Only an effective, exact Authority Record revision issued from an attributable Governance Decision supplies mission-level authority. |
| ADR-INV-AUTH-002 | Authority | A Mission Contract, WOP, receipt, queue, evidence file, notification, commit, lease, or projection never becomes authority. |
| ADR-INV-AUTH-003 | Authority | Authority Resolution is the only production owner of REAC, PMA is narrow-only, and Zeus EWI is the only terminal initiation owner. |
| ADR-INV-AUTH-004 | Authority | Every downstream envelope is a provable subset of its upstream scope, actions, resources, identities, effects, and time bounds. |
| ADR-INV-LIFE-001 | Lifecycle | Governance, planning, execution, controlled-document, publication, and synchronization transitions are owned and evaluated independently. |
| ADR-INV-LIFE-002 | Lifecycle | No event in one lifecycle implies a transition in another without the other lifecycle owner's explicit decision mechanism. |
| ADR-INV-LIFE-003 | Lifecycle | New states require a demonstrated distinction that cannot be represented by an existing state, reason code, predicate, evidence record, or successor revision. |
| ADR-INV-STATE-001 | State | Every authoritative fact has one permitted writer; all copies name their source, revision, derivation, and invalidation rule. |
| ADR-INV-STATE-002 | State | Derived predicates and projections are read-only and cannot be reverse-synchronized or promoted by recency. |
| ADR-INV-STATE-003 | State | Conflicting or ambiguous owner facts fail closed; Runtime components do not merge them by preference. |
| ADR-INV-SYNC-001 | Synchronization | EOS synchronizes only from an explicit authoritative source boundary toward a declared projection. |
| ADR-INV-SYNC-002 | Synchronization | Each synchronization transaction is idempotent, resumable, digest-bound, and records partial and final outcomes. |
| ADR-INV-SYNC-003 | Synchronization | EOS never issues, repairs, revokes, supersedes, or qualifies authority or another owner's fact. |
| ADR-INV-SYNC-004 | Synchronization | Reconciliation reports drift and applies only owner-authorized direction; ambiguous direction fails closed. |
| ADR-INV-PUB-001 | Publication | Publication binds an exact path inventory, bytes, digests, dependency order, repository identity, commit, and publication identifier. |
| ADR-INV-PUB-002 | Publication | Publication is reproducible from a clean checkout and is distinct from approval, activation, qualification, and EOS synchronization. |
| ADR-INV-PUB-003 | Publication | No unrelated, legacy, generated, or untracked path enters a publication without explicit classification and inclusion. |
| ADR-INV-REPLAY-001 | Replay | Deterministic replay uses captured canonical inputs, component and policy revisions, stable ordering, stable tie-breaking, and the original identity graph. |
| ADR-INV-REPLAY-002 | Replay | Replay is non-side-effecting by default; an effect may repeat only when the exact operation is explicitly idempotent and uses the same effect key. |
| ADR-INV-REPLAY-003 | Replay | Replay divergence is evidence and a stop condition; it never selects whichever result is newest. |
| ADR-INV-REPLAY-004 | Replay | Replaying derivation reproduces byte-identical Mission Contracts, candidate selection, authority resolution, and decision receipts from identical inputs. |
| ADR-INV-REC-001 | Recovery | Resume revalidates current authority, freshness, admission, resource lease, agent, and environment before any effect. |
| ADR-INV-REC-002 | Recovery | Only a checkpoint with proven identity and effect boundary may resume the same attempt; otherwise recovery creates a new attempt or stops. |
| ADR-INV-REC-003 | Recovery | An uncertain non-idempotent effect is never retried automatically; it requires reconciliation evidence. |
| ADR-INV-REC-004 | Recovery | Distributed workers require atomic reservation and fenced leases; partition, stale replica, conflicting checkpoint, or lost quorum fails closed. |
| ADR-INV-ADM-001 | Admission | WOP, mission Runtime, and Stage 1 admission have distinct subjects, schemas, owners, and receipts. |
| ADR-INV-ADM-002 | Admission | Receipt type, schema, issuer, integrity, subject, purpose, and input bindings validate before semantic reuse. |
| ADR-INV-ADM-003 | Admission | A receipt of one type cannot satisfy another type, even when fields overlap. |
| ADR-INV-ADM-004 | Admission | Admission never widens the effective Authority Record or substitutes for EWI. |
| ADR-INV-COMP-001 | Compatibility | No compatibility component can emit production `ALLOW`, widen an envelope, or become an owner through fallback. |
| ADR-INV-COMP-002 | Compatibility | Each compatibility path has an explicit class, consumer boundary, source and output schemas, authority limit, and retirement evidence. |
| ADR-INV-COMP-003 | Compatibility | Removal requires consumer-complete, reachability, regression, recovery, and historical-preservation evidence. |

## 17. Interaction architecture

### 17.1 Canonical interfaces

Interface names identify architecture contracts, not required transport or
process boundaries.

| Interface | Producer | Consumer | Required input binding | Output | Failure boundary |
|---|---|---|---|---|---|
| `GOVERNANCE-DECIDE` | ADR-C-001 | ADR-C-002 | proposal, policy revision, reviewer evidence, principal identity | Governance Decision and Authority Record revision | reject or no record; never partial authority |
| `MISSION-CONTRACT-DERIVE` | ADR-C-004 | ADR-C-003, ADR-C-005, ADR-C-006 | Authority Record, schema, mapping, immutable lookup digests | byte-reproducible Mission Contract and derivation manifest | no artifact on ambiguity or nondeterminism |
| `EMP-CANDIDATES` | ADR-C-003 | ADR-C-008 | Work Registry revision, dependency and priority policy, eligible Authority Record identities | immutable ordered snapshot and digest | no selection from partial snapshot |
| `WOP-ADMIT` | ADR-C-005 | ADR-C-006, ADR-C-008 | contract, exact WOP bytes, schema, qualification binding | typed WOP Admission receipt | rejected package remains immutable |
| `AUTHORITY-RESOLVE` | ADR-C-006 | ADR-C-007, ADR-C-008 | exact owner facts, bundle selection, observations, contract, WOP and receipts | REAC and resolution receipt | `STOP` with provenance; no partial context |
| `PMA-NARROW` | ADR-C-007 | ADR-C-008 | REAC, gate state, evidence and prerequisite identities | monotonic eligibility result | block or `STOP`; never widen |
| `EWI-DECIDE` | ADR-C-008 | ADR-C-009 and Zeus execution supervisor | REAC, PMA result if applicable, admission receipts, observations, claims, agent and policy | terminal initiation receipt | `DENY` or `STOP`; no reservation |
| `RESOURCE-RESERVE` | ADR-C-009 | ADR-C-008 | EWI envelope, full claim set, attempt identity | atomic reservation, leases, fencing tokens | all-or-none failure |
| `ZEUS-EXECUTE` | ADR-C-008 | execution agent and ADR-C-010 | exact attempt envelope, WOP, leases, checkpoint | effect intents/results, checkpoints, completion, evidence | blocked or failed attempt; no authority mutation |
| `QUALIFY` | ADR-C-010 | EWI, acceptance, lifecycle consumers | sealed evidence, exact criteria and candidate identity | immutable qualification receipt | fail determination; evidence unchanged |
| `PUBLISH` | ADR-C-013 | Git boundary, registries, ADR-C-011 | approved exact inventory, dependency order, qualification, publication authority | commit/tag or publication identity, metadata and receipt | recoverable or failed transaction; no implicit sync |
| `EOS-SYNC` | ADR-C-011 | declared operational projection | frozen published boundary, mapping, checkpoint, idempotency key | projection, checkpoint and reconciliation receipt | partial/pending transaction; source unchanged |
| `EENS-EVENT` | source owner | ADR-C-012 and consumers | event identity, source revision, type, payload digest, ordering key | durable event, delivery projection and checkpoint | delivery failure only; source decision unchanged |

All interface outputs use canonical serialization, stable type and schema
identifiers, producer identity, subject and purpose binding, input digests,
policy or algorithm revision, result or reason code, creation sequence, and
integrity data. Transport retries use the same idempotency identity.

### 17.2 Authority and execution flow

```text
Governance proposal
  -> GOVERNANCE-DECIDE
  -> exact Authority Record revision
  -> MISSION-CONTRACT-DERIVE
  -> derived Mission Contract
  -> WOP-ADMIT and independent WOP qualification
  -> EMP-CANDIDATES
  -> Zeus selects one candidate
  -> AUTHORITY-RESOLVE
  -> PMA-NARROW when Progressive
  -> EWI-DECIDE
  -> RESOURCE-RESERVE
  -> ZEUS-EXECUTE
  -> evidence and QUALIFY
  -> owner-specific completion and reconciliation
```

The selected candidate binds to, but does not interrupt or replace, the
authority chain. Any identity mismatch returns to the owning boundary rather
than being repaired downstream.

### 17.3 Data and event flow

Authoritative data moves only through typed read interfaces. Derived artifacts
carry source digests. Zeus execution emits evidence and source events; it does
not directly mutate EMP planning, Governance, EOS projections, EENS delivery
state, or independent qualification. Owners consume the event or receipt and
decide their own transition.

```text
Owner fact -> immutable interface artifact -> consumer decision
                                         \-> EENS durable observation
```

EENS ordering and delivery are observational. Missing or delayed notification
cannot change the source decision.

### 17.4 Synchronization flow

```text
frozen published source boundary
  -> EOS validates source identity and mapping
  -> EOS creates or resumes one idempotent transaction
  -> projection is written
  -> read-back digest is compared
  -> checkpoint and reconciliation receipt are appended
```

Drift in an owned source is repaired only by its owner. Drift in a projection
is repaired from the source. When direction or ownership is ambiguous, EOS
reports and stops.

### 17.5 Recovery flow

```text
interruption detected
  -> load exact attempt and last sealed checkpoint
  -> re-read declared owners
  -> revalidate Authority Record, REAC freshness, admissions and policy
  -> reconcile uncertain effects
  -> reacquire atomically fenced resources
  -> resume same attempt only if identity and effect proof remain valid
  -> otherwise stop or create a new attempt
```

An agent-local file, newest checkpoint, or synchronized projection cannot
override a sealed attempt record.

### 17.6 Publication flow

```text
exact candidate inventory
  -> dependency and exclusion review
  -> clean-checkout qualification
  -> controlled approval and publication authority, when applicable
  -> immutable publication transaction
  -> Git/publication identity and metadata
  -> clean-checkout reproduction
  -> optional separately invoked EOS synchronization
```

This flow defines architectural order only. It does not grant publication,
approval, synchronization, or implementation authority.

## 18. Orthogonal lifecycle and state model

| Domain | Owner | Canonical states or facts | Transition or evaluation rule | Prohibited coupling |
|---|---|---|---|---|
| Governance | Governance | `Proposed`, `Authorized`, `Revoked` | attributable Governance Decision or revocation event | execution or sync result changes Governance |
| Authority | exact Authority Record plus Authority Resolution evaluator | immutable revision; derived `effective` / `not effective` with reason | recompute from integrity, approval lineage, applicability, validity, qualification, supersession and revocation | mutable effectiveness lifecycle or projection repair |
| Mission planning | EMP | inventory membership, priority, dependency satisfaction, planning eligibility | EMP policy over exact Work Registry and owner facts | priority implies selection or authority |
| Execution | Zeus | `Planned`, `Ready`, `Running`, `Blocked`, `Complete`, `Failed` | `Planned -> Ready -> Running`; `Running -> Blocked|Complete|Failed`; `Blocked -> Ready|Failed`; a retry after terminal state creates a new attempt | execution result revokes authority or reconciles sync |
| Controlled document | applicable controlled-document lifecycle owner | lifecycle defined by superior controlled-document standards | only its authorized lifecycle mechanism | Git persistence or ADR content implies activation |
| Publication | publication transaction owner | immutable input freeze, append-only operation outcomes, final transaction result | procedure-owned transaction; correction is successor or recovery output | publication implies approval, activation, or EOS sync |
| Synchronization | EOS | `Dirty`, `Pending`, `Reconciled` | source/projection digest comparison and idempotent transaction | synchronized projection modifies owner fact |

Readiness, freshness, admission success, gate eligibility, reservation
availability, notification delivery, and qualification are typed decisions or
predicates, not extra execution states. The overall Engineering lifecycle is
the observed tuple of these independent domains. No component may serialize
that tuple into a new writable “global mission state.”

## 19. Future implementation architecture

These units are traceability targets for future specifications and bounded
implementation work. They do not authorize implementation. Dependency order
is derived from the ARCH Decision Request DAG.

| ID | Future implementation unit | Architectural scope | Prerequisites | Required exit evidence |
|---|---|---|---|---|
| ADR-FI-001 | Authority Record and Mission Contract derivation | schemas, Governance issuance lineage, EMP deterministic derivation and registry | ADR-D-001, ADR-D-008, ADR-D-015 | byte-identical derivation; mutation rejection; revocation/supersession tests |
| ADR-FI-002 | Immutable WOP and qualification binding | WOP identity, admission, immutable qualification inputs | ADR-FI-001 | package mutation rejection; qualification independence |
| ADR-FI-003 | Authority publication selection and REAC | Authorization Bundle carrier, generation applicability, effectiveness and REAC | ADR-FI-001, ADR-FI-006, ADR-FI-016 | ambiguity/freshness/revocation matrix; deterministic REAC replay |
| ADR-FI-004 | Narrow-only PMA | monotonic gate evaluation | ADR-FI-003, ADR-FI-016 | property tests proving no widening or initiation |
| ADR-FI-005 | Zeus EWI terminal boundary | sole terminal result and no Execution Grant | ADR-FI-002 through ADR-FI-004, ADR-FI-009, ADR-FI-010, ADR-FI-013 | one reachable entry; negative bypass tests; exact receipt binding |
| ADR-FI-006 | State owners and projections | owner declarations, derived predicates, projection invalidation | ADR-FI-001 | drift, stale projection, and reverse-sync rejection |
| ADR-FI-007 | Publication and EOS separation | exact publication transaction and directional synchronization | ADR-FI-006, ADR-FI-016 | clean reproduction; idempotent sync; source-preservation proof |
| ADR-FI-008 | Mission-description convergence | generated execution-mission projection and consumer migration | ADR-FI-001, ADR-FI-016 | read-only enforcement; zero independent writers; consumer inventory |
| ADR-FI-009 | Repository observation policy | phase-specific cleanliness and remote freshness | ADR-FI-006 | deterministic observation fixtures and fail-closed remote tests |
| ADR-FI-010 | Typed receipt and admission layers | receipt taxonomy; WOP, Runtime, Stage 1 boundaries | ADR-FI-002, ADR-FI-003, ADR-FI-016 | cross-type substitution negatives; exact subject binding |
| ADR-FI-011 | Compatibility and PMCT retirement | compatibility classes, pure predicate extraction, consumer retirement | ADR-FI-003 through ADR-FI-005, ADR-FI-010 | production reachability negative; preserved fixtures; consumer-free proof |
| ADR-FI-012 | EENS bounded integration | events, replay, checkpoints, delivery only | ADR-FI-016 | idempotency/order tests; decision non-interference |
| ADR-FI-013 | Generalized resources | claim registry, conflict matrix, atomic lease and fencing | ADR-FI-001, ADR-FI-006, ADR-FI-016 | type extension, containment, conflict, lease-loss and fencing tests |
| ADR-FI-014 | Recovery, replay, and scale | attempts, checkpoints, effect fencing, deterministic selection, distributed safety | ADR-FI-003, ADR-FI-005 through ADR-FI-007, ADR-FI-010, ADR-FI-013 | reboot, interruption, uncertain effect, duplicate dispatch, partition, stale state and replay evidence |
| ADR-FI-015 | Architecture cutover qualification | alternate-path elimination, compatibility authority negatives, rollback boundary | ADR-FI-001 through ADR-FI-014 | clean exact candidate; end-to-end proof; zero alternate authorizers |
| ADR-FI-016 | Subsystem interface conformance | typed handoffs and prohibited-responsibility checks across all components | ADR-FI-001, ADR-FI-006 | component contract tests and ownership audit; prerequisite for all cross-subsystem units |

`ADR-FI-016` begins with interface specifications and then remains a
cross-cutting conformance obligation. It does not imply that implementation
may begin before this Draft is separately reviewed, approved, activated, and
translated into a reconciled specification.

## 20. Bidirectional architecture traceability

### 20.1 Finding-to-implementation chains

| ARCH finding | Engineering recommendation | Decision Request | ADR decision | Architectural component | Future implementation |
|---|---|---|---|---|---|
| ARCH-F-001 | ARCH-REC-001 | ARCH-DR-004 | ADR-D-005 | ADR-C-007 | ADR-FI-004, ADR-FI-015 |
| ARCH-F-002 | ARCH-REC-001, ARCH-REC-007 | ARCH-DR-002 through ARCH-DR-004 | ADR-D-004 through ADR-D-006 | ADR-C-006 through ADR-C-008 | ADR-FI-003 through ADR-FI-005 |
| ARCH-F-003 | ARCH-REC-007 | ARCH-DR-002 through ARCH-DR-005; ARCH-DR-010; ARCH-DR-014; ARCH-DR-016, ARCH-DR-017, ARCH-DR-019 | ADR-D-003 through ADR-D-007, ADR-D-012, ADR-D-013, ADR-D-015 | ADR-C-002, ADR-C-006 through ADR-C-008, ADR-C-014 | ADR-FI-003 through ADR-FI-005, ADR-FI-010, ADR-FI-011, ADR-FI-016 |
| ARCH-F-004 | ARCH-REC-009 | ARCH-DR-001, ARCH-DR-008 | ADR-D-001, ADR-D-008, ADR-D-012 | ADR-C-001 through ADR-C-004, ADR-C-014 | ADR-FI-001, ADR-FI-008 |
| ARCH-F-005 | ARCH-REC-004 | ARCH-DR-005, ARCH-DR-012, ARCH-DR-015 | ADR-D-012 | ADR-C-014 | ADR-FI-011, ADR-FI-015 |
| ARCH-F-006 | ARCH-REC-005, ARCH-REC-009 | ARCH-DR-006, ARCH-DR-018 through ARCH-DR-020 | ADR-D-008, ADR-D-014 through ADR-D-016 | ADR-C-001, ADR-C-003, ADR-C-008, ADR-C-009, ADR-C-011 | ADR-FI-006, ADR-FI-013, ADR-FI-014, ADR-FI-016 |
| ARCH-F-007 | ARCH-REC-002, ARCH-REC-003, ARCH-REC-008 | ARCH-DR-007, ARCH-DR-009, ARCH-DR-015 | ADR-D-010, ADR-D-012 | ADR-C-011, ADR-C-013, ADR-C-014 | ADR-FI-007, ADR-FI-009, ADR-FI-015 |
| ARCH-F-008 | ARCH-REC-003 | ARCH-DR-009, ARCH-DR-015, ARCH-DR-016 | ADR-D-002, ADR-D-004, ADR-D-006, ADR-D-012 | ADR-C-005, ADR-C-006, ADR-C-008, ADR-C-010, ADR-C-013 | ADR-FI-002, ADR-FI-009, ADR-FI-010, ADR-FI-015 |
| ARCH-F-009 | ARCH-REC-009 | ARCH-DR-006, ARCH-DR-019 | ADR-D-008, ADR-D-015 | ADR-C-001 through ADR-C-014 | ADR-FI-006, ADR-FI-016 |
| ARCH-F-010 | ARCH-REC-007 | ARCH-DR-013, ARCH-DR-019 | ADR-D-011, ADR-D-015 | ADR-C-012 | ADR-FI-012, ADR-FI-016 |
| ARCH-F-011 | ARCH-REC-007 | ARCH-DR-019, ARCH-DR-020 | ADR-D-007, ADR-D-015, ADR-D-016 | ADR-C-008 through ADR-C-012 | ADR-FI-014, ADR-FI-016 |
| ARCH-F-012 | ARCH-REC-002, ARCH-REC-003, ARCH-REC-008 | ARCH-DR-009, ARCH-DR-015 | ADR-D-003, ADR-D-004, ADR-D-006, ADR-D-012 | ADR-C-006, ADR-C-008, ADR-C-013, ADR-C-014 | ADR-FI-009, ADR-FI-015 |
| ARCH-F-013 | ARCH-REC-004, ARCH-REC-006 | ARCH-DR-005, ARCH-DR-015 | ADR-D-012 | ADR-C-014 | ADR-FI-011, ADR-FI-015 |

### 20.2 Risk disposition

| ARCH risk | Architectural disposition |
|---|---|
| ARCH-RISK-001 | ARCH-DR-002 through ARCH-DR-005 and ARCH-DR-014; one REAC, narrow-only PMA, one EWI, exact generation selection |
| ARCH-RISK-002 | ARCH-DR-009 and ARCH-DR-015; phase policy and clean exact cutover proof |
| ARCH-RISK-003 | ARCH-DR-005, ARCH-DR-012, ARCH-DR-015; bounded compatibility and consumer-complete retirement |
| ARCH-RISK-004 | ARCH-DR-001 and ARCH-DR-008; Authority Record source plus derived Mission Contract and generated projection |
| ARCH-RISK-005 | ARCH-DR-007; publication precedes separate EOS synchronization |
| ARCH-RISK-006 | ARCH-DR-006 and ARCH-DR-020; one writer, projection direction, checkpoint and stale-owner recovery |
| ARCH-RISK-007 | ARCH-DR-009 and ARCH-DR-015; clean candidate and end-to-end cutover qualification |
| ARCH-RISK-008 | ARCH-DR-006 and ARCH-DR-019; explicit owner, lifecycle, and subsystem boundaries |
| ARCH-RISK-009 | ARCH-DR-004 and ARCH-DR-015; gate narrowing and separate cutover acceptance |
| ARCH-RISK-010 | ARCH-DR-010, ARCH-DR-011, ARCH-DR-016; exact bundle generation and non-substitutable typed receipts |
| ARCH-RISK-011 | ARCH-DR-009 and ARCH-DR-015; complete inventory and exact publication exclusion |
| ARCH-RISK-012 | No architecture selection is required. The controlled-document semantic-profile gap remains an explicit framework deferral outside this ADR. |
| ARCH-RISK-013 | ARCH-DR-015 and ARCH-DR-020; protected dispatch evidence, recovery, and effect safety before commissioning |
| ARCH-RISK-014 | ARCH-DR-019; evidence producers remain separate while typed discovery is a cross-subsystem contract |
| ARCH-RISK-015 | ARCH-DR-020; bound attempt identity, fencing, checkpoint proof, revalidation, and distributed fail-closed behavior |

### 20.3 Decision Request coverage

Section 14's twenty-row matrix is the forward index from each Decision
Request to its exact resolution section, decision, component, and Future
Implementation unit. Each Section 14 resolution also traces backward to one
Decision Request and records rationale, alternatives, owners, lifecycle,
constraints, and compatibility. Therefore no Decision Request is orphaned or
resolved only by inference.

### 20.4 Reverse component traceability

| Component | Decisions and Decision Requests | Future implementation |
|---|---|---|
| ADR-C-001 Governance | ADR-D-001, ADR-D-013, ADR-D-015; ARCH-DR-001, ARCH-DR-006, ARCH-DR-017, ARCH-DR-019 | ADR-FI-001, ADR-FI-006, ADR-FI-016 |
| ADR-C-002 Authority model | ADR-D-001, ADR-D-003, ADR-D-004; ARCH-DR-001, ARCH-DR-002 | ADR-FI-001, ADR-FI-003 |
| ADR-C-003 EMP | ADR-D-001, ADR-D-007, ADR-D-015; ARCH-DR-001, ARCH-DR-006, ARCH-DR-008, ARCH-DR-019 | ADR-FI-001, ADR-FI-006, ADR-FI-008, ADR-FI-016 |
| ADR-C-004 Mission Contract | ADR-D-001; ARCH-DR-001, ARCH-DR-008 | ADR-FI-001, ADR-FI-008 |
| ADR-C-005 WOP | ADR-D-002, ADR-D-009; ARCH-DR-011, ARCH-DR-016 | ADR-FI-002, ADR-FI-010 |
| ADR-C-006 Authority Resolution | ADR-D-003, ADR-D-004; ARCH-DR-002, ARCH-DR-009, ARCH-DR-010, ARCH-DR-014, ARCH-DR-016 | ADR-FI-003, ADR-FI-009, ADR-FI-010 |
| ADR-C-007 PMA | ADR-D-005; ARCH-DR-004, ARCH-DR-012 | ADR-FI-004, ADR-FI-011 |
| ADR-C-008 Zeus | ADR-D-006 through ADR-D-009, ADR-D-013, ADR-D-015, ADR-D-016; ARCH-DR-003, ARCH-DR-004, ARCH-DR-006, ARCH-DR-009, ARCH-DR-011, ARCH-DR-015 through ARCH-DR-017, ARCH-DR-019, ARCH-DR-020 | ADR-FI-005, ADR-FI-006, ADR-FI-009, ADR-FI-010, ADR-FI-014 through ADR-FI-016 |
| ADR-C-009 Resource Coordination | ADR-D-014, ADR-D-016; ARCH-DR-018, ARCH-DR-020 | ADR-FI-013, ADR-FI-014 |
| ADR-C-010 Evidence and Qualification | ADR-D-009; ARCH-DR-011, ARCH-DR-015, ARCH-DR-019 | ADR-FI-002, ADR-FI-010, ADR-FI-015, ADR-FI-016 |
| ADR-C-011 EOS | ADR-D-010, ADR-D-015, ADR-D-016; ARCH-DR-006, ARCH-DR-007, ARCH-DR-019, ARCH-DR-020 | ADR-FI-006, ADR-FI-007, ADR-FI-014, ADR-FI-016 |
| ADR-C-012 EENS | ADR-D-011, ADR-D-015; ARCH-DR-013, ARCH-DR-019 | ADR-FI-012, ADR-FI-016 |
| ADR-C-013 Controlled documents and publication | ADR-D-010; ARCH-DR-007, ARCH-DR-009, ARCH-DR-015 | ADR-FI-007, ADR-FI-009, ADR-FI-015 |
| ADR-C-014 Compatibility | ADR-D-012; ARCH-DR-005, ARCH-DR-008, ARCH-DR-010, ARCH-DR-012, ARCH-DR-014, ARCH-DR-015 | ADR-FI-008, ADR-FI-011, ADR-FI-015 |

### 20.5 Downstream traceability

`SPEC-0002` Draft 1.2 remains a read-only downstream reference during this
development. It already traces ADR-D-001 through ADR-D-016, but it shall be
reconciled against the complete Draft 1.3 ownership, interface, invariant,
receipt, lifecycle, and Future Implementation architecture before it can
claim conformance to this revision. That reconciliation may add technical
requirements; it may not reopen an architectural answer without revising this
ADR through controlled review.

## 21. Architecture completion determination

### 21.1 ARCH-0001 completion-criteria mapping

| ARCH-0001 criterion | ADR-0001 evidence |
|---|---|
| all Decision Requests resolved with rationale | Sections 14.1 through 14.20 |
| architectural assumptions | Section 4.1 |
| architectural invariants | Section 16 |
| authoritative ownership boundaries | Sections 8 and 15 |
| authority derivation | ADR-D-001, ADR-D-003, ADR-D-004; Sections 14.1, 14.2 |
| Mission Contract derivation | ADR-D-001; Sections 14.1, 15, 17.1 |
| authoritative and derived-state ownership | Section 8 |
| lifecycle ownership | ADR-D-015; Section 18 |
| failure boundaries | Section 17.1 and ADR-INV families |
| recovery guarantees | ADR-D-016; Sections 14.20, 16, 17.5 |
| synchronization guarantees | ADR-D-010, ADR-D-016; Sections 14.7, 16, 17.4 |
| replay guarantees | ADR-D-001, ADR-D-016; Sections 14.20 and 16 |
| compatibility strategy | ADR-D-012; Sections 10, 14.5, 14.8, 14.12, 14.15 |
| migration strategy | Section 10 and ADR-FI-001 through ADR-FI-016 |
| rollback boundaries | Section 14.15 |
| implementation constraints | Sections 14, 16, 17, and 19 |
| prohibited responsibilities | Sections 15 and 16 |
| decision traceability | Sections 14 and 20 |
| completeness evidence | this matrix and the HF-001 validation evidence |

### 21.2 Internal-consistency determination

The architecture is internally consistent at the document level because:

1. Governance is the only issuer and revoker of mission authority.
2. Derived Mission Contracts, WOPs, qualifications, receipts, leases, events,
   publications, and projections are explicitly non-authoritative.
3. Authority Resolution, PMA, and EWI have distinct resolve, narrow, and
   terminal-decision roles.
4. The ownership matrix assigns one writer for every fact needed by
   Operational Alpha.
5. State models are orthogonal and no composite mission lifecycle exists.
6. Publication and EOS synchronization have separate owners and transactions.
7. Typed admission receipts cannot substitute across decision layers.
8. Recovery, replay, and horizontal scale preserve exact identity, authority,
   leases, effect safety, and source-directed synchronization.
9. Compatibility paths cannot authorize and have evidence-gated retirement.
10. Every ARCH Decision Request, finding, recommendation, and risk has an
    explicit disposition or bounded non-architectural deferral.

No architectural question required for Operational Alpha remains unanswered
in this Draft. Section 12 defers implementation technology or future-scope
extensions within decided invariants; those entries are not unresolved
ownership, authority, lifecycle, recovery, or interaction decisions.

### 21.3 Lifecycle and implementation boundary

This Draft is content-complete but remains `Draft`, `Pending` approval, and
`Pending` persistence. It does not activate the architecture, supersede an
Active record, reconcile Runtime state, authorize implementation, approve a
publication, or permit dispatch. Controlled review, approval, activation,
SPEC-0002 reconciliation, bounded implementation authority, qualification,
publication, commissioning, and declaration remain separate operations.

## 22. Revision history

| Version | Date | Lifecycle | Description |
|---|---|---|---|
| 1.0 | 2026-07-30 | Draft | Recorded the proposed layered Zeus architecture, canonical ownership, narrow-only authority composition, sole terminal initiation decision, migration sequence, consequences, and deferrals derived from ARCH-0001. |
| 1.1 | 2026-07-30 | Draft | Incorporated architecture review recommendations by establishing the Authority Record above the derived Mission Contract, removing Execution Grant from the standard path, generalizing resource conflicts, separating Governance from EMP/Zeus/WOP/EENS/EOS responsibilities, and adopting minimal orthogonal Governance, execution, and synchronization states. |
| 1.2 | 2026-07-30 | Draft | Refined Authority Record lineage and effectiveness, deterministic Mission Contract derivation, EMP/Zeus ownership, EOS non-authority, orthogonal state dimensions, interruption recovery, duplicate-effect prevention, deterministic autonomous selection, distributed safety, and horizontal-scaling invariants without adding authority objects or lifecycle states. |
| 1.3 | 2026-07-30 | Draft | Resolved all twenty ARCH-0001 Draft 1.6 Decision Requests with explicit rationale, alternatives, ownership, lifecycle, implementation, and compatibility effects; established complete subsystem contracts, ownership, invariants, interaction flows, orthogonal state models, Future Implementation units, and bidirectional assessment-to-implementation traceability. |
