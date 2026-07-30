# Lifecycle and Authority Model

Date: 2026-07-30

Status: Proposed; not operational authority

## 1. State-domain rule

Every state value is qualified by its owner. No unqualified `Active`,
`Completed`, `Blocked`, or `Authorized` status is used in an API or
authoritative record.

The target model uses three small, orthogonal state machines:

| Domain | Owner | States |
| --- | --- | --- |
| Governance | Governance | `Proposed`, `Authorized`, `Revoked` |
| Execution | Zeus runtime | `Planned`, `Ready`, `Running`, `Blocked`, `Complete`, `Failed` |
| Synchronization | EOS | `Dirty`, `Pending`, `Reconciled` |

Artifact maturity, controlled-document lifecycle, publication, evidence, and
qualification remain separately owned status or evidence domains. A new state
is added only when a demonstrable requirement cannot be represented by an
existing state plus a typed reason, condition, or evidence record.

## 2. Governance lifecycle

Owner: Governance

```text
Proposed -> Authorized -> Revoked
    \--------------------^
```

| State | Meaning |
| --- | --- |
| `Proposed` | A Governance Decision or proposed Authority Record exists, but no permission is effective. |
| `Authorized` | The Authority Record is effective within its exact scope, resource claims, conditions, and time boundary. |
| `Revoked` | Permission is no longer effective. The reason records withdrawal, denial, supersedence, expiry, closure, or explicit revocation. |

Rules:

- only an Authority Record in `Authorized` state conveys mission permission;
- the Mission Contract is a derived representation and has no independent
  Governance lifecycle;
- a Governance Decision precedes the Authority Record and is retained for
  audit;
- status changes are append-only events, not payload rewrites;
- `suspended` is represented by revocation plus a successor authorization if
  work later resumes;
- `superseded`, `expired`, and `closed` are revocation reasons;
- successor authorization and predecessor revocation occur in one authority
  transaction when atomic replacement is required; and
- execution outcome never transitions Governance state by inference.

## 3. Execution lifecycle

Owner: Zeus runtime

```text
Planned -> Ready -> Running -> Complete
   |         |         |
   +---------+---------+-> Blocked
   |         |         |
   +---------+---------+-> Failed
```

| State | Meaning |
| --- | --- |
| `Planned` | EMP selected work and a WOP describes the bounded execution, but readiness is not established. |
| `Ready` | Authority, Mission Contract derivation, WOP qualification, dependencies, resources, environment, and executor checks pass. |
| `Running` | Zeus has begun the exact bound attempt. |
| `Blocked` | A recoverable prerequisite or external condition prevents progress. |
| `Complete` | The attempt produced its required terminal outcome and evidence. |
| `Failed` | The attempt ended without satisfying its required outcome. |

Retry, resumption, and correction create or resume a specifically identified
attempt under the applicable WOP and policy. They do not add Governance states
or widen authority.

The standard execution path is:

```text
Governance Decision
  -> Authority Record
  -> derived Mission Contract
  -> qualified WOP
  -> Ready
  -> Running
  -> Complete | Blocked | Failed
```

There is no Execution Grant in the standard lifecycle. Any future need to
withhold authorization after WOP qualification requires a separately
controlled exceptional extension supported by a concrete engineering
requirement.

## 4. Synchronization lifecycle

Owner: EOS

```text
Dirty -> Pending -> Reconciled
  ^         |
  +---------+
```

| State | Meaning |
| --- | --- |
| `Dirty` | A source/projection difference exists or source advancement has not been evaluated. |
| `Pending` | EOS has accepted a bounded synchronization or reconciliation operation. |
| `Reconciled` | The declared source boundary and owned projection agree. |

Synchronization state never grants, revokes, expands, or narrows Governance
authority. A stale projection can block a consumer that requires it, but it
cannot invalidate an otherwise valid Authority Record.

## 5. Artifact and evidence statuses

WOP is an execution package, not a lifecycle authority. Its minimal artifact
status is:

```text
Draft -> Qualified -> Retired
```

Review and qualification are evidenced determinations. `Active`, `Authorized`,
and `Admitted` are not WOP authority states.

Controlled-document approval, activation, persistence, publication, and
baseline designation remain owned by their controlled-document and
publication procedures. They do not join the three mission state machines.

## 6. Dependency and prioritization architecture

### 6.1 Dependency classes

| Class | Owner | Example | Effect |
| --- | --- | --- | --- |
| Authority parent | Governance | Authority Record -> Governance Decision | Required to resolve authority |
| Planning dependency | EMP / Work Registry | ADR review before SPEC work | Affects selection |
| Work-package prerequisite | WOP | archive digest must validate | Affects qualification |
| Execution prerequisite | Zeus | required environment is available | Affects readiness |
| Resource conflict | Zeus resource coordinator | exclusive hardware claim overlaps | Affects readiness/running |
| Evidence dependency | Qualification | report consumes evidence package | Affects conclusion |
| Publication dependency | Publication procedure | exact frozen manifest | Affects publication |
| Traceability relation | Documentation/index | document indexed by DOC-0001 | Discovery only |

No dependency changes class by inference.

### 6.2 Dependency rules

- authority-parent edges form a ranked DAG;
- planning cycles fail EMP validation unless explicitly modeled as one coupled
  unit;
- WOP prerequisites cannot create authority;
- runtime blockers cannot revoke Governance authorization;
- waiver requires a Governance decision when the prerequisite is governed;
- dependency satisfaction is recorded by the owning domain; and
- derived status cites the source event or evidence digest.

### 6.3 Priority

Priority belongs exclusively to EMP planning. Governance may set policy
constraints or deadlines, but highest priority does not grant authority.
Mission authorization does not force immediate selection.

Zeus selects only work supplied by EMP planning, backed by an effective
Authority Record, and ready under its qualified WOP. Selection is planning or
orchestration state, not a Governance grant.

## 7. Generalized resource-conflict model

Every Authority Record and WOP uses resource claims rather than
repository-specific conflict keys.

```text
resource_namespace
resource_type
resource_identity
access_mode: observe | shared | exclusive
effect_class
scope_selector
lease_policy
containment_rule
```

The model supports repositories, infrastructure, services, hardware,
environments, documents, publication units, credential boundaries, and future
resource types. A new type registers taxonomy, identity, and containment
rules; it does not require an architectural change.

Governance authorizes bounded claims. WOP specifies the resources required for
the execution plan. Zeus evaluates compatibility and acquires operational
leases. EMP uses the same claims for planning forecasts. Neither a lease nor a
planning selection conveys authority.

## 8. Governance-to-planning model

Governance publishes:

- policy;
- Governance Decisions;
- Authority Records and state events;
- constraints and resource claims; and
- audit lineage.

EMP consumes those records as read-only inputs for mission planning,
dependencies, prioritization, selected focus, and Work Registry projections.
EMP may propose but cannot approve, authorize, or revoke.

An authorization event triggers an idempotent planning projection. Projection
failure raises `PLANNING_PROJECTION_STALE`; it does not invalidate the
Authority Record.

## 9. Planning-to-execution model

EMP supplies:

- selected mission/work item;
- dependency and priority state;
- expected resource demand; and
- planning constraints.

WOP supplies:

- the qualified immutable execution package;
- exact effects and prohibited effects;
- resource claims;
- checkpoints;
- evidence requirements; and
- rollback.

Zeus independently resolves:

- effective Authority Record;
- derived Mission Contract identity and digest;
- WOP binding and qualification;
- exact requested-effect subset;
- repository/environment identity and exact attempt boundary;
- resource compatibility and leases;
- executor eligibility; and
- execution readiness and blockers.

Planning cannot dispatch by itself. Zeus cannot select unrelated work, widen
the request, or create Governance authority.

## 10. Subsystem responsibility boundaries

| Subsystem | Owns | Does not own |
| --- | --- | --- |
| Governance | policy, approval, authority, audit | planning, orchestration, execution, observation, synchronization |
| EMP | planning and mission management | approval, authority, dispatch |
| Zeus | orchestration and reasoning | Governance decisions or planning source truth |
| WOP | immutable execution package | authority or orchestration |
| EENS | observation and notification | decisions, execution state, synchronization |
| EOS | synchronization and reconciliation | authority, planning, orchestration |

No subsystem may obtain another subsystem's responsibility merely by copying
its state.

## 11. Synchronization architecture

### 11.1 Source-of-truth directions

```text
Governance records ----> EMP authority projection
        |--------------> Project/mission status view
        |--------------> EOS/resume view
        |--------------> audit index

EMP -------------------> planning and selection views
Zeus events -----------> execution status and evidence views
Qualification ---------> qualification views
EENS ------------------> observation and notification views
```

Arrows are one-way. No projection writes back to the source.

### 11.2 Projection protocol

Each projector:

1. reads a source revision/event cursor;
2. deterministically renders its candidate;
3. atomically writes only its owned projection;
4. records source digest, projector version, output digest, and cursor;
5. supports idempotent replay;
6. reports lag or conflict;
7. never alters the source decision; and
8. never blocks source authorization merely because a projection is stale.

Protected execution may require projections to be current only when the
consumer cannot resolve the canonical source directly. Direct resolution plus
projection comparison is preferred.

## 12. Repository authority boundary

The repository is:

- the controlled persistence location for policy, architecture, Governance
  Decisions, Authority Records, derived contracts, schemas, and evidence;
- an integrity and review boundary;
- a source for deterministic authority resolution; and
- a historical audit log through Git.

The repository is not:

- the origin of human Governance authority;
- a substitute for an attributable decision;
- an automatic approver because a file exists;
- an authority source merely because a record is indexed;
- a reason to treat Project State or Work Registry as Governance; or
- permission to execute because the filesystem is writable.

Repository writes have four classes:

| Class | Examples | Authority effect |
| --- | --- | --- |
| Governance source | signed Governance Decision and Authority Record | may create exact effect after validation |
| Planning source | EMP registry and roadmap | none |
| Execution/evidence source | WOP, attempt, receipt, report | none beyond consumed authority |
| Projection | Project summary, EOS, dashboard | none |

## 13. Mission replacement

One authority transaction:

1. locks the affected resource-claim namespace;
2. validates the predecessor Authority Record and current event;
3. validates the successor decision, authority parent, scope, and resource
   claims;
4. creates the successor Authority Record and `Authorized` event;
5. appends predecessor `Revoked` with reason `SUPERSEDED`;
6. derives the successor Mission Contract;
7. verifies post-transaction resolution;
8. commits or restores before-images; and
9. emits a receipt.

EMP, Project State, and EOS projections follow asynchronously.

## 14. Recovery without bootstrap exceptions

The ultimate authority can issue a signed, bounded Governance Decision whose
subject is authority restoration. That decision:

- identifies the broken records;
- authorizes only repair preparation, review, validation, and publication;
- denies product or unrelated execution;
- expires on repair completion or a fixed deadline; and
- produces the authoritative repair Authority Record.

The repair Mission Contract is derived from that Authority Record. Because
authority derives directly from the ultimate authority rather than from the
broken mission path, this is ordinary root authority, not an exception. The
same validation, signatures, evidence, review, and audit controls apply.
