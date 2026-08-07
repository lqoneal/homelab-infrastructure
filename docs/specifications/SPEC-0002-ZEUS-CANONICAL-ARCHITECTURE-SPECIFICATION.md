---
document_id: SPEC-0002
title: Zeus Canonical Architecture Specification
version: 1.4
status: Draft
owner: Homelab Infrastructure
created: 2026-07-30
last_updated: 2026-08-07
phase: Zeus Operational Alpha
domain: Engineering Architecture
classification: Engineering Specification
predecessor_revision: SPEC-0002@1.3
successor_revision: null
approval_status: Pending
approval_authority: null
approval_reference: null
approval_date: null
persistence_status: Pending
source_of_truth: true
information_scope: Zeus component, repository, runtime, authority, lifecycle, evidence, publication, synchronization, notification, interface, state, and recovery architecture
declared_deferrals:
  - cross-project-mission-federation
  - distributed-dispatch-implementation-topology
  - advanced-notification-routing
  - general-authority-topology-registry
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
  - type: implements
    target: ADR-0001
  - type: related_to
    target: ARCH-0001
  - type: related_to
    target: EDR-0002
  - type: related_to
    target: EDR-0003
  - type: related_to
    target: EMP-0001
  - type: related_to
    target: SPEC-0005
  - type: related_to
    target: SPEC-0006
  - type: related_to
    target: SPEC-0009
  - type: related_to
    target: SPEC-0011
  - type: related_to
    target: SPEC-0012
  - type: related_to
    target: SPEC-0013
  - type: indexed_by
    target: DOC-0001
tags:
  - zeus
  - architecture
  - authority
  - runtime
  - execution
  - operational-alpha
---

# Zeus Canonical Architecture Specification

## 1. Purpose

This specification defines the proposed canonical technical architecture for
Zeus. It translates the decisions in `ADR-0001` Draft 1.3 into component, ownership,
repository, runtime, authority, lifecycle, evidence, publication,
synchronization, notification, interface, state, and recovery requirements.

This Draft is an implementation reference candidate. It does not activate
runtime behavior, authorize implementation, approve migration, enable
dispatch, alter accepted gate state, or supersede an Active specification.
Future work shall reference an exact approved and applicable revision before
treating these requirements as operational.

## 2. Scope

### 2.1 In scope

- conversion of operator intent into a Governance Decision, Authority Record,
  and derived repository Mission Contract;
- immutable WOP publication, admission, and staging;
- authority-owner input resolution;
- Progressive gate eligibility;
- terminal Engineering Work Initiation;
- reservation, supervision, and execution;
- evidence, qualification, reconciliation, and lifecycle boundaries;
- repository publication and EOS synchronization;
- EENS event and notification integration;
- interface and error contracts;
- state ownership and projection;
- generalized governed-resource conflict evaluation;
- subsystem responsibility boundaries;
- minimal orthogonal Governance, Authority-effectiveness, mission-planning,
  execution, and synchronization state dimensions;
- restart, replay, partial-effect recovery, and distributed-safety invariants;
- autonomous mission selection, resumable execution, and horizontal-scaling
  readiness; and
- traceability to architecture decisions and future WOPs.

### 2.2 Out of scope

- implementation changes;
- production activation or dispatch;
- governance or lifecycle approval;
- cross-project federation;
- selection of a distributed scheduling transport, persistence, consensus, or
  deployment topology;
- generalized authority topology;
- provider-specific notification expansion;
- user-interface visual design;
- repository relocation; and
- replacement of existing controlled-record owners.

## 3. Governing principles

### ZCA-P-001 — One information owner

Every mission, authority, state, evidence, and decision fact shall have one
named information owner. Other representations are references, projections,
or historical evidence.

### ZCA-P-002 — Resolve, narrow, decide

Authority processing consists of three distinct operations:

1. resolve authoritative facts into one context;
2. narrow eligibility through applicable mission and gate rules; and
3. emit one terminal initiation decision.

No component may perform a later operation implicitly while claiming to
perform an earlier one.

### ZCA-P-003 — Immutable input, append-only outcome

Governance Decision, Authority Record, derived Mission Contract revision,
qualified WOP, publication receipt, Admission Record, owner publications,
repository observation, and initiation inputs are identified exactly.
Decisions, evidence, and reconciliation outputs are append-only or successor
records.

### ZCA-P-004 — Downward-only authority

Authority Record scope is always equal to or narrower than its superior
authority. Derived contracts and downstream decisions cannot widen it. Missing
proof of narrowing is a stop condition.

### ZCA-P-005 — Deterministic replay

The same exact inputs and applicable policy revision shall produce the same
normalized result. Time, environment, keys, and remote observations that affect
a result shall be captured explicitly. Replay shall not repeat an external
effect unless the exact operation is declared and proven idempotent.

### ZCA-P-006 — Projections do not govern

EMP, EOS, CLI, dashboards, notifications, caches, and reports do not acquire
the authority of their sources.

### ZCA-P-007 — Qualification is independent

Implementation, verification, evidence sealing, qualification, acceptance,
publication, and activation are separate states and decisions.

### ZCA-P-008 — Fail closed

Missing, ambiguous, duplicate, stale, malformed, unauthorized, or conflicting
inputs return a typed non-allow result.

### ZCA-P-009 — Contracts represent; Authority Records authorize

The Authority Record is the authoritative mission-level governance object.
The Mission Contract is a deterministic representation derived from it and
cannot independently authorize execution.

### ZCA-P-010 — Governance does not orchestrate

Governance owns policy, approval, authority, and audit only. EMP owns planning
and mission management; Zeus owns orchestration and reasoning; WOP owns the
execution package; EENS owns observation and notification; EOS owns
synchronization and reconciliation.

### ZCA-P-011 — States are minimal and orthogonal

Governance, Authority effectiveness, mission planning, execution, and
synchronization remain independent state dimensions. Authority effectiveness
and planning eligibility are derived predicates, not new mutable lifecycles.
Additional detail uses reason codes, conditions, evidence, and successor
records unless a demonstrable requirement justifies a new state.

### ZCA-P-012 — Personal engineering operating model

Zeus is primarily a personal engineering execution and orchestration system.
Its documentation architecture shall be rigorous where rigor improves
determinism, discoverability, machine interpretation, repeatability,
efficiency, integrity, traceability, recoverability, evidence, reconciliation,
or preservation of user intent. It shall not import enterprise approval,
segregation-of-duties, committee, compliance, or administrative ceremony
unless the applicable control mitigates a concrete technical, integrity,
safety, destructive-action, credential, external-system, or irreversible-state
risk.

This principle does not weaken credential, destructive-action, repository,
runtime, identity, provenance, replay, publication, synchronization, or
irreversible-effect protections. It requires those protections to be tied to
the risk they control and to the smallest authoritative boundary that needs
them.

### ZCA-P-013 — Authorized forward progress

Within an applicable Development Mode or other authorized execution scope,
the default is to allow authorized forward progress after the required facts
have been verified. Zeus shall stop when proceeding would be unsafe or
non-deterministic, including for authority ambiguity where authority is
required, conflicting identity or bindings, duplicate active execution,
destructive or irreversible action without explicit intent, loss of required
evidence, unreconcilable state, credential/security-boundary violation, or an
actual mission/WOP/procedure blocker. Optional descriptive or administrative
incompleteness does not independently block when Zeus can deterministically
reconcile the required state.

Explicit user authorization is the primary source of operator intent within
the applicable scope. It does not replace mission/WOP scope, technical
integrity checks, qualification, publication, or destructive-action
boundaries, and it does not create authority that the governing records do not
grant.

### ZCA-P-014 — Procedure-first operational instruction

Controlled procedures should be usable as machine-consumable operational
instruction. Where applicable, a procedure should identify entry conditions,
identity and state verification, authorized action, execution controller,
required output, completion condition, fail-closed conditions, recovery,
evidence, reconciliation, and the next authorized action. The sequence is a
documentation contract; it does not transfer ownership or create authority.

Zeus shall verify a fact once at a genuine trust or mutation boundary, retain
its provenance, and reuse it until an invalidation condition requires
re-verification. Repeated ceremony without a changed fact is not an
independent safety control.

Roadmap, mission, WOP, execution, qualification, publication, EENS, and EOS
records retain their existing information ownership. A roadmap remains
planning structure and never independently authorizes execution. A qualification
claim for a runtime-dependent capability still requires the true active
demonstration defined by PROC-0006; implementation or inactive evidence alone
does not establish full satisfaction.

## 4. Terminology

| Term | Definition |
|---|---|
| Governance Decision | Attributable decision that directs creation, denial, or revocation of an exact Authority Record |
| Authority Record | Immutable revision of the authoritative governance object granting bounded mission permission |
| Mission Contract | Byte-reproducible immutable mission representation derived from exactly one Authority Record revision; not authority |
| WOP | Immutable bounded execution package after required validation and qualification |
| Publication Receipt | Integrity-bound evidence that the exact WOP publication event completed |
| Admission Record | Immutable decision that an exact WOP satisfied package-admission requirements |
| Owner Publication | Signed or controlled record that owns one authority or configuration fact |
| Repository Observation | Exact branch, commit, worktree, remote, baseline, and operation state observed for initiation |
| REAC | Resolved Execution and Authority Context produced by Authority Resolution |
| PMA | Progressive Mission Authority narrow-only gate determination |
| EWI | Engineering Work Initiation terminal decision boundary |
| Decision Envelope | Exact allowed identity, scope, actions, resources, agents, repository, baseline, time, and constraints |
| Projection | Derived view that references an owner and cannot modify it by inference |
| Evidence Seal | Digest and identity binding that makes produced evidence integrity-verifiable |
| Resource Claim | Typed reference to a governed resource, access mode, effect, scope, lease policy, and containment rule |
| Resource Conflict | Incompatibility between concurrent resource claims after identity, access, effect, scope, and containment evaluation |
| Candidate Snapshot | Canonical EMP output containing the exact mission inventory boundary, priorities, planning-eligibility results, dependencies, policy revision, and digest presented to Zeus |
| Execution Attempt | Zeus-owned immutable identity binding one selection, authority chain, WOP, EWI decision, lease set, agent, and idempotency key |
| Checkpoint | Append-only execution recovery record identifying the last proven safe boundary, completed effects, pending effects, and resume inputs |
| Fencing Token | Monotonic lease generation that prevents a stale worker from committing execution effects after ownership changes |

## 5. Component model

```text
+-------------------+
| Operator Interface|
+---------+---------+
          |
          v
+-------------------+
| Governance        |
| Decision          |
+---------+---------+
          |
          v
+-------------------+
| Authority Record  |
+---------+---------+
          |
          v
+-------------------+       +---------------------+
| Derived Mission   |------>| Qualified WOP       |
| Contract          |       | Package             |
+---------+---------+       +----------+----------+
          |                            |
          +-------------+--------------+
                        v
              +---------------------+
EMP Candidate>| Zeus Selection,     |<------- Repository
Snapshot      | Authority, Readiness|        Observation
              | and Orchestration   |
              +----------+----------+
                         |
                         v
              +---------------------+
              | Progressive Mission |
              | Authority           |
              +----------+----------+
                         |
                         v
              +---------------------+
              | Zeus Engineering    |
              | Work Initiation     |
              +----------+----------+
                         |
                         v
              +---------------------+
              | Zeus Reservation,   |
              | Supervision, Agent  |
              +----------+----------+
                         |
                         v
       +-----------------+-----------------+
       |                                   |
       v                                   v
+--------------+  +---------------+  +-------------+
| Evidence and |->| Qualification |  | EOS Sync and|
| Attestation  |  +---------------+  | Reconcile   |
+------+-------+                     +-------------+
       |
       v
+-------------------+
| EENS Observation  |
| and Notification  |
+-------------------+
```

### 5.1 Operator interface

The operator interface:

- accepts explicit operator intent;
- discovers current owner state;
- displays eligible next actions and stop reasons;
- submits exact identifiers and confirmations; and
- renders results and provenance.

It shall not create an Authority Record, treat a Mission Contract as
authority, bypass WOP qualification, infer approval, or reinterpret a terminal
result.

### 5.2 Governance authority and Mission Contract derivation

Governance:

- owns policy, approval, authority, and audit;
- records one attributable Governance Decision;
- issues one immutable Authority Record revision from an approved decision;
- records `Proposed`, `Authorized`, or `Revoked` status events; and
- does not plan, orchestrate, execute, observe, notify, synchronize, or
  reconcile.

The Mission Contract derivation service:

- consumes the exact Authority Record canonical bytes, declared contract
  schema, derivation mapping revision, and explicitly identified
  non-authoritative lookup inputs;
- derives stable mission and contract-revision identities;
- deterministically derives objective, scope, exclusions, dependencies,
  constraints, resource claims, and WOP locator from one Authority Record;
- binds the Authority Record, Governance Decision, and derivation revision;
- canonicalizes ordering and serialization;
- excludes uncaptured clock, random, directory-order, environment, remote, or
  projection values;
- produces immutable revision identity, input manifest, and output digest;
- reproduces byte-identical output for identical inputs; and
- exposes deterministic discovery.

Exactly one effective Authority Record and one matching derived Mission
Contract shall resolve for a mission initiation. Zero, multiple, or mismatched
records return `STOP`.

An Authority Record or derivation-input change produces a successor Mission
Contract revision. Regeneration shall either reproduce the registered bytes or
return an integrity failure. It never edits or silently replaces the prior
revision. Mission Contract publication records provenance, digest, and
discovery location only; it does not authorize, approve, revoke, or
supersede mission authority.

### 5.3 WOP publication, admission, and qualification

The WOP service:

- validates package schema and path inventory;
- computes exact package identity and content digest;
- verifies publication receipt binding;
- applies admission policy;
- creates one immutable Admission Record;
- applies the required qualification profile and records its determination;
- supports idempotent replay; and
- stages the admitted candidate without dispatch.

Admission and qualification prove package validity and readiness only. They do
not create mission authority or initiate work.

### 5.4 Authority Resolution Service

The Authority Resolution Service:

- resolves owner publications and controlled records;
- verifies signatures, revisions, lifecycle, scope, and applicability;
- binds Authority Record, derived Mission Contract, qualified WOP, admission,
  repository, operator, policy, and environment facts;
- detects ambiguity and conflict;
- produces the canonical REAC; and
- never emits terminal execution authorization.

### 5.5 Progressive Mission Authority

PMA:

- verifies current gate identity and locked order;
- verifies accepted prerequisite lineage;
- binds current evidence, marker, receipt, package, and state;
- evaluates gate-specific eligibility; and
- returns a narrow-only determination.

PMA applies only where a Progressive package declares it. It is not a general
replacement for owner authority or EWI.

### 5.6 Engineering Work Initiation

EWI is a Zeus orchestration component. It:

- receives one REAC;
- receives the PMA result when applicable;
- verifies environment, freshness, agent, policy, admission, repository, and
  resource-conflict preconditions;
- creates one terminal decision envelope;
- emits `ALLOW`, `DENY`, or `STOP`; and
- preserves stable reason codes and provenance.

Only an exact `ALLOW` may be consumed by reservation.

### 5.7 Reservation and execution

The Zeus execution subsystem:

- consumes one canonical EMP candidate snapshot;
- deterministically selects one planning-eligible mission using a declared
  selection-policy revision and stable tie-breaker;
- reserves the exact mission/WOP/decision tuple;
- leases the exact compatible governed-resource claims;
- selects only an eligible registered agent;
- supervises invocation, heartbeat, timeout, cancellation, interruption, and
  bounded adaptation;
- enforces idempotency and action bounds;
- records attempt identity, checkpoints, terminal result, and resume token;
- publishes execution events and evidence.

Execution may stop more strictly for safety but may never widen the decision.
Adaptation remains within the Authority Record, derived Mission Contract,
qualified WOP, EWI envelope, and live resource leases. Work outside those
bounds returns to EMP for replanning and, where authority changes, to
Governance.

### 5.8 Evidence and qualification

The evidence subsystem owns produced evidence bytes, identifiers, digests,
provenance, and attestation. Zeus owns the orchestration that requests
evidence production, submits the frozen subject and inventory, and consumes
the result for completion evaluation. Independent qualification owns criteria
evaluation and determination. Neither evidence production nor qualification
owns approval, acceptance, publication, or lifecycle transition.

### 5.9 Reconciliation

EOS reconciliation:

- compares an information owner with declared projections;
- classifies exact mismatch;
- proposes or performs only authorized directional repair;
- records before/after identity and evidence; and
- retries idempotently from the declared source boundary;
- never selects authority by newest timestamp; and
- cannot create, qualify, make effective, revoke, renew, supersede, or repair
  an Authority Record from a projection.

### 5.10 EENS

EENS observes and persists typed engineering events, supports idempotent
acceptance and ordered replay, maintains consumer checkpoints, and routes
notifications. EENS events are evidence or projections of source operations;
they are not source decisions, orchestration commands, or synchronization
state.

### 5.11 Subsystem responsibility boundaries

| Subsystem | Required ownership | Prohibited ownership |
|---|---|---|
| Governance | policy, approval, Authority Record issuance/revocation, audit | planning, prioritization, selection, orchestration, WOP construction, execution, observation, synchronization |
| EMP | mission inventory, prioritization, dependency management, planning eligibility, Governance proposal/status interaction | approval, authority issuance, runtime mission selection, dispatch |
| Zeus | deterministic mission selection, orchestration, reasoning, bounded adaptation, execution, recovery, evidence and qualification orchestration, completion | Governance decisions, EMP planning source truth, qualification determination, notification transport, synchronization |
| WOP | immutable qualified execution package and completion criteria | authority, planning, selection, orchestration |
| EENS | observation, durable events, notification, consumer replay | governance, execution decisions, synchronization |
| EOS | directional synchronization and reconciliation | governance, authority, planning, selection, orchestration |

An implementation shall not satisfy a missing owner by embedding that owner's
logic into Governance or another subsystem.

### 5.12 ADR component conformance map

This matrix is the normative specification mapping for all fourteen canonical
components defined by `ADR-0001` Draft 1.3. The ADR owns the component
selection and responsibility boundary. This specification defines the
corresponding implementation contract and verification obligation without
changing that selection.

| ADR component | Specification realization | Authoritative or derived output owner | Required negative verification |
|---|---|---|---|
| `ADR-C-001` Governance | Sections 5.2, 8.1, 9, and 17 | Governance owns policy, approval, Governance Decisions, Authority Record issuance/revocation, and audit lineage | prove Governance contains no planning, selection, orchestration, execution, qualification-determination, notification, or synchronization writer |
| `ADR-C-002` Authority Record and effectiveness model | Sections 5.2, 6.2, 8.1–8.2, 9, and 17 | Governance owns immutable Authority Record revisions; Authority Resolution owns the derived effectiveness determination | reject Runtime mutation, projection repair, contract-as-authority, and independently writable effectiveness state |
| `ADR-C-003` EMP | Sections 5.7, 7, 9–10, and 17 | EMP owns inventory, priority, dependencies, planning eligibility, Governance interaction, and immutable candidate snapshots | reject approval, authority issuance, terminal selection, dispatch, and execution behavior |
| `ADR-C-004` Mission Contract Deriver and Registry | Sections 5.2, 6.2, 8.1–8.2, and 17 | EMP derivation owns byte-reproducible contract materialization, immutable derived identity, discovery, and regeneration | reject uncaptured inputs, byte drift, mutation, authority widening, or independently edited authority-bearing fields |
| `ADR-C-005` WOP and Admission | Sections 5.3, 6.3, 10, 12, 16.5, and 17 | WOP publication/admission owns the immutable package, completion criteria, typed WOP Admission receipt, and qualification binding | reject mission authority, prioritization, Runtime selection, orchestration, evidence evaluation, and cross-type receipt substitution |
| `ADR-C-006` Authority Resolution Service | Sections 5.4, 8.1–8.2, 16.5, and 17 | Authority Resolution owns source selection, the effectiveness predicate, canonical REAC, and resolution receipt | reject terminal initiation, source mutation, fact ownership, widening, ambiguity, and recency-based selection |
| `ADR-C-007` Progressive Mission Authority | Sections 5.5, 8.3, 11, 16.5, and 17 | PMA owns only the immutable monotonic Progressive eligibility result | property-test that PMA cannot create authority, widen an envelope, initiate, or dispatch |
| `ADR-C-008` Zeus | Sections 5.6–5.8, 7, 10, 16.4–16.5, 17, and 18 | Zeus owns deterministic selection, Runtime/Stage 1 admission, EWI, reservation, execution, recovery, completion, and qualification orchestration | reject Governance decisions, EMP-source mutation, qualification determination, notification transport, EOS synchronization, and execution outside the exact envelope |
| `ADR-C-009` Resource Coordination | Sections 5.7, 8.5, 16.5, 17, and 18.5–18.8 | Zeus Resource Coordination owns deterministic conflicts, atomic reservation, leases, and fencing generations | reject authority issuance, mission selection, partial reservation, stale fencing commits, and successful-effect inference |
| `ADR-C-010` Evidence and Independent Qualification | Sections 5.8, 12, 16.5, 17, and 21 | evidence producers own evidence bytes/seals; the independent qualifier owns the immutable determination | reject evidence rewriting, execution orchestration, authority issuance, self-qualification, and automatic lifecycle transition |
| `ADR-C-011` EOS | Sections 5.9, 14, 16.5, 17, and 18.7 | EOS owns directional synchronization transactions, projection checkpoints, drift classification, reconciliation, and receipts | reject authority, approval, planning, selection, source publication, reverse synchronization, and recency-based repair |
| `ADR-C-012` EENS | Sections 5.10, 15, 16.5, and 17 | EENS owns durable typed events, ordered delivery replay, consumer checkpoints, and notification projections | reject approval, authority, lifecycle, execution, qualification, and synchronization decisions |
| `ADR-C-013` Controlled-document and Publication Framework | Sections 6.1, 13, 16.5, 17, and 21–22 | existing controlled-document owners own lifecycle; the publication transaction and Git boundary own publication identity and receipts | reject Runtime authority inference, implementation execution, implicit activation, and implicit EOS synchronization |
| `ADR-C-014` Compatibility Boundary | Sections 7.4, 20, 21, and 22 | each classified compatibility producer owns only translation, offline comparison, fixture, historical, consumer, or retirement evidence | prove no production allow/deny ownership, widening, hidden fallback, newest-result selection, or deletion without consumer-complete evidence |

Every component row is mandatory. A component may be implemented as one or
more processes, libraries, or records, but its information owner and
prohibited responsibilities shall not be split, duplicated, or transferred by
deployment topology.

## 6. Repository architecture

### 6.1 Controlled documentation

```text
docs/
  architecture/       ARCH and ADR controlled records
  specifications/     SPEC controlled records
  project/            project, phase, and milestone records
  ...
```

`DOC-0001` owns controlled-document discovery. `ARCH-0001` owns the current
assessment only after applicable activation. `ADR-0001` owns the architecture
decision only after applicable activation. This specification owns technical
requirements only after applicable activation.

### 6.2 Authority Records and derived Mission Contracts

Candidate logical locations:

```text
engineering/governance/authority-records/
engineering/mission-contracts/contracts/
```

Requirements:

- one immutable object per Authority Record revision;
- one derived file or immutable object per Mission Contract revision;
- schema validation before discovery eligibility;
- stable mission identity independent of filename;
- exact Governance Decision, approval lineage, Authority Record revision,
  predecessor, Governance event-chain, supersession/revocation policy, and
  qualification references;
- deterministic contract derivation with schema and mapping versions, exact
  input manifest, canonical serialization, and output digest;
- byte-identical regeneration from the declared inputs;
- append-only publication metadata containing source revision, derivation
  revision, digest, locator, and publication event;
- no separately editable duplicate mission facts;
- exact WOP and authority references; and
- explicit Authority Record status-event and revocation-reason references.

Authority Record and Mission Contract revisions are immutable even when
stored in a mutable repository. A correction creates a successor with explicit
lineage. A superseded, revoked, expired, unqualified, or derivation-mismatched
revision remains historical but is ineligible for new execution. Repository
publication or EOS synchronization does not make either object authoritative;
authority comes only from the applicable Governance Decision and effective
Authority Record.

The exact Authority Record filesystem location remains a controlled design
detail. An implementation may choose another registered location without
changing the ownership architecture.

`engineering/execution/missions/` shall be classified as a projection,
compatibility input, fixture, or retired location before canonical activation.

### 6.3 WOP packages

WOP schemas and reusable services may remain under `engineering/wop/`.
Package instances may remain in their registered package locations. The
derived Mission Contract, publication receipt, Admission Record where
applicable, and qualification record shall provide the canonical package
locator; directory scanning alone is insufficient.

The current Progressive package remains:

```text
engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/
```

This specification does not reclassify Engineering Work Orders or move
existing packages.

### 6.4 Runtime state

Runtime state resides only in declared runtime stores or package-local runtime
locations. Each store shall identify:

- state owner;
- schema and schema version;
- allowed writers;
- transition contract;
- integrity mechanism;
- projection consumers;
- recovery source; and
- whether the state is ignored, committed, published, or external.

### 6.5 Evidence

Evidence may exist in central, WOP-local, and runtime evidence domains when
each has a distinct producer and owner. A catalogue shall provide discovery
without moving or merging historical bytes.

### 6.6 Generated and temporary content

Caches, bytecode, temporary reports, local secrets, environment-specific
configuration, and runtime databases are not controlled source. Their
exclusion or publication treatment shall be explicit in candidate manifests.

## 7. Runtime architecture

Governance is outside the runtime and supplies policy, decisions, Authority
Records, and audit inputs. EMP supplies the canonical mission inventory,
priorities, dependency and planning-eligibility results, Governance
interaction, and candidate snapshot. Zeus selects the exact mission. WOP
supplies the qualified package. Within Zeus, the runtime follows the
downward-only layering already established for the Progressive Runtime Layer:

```text
Layer 1: Authority and Decision Primitives
    |
    v
Layer 2: Lifecycle and State Projections
    |
    v
Layer 3: Command and Presentation Adapters
```

### 7.1 Layer 1 — authority and decision primitives

Owns:

- schema validation;
- identity and digest verification;
- candidate-snapshot validation and deterministic mission selection;
- Authority Record resolution and Mission Contract derivation validation;
- owner-publication resolution;
- WOP admission;
- REAC construction;
- PMA narrow-only determination;
- EWI terminal decision;
- reservation and execution decisions; and
- checkpoint and effect-fencing decisions;
- evidence integrity; and
- requests to the independent qualification service.

Layer 1 shall not import presentation or command adapters.

### 7.2 Layer 2 — lifecycle and projections

Owns:

- lifecycle state projection;
- next-action calculation from Layer 1 results;
- management and operator status projections;
- replay views; and
- source-linked recovery context.

Layer 2 shall not originate a Layer 1 authority decision.

### 7.3 Layer 3 — command and presentation

Owns:

- CLI parsing;
- human-readable output;
- explicit confirmations;
- command exit mapping; and
- transport to Layer 1/2 services.

Layer 3 shall not contain hidden allow rules or reconstruct raw authority.

### 7.4 Dependency rule

Dependencies shall point downward only. A lower layer shall not import a
higher layer. Compatibility imports shall be declared, bounded, and excluded
from production decision paths.

These layers do not transfer responsibility between subsystems. EENS consumes
events after source operations, and EOS synchronizes/reconciles source and
projection boundaries. Neither is a Zeus decision layer or a Governance
component.

## 8. Authority architecture

### 8.1 Authority Record, Mission Contract, and REAC required fields

Every Authority Record revision shall contain:

| Field group | Required content |
|---|---|
| Identity | Authority Record ID, immutable revision, schema version, mission ID, canonical digest |
| Governance lineage | Governance Decision ID and digest, approving principal, approval role, policy revision, approval basis, decision time |
| Authority | objective, included and excluded scope, permitted and prohibited effects, actors, constraints, resource claims, dependencies |
| Applicability | repository, environment, project, phase, WOP class or exact WOP binding, effective and expiry boundaries where applicable |
| Revision lineage | predecessor revision or explicit null, change reason, Governance event-chain locator, supersession policy |
| Revocation | revocation policy, affected-attempt and safe-stop rules; the resolver binds the exact revoking Governance Decision or explicit null without modifying the record |
| Integrity | canonical serialization revision, digest, signature or controlled integrity mechanism |
| Qualification | required profile ID and revision, frozen subject digest, determination, report digest and locator |
| Audit | creation event, source owner, evidence locators, material decision rationale |
| Synchronization | source locator, permitted projections, source-to-EOS direction, last declared synchronization boundary as non-authoritative metadata |

The approving principal and role shall be attributable under the referenced
policy revision. Approval, qualification, supersession, and revocation
references shall resolve exactly and shall not be inferred from filename,
directory location, timestamp, repository commit, or EOS state.
Authority Record qualification validates the frozen record against its
declared profile; it cannot approve, issue, renew, or revoke authority.

An Authority Record revision is effective only when all of the following are
true:

1. its issuing Governance Decision is `Authorized`;
2. identity, schema, canonical digest, integrity, and approval lineage verify;
3. the required qualification determination is acceptable for the exact
   frozen revision;
4. subject, operation, resources, repository/environment, and time are
   applicable;
5. no applicable successor supersedes it; and
6. no applicable Governance Decision revokes it.

`effective` and `not effective` are resolver determinations, not Authority
Record lifecycle states. Zero or multiple effective revisions return `STOP`.

Every derived Mission Contract revision shall contain:

| Field group | Required content |
|---|---|
| Identity | contract ID, immutable revision, schema version, mission ID, canonical output digest |
| Authority source | exact Authority Record ID, revision, digest, and Governance Decision reference |
| Derivation | derivation service and mapping revision, exact input-manifest digest, canonical serialization revision |
| Mission representation | objective, included and excluded scope, constraints, dependencies, resource claims, WOP locator |
| Reproduction | deterministic ordering rules, absent-value rules, regeneration command or interface identity, expected output digest |
| Publication | immutable locator, publication event, publication digest, predecessor reference; discovery projections may enumerate successors |
| Authority boundary | explicit declaration that the contract is derived, cannot authorize, and cannot be an authority parent |

The derivation input manifest contains the exact Authority Record canonical
bytes plus every schema, mapping, and lookup input that can affect output. A
derivation that reads an undeclared mutable input is invalid. Identical input
manifests shall reproduce byte-identical output. A mismatch returns
`INTEGRITY_*` or `AUTHORITY_*` and never falls back to an older or newer
contract by timestamp.

Mission Contract publication may register immutable bytes and discovery
metadata. Publication does not make a contract authoritative. Regeneration
never overwrites a published revision; source or mapping changes create a
successor with explicit lineage.

A REAC shall contain at least:

| Field group | Required content |
|---|---|
| Identity | context ID, schema version, creation time, policy revision |
| Governance | Governance Decision and Authority Record IDs, revisions, digests, approval and qualification lineage, effectiveness determination, authority parent |
| Mission | derived Mission Contract ID, revision, digest, input-manifest digest, schema and derivation revisions, objective, scope, exclusions |
| Planning | EMP candidate-snapshot ID and digest, inventory boundary, priority, dependency and planning-eligibility result, selection-policy revision |
| WOP | package ID, revision, digest, locator, publication receipt |
| Admission | Admission Record ID, determination, digest, policy |
| Repository | repository ID, root, branch, HEAD, baseline, remote, worktree policy |
| Operator | principal identity and authentication evidence reference |
| Authority | resolved owner publications, revisions, scopes, signatures, applicability |
| Controlled baseline | applicable controlled records and exact revisions |
| Environment | host/runtime identity and required service observations |
| Constraints | allowed actions, resources, agents, time, and prohibited effects |
| Resources | normalized resource claims, containment results, lease requirements, and typed conflicts |
| Provenance | source locators and digests for every resolved fact |
| Determination | `RESOLVED` or typed non-resolved status; never `ALLOW` |

### 8.2 Resolution invariants

- Every source identity resolves exactly once.
- Every digest and signature required by its owner validates.
- Exactly one effective Authority Record resolves for the exact mission and
  operation.
- Authority Record approval, qualification, supersession, revocation,
  applicability, and validity resolve from their declared owners.
- The Mission Contract derives exactly and byte-reproducibly from that
  Authority Record and its declared derivation inputs.
- Every authority is applicable to the exact WOP, governed resources,
  repository/environment where applicable, and operation.
- Authority scopes form a compatible chain.
- Resource conflicts are never resolved by unrecorded precedence.
- Unknown resource types or containment rules fail closed.
- The result is canonical and deterministically serializable.
- Replaying identical inputs yields identical semantic content.
- EMP priority or eligibility, Mission Contract publication, Git persistence,
  EOS reconciliation, and projection recency cannot make authority effective.

### 8.3 Narrow-only PMA contract

PMA input:

- exact REAC identity and digest;
- exact package and gate;
- accepted predecessor receipts;
- current package state;
- gate evidence and marker; and
- Progressive policy revision.

PMA output:

- determination: `ELIGIBLE`, `BLOCKED`, `DEFERRED`, `INELIGIBLE`, or `STOP`;
- current gate;
- satisfied and unsatisfied prerequisites;
- narrowed decision envelope;
- evidence and receipt bindings;
- reason codes; and
- canonical digest.

`ELIGIBLE` is not execution `ALLOW`.

### 8.4 Terminal EWI contract

EWI input:

- exact REAC;
- applicable PMA output;
- current repository/environment freshness observation;
- agent eligibility;
- admission and reservation availability;
- policy bundle; and
- mission-specific preconditions.

EWI output:

- decision ID and timestamp;
- input identities and digests;
- determination: `ALLOW`, `DENY`, or `STOP`;
- exact decision envelope;
- stable reason codes;
- expiration or freshness boundary;
- required evidence obligations;
- replay/idempotency key; and
- canonical digest.

An `ALLOW` without a complete envelope is invalid.

### 8.5 Generalized resource-conflict contract

Every governed resource claim contains:

```text
resource_namespace
resource_type
resource_identity
access_mode
effect_class
scope_selector
lease_policy
containment_rule
```

`access_mode` is `observe`, `shared`, or `exclusive`. The initial taxonomy
supports repositories, infrastructure, services, hardware, environments,
controlled documents, publication units, and credential boundaries.

Conflict evaluation:

1. normalizes identity through the registered resource-type rule;
2. expands declared parent/child containment without guessing;
3. compares effect class, scope, and access mode;
4. identifies compatible and incompatible claim sets;
5. requires a Zeus operational lease for an execution claim;
6. fails closed for an unknown type, ambiguous identity, missing containment
   rule, or incompatible live lease; and
7. records the exact claims and rule revision in the EWI result.

Governance authorizes resource claims. EMP plans against them. WOP declares the
bounded resources needed by its plan. Zeus evaluates conflicts and leases.
Neither planning state nor an operational lease grants authority.

## 9. Governance, Authority, and mission state models

The architecture uses orthogonal state dimensions instead of one composite
mission lifecycle.

| Dimension | Owner | Minimal representation | Non-ownership rule |
|---|---|---|---|
| Governance decision | Governance decision and audit chain | `Proposed`, `Authorized`, `Revoked` | execution or synchronization cannot transition it |
| Authority effectiveness | Authority Resolution Service, derived from owner inputs | `effective` or `not effective` determination with reason codes | not a persisted lifecycle and never inferred from Mission Contract, EMP, execution, or EOS state |
| Mission planning | EMP Work Registry | inventory membership, priority, dependencies, planning-eligibility result, candidate-snapshot revision | does not authorize or indicate execution progress |
| Execution | Zeus execution owner | `Planned`, `Ready`, `Running`, `Blocked`, `Complete`, `Failed` | does not approve, revoke, reprioritize, or synchronize |
| Synchronization | EOS | `Dirty`, `Pending`, `Reconciled` | does not change source-owner facts or authority |

Governance uses only:

```text
Proposed -> Authorized -> Revoked
    \--------------------^
```

Reasons such as `WITHDRAWN`, `DENIED`, `SUPERSEDED`, `EXPIRED`, `CLOSED`, and
explicit revocation qualify a Governance event or Authority-effectiveness
determination; they are not additional core states.

The Authority Record is an immutable revision, not a mutable workflow. The
Mission Contract is derived and has no authority lifecycle. EMP planning
eligibility is recomputed from its declared inventory, dependency, priority,
and policy inputs. Mission selection creates an execution attempt but does not
alter Governance or Authority state.

An effective Authority Record may coexist with any EMP planning fact,
execution state, or synchronization state. Execution completion does not
close or revoke authority. Revocation does not erase prior completion or
evidence, but Zeus shall apply the record's safe-stop policy to an affected
live attempt.

## 10. Execution lifecycle

```text
Planned -> Ready -> Running -> Complete
   |         |         |
   +---------+---------+-> Blocked
   |         |         |
   +---------+---------+-> Failed
```

Requirements:

- EMP publishes a canonical candidate snapshot containing the inventory
  boundary, priorities, dependency results, planning eligibility, applicable
  policy revision, and digest;
- Zeus selects one candidate deterministically from that immutable snapshot
  using a declared selection-policy revision and stable tie-breaker;
- `Planned` binds the Zeus selection, candidate snapshot, Authority Record,
  derived Mission Contract, and identified WOP;
- `Ready` requires one effective Authority Record, the matching derived
  Mission Contract, a qualified WOP, satisfied dependencies, compatible
  resource claims, environment readiness, and eligible executor;
- reservation binds mission, WOP, EWI decision, governed resources,
  repository/environment, agent class, attempt identity, fencing generation,
  and idempotency key;
- assignment selects an eligible agent without changing scope;
- starting revalidates freshness and exact binding;
- running emits heartbeats, checkpoints, effect intents, effect outcomes, and
  bounded progress evidence;
- `Complete` and `Failed` are terminal for an attempt;
- `Blocked` records a typed reason and last safe boundary; and
- resume repeats applicable resolution and initiation checks.

Zeus records `Complete` only when the exact WOP completion criteria are met
and every required independent qualification determination is acceptable.
Zeus orchestrates qualification and consumes its result; it cannot manufacture
or alter that determination. Completion of one attempt does not close the
Governance authorization or alter EMP priority for other missions.

No automatic retry occurs unless the exact WOP and policy authorize it.
There is no Execution Grant in the standard lifecycle. Any future
delayed-execution authorization requires a separate controlled extension and a
demonstrated requirement that Authority Record conditions, WOP qualification,
and pre-dispatch validation cannot satisfy.

## 11. Progressive gate lifecycle

The Progressive gate sequence remains locked and cumulative:

```text
PENDING
  -> IMPLEMENTATION_REQUIRED
  -> IMPLEMENTED
  -> VERIFICATION_REQUIRED
  -> VERIFIED
  -> ACCEPTANCE_REQUIRED
  -> ACCEPTED
```

Equivalent repository-specific labels may be used only when mapped
deterministically to these meanings.

Rules:

- gate `N+1` cannot become eligible before gate `N` is accepted;
- implementation does not imply verification;
- verification does not imply acceptance;
- acceptance binds exact evidence, marker, receipt, operator, package, state,
  and supersedence lineage;
- stale evidence cannot be replayed as current acceptance; and
- later-gate existing code may be reused but not pre-accepted.

## 12. Evidence lifecycle

```text
DECLARED
  -> PRODUCED
  -> SEALED
  -> INTEGRITY_VERIFIED
  -> QUALIFICATION_INPUT
  -> RETAINED
```

### 12.1 Evidence identity

Every evidence artifact shall identify:

- evidence ID and type;
- producer and production event;
- mission, WOP, gate, execution, and decision bindings as applicable;
- repository and baseline;
- creation time;
- content digest;
- acquisition or generation method;
- confidentiality or exclusion treatment; and
- retention location.

### 12.2 Evidence immutability

Sealed evidence is immutable. A correction is a successor artifact with an
explicit relationship and reason. Qualification reports reference evidence
digests rather than silently embedding changed evidence.

### 12.3 Qualification boundary

Qualification:

- receives a frozen subject and evidence inventory;
- applies an exact criteria/profile revision;
- reports PASS, FAIL, BLOCKED, or other defined result;
- records unresolved observations;
- cannot regenerate source evidence during evaluation; and
- cannot approve or activate its own result.

## 13. Publication lifecycle

```text
CANDIDATE_INVENTORIED
  -> DEPENDENCIES_RESOLVED
  -> EXACT_PATHS_FROZEN
  -> DIGESTS_VERIFIED
  -> PUBLICATION_AUTHORIZED
  -> PERSISTED
  -> IDENTIFIED
  -> REPRODUCED
  -> METADATA_FINALIZED
```

Requirements:

- include and exclude paths explicitly;
- preserve publication ordering;
- bind publication to exact source bytes and starting repository identity;
- prevent unrelated files from entering the transaction;
- create commit/tag or baseline identity only when separately authorized;
- reproduce from a clean checkout;
- rerun applicable qualification after persistence; and
- record final metadata and lifecycle outcome.

Publication does not automatically synchronize EOS or deploy runtime.

## 14. Synchronization model

### 14.1 Direction

Repository-controlled records and publications are source. EOS owns
synchronization and reconciliation plus its derived operational projection. It
does not own source Governance, planning, or execution facts.
EOS is infrastructure, not an authority source. It cannot issue or revoke an
Authority Record, validate Governance approval, derive a Mission Contract as
an authority operation, select a mission, initiate execution, or resolve a
source conflict by projection recency.

```text
Repository owner
      |
      v
Explicit synchronization transaction
      |
      v
EOS projection
```

Synchronization state is:

```text
Dirty -> Pending -> Reconciled
  ^         |
  +---------+
```

`Dirty` means a difference exists or requires evaluation. `Pending` means EOS
has accepted a bounded operation. `Reconciled` means the declared source
boundary and EOS-owned projection agree. These states cannot change
Governance authority, Authority effectiveness, EMP planning facts, Zeus
execution state, or source publication identity.

### 14.2 Synchronization transaction

A synchronization transaction shall record:

- source repository identity and exact commit;
- source paths, identifiers, versions, and digests;
- destination projection and pre-state;
- transformation or mapping revision;
- exclusions;
- authority for the synchronization action;
- result and post-state;
- validation evidence; and
- rollback or recovery disposition.

The transaction uses an idempotency key over source boundary, mapping
revision, destination, and expected pre-state. Partial application remains
`Pending` with its exact checkpoint or returns `Dirty`; it never reports
`Reconciled`. Retry resumes from the source boundary and declared checkpoint.
A destination write is committed only after post-state digest validation.

### 14.3 Drift classification

| Classification | Meaning | Response |
|---|---|---|
| Aligned | source and projection match | no action |
| Expected publication drift | repository advanced before declared sync boundary | observe; do not auto-repair |
| Synchronization required | declared boundary reached | stop advancement and synchronize under applicable authority |
| Projection stale | EOS does not represent current source | regenerate from source |
| Source conflict | repository owners disagree | stop; owner resolution required |
| Runtime-state failure | EOS-owned runtime fact invalid | repair runtime through its owner |

No classification permits reverse inference of repository authority.
When EOS cannot determine the authoritative source or finds conflicting
source-owner revisions, it stops and records `Source conflict`. It shall not
merge, select the newest timestamp, or reconstruct missing Governance
lineage.

## 15. Notification model

### 15.1 Event contract

Every event shall contain:

- event ID and schema version;
- event type;
- source subsystem and source record identity;
- mission, WOP, execution, gate, or publication binding when applicable;
- occurrence and acceptance times;
- idempotency key;
- severity and lifecycle category;
- safe summary;
- evidence locator where permitted; and
- content digest or integrity metadata.

### 15.2 Secret boundary

Notifications shall exclude prompts, credentials, tokens, private topics,
repository content, unrestricted diffs, and sensitive evidence. Repository
templates contain safe placeholders only.

### 15.3 Decision boundary

EENS persistence, transport delivery, acknowledgement, retry, or failure does
not modify source lifecycle or authority. A future authenticated approval
transport requires a separate decision and specification.

## 16. Interface contracts

### 16.1 Common response envelope

All canonical service results shall provide:

```text
schema_version
result_id
operation
subject_identity
determination
reason_codes[]
source_references[]
created_at
canonical_digest
```

Optional diagnostic detail shall not change semantic determination.

### 16.2 Stable reason-code families

| Family | Meaning |
|---|---|
| `IDENTITY_*` | missing, duplicate, or mismatched identity |
| `INTEGRITY_*` | digest, signature, or immutable-content failure |
| `AUTHORITY_*` | missing, inapplicable, conflicting, or exceeded authority |
| `RESOURCE_*` | unknown, ambiguous, incompatible, stale, or unavailable governed resource claim |
| `LIFECYCLE_*` | invalid or stale lifecycle state |
| `ADMISSION_*` | package or admission failure |
| `REPOSITORY_*` | branch, HEAD, baseline, worktree, remote, or operation failure |
| `POLICY_*` | explicit policy denial |
| `FRESHNESS_*` | expired or stale evidence/context |
| `AGENT_*` | unavailable or ineligible execution agent |
| `EVIDENCE_*` | missing, stale, incomplete, or invalid evidence |
| `SYNC_*` | synchronization boundary or result |
| `RUNTIME_*` | execution environment or runtime-state failure |

Reason codes shall be documented, deterministic, and backward-compatible
within a schema revision.

### 16.3 Canonical serialization

Machine-readable decisions shall:

- use a declared schema version;
- sort or normalize unordered collections;
- use UTC timestamps with explicit offset;
- avoid environment-dependent path aliases;
- represent absent values explicitly where semantically relevant;
- compute digests over canonical bytes; and
- reject unknown critical fields.

### 16.4 Idempotency

An idempotency key binds operation, exact subject, input digests, actor, and
policy revision. Repeated submission returns the existing result or a typed
conflict; it shall not duplicate a transition or execution.

Execution idempotency additionally binds candidate snapshot, selection-policy
revision, attempt ID, EWI decision, WOP, resource claims, lease generation,
checkpoint, and effect identity. Each external effect has a durable intent
before invocation and a durable outcome after observation. If recovery cannot
prove whether a non-idempotent effect completed, it returns `STOP` for
reconciliation instead of invoking the effect again.

### 16.5 ADR interface conformance map

Each named interface below implements the corresponding canonical interface in
`ADR-0001` Draft 1.3 Section 17.1. The names identify semantic contracts and
do not mandate a transport or process topology. Every implementation shall
apply Sections 16.1–16.4 in addition to the row-specific binding.

| Canonical interface | Producer → consumer | Required exact input binding | Required output | Failure and verification contract |
|---|---|---|---|---|
| `GOVERNANCE-DECIDE` | `ADR-C-001` → `ADR-C-002` | proposal, policy revision, reviewer evidence, and principal identity | attributable Governance Decision and immutable Authority Record revision | rejection produces no record and partial authority is impossible; verify approval lineage, identity, integrity, and negative partial-write cases |
| `MISSION-CONTRACT-DERIVE` | `ADR-C-004` → `ADR-C-003`, `ADR-C-005`, `ADR-C-006` | exact Authority Record canonical bytes, schema, mapping revision, and immutable lookup digests | byte-reproducible Mission Contract plus derivation manifest | ambiguity or nondeterminism produces no artifact; verify identical-input byte reproduction, successor behavior, and mutation rejection |
| `EMP-CANDIDATES` | `ADR-C-003` → `ADR-C-008` | exact Work Registry revision, dependency and priority policy, planning-eligibility inputs, and eligible Authority Record identities | immutable ordered candidate snapshot, policy revision, and digest | partial or mutable inventory cannot be selected; verify stable ordering, tie inputs, and deterministic replay |
| `WOP-ADMIT` | `ADR-C-005` → `ADR-C-006`, `ADR-C-008` | derived contract, exact WOP bytes, WOP schema, publication binding, and qualification binding | typed immutable WOP Admission receipt | rejection leaves the package immutable; verify exact subject binding and cross-type receipt-substitution negatives |
| `AUTHORITY-RESOLVE` | `ADR-C-006` → `ADR-C-007`, `ADR-C-008` | exact owner facts, applicable bundle generation, repository/environment observations, Authority Record, contract, WOP, and typed receipts | canonical REAC and resolution receipt | missing, stale, ambiguous, conflicting, or invalid input returns `STOP` with provenance and no partial context; verify deterministic replay |
| `PMA-NARROW` | `ADR-C-007` → `ADR-C-008` | exact REAC, Progressive gate state, accepted predecessor, evidence, and prerequisite identities | immutable monotonic eligibility result and narrowed envelope | failed monotonic proof blocks or returns `STOP`; verify no widening and no initiation path |
| `EWI-DECIDE` | `ADR-C-008` → `ADR-C-009` and Zeus execution supervisor | REAC, PMA result when applicable, all typed admission receipts, fresh observations, claims, agent, and policy | one terminal initiation receipt containing `ALLOW`, `DENY`, or `STOP` and an exact envelope | `DENY` or `STOP` creates no reservation; verify one reachable terminal entry and downstream non-reinterpretation |
| `RESOURCE-RESERVE` | `ADR-C-009` → `ADR-C-008` | exact EWI envelope, complete normalized claim set, attempt identity, and expected reservation boundary | atomic reservation, compatible leases, and fencing tokens | acquisition is all-or-none; verify conflict, containment, lease-loss, stale-fence, and partial-acquisition negatives |
| `ZEUS-EXECUTE` | `ADR-C-008` → fenced execution agent and `ADR-C-010` | exact attempt envelope, immutable WOP, resource leases, fencing generation, and checkpoint | effect intents/results, checkpoints, completion result, events, and evidence | unsafe execution becomes `Blocked` or `Failed` and never mutates authority; verify bounds, idempotency, duplicate dispatch, interruption, and effect uncertainty |
| `QUALIFY` | `ADR-C-010` → EWI, acceptance, and lifecycle consumers | sealed evidence, exact criteria/profile revision, exact frozen candidate identity, and policy identities | immutable qualification receipt and findings | failure leaves evidence unchanged and does not transition lifecycle; verify independence, subject binding, and non-self-approval |
| `PUBLISH` | `ADR-C-013` → Git boundary, registries, and `ADR-C-011` | separately approved exact-path inventory, dependency order, qualification evidence, repository identity, and publication authority | immutable commit/tag or publication identity, metadata, and receipt | failure is recoverable or terminally recorded and never implies EOS synchronization; verify exclusions and clean reproduction |
| `EOS-SYNC` | `ADR-C-011` → declared operational projection | frozen published source boundary, mapping revision, prior checkpoint, destination pre-state, and idempotency key | projection, checkpoint, reconciliation receipt, and synchronization state | partial work remains `Pending` or `Dirty`, source is unchanged, and ambiguity stops; verify idempotent resume and read-back digest |
| `EENS-EVENT` | source owner → `ADR-C-012` and declared consumers | event identity, source revision, event type, payload digest, ordering key, and safe transport metadata | durable event, ordered delivery projection, and consumer checkpoint | delivery failure affects delivery only and never changes the source decision; verify idempotent acceptance, replay order, and decision non-interference |

An interface fails conformance if its producer, consumer, input subject,
output type, or failure behavior can be substituted by field similarity or
transport convenience. The thirteen interface names shall remain discoverable
in schemas, fixtures, tests, and future WOP evidence.

## 17. State ownership

| State | Owner | Allowed writers | Projections |
|---|---|---|---|
| Controlled mission/phase | applicable controlled record | authorized document lifecycle process | resume, EMP, EOS |
| Governance policy, approval, authority, audit | Governance | applicable Governance process | resolver, EMP, audit views |
| Mission authority | Authority Record | Governance issuance/revocation transaction | derived Mission Contract, resolver, EMP |
| Mission identity, objective, scope, dependencies, resource claims | derived Mission Contract | deterministic derivation service only | WOP, EMP, resolver |
| Mission inventory, priority, dependencies, planning eligibility | EMP Work Registry | EMP registry service | candidate snapshot, status, context |
| Candidate snapshot | canonical EMP snapshot | EMP snapshot service | Zeus selector, audit |
| Mission selection | Zeus selection result | Zeus deterministic selector | reservation, EMP outcome projection, audit |
| WOP content | published package | publication transaction | admission and runtime readers |
| WOP qualification | qualification record | independent qualifier | resolver, Zeus, status |
| Admission | Admission Record where applicable | WOP admission service | staging, resolver, status |
| Authority owner facts | designated publications/records | designated owner publication process | REAC |
| Resolved context | Authority Resolution Service | resolver only | PMA, EWI, diagnostics |
| Gate eligibility | PMA | PMA only | EWI, operator status |
| Terminal initiation | EWI | EWI only | reservation, audit |
| Resource leases and fencing generations | Zeus resource coordinator | exact EWI/reservation operation | execution, oversight |
| Execution attempts, checkpoints, adaptations, effects, and result | Zeus runtime | supervisor and exact fenced agent | evidence, qualification orchestration, EMP outcome projection, status |
| Gate acceptance | Progressive decision store | explicit acceptance operation | runtime state, status |
| Evidence | evidence record | bound producer/sealer | qualification, audit |
| Qualification | qualification report | independent qualifier | decision consumers |
| Project state | PROJ owner | controlled project-state process | EMP, EOS, resume |
| Publication | publication transaction and Git | publication process | registry, EOS sync |
| Synchronization, reconciliation, and EOS projection | EOS | EOS synchronization owner | resume, operator; never an authority input except as an explicitly non-authoritative freshness observation |
| Observations and notifications | EENS | EENS acceptance service | notification consumers |

Any implementation containing an undeclared second writer fails conformance.

## 18. Recovery model

### 18.1 Recovery principles

- preserve evidence before repair;
- identify the authoritative owner before selecting a source;
- revalidate all authority and freshness after interruption;
- retain one immutable execution-attempt identity across resume;
- fence stale workers before any resumed effect;
- record effect intent durably before invocation and outcome after observation;
- never reconstruct approval or evidence that did not exist;
- do not mutate immutable inputs;
- use successor records for corrections; and
- retain an auditable stop reason.

Recovery does not add a lifecycle state or an authority object. Recovery
details are attempt records, checkpoints, evidence, reason codes, leases, and
owner projections within the existing state models.

### 18.2 Attempt and checkpoint contract

Every execution attempt records:

- attempt ID and predecessor attempt or resume reference;
- candidate-snapshot and selection-policy identities;
- Governance Decision, Authority Record, derived Mission Contract, WOP,
  REAC, PMA when applicable, and EWI identities and digests;
- repository, environment, agent, resource-claim, lease, and fencing
  identities;
- idempotency key;
- ordered checkpoint and effect identities;
- last proven safe boundary;
- pending, completed, compensated, and uncertain effects;
- required resume validations; and
- terminal result or typed interruption reason.

A checkpoint is acknowledged only after its content and referenced evidence
are durable under the declared owner. Checkpoints never contain reconstructed
approval or authority.

### 18.3 Reboot, restart, and power loss

On process restart:

1. discover the last sealed attempt and checkpoint from their declared owners;
2. verify checksums, checkpoint order, effect ledger, and transition lineage;
3. verify Governance Decision, Authority Record, derived Mission Contract,
   qualified WOP, candidate snapshot, repository/environment, resource leases,
   qualification inputs, and owner publications;
4. reconstruct REAC;
5. rerun PMA and EWI as applicable;
6. acquire a new fenced lease generation and invalidate stale workers;
7. compare the new decision to the interrupted envelope;
8. resume only if identities, scope, policy, freshness, completed effects, and
   the last safe checkpoint remain compatible; and
9. otherwise stop and preserve the prior attempt and evidence.

Power loss between effect intent and observed outcome marks the effect
`uncertain` through a reason code. A non-idempotent uncertain effect is not
retried automatically.

### 18.4 Interruption and partial execution

Cancellation, timeout, agent loss, operator interruption, or partial execution
shall:

1. stop new effect issuance;
2. fence or expire the current lease;
3. seal available evidence and the last durable checkpoint;
4. classify each initiated effect as completed, compensated, pending, or
   uncertain;
5. record the exact interruption reason; and
6. enter `Blocked` or `Failed` according to the existing execution model.

Resume uses the same WOP-defined checkpoint and compensation contract. Zeus
may skip only an effect proven completed and may repeat only an effect whose
declared idempotency contract remains valid. A required scope or plan change
returns to EMP and Governance.

### 18.5 Duplicate-execution prevention

Atomic reservation shall admit one active attempt for the same mission, WOP,
decision envelope, and effect boundary. Duplicate submissions return the
existing attempt or a typed conflict.

Before committing an effect or checkpoint, a worker verifies:

- attempt and idempotency identity;
- current fencing token;
- unexpired compatible resource lease;
- expected previous checkpoint;
- effect intent uniqueness; and
- current EWI and Authority effectiveness where required.

A stale or duplicate worker cannot commit after a newer fencing generation.
The architecture guarantees deterministic deduplication and effect fencing;
it does not claim physically impossible exactly-once delivery.

### 18.6 Stale-state recovery

Staleness is determined by owner revision, digest, validity, and freshness
policy, not timestamp alone. A stale projection is regenerated from its
declared owner. Conflicting owner records, multiple effective Authority
Records, mismatched Mission Contract bytes, stale candidate snapshots, or
divergent checkpoints return `STOP`.

Recovery never promotes an EMP, EENS, EOS, CLI, cache, dashboard, or worker
projection into source truth.

### 18.7 Synchronization failure

EOS recovery:

1. verifies the declared source owner and exact source boundary;
2. verifies the mapping revision and destination pre-state;
3. locates the last acknowledged synchronization checkpoint;
4. resumes idempotently or restores the previous complete destination
   projection;
5. validates the complete destination digest; and
6. records `Reconciled` only after full validation.

Partial synchronization remains `Pending` or returns `Dirty`. Source
authority and source-owner facts remain unchanged. Conflicting sources stop
for owner resolution; EOS cannot choose by recency or repair Governance
lineage.

### 18.8 Distributed recovery and horizontal scale

Multiple Zeus workers may evaluate immutable candidate snapshots and readiness
inputs in parallel. Exactly one worker may own an attempt/effect boundary
through atomic reservation and a fenced resource lease.

Distributed execution shall:

- use stable mission, attempt, checkpoint, effect, and idempotency identities;
- treat wall-clock time as an observation, never as tie-breaking authority;
- require a declared quorum or lease-owner decision for ownership transfer;
- reject commits from a stale fencing generation;
- stop on network partition, lost quorum, conflicting checkpoints, or
  ambiguous owner state;
- transfer only sealed checkpoints and declared resume inputs; and
- preserve evidence and qualification independence across workers.

Horizontal scaling partitions work by governed-resource compatibility and
atomic reservation. It may replicate stateless validation and reasoning, but
shall not replicate an information owner or create another authority path.
The transport, storage, consensus, and deployment topology remains deferred.

### 18.9 Replay

Replay is read-only unless a contract explicitly authorizes idempotent
reprocessing. Deterministic mission-selection replay consumes the exact
candidate snapshot, selection-policy revision, tie-break inputs, and captured
observations. Execution replay reports what would occur and does not acquire a
lease or emit an external effect. Replayed evidence or decisions retain
original occurrence identity. Delivery replay cannot recreate source
execution.

### 18.10 Corruption and dependency loss

Digest, signature, schema, transition, or lineage corruption results in
quarantine and `STOP`. Recovery uses the designated source owner or immutable
historical object. Newer timestamp alone is not recovery authority.

Loss of remote, notification, EOS, or external compatibility sources shall not
change repository authority. The operation stops when the dependency is
mandatory and continues with an explicit degraded observation only when the
contract permits it.

## 19. Operational constraints

The canonical implementation shall:

- keep production dispatch disabled until separately commissioned;
- never consume the external historical Progressive WOP as current authority;
- never treat a Mission Contract, WOP, registry state, or directory count as
  authority;
- require exactly one effective Authority Record and one matching derived
  Mission Contract;
- verify Authority Record approval, qualification, version, supersession,
  revocation, audit, and applicability lineage before every initiation and
  recovery boundary;
- reproduce the exact Mission Contract bytes from its declared derivation
  inputs;
- reject independently editable projection facts;
- reject unknown or ambiguous resource types, identities, containment rules,
  or incompatible claims;
- omit Execution Grant from the standard mission path;
- introduce no mission-level authority object other than the Authority Record;
- prevent Governance components from owning EMP, Zeus, WOP, EENS, or EOS
  responsibilities;
- prohibit raw authority reconstruction in presentation layers;
- isolate live runtime and tests;
- keep local secrets and runtime databases outside controlled source;
- preserve accepted gate and evidence history;
- operate without requiring notification delivery for correctness;
- bind every execution to exact repository and package identities;
- bind mission selection to an exact EMP candidate snapshot and deterministic
  selection-policy revision;
- bind every execution to exact governed-resource claims and leases;
- bind every attempt, checkpoint, effect, and resume to exact identities and a
  current fencing generation;
- stop rather than repeat an uncertain non-idempotent effect;
- prevent EOS state or synchronization success from becoming an authority
  input;
- keep publication, deployment, and synchronization separate; and
- support deterministic clean-checkout qualification.

### 19.1 Future-readiness conformance

| Capability | Architectural support | Operational Alpha boundary |
|---|---|---|
| Autonomous mission selection | EMP candidate snapshot plus Zeus deterministic policy and stable tie-breaker | dispatch remains separately commissioned; selection cannot widen authority |
| Deterministic replay | canonical input manifests, captured observations, policy revisions, digests, and non-side-effecting replay | external effects require explicit idempotency and current authorization |
| Resumable execution | durable attempt identity, sealed checkpoint, effect ledger, revalidation, and fenced lease reacquisition | uncertain non-idempotent effects stop for reconciliation |
| Distributed execution | atomic reservation, fencing, partition stop rules, portable sealed checkpoints | implementation topology remains deferred |
| Evidence qualification | Zeus orchestrates frozen evidence submission; independent qualification owns the determination | no execution component may self-qualify |
| Horizontal scaling | stateless evaluation may replicate; work partitions by resource compatibility and atomic reservation | information owners and authority paths do not replicate |

These capabilities reuse the existing Authority Record, Mission Contract,
WOP, execution, evidence, and synchronization models. They introduce no
Execution Grant, authority object, or lifecycle state.

## 20. Compatibility and migration

### 20.1 Compatibility classes

Each noncanonical component shall be assigned exactly one:

- `OFFLINE_VALIDATOR`;
- `SYNTAX_TRANSLATOR`;
- `GENERATED_PROJECTION`;
- `TEST_FIXTURE`;
- `HISTORICAL_RECORD`; or
- `RETIRED`.

Compatibility output contains source identity and class. It cannot emit
production `ALLOW`.

### 20.2 Consumer migration

Before retiring a component:

1. inventory imports, CLI routes, tests, services, recovery paths, and external
   consumers;
2. map each consumed field and semantic;
3. provide a canonical replacement or prove the field obsolete;
4. run comparison qualification;
5. remove production routing;
6. preserve historical evidence;
7. run clean regression; and
8. record the retirement boundary.

### 20.3 Known candidate dispositions

| Existing path | Candidate disposition |
|---|---|
| Authority Graph engine | offline topology validator |
| WOP compatibility evaluator | syntax/compatibility validator |
| historical OA-02 lifecycle | retired after consumer proof |
| legacy gate approval service | transitional, then retired from production |
| standalone PMCT approval projection | test/observation harness only |
| external Progressive WOP tree | historical compatibility package |
| `engineering/execution/missions/` | generated projection or retirement |

These are specification candidates until the applicable implementation WOP
verifies actual consumers.

## 21. Validation and qualification requirements

### 21.1 Structural validation

- identifiers are unique;
- metadata and relationships resolve;
- interfaces conform to schemas;
- canonical serialization and digests reproduce;
- dependency direction has no prohibited upward edge; and
- each state has one declared writer.

### 21.2 Authority validation

- zero or multiple effective Authority Records stop;
- Authority Record permanent identity, immutable revision, schema, digest,
  approval lineage, policy, applicability, qualification, predecessor,
  supersession, revocation, audit, and synchronization fields validate;
- effectiveness is derived from owner inputs and never persisted as an
  independently writable grant;
- missing, multiple, or mismatched Mission Contract derivations stop;
- identical declared derivation inputs reproduce byte-identical Mission
  Contract output;
- regeneration or publication cannot overwrite a Mission Contract revision;
- Mission Contract and WOP records cannot be authority parents;
- EMP eligibility, Zeus selection, Git publication, and EOS projection state
  cannot create authority;
- owner-publication conflict stops;
- unknown resource semantics and incompatible claims stop;
- REAC never returns terminal `ALLOW`;
- PMA cannot widen a generated envelope;
- only EWI emits terminal `ALLOW`;
- reservation rejects unmatched decisions;
- no compatibility path reaches production execution;
- no standard path requires or consumes an Execution Grant; and
- subsystem import and ownership checks reject Governance orchestration.

### 21.3 Lifecycle validation

- implementation, verification, acceptance, qualification, publication, and
  synchronization remain distinct;
- Progressive gates cannot skip order;
- stale receipts and evidence cannot replay as current;
- Governance state is only `Proposed`, `Authorized`, or `Revoked`;
- Authority effectiveness is a derived predicate, not a lifecycle;
- mission inventory, priority, dependency satisfaction, and planning
  eligibility remain EMP facts;
- execution state is only `Planned`, `Ready`, `Running`, `Blocked`,
  `Complete`, or `Failed`;
- synchronization state is only `Dirty`, `Pending`, or `Reconciled`;
- reason codes preserve supersedence, expiry, closure, interruption, timeout,
  cancellation, and retry detail without adding core states;
- projections cannot transition owners; and
- successor records preserve lineage.

### 21.4 Recovery validation

- reboot and power-loss recovery reconstruct the exact attempt and last sealed
  checkpoint deterministically;
- interruption and partial execution seal evidence, classify effects, and
  require authority, freshness, lease, and checkpoint revalidation;
- duplicate submission returns the existing attempt or a typed conflict;
- a stale fencing token cannot commit an effect or checkpoint;
- uncertain non-idempotent effects are not automatically retried;
- stale owner or projection state fails closed and cannot win by timestamp;
- EOS partial synchronization never reports `Reconciled` and retries
  idempotently from the declared source boundary;
- network partition, lost quorum, and conflicting distributed checkpoints
  stop without split-brain commit;
- corrupted state is quarantined;
- selection and decision replay are deterministic and non-side-effecting;
- notification outage does not alter correctness; and
- clean checkout reproduces publication and qualification.

### 21.5 Required evidence

Future WOPs shall produce:

- exact-path and digest manifests;
- owner/consumer inventories;
- dependency and import graphs;
- canonical interface fixtures;
- positive and negative authority cases;
- Authority Record identity, approval, policy, applicability, qualification,
  supersession, revocation, audit, and EOS projection cases;
- Authority Record-to-Mission Contract derivation fixtures;
- byte-identical Mission Contract regeneration and successor-publication
  fixtures;
- generalized resource identity, containment, compatibility, and lease cases;
- subsystem dependency/ownership checks;
- minimal-state transition and reason-code cases;
- EMP candidate-snapshot and Zeus deterministic-selection fixtures;
- replay, reboot, power loss, interruption, partial effect, duplicate
  execution, stale state, synchronization failure, corruption, fencing,
  partition, and distributed recovery cases;
- independent evidence-qualification and execution-completion cases;
- proof that legacy paths cannot initiate execution;
- clean-checkout validation; and
- runtime-preservation evidence.

### 21.6 ADR invariant conformance map

The following matrix maps every invariant owned by `ADR-0001` Draft 1.3
Section 16 to a testable specification requirement, failure behavior, and
planned evidence class. The ADR statement remains authoritative for the
architectural invariant; this matrix does not weaken, combine, or reinterpret
it.

| ADR invariant | Normative SPEC realization | Required enforcement or failure behavior | Planned evidence |
|---|---|---|---|
| `ADR-INV-AUTH-001` | Sections 5.2, 8.1–8.2, 17, and 24.1 | zero, multiple, inapplicable, unqualified, superseded, revoked, or integrity-invalid Authority Records return `STOP` | attributable issuance plus identity, qualification, applicability, supersession, and revocation matrix |
| `ADR-INV-AUTH-002` | Principles ZCA-P-006 and ZCA-P-009; Sections 8.2, 9, 17, 19, and 24.2–24.3 | any attempt to treat a contract, WOP, receipt, queue, evidence, notification, commit, lease, or projection as authority is rejected | negative authority-parent and projection-promotion fixtures |
| `ADR-INV-AUTH-003` | Sections 5.4–5.6, 8.2–8.4, 16.5, 17, and 24.4–24.6 | non-resolver REAC, widening PMA, or non-EWI terminal initiation is invalid and blocks execution | one-owner, no-widening, and one-reachable-terminal-entry proofs |
| `ADR-INV-AUTH-004` | Principles ZCA-P-002 and ZCA-P-004; Sections 8.2–8.5 and 21.2 | inability to prove subset containment for scope, actions, resources, identities, effects, or time returns `STOP` | monotonic property tests and decision-envelope comparison fixtures |
| `ADR-INV-LIFE-001` | Sections 9–14 and 17 | each lifecycle transition is accepted only from its declared owner; cross-domain writes fail | owner/writer inventory and orthogonal-transition tests |
| `ADR-INV-LIFE-002` | Sections 9, 13–15, 17, and 24.9–24.15 | an event or result cannot imply another lifecycle transition without that owner's explicit decision | negative implication and notification/synchronization non-interference tests |
| `ADR-INV-LIFE-003` | Principle ZCA-P-011; Sections 9 and 21.3 | an undeclared state is rejected unless a controlled requirement proves the existing states, predicates, reason codes, evidence, and successors insufficient | state-enum validation and reason-code coverage |
| `ADR-INV-STATE-001` | Principles ZCA-P-001 and ZCA-P-006; Sections 5.12, 6.4, and 17 | a duplicate or undeclared writer fails conformance; every projection requires source, revision, derivation, and invalidation | ownership audit, writer reachability, and projection-schema fixtures |
| `ADR-INV-STATE-002` | Sections 5.9, 9, 14, and 17 | reverse synchronization, recency promotion, or projection mutation of an owner fact returns `STOP` | stale/newer projection and reverse-write negative cases |
| `ADR-INV-STATE-003` | Principle ZCA-P-008; Sections 8.2, 14.3, and 18.6 | conflicting or ambiguous owners are never merged or preferred; the operation stops | conflicting owner, duplicate identity, and newest-timestamp negative cases |
| `ADR-INV-SYNC-001` | Sections 5.9 and 14.1–14.2 | EOS requires one explicit source boundary and one declared projection direction | source/destination identity and directional-mapping fixtures |
| `ADR-INV-SYNC-002` | Sections 14.2, 16.4, 18.7, and 21.4 | partial synchronization remains `Pending`/`Dirty`; replay uses the same key/checkpoint and validates final digest | interrupted synchronization, idempotent retry, and digest-reproduction evidence |
| `ADR-INV-SYNC-003` | Sections 5.9, 14, 17, 19, and 21.2 | EOS attempts to issue, repair, revoke, supersede, qualify, or reverse-write owner facts are rejected | prohibited-operation and projection-authority negatives |
| `ADR-INV-SYNC-004` | Sections 14.2–14.3 and 18.7 | only owner-authorized direction may repair drift; ambiguous ownership or direction stops | drift-classification and conflicting-source fixtures |
| `ADR-INV-PUB-001` | Sections 13, 16.5, and 22 | publication requires exact paths, bytes, digests, dependency order, repository identity, commit, and publication identity | frozen manifest, digest list, publication receipt, and repository identity |
| `ADR-INV-PUB-002` | Sections 13, 14, and 21.4 | publication, approval, activation, qualification, and EOS synchronization remain separate; clean reconstruction must match | clean-checkout reproduction and cross-domain non-implication evidence |
| `ADR-INV-PUB-003` | Sections 6.6, 13, and 24 | an unclassified unrelated, legacy, generated, or untracked path blocks publication | complete include/exclude inventory and negative scope audit |
| `ADR-INV-REPLAY-001` | Principle ZCA-P-005; Sections 16.3–16.4 and 18.9 | missing captured input, revision, stable order, tie-breaker, or identity graph blocks replay | repeated canonical replay with fixed inputs and environment observations |
| `ADR-INV-REPLAY-002` | Sections 16.4 and 18.3–18.5, 18.9 | replay emits no effect unless exact idempotency is declared and the same effect key is proven | side-effect-negative replay and idempotent-effect fixtures |
| `ADR-INV-REPLAY-003` | Sections 18.9–18.10 | divergent replay is sealed as evidence and returns `STOP`; newest-result selection is prohibited | injected divergence and timestamp-preference negative cases |
| `ADR-INV-REPLAY-004` | Sections 5.2, 8.1–8.2, 10, 16.3–16.5, and 18.9 | identical declared inputs must reproduce contract bytes and semantic selection/resolution/receipt outputs | byte-identical derivation plus selection, REAC, and receipt replay fingerprints |
| `ADR-INV-REC-001` | Sections 10 and 18.1–18.4 | resume cannot issue an effect before current authority, freshness, admission, lease, agent, and environment revalidation | reboot, interruption, revocation, lease-loss, and stale-environment tests |
| `ADR-INV-REC-002` | Sections 18.2–18.4 | only a proven checkpoint resumes the same attempt; otherwise create a new attempt or stop | checkpoint identity, effect-boundary, and invalid-resume cases |
| `ADR-INV-REC-003` | Sections 16.4 and 18.3–18.4 | an uncertain non-idempotent effect is never automatically invoked again | power-loss-between-intent-and-result fixture plus reconciliation evidence |
| `ADR-INV-REC-004` | Sections 18.5 and 18.8 | atomic reservation and fencing are mandatory; partition, stale replica, checkpoint conflict, or lost quorum fails closed | concurrent worker, stale token, partition, and conflicting-checkpoint tests |
| `ADR-INV-ADM-001` | Sections 5.3, 16.5, 17, and 21.2 | WOP, mission Runtime, and Stage 1 admission preserve separate subjects, schemas, owners, and receipts | typed receipt schemas and boundary-specific positive/negative fixtures |
| `ADR-INV-ADM-002` | Sections 16.1–16.4 and 21.2 | receipt type, schema, issuer, integrity, subject, purpose, and input binding all validate before use | mutation, wrong issuer, wrong purpose, stale subject, and digest negatives |
| `ADR-INV-ADM-003` | Sections 5.3, 17, and 21.2 | field overlap never permits one receipt type to satisfy another | exhaustive cross-type substitution matrix |
| `ADR-INV-ADM-004` | Sections 5.3–5.6, 8.3–8.4, and 21.2 | admission cannot widen authority or replace the EWI terminal result | widening and admission-as-allow negative cases |
| `ADR-INV-COMP-001` | Sections 7.4, 20, 21.2, and 24.18 | compatibility cannot emit production `ALLOW`, widen, or become owner by fallback | production call-graph and negative reachability evidence |
| `ADR-INV-COMP-002` | Sections 20.1–20.3 and 22 | every compatibility path requires class, consumer boundary, schemas, authority limit, and retirement evidence | complete compatibility inventory and per-consumer mapping |
| `ADR-INV-COMP-003` | Sections 20.2–20.3 and 21.5 | deletion or retirement is prohibited until consumer, reachability, regression, recovery, and history evidence is complete | consumer-free proof, clean regression, recovery proof, and archive digest |

Conformance is all-or-nothing for each applicable invariant. Equivalent prose
or a passing happy-path test does not satisfy the identifier-level mapping or
the required negative evidence.

## 22. Future WOP conformance

A future WOP claiming conformance shall identify:

- exact `SPEC-0002` revision;
- implemented decision and requirement identifiers;
- in-scope components and paths;
- pre-existing and unrelated changes;
- state owners and migration direction;
- Authority Record and Mission Contract derivation revisions;
- EMP candidate-snapshot and Zeus selection-policy revisions;
- compatibility disposition;
- required tests and evidence;
- publication and synchronization boundaries;
- checkpoint, idempotency, effect-fencing, rollback, and recovery;
- prohibited runtime effects; and
- acceptance criteria.

A WOP may implement a bounded subset only when it preserves every invariant and
declares remaining dependencies.

### 22.1 ADR Future Implementation conformance map

The following units are specification and traceability boundaries only. They
do not authorize implementation. A future WOP may claim a unit only when it
names the exact applicable architecture baseline, preserves the listed
prerequisites, implements the mapped requirements, and produces the required
exit evidence.

| ADR unit | Prerequisites preserved from ADR | SPEC implementation scope | Required exit evidence |
|---|---|---|---|
| `ADR-FI-001` Authority Record and Mission Contract derivation | `ADR-D-001`, `ADR-D-008`, `ADR-D-015` | Sections 5.2, 6.2, 8.1–8.2, 9, 16.5, 17, and 21.2 | byte-identical derivation, mutation rejection, and revocation/supersession cases |
| `ADR-FI-002` Immutable WOP and qualification binding | `ADR-FI-001` | Sections 5.3, 6.3, 10, 12, 16.5, 17, and 21.2 | package mutation rejection, immutable receipts, and qualification-independence proof |
| `ADR-FI-003` Authority publication selection and REAC | `ADR-FI-001`, `ADR-FI-006`, `ADR-FI-016` | Sections 5.4, 8.1–8.2, 16.5, 17, 18.6, and 21.2 | ambiguity, freshness, applicability, generation, revocation, and deterministic REAC replay matrix |
| `ADR-FI-004` Narrow-only PMA | `ADR-FI-003`, `ADR-FI-016` | Sections 5.5, 8.3, 11, 16.5, and 21.2 | property evidence proving no widening, authority creation, or initiation |
| `ADR-FI-005` Zeus EWI terminal boundary | `ADR-FI-002` through `ADR-FI-004`, `ADR-FI-009`, `ADR-FI-010`, `ADR-FI-013` | Sections 5.6, 8.4, 10, 16.5, 17, 19, and 21.2 | one reachable terminal entry, negative bypass tests, exact receipt binding, and no Execution Grant |
| `ADR-FI-006` State owners and projections | `ADR-FI-001` | Sections 5.12, 6.4, 9, 14, 17, and 21.3 | owner/writer audit, drift and stale-projection cases, invalidation, and reverse-sync rejection |
| `ADR-FI-007` Publication and EOS separation | `ADR-FI-006`, `ADR-FI-016` | Sections 13–14, 16.5, 17, 18.7, and 21.4 | clean reproduction, idempotent synchronization, partial recovery, and source-preservation proof |
| `ADR-FI-008` Mission-description convergence | `ADR-FI-001`, `ADR-FI-016` | Sections 5.2, 6.2, 17, 20, and 21.2 | generated-projection enforcement, zero independent writers, and consumer-complete inventory |
| `ADR-FI-009` Repository observation policy | `ADR-FI-006` | Sections 8.1, 10, 16.5, 18.6, 19, and 21.2 | phase-specific deterministic observation fixtures and fail-closed remote/freshness tests |
| `ADR-FI-010` Typed receipt and admission layers | `ADR-FI-002`, `ADR-FI-003`, `ADR-FI-016` | Sections 5.3, 8.1, 10, 16.1–16.5, 17, and 21.2 | cross-type substitution negatives, issuer/integrity checks, and exact subject/purpose binding |
| `ADR-FI-011` Compatibility and PMCT retirement | `ADR-FI-003` through `ADR-FI-005`, `ADR-FI-010` | Sections 7.4, 20, 21.5–21.6, and 24.18 | production-reachability negatives, preserved fixtures, recovery evidence, and consumer-free proof |
| `ADR-FI-012` EENS bounded integration | `ADR-FI-016` | Sections 5.10, 15, 16.5, 17, and 21 | idempotent acceptance, ordering, checkpoint, replay, secret-boundary, and decision-noninterference tests |
| `ADR-FI-013` Generalized resources | `ADR-FI-001`, `ADR-FI-006`, `ADR-FI-016` | Sections 5.7, 8.5, 10, 16.5, 17, 18.5–18.8, and 21 | type extension, containment, conflict, atomic reservation, lease-loss, and fencing tests |
| `ADR-FI-014` Recovery, replay, and scale | `ADR-FI-003`, `ADR-FI-005` through `ADR-FI-007`, `ADR-FI-010`, `ADR-FI-013` | Sections 10, 16.4–16.5, 18, 19.1, and 21.4 | reboot, interruption, power loss, uncertain effect, duplicate dispatch, partition, stale state, synchronization failure, and replay evidence |
| `ADR-FI-015` Architecture cutover qualification | `ADR-FI-001` through `ADR-FI-014` | Sections 13, 20–21, 24–25, and this conformance map | clean exact candidate, end-to-end proof, zero alternate authorizers, compatibility negatives, and bounded rollback evidence |
| `ADR-FI-016` Subsystem interface conformance | `ADR-FI-001`, `ADR-FI-006`; remains prerequisite for every cross-subsystem unit | Sections 5.11–5.12, 16.5, 17, and 21.6 | component contract tests, exact interface fixtures, ownership audit, and prohibited-responsibility checks |

The prerequisite graph is acyclic. `ADR-FI-016` begins with specification and
fixture work and remains a cross-cutting conformance obligation; it does not
permit implementation before the applicable controlled approval and
implementation authority exist.

## 23. Traceability

### 23.1 ADR decision map

This Draft is reconciled specifically to `ADR-0001` Draft 1.3. The following
decision map is unchanged in meaning from Draft 1.2 and is supplemented by the
component, invariant, interface, and Future Implementation maps below.

| ADR decision | Specification implementation |
|---|---|
| ADR-D-001 | Sections 3, 4, 5.2, 6.2, 8, 9, 14, 17, and 21 |
| ADR-D-002 | Sections 5.3, 6.3, 10, 13 |
| ADR-D-003 | Sections 5.4, 8.1, 17 |
| ADR-D-004 | Sections 5.4, 8.1, 8.2 |
| ADR-D-005 | Sections 5.5, 8.3, 11 |
| ADR-D-006 | Sections 5.6, 8.4, 16 |
| ADR-D-007 | Sections 5.7, 7, 10, 16, 18, 19, and 21 |
| ADR-D-008 | Sections 14, 17, 18 |
| ADR-D-009 | Sections 5.8, 12, 21 |
| ADR-D-010 | Sections 13 and 14 |
| ADR-D-011 | Sections 5.10 and 15 |
| ADR-D-012 | Section 20 |
| ADR-D-013 | Sections 3, 10, 19, and 21 |
| ADR-D-014 | Sections 4, 5.7, 8.5, 16.2, 17, 19, and 21 |
| ADR-D-015 | Sections 3, 5.8–5.11, 7, 9, 10, 14, 17, and 21 |
| ADR-D-016 | Sections 3, 5.7–5.9, 7, 10, 14, 16–19, and 21 |

### 23.2 Complete downstream mapping

| ADR domain | Owned definitions in ADR-0001 Draft 1.3 | Exact downstream SPEC mapping | Future implementation boundary |
|---|---:|---|---|
| decisions | 16 (`ADR-D-001`–`ADR-D-016`) | Section 23.1 | Section 22.1 and future WOP-declared decision scope |
| canonical components | 14 (`ADR-C-001`–`ADR-C-014`) | Section 5.12 | Section 22.1 component and ownership obligations |
| architectural invariants | 32 (`ADR-INV-*`) | Section 21.6 | every applicable WOP requirement and negative-evidence obligation |
| canonical interfaces | 13 named contracts | Section 16.5 | `ADR-FI-016` plus each consuming unit in Section 22.1 |
| Future Implementation units | 16 (`ADR-FI-001`–`ADR-FI-016`) | Section 22.1 | future qualified WOPs; no implementation authority conveyed here |

### 23.3 Bidirectional assessment-to-implementation chain

The complete trace direction is:

```text
ARCH-0001 Draft 1.6 finding / recommendation / risk
    -> ARCH Decision Request
    -> ADR-0001 Draft 1.3 resolution and ADR-D decision
    -> ADR-C component + ADR-INV invariant + canonical interface
    -> SPEC-0002 Draft 1.3 requirement and validation obligation
    -> ADR-FI unit
    -> future WOP-declared implementation and evidence
```

`ADR-0001` Sections 14 and 20 own the forward and reverse mappings from all
ARCH findings, recommendations, risks, and Decision Requests to decisions,
components, and `ADR-FI` units. SPEC Sections 5.12, 16.5, 21.6, 22.1, and
23.1 map every resulting ADR identifier domain to normative implementation
and evidence requirements. A future WOP closes the final edge only by naming
the exact applicable SPEC revision and every implemented identifier.

Reverse trace begins with a future WOP requirement, resolves its Section 22.1
`ADR-FI` unit, follows the mapped SPEC requirements to the ADR component,
interface, invariant, and decision, and then uses ADR Sections 14 and 20 to
resolve the originating ARCH Decision Requests, findings, recommendations,
and risks.

The mapping is zero-orphan only when:

1. every owned ADR definition appears exactly once in its ADR inventory;
2. every decision, component, invariant, interface, and `ADR-FI` identifier
   has at least one exact downstream SPEC locator;
3. no SPEC requirement contradicts its ADR definition;
4. every future WOP names the exact SPEC revision and applicable identifiers;
5. all forward and reverse locators resolve; and
6. no implementation or evidence artifact is treated as architectural
   authority.

### 23.4 Historical lineage

Historical evidence trace:

```text
ENGINEERING-CONVERGENCE-REVIEW-001
    -> ARCH-0001
    -> ADR-0001
    -> SPEC-0002
    -> future bounded WOPs
```

The archived review remains evidence only. Future WOPs derive requirements from
an applicable controlled revision of this specification, not directly from
historical review prose.

## 24. Conformance criteria

The architecture is conformant when:

1. exactly one fully identified, qualified, applicable, non-superseded, and
   non-revoked Authority Record resolves;
2. exactly one Mission Contract derives byte-reproducibly from its declared
   inputs and published revisions remain immutable;
3. exactly one qualified immutable WOP binds to the derived contract;
4. owner facts resolve into one REAC;
5. PMA only narrows;
6. Zeus EWI alone emits terminal initiation;
7. execution consumes the exact decision without a standard Execution Grant;
8. generalized resource claims resolve and lease without ambiguity;
9. evidence and qualification remain separate;
10. Governance, Authority effectiveness, mission planning, execution, and
    synchronization remain orthogonal without added lifecycle states;
11. EMP owns inventory, priority, dependencies, planning eligibility, and
    Governance interaction while Zeus owns deterministic selection, bounded
    adaptation, execution, recovery, qualification orchestration, and
    completion;
12. Governance, WOP, EENS, and EOS preserve their assigned boundaries;
13. EOS remains directional synchronization/reconciliation infrastructure and
    never becomes an authority source;
14. publication and synchronization remain separate;
15. notifications remain non-authoritative;
16. reboot, interruption, power loss, partial execution, duplicate dispatch,
    stale state, synchronization failure, and distributed recovery preserve
    authority, attempt identity, effect safety, and fencing;
17. autonomous selection and replay are deterministic;
18. compatibility paths cannot reach production execution; and
19. clean-checkout qualification reproduces.

Any failed criterion blocks a canonical-architecture conformance claim.

## 25. Compliance

Compliance with this specification requires evidence for every applicable
criterion in Section 24 and every implemented requirement in the future WOP's
declared scope.

A compliant implementation:

- identifies the exact approved and applicable `SPEC-0002` revision;
- preserves the information owners and authority boundaries in this document;
- proves Governance Decision-to-Authority Record issuance and deterministic
  Mission Contract derivation;
- proves Authority Record identity, approval, version, qualification,
  supersession, revocation, audit, and synchronization boundaries;
- proves the resolve, narrow, and terminal-decision separation;
- validates generalized resource conflicts and subsystem boundaries;
- demonstrates the minimal orthogonal state models;
- demonstrates EMP/Zeus handoffs, deterministic selection, resumable
  execution, effect fencing, independent qualification, and completion;
- demonstrates that EOS projections cannot create or repair authority;
- demonstrates that compatibility paths cannot initiate production execution;
- validates lifecycle, recovery, evidence, publication, synchronization, and
  notification boundaries;
- produces the evidence required by Section 21; and
- completes the applicable independent qualification and lifecycle decisions.

Partial implementation may be reported only as partial conformance. A passing
unit test, existing implementation, Draft document, WOP completion statement,
or publication event does not independently establish full compliance.

Noncompliance shall identify the failed requirement, affected component,
evidence, impact, and required disposition. It shall not be concealed by a
projection, compatibility adapter, exception inferred by an implementation
agent, or newer timestamp.

## 26. Revision history

| Version | Date | Lifecycle | Description |
|---|---|---|---|
| 1.0 | 2026-07-30 | Draft | Defined the proposed canonical Zeus component, ownership, repository, runtime, authority, execution, mission, evidence, publication, synchronization, notification, interface, state, recovery, compatibility, validation, and traceability architecture implementing ADR-0001. |
| 1.1 | 2026-07-30 | Draft | Incorporated ADR-0001 Draft 1.1 by making Authority Records authoritative and Mission Contracts derived, removing Execution Grant from the standard path, defining generalized resource conflicts, enforcing Governance/EMP/Zeus/WOP/EENS/EOS boundaries, and specifying minimal orthogonal Governance, execution, and synchronization states. |
| 1.2 | 2026-07-30 | Draft | Specified complete Authority Record identity, lineage, effectiveness, qualification, audit, and synchronization contracts; byte-reproducible Mission Contract derivation and publication; exact EMP/Zeus ownership; EOS non-authority; orthogonal state dimensions; reboot, power-loss, partial-effect, duplicate, stale-state, synchronization, and distributed recovery; and deterministic autonomous selection, resumability, evidence qualification, and horizontal-scaling readiness without adding authority objects, Execution Grants, or lifecycle states. |
| 1.3 | 2026-07-30 | Draft | Reconciled the specification to ADR-0001 Draft 1.3 by adding exact normative mappings for all 14 canonical components, 32 architectural invariants, 13 canonical interfaces, and 16 Future Implementation units; established zero-orphan bidirectional assessment-to-implementation traceability and required negative evidence without changing an architectural decision. |
| 1.4 | 2026-08-07 | Draft | Added the personal engineering operating model, risk-proportional security boundary, authorized-forward-progress rule, user-intent boundary, and procedure-first/fact-reuse contract without changing authority ownership, execution authority, lifecycle ownership, or runtime implementation. |
