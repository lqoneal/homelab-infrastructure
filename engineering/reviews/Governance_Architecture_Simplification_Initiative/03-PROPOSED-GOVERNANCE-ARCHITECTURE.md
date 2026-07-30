# Proposed Governance Architecture

Date: 2026-07-30

Status: Proposed; not approved, active, implemented, or published

## 1. Design objectives

The target architecture shall:

- preserve human Governance authority and auditability;
- allow Governance to authorize Governance work without recursion;
- represent each authoritative fact once;
- separate decision, planning, execution, evidence, and projection state;
- preserve strict review and high-risk approval gates;
- allow Zeus to orchestrate autonomously only inside explicit authority;
- fail closed on ambiguity or integrity failure;
- support safe mission replacement and concurrent non-conflicting missions;
- make synchronization retryable and non-authorizing; and
- retain historical evidence during migration.

## 2. Four-plane model

### 2.1 Governance plane

Owns:

- policy;
- approval;
- Governance decisions;
- Authority Records;
- authorization and revocation;
- authority delegation;
- exceptions and risk acceptance; and
- audit of governance decisions and authority lineage.

The Governance plane does not own mission planning, priority, orchestration,
execution readiness, work-package construction, checkpoints, technical
project condition, observation delivery, or synchronization status.

### 2.2 Planning plane

Owns:

- mission proposals;
- roadmap membership;
- phases and work breakdown;
- dependencies;
- priority;
- queue position;
- selected focus;
- capacity;
- deferral; and
- planning completion.

EMP owns this plane. The Work Registry remains the canonical planning store.
It references Governance records but never gates creation of those records
and never grants authority.

### 2.3 Execution plane

WOP owns:

- work-package construction and validation;
- execution-plan qualification;
- requested effect calculation;

Zeus owns:

- orchestration and reasoning;
- mission selection under EMP planning constraints;
- authority and readiness resolution;
- resource-conflict evaluation and reservation;
- dispatch eligibility;
- execution attempts;
- checkpoints;
- pause/resume;
- outcome; and
- runtime diagnostics.

WOP packages and Zeus consume authority. Neither creates, widens, revokes, or
audits Governance authority.

### 2.4 Evidence and projection plane

EENS owns:

- immutable evidence;
- observation and notification events;
- durable delivery and replay state; and
- consumer checkpoints.

EOS owns:

- synchronization and reconciliation;
- derived operational projections; and
- synchronization state.

Domain evidence owners retain:

- decision and publication receipts;
- qualification reports;
- Project State technical summaries;
- dashboards;
- derived mission status.

Evidence proves facts but does not become authority unless an attributable
Governance decision explicitly consumes it. Projections are replaceable and
rebuildable. EENS does not decide, and EOS does not orchestrate.

## 3. Canonical record model

### 3.1 Governance Decision Record

The Governance Decision Record is the permanent, attributable expression of
the Chief Engineer's decision. Draft PROC-0008 contains a useful proposed
shape and should be matured rather than replaced.

Minimum fields:

- decision ID;
- decision maker and authenticated principal;
- superior authority;
- exact subject ID and digest;
- decision type;
- disposition;
- authorized and denied effects;
- effective time;
- conditions;
- expiry;
- supersedence or revocation rules;
- evidence reviewed; and
- signature and canonical digest.

An approved decision authorizes creation of an Authority Record. The decision
captures the human governance act; it is not the execution-facing Mission
Contract and does not perform orchestration. It does not depend on a Mission
Contract when it is the root decision from which mission authority is
recorded.

### 3.2 Authority Record

The Authority Record is the immutable authoritative governance object. It is
created from an approved Governance Decision and is the only standard
mission-level record that grants permission.

Minimum fields:

- authority-record ID and revision;
- decision ID and digest;
- one superior `authority_parent`;
- authorized subject and purpose;
- allowed and denied effect classes;
- governed resource claims;
- constraints and stop conditions;
- eligible principal or executor classes;
- effective time and expiry;
- revocation and supersedence rules;
- required review and qualification policy;
- canonical digest; and
- signature binding.

The Authority Record does not contain planning priority, WOP lifecycle,
execution progress, Project State, or synchronization status. Its governance
state is derived from append-only status events and is limited to `Proposed`,
`Authorized`, or `Revoked`. Expiry, supersedence, and closure are revocation
reasons, not additional core states.

### 3.3 Mission Proposal

A Mission Proposal is planning input only. It may be created without execution
authority because it has no effects.

Minimum fields:

- proposal ID;
- objective;
- proposed scope;
- proposed outcomes;
- affected repositories;
- risk class;
- proposed phases and dependencies;
- requested authority;
- author; and
- evidence/assessment references.

States: `draft`, `reviewable`, `withdrawn`, `decided`.

Proposal intake replaces the overloaded Governance “Submitted” and “Admitted”
states. Receipt means only that a proposal exists.

### 3.4 Mission Contract v2

Mission Contract v2 is an immutable mission representation derived
deterministically from an effective Authority Record. It represents what
mission has been authorized; it is not itself the governance authority.

Minimum fields:

- contract ID and revision;
- mission ID;
- proposal, decision, and Authority Record references and digests;
- objective;
- allowed scope and excluded scope;
- permission/effect classes;
- constraints and stop conditions;
- eligible executor classes;
- review and qualification policy;
- repository identity constraints;
- effective time and expiry;
- governed resource claims;
- supersedes references;
- canonical digest; and
- derivation metadata.

The payload shall not contain:

- Work Registry lifecycle;
- queue position or priority;
- Project State;
- WOP lifecycle;
- execution checkpoints;
- synchronization status;
- completion-report availability;
- mutable approval fields;
- current HEAD unless the mission is intentionally single-baseline; or
- broad operational role inventories unrelated to authority.

The term “Mission Contract” may be retained to minimize controlled-document and
consumer churn, but its semantics must be singular: it is the derived contract
for an authorized mission, not a composite of registry plus WOP and not an
authority node.

### 3.5 Authority Status Event

Governance status changes are append-only events against the Authority Record,
not mutations of the Authority Record or Mission Contract payload:

- `PROPOSED`;
- `AUTHORIZED`;
- `REVOKED`.

Each event binds the Authority Record digest, predecessor event digest, actor,
superior authority, timestamp, rationale, reason code, conditions, and
signature. `SUPERSEDED`, `EXPIRED`, `CLOSED`, and `WITHDRAWN` are reason codes
for `REVOKED` or `PROPOSED` disposition rather than additional lifecycle
states. Current state is a deterministic fold over the event chain.

### 3.6 Work Plan and Work Registry

The Work Registry contains the Mission, Phase, Work Item, dependency, priority,
and deferral projections. Its state set should use planning terms:

- mission: `proposed`, `planned`, `selected`, `in_progress`, `blocked`,
  `completed`, `cancelled`, `deferred`;
- work item: `proposed`, `ready`, `selected`, `in_progress`, `blocked`,
  `completed`, `cancelled`, `deferred`.

`authorized` should not be a planning state. A derived field such as
`authority_status: Proposed|Authorized|Revoked` may be displayed with a source
Authority Record and event digest, but it is never user-editable.

### 3.7 Work Package

A WOP becomes an immutable execution plan, not an authority source. It binds:

- mission and optional phase/work-item identities;
- Authority Record and derived Mission Contract digests;
- exact requested effects;
- procedure;
- inputs and outputs;
- dependencies;
- checkpoints;
- evidence requirements;
- rollback;
- executor compatibility; and
- package digest.

WOP artifact states describe package readiness only: `draft`, `qualified`,
`retired`. Review and qualification results remain separate evidence. Terms
such as `Authorized` or `Active` should be removed from the package lifecycle.

### 3.8 Exceptional delayed-execution extension

The standard mission lifecycle has no Execution Grant:

```text
Governance Decision
  -> Authority Record
  -> derived Mission Contract
  -> qualified WOP
  -> Zeus execution
```

Any review, dual control, timing, or high-risk restriction required before
execution is expressed in the Authority Record and WOP qualification policy.
Zeus revalidates those conditions immediately before dispatch.

If a future demonstrable requirement needs authorization to be intentionally
withheld after the WOP is qualified, it requires a separately controlled
exception specification. That extension must name its narrow purpose, must not
enter the standard lifecycle, and must not be inferred from planning or
runtime state.

### 3.9 Execution Attempt

Execution uses the orthogonal state model:

`Planned -> Ready -> Running -> Complete|Failed`, with `Blocked` reachable
from `Planned`, `Ready`, or `Running`.

An attempt binds exact repository state and consumes an effective Authority
Record, its derived Mission Contract, and a qualified WOP. A blocked or failed
attempt does not alter Governance authorization.

### 3.10 Evidence and projections

Evidence is append-only. Project State, Work Registry authority status, EOS,
resume, dashboards, and status output are deterministic projections.
Projection lag is reported as a synchronization observation. It cannot
retroactively invalidate an otherwise valid signed decision.

## 4. Authority graph

Only these records may be authority nodes:

```text
rank 0  Ultimate Engineering Authority
rank 1  Charter/delegation or direct root Governance Decision
rank 2  Governance Baseline or delegated Governance Decision
rank 3  Bounded Authority Record
```

Rules:

1. every non-root node has exactly one authority parent;
2. the parent is already effective;
3. parent rank is lower than child rank;
4. a child can only narrow parent authority;
5. Mission Contracts, traceability, workflow, evidence, registry, Project
   State, WOP, and projection records cannot be authority parents;
6. revocation or expiry is resolved before execution;
7. ambiguity or a repeated node fails closed; and
8. direct root Governance decisions are attributable exercises of existing
   human authority, not bootstrap exceptions.

## 5. Governance decision to execution flow

```text
Mission Proposal
  -> deterministic proposal validation
  -> human Governance review
  -> signed Governance Decision
  -> immutable Authority Record
  -> deterministically derived Mission Contract v2
  -> asynchronous planning projections
  -> WOP preparation and qualification
  -> execution readiness evaluation
  -> Zeus dispatch
  -> execution attempt
  -> evidence and qualification
  -> Governance revocation or closure disposition when applicable
  -> asynchronous projections
```

No step points back to authorize an earlier step.

## 6. Admission and activation model

### 6.1 Remove Mission Admission as authority

Retain proposal intake and package validation, but name results precisely:

- `PROPOSAL_RECEIVED`;
- `PROPOSAL_INVALID`;
- `PACKAGE_VALID`;
- `PACKAGE_INVALID`;
- `DECISION_BLOCKED`.

None grants authority.

### 6.2 Replace Admission plus Activation with Authorize

One `authorize-mission` operation:

1. validates decision identity, signature, subject digest, authority parent,
   schema, scope, and governed resource claims;
2. creates the immutable Authority Record;
3. appends the initial `AUTHORIZED` status event;
4. derives the immutable Mission Contract from the Authority Record;
5. atomically revokes explicitly named predecessor Authority Records when
   requested;
6. verifies deterministic resolution; and
7. emits a transaction receipt.

The transaction does not write Work Registry, Project State, WOP, EOS, or
runtime records.

### 6.3 Compatibility

During migration:

- legacy `candidate` maps to proposal state, not authority;
- legacy `active` maps to an imported Authority Record and `AUTHORIZED` event;
- legacy `suspended`, `revoked`, `superseded`, `expired`, and `completed` map
  to `REVOKED` events with typed reasons;
- `admit` commands become proposal/package validation aliases;
- `activate` becomes a deprecated alias for `authorize-mission`; and
- compatibility output must identify itself as a projection.

## 7. Conflict and concurrency model

Replace global one-active-contract cardinality and repository-specific conflict
keys with generalized resource claims. Each claim contains:

- resource namespace;
- resource type;
- stable resource identity;
- access mode: `observe`, `shared`, or `exclusive`;
- operation/effect class;
- scope or selector;
- lease and freshness policy; and
- parent/child containment rules.

Initial resource types include repository, infrastructure, service, hardware,
environment, controlled document, publication unit, and credential boundary.
New resource types register taxonomy and containment rules without changing
the conflict-evaluation architecture.

Rules:

- multiple authorized missions may coexist;
- planning selects current focus independently;
- compatible observation and shared claims may run concurrently;
- only incompatible execution claims are serialized;
- a Zeus execution attempt acquires leases for its qualified WOP resource
  claims without creating authority;
- successor authorization can atomically revoke a predecessor where resource
  claims and subject scope overlap; and
- policy may declare exclusivity for any resource type and high-risk effect
  class.

## 8. Autonomous Zeus boundary

Zeus may autonomously:

- inventory proposals and authorized missions;
- consume EMP dependencies, priorities, and selected work;
- construct WOP drafts;
- validate and qualify;
- reason about readiness and resource conflicts;
- execute effects within an effective Authority Record through its derived
  Mission Contract and qualified WOP;
- pause on blockers;
- collect evidence;
- request EOS reconciliation; and
- propose closeout.

Zeus may not autonomously:

- originate a Governance decision;
- expand authority;
- waive a review or qualification policy;
- accept its own work when independent acceptance is required;
- publish or perform destructive/external effects not already authorized and
  qualified;
- convert projection state into authority; or
- repair authority without a direct attributable Governance decision.

## 9. Architectural invariants

1. One owner per fact.
2. One immutable Authority Record owns mission authorization.
3. Each Mission Contract derives from exactly one effective Authority Record.
4. Authority events are append-only.
5. Governance owns only policy, approval, authority, and audit.
6. EMP plans; Zeus orchestrates; WOP packages; EENS observes; EOS reconciles.
7. Planning never grants authority.
8. WOPs describe work; they do not authorize it.
9. The standard lifecycle has no Execution Grant.
10. Evidence never selects a Governance disposition.
11. Projections never become prerequisites for source creation.
12. Exact HEAD binds attempts and publications, not every long-lived mission.
13. Every protected effect resolves one unambiguous authority chain and one
    compatible set of generalized resource claims.
14. Every authority successor is transactional with predecessor disposition.
15. Missing or conflicting authority always fails closed.
