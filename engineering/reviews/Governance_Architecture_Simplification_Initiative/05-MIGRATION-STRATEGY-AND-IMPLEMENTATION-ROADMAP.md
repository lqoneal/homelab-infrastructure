# Migration Strategy and Implementation Roadmap

Date: 2026-07-30

Status: Proposed roadmap; no implementation authorization

## 1. Migration principles

- Preserve all current records and their historical meaning.
- Evolve existing controlled documents before creating replacements.
- Introduce no live behavior until the target architecture is controlled and
  qualified.
- Add new schemas and resolvers before mutating current authority.
- Run shadow comparison before enforcement.
- Maintain an explicit rollback point at every cutover.
- Migrate consumers before retiring producers.
- Never infer an imported authority state from a planning label alone.

## 2. Migration sequence

### Phase 0 — Decision and baseline preparation

Purpose: convert this proposal into controlled architecture.

Deliverables:

- Governance review disposition;
- ADR decision for the target authority model;
- authoritative technical specification;
- exact controlled-document change matrix;
- qualification plan;
- migration inventory;
- current-authority snapshot and hashes; and
- rollback policy.

Exit criteria:

- architecture is approved;
- unresolved decisions below are answered;
- no implementation is authorized merely by this assessment.

### Phase 1 — Controlled-document evolution

Revise the existing documents in one synchronized governance change:

- POL-0001;
- PROC-0001, PROC-0002, PROC-0004, and proposed PROC-0008;
- SPEC-0001, SPEC-0005, SPEC-0006, SPEC-0011, SPEC-0012, and SPEC-0013;
- applicable EWO/WOP standards and templates;
- authority and transaction design records;
- DOC-0001; and
- repository/EOS authority mapping.

Required results:

- one definition of Authority Record as the governance authority;
- one definition of Mission Contract as a derived mission representation;
- one authority-parent relation;
- direct root Governance decision semantics;
- minimal, domain-qualified Governance, execution, and synchronization state
  models;
- clear proposal, authorization, planning, execution, and projection boundaries;
- explicit Governance, EMP, Zeus, WOP, EENS, and EOS responsibility
  boundaries;
- a generalized resource-conflict model;
- no Execution Grant in the standard lifecycle; and
- controlled compatibility rules.

### Phase 2 — Offline schemas and validators

Implement without live activation:

- Governance Decision schema;
- Authority Record schema;
- Mission Proposal schema;
- Mission Contract v2 schema;
- Authority Status Event schema;
- authority-ledger transaction schema;
- generalized resource-claim and conflict model;
- ranked authority-DAG validator;
- event-chain validator;
- compatibility mapping validator; and
- fixtures for all failure modes.

Qualification:

- canonical byte determinism;
- signature and digest tests;
- parent cardinality and rank;
- narrowing-only authority;
- successor transaction rollback;
- event replay;
- duplicate/conflict rejection;
- invalid projection non-authority; and
- root governance repair without Mission Contract recursion.

### Phase 3 — Shadow resolver and projections

Add a read-only v2 resolver alongside the legacy resolver.

For each current mission, compare:

- authority decision;
- effective scope;
- permissions;
- lifecycle;
- blockers;
- current planning selection;
- required WOP;
- execution readiness; and
- next permitted effect.

The legacy resolver remains enforcement authority during this phase. Every
disagreement is classified and reviewed. No silent fallback is allowed.

Add one-way projectors for Work Registry, Project State/resume, and EOS.
Projection failures are reported but cannot alter the v2 authority result.

### Phase 4 — Current-authority import

Construct reviewed import records for each still-effective legacy authority:

- immutable Authority Record;
- deterministically derived Mission Contract v2;
- initial authority event;
- source legacy contract digest;
- applicable approval/activation evidence;
- authority parent;
- scope and permission mapping;
- generalized resource claims;
- WOP compatibility binding; and
- expiry/closeout rule.

Import does not rewrite legacy records. Every imported authority requires an
attributable Governance adoption decision.

The current active publication contract requires an explicit disposition:

- import as a bounded v2 authorization if work remains;
- close it under legacy authority before cutover if complete; or
- atomically supersede it with an approved successor during cutover.

### Phase 5 — Enforcement cutover

Cut over one protected effect class at a time:

1. read-only inspection;
2. repository-local evidence generation;
3. non-runtime documentation changes;
4. implementation changes;
5. controlled publication;
6. external effects;
7. destructive/high-risk work.

For each class:

- v2 resolution becomes authoritative;
- legacy output remains observational;
- differences fail closed;
- rollback restores the prior resolver;
- qualification proves no authority broadening.

### Phase 6 — Admission and activation simplification

After v2 enforcement is qualified:

- replace mission admission with proposal/package intake vocabulary;
- replace activation with `authorize-mission`;
- move exact HEAD validation to WOP qualification and execution-attempt
  boundaries;
- remove Work Registry, Project State, WOP lifecycle, and EOS writes from the
  authority transaction;
- implement atomic successor/predecessor Authority Record events;
- replace repository-wide active cardinality with generalized resource
  conflict evaluation;
- remove Execution Grant from the core mission lifecycle;
- update CLI and status output with domain-qualified state names.

### Phase 7 — Consumer migration

Migrate:

- Engineering Work Initiation;
- `engctl execution` and resume;
- Zeus mission discovery/resolution/eligibility;
- WOP generation and lifecycle;
- dispatch;
- Progressive gate authority;
- evidence and qualification;
- reconciliation and closeout;
- EOS synchronization;
- notifications; and
- operator documentation.

Each consumer must prove it does not:

- read legacy authority as primary;
- promote planning/projection state into authority;
- mutate an Authority Record or derived Mission Contract payload;
- rely on unqualified lifecycle labels; or
- bypass Authority Record or WOP qualification policy.

### Phase 8 — Legacy retirement

Only after consumer-complete evidence:

- freeze legacy Mission Contract schemas and activation transactions;
- mark legacy admission/activation commands compatibility-only;
- remove legacy writes;
- preserve historical contracts, approvals, transactions, and evidence;
- remove duplicate editable mission descriptions;
- retire reverse or multi-owner synchronization;
- qualify clean-checkout reproducibility; and
- publish the simplified Governance baseline.

## 3. Work that can be eliminated

The following work should not be carried forward:

- building another bootstrap exception;
- adding a second active-contract replacement service around the current
  multi-record transaction;
- extending Work Registry authority semantics;
- making EOS synchronization a stronger activation prerequisite;
- reconciling more lifecycle fields into Project State;
- introducing another admission layer;
- maintaining candidate contracts as mutable quasi-authority;
- building another general relationship-graph authority resolver; and
- creating a third editable Mission Contract store.

## 4. Work that should be merged

| Current work | Merge target |
| --- | --- |
| manual Governance submission plus Mission Contract admission plus activation approval | Governance Decision, immutable Authority Record, and `authorize-mission` transaction |
| YAML contract lifecycle mutations | immutable Authority Record, status-event chain, and derived Mission Contract |
| registry authority labels | derived authority-status projection |
| WOP `Active/Authorized` lifecycle | package review/qualification lifecycle |
| activation reconciliation plus EOS sync | independent idempotent projectors |
| bootstrap detection/correction exception | ordinary direct root Governance repair decision |
| multiple mission description stores | Mission Proposal + Authority Record + derived Mission Contract, with read-only projections |

## 5. Work that should be deferred

- generalized multi-user quorum Governance;
- cross-repository distributed authority transactions;
- automatic Governance decision making;
- dynamic policy synthesis;
- broad repository reorganization;
- historical record rewriting;
- advanced scheduling;
- dashboard redesign; and
- any delayed-execution authorization extension without a demonstrated
  requirement and separate controlled design.

These are not needed to eliminate bootstrapping.

## 6. Verification gates

| Gate | Required proof |
| --- | --- |
| Architecture | authority DAG is acyclic; one owner per fact; lifecycle domains are disjoint |
| Schema | canonical payloads and event chains validate deterministically |
| Security | signatures, identity, revocation, expiry, narrowing, and generalized resource conflicts fail closed |
| Migration | every effective legacy authority has an attributable disposition |
| Shadow | legacy/v2 differences are zero or reviewed and accepted |
| Projection | stale/corrupt projection cannot create, widen, or revoke authority |
| Execution | requested effects are a subset of Authority Record and qualified WOP; exact attempt HEAD is bound |
| Replacement | successor/predecessor transaction is atomic and rollback-safe |
| Recovery | root Governance repair works without pre-existing Mission Contract authority |
| Retirement | zero primary legacy consumers and complete historical preservation |

## 7. Proposed implementation mission sequence

These are recommendations, not active missions:

1. **GAS-DECISION-001** — controlled review and architecture decision.
2. **GAS-DOCS-001** — synchronized controlled-document revisions.
3. **GAS-SCHEMA-001** — offline v2 record schemas and validators.
4. **GAS-RESOLVER-SHADOW-001** — read-only v2 resolution and comparison.
5. **GAS-PROJECTION-001** — one-way projection services.
6. **GAS-IMPORT-001** — reviewed current-authority import package.
7. **GAS-CUTOVER-001** — staged enforcement cutover.
8. **GAS-CONSUMER-MIGRATION-001** — full consumer migration.
9. **GAS-RETIREMENT-001** — legacy write-path retirement and baseline
   publication.

Each mission requires its own separately authorized Authority Record under the
then-effective governance model.

## 8. Estimated critical path

```text
Architecture decision
  -> controlled-document suite
  -> schemas/validators
  -> shadow resolver
  -> current-authority import
  -> staged cutover
  -> consumer migration
  -> retirement and publication
```

Projection work can proceed in parallel with shadow resolution after the
schemas stabilize. Consumer inventory can proceed read-only during the
controlled-document phase. No live cutover should precede a reviewed import
disposition for the current active contract.

## 9. Rollback

Before each enforcement step:

- capture exact source and resolver versions;
- capture current authority and event-chain digests;
- record affected consumers;
- preserve legacy read behavior;
- prohibit dual writers;
- define the rollback command and success checks; and
- verify that rollback does not erase v2 evidence.

Rollback changes which resolver enforces effects. It does not rewrite
Governance decisions or execution evidence.
