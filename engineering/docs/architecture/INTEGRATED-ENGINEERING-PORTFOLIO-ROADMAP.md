---
roadmap_id: INTEGRATED-ENGINEERING-PORTFOLIO-ROADMAP
title: Integrated Engineering Portfolio Roadmap
version: 0.1
classification: AUTHORITATIVE_PLANNING_ROADMAP_CANDIDATE
lifecycle_state: CANDIDATE_PENDING_OPERATOR_REVIEW
persistence_status: RECORDED_NOT_PUBLISHED
source_of_truth: false
scope: Operation Beta cross-system engineering portfolio sequencing
operation_id: OPERATION-BETA
mission_id: MISSION-BETA-562F443E16C69401
repository: homelab-6bd83f9079d6fc57
published_baseline: 70f6671239f9d4c561960a87216765eef758a949
authority_source: engineering/docs/operations/OPERATION-BETA-CHARTER.md
governing_procedure: docs/procedures/PROC-0009-ROADMAP_PLANNING_RECORDING_PROCEDURE.md
predecessor: none
successor: none
eos_projection: NOT_APPLIED
execution_authority: NONE
publication_authority: ENGINEERING_GOVERNANCE_REVIEW_REQUIRED
---

# Integrated Engineering Portfolio Roadmap

## 1. Purpose and status

This record reconciles the current Zeus Operational Alpha path with the
converged WOP/Managed Handoff, EENS, and EMP development tracks. It is the
proposed portfolio-level planning reference for cross-system ordering and
dependencies. It is recorded for operator review and is not yet a published
or active controlling roadmap.

This record does not authorize implementation, execution, provider
invocation, repository mutation, acceptance, publication, EOS synchronization,
or any lifecycle advancement. Missions, WOPs, approvals, execution records,
controlled documents, EOS, and subsystem roadmaps retain their existing
authority and ownership.

The existing Operation Beta roadmap remains the published operation-level
planning baseline. The existing Zeus candidate roadmap remains a separate
Zeus-scope planning candidate. This portfolio record adds cross-system
sequencing without replacing either source before governance review.

## 2. Record identity and provenance

| Field | Value |
|---|---|
| `ROADMAP_ID` | `INTEGRATED-ENGINEERING-PORTFOLIO-ROADMAP` |
| `REVISION` | `0.1` |
| `CLASSIFICATION` | `AUTHORITATIVE_PLANNING_ROADMAP_CANDIDATE` |
| `LIFECYCLE_STATE` | `CANDIDATE_PENDING_OPERATOR_REVIEW` |
| `PERSISTENCE_STATUS` | `RECORDED_NOT_PUBLISHED` |
| `OPERATION` | `OPERATION-BETA` |
| `MISSION_CONTEXT` | `MISSION-BETA-562F443E16C69401` |
| `REPOSITORY` | `homelab-6bd83f9079d6fc57` |
| `PUBLISHED_BASELINE` | `70f6671239f9d4c561960a87216765eef758a949` |
| `CANONICAL_ZEUS_ROADMAP_MUTATION` | `NO` |
| `EOS_PROJECTION` | `NOT_APPLIED` |
| `EXECUTION_AUTHORITY` | `NONE` |

Primary planning inputs:

- `engineering/docs/architecture/OPERATION-BETA-ROADMAP.md`
- `engineering/docs/architecture/ZEUS-CANONICAL-DEVELOPMENT-ROADMAP.md`
- `engineering/docs/architecture/ZEUS-ROADMAP-INTEGRATION-ROADMAP.md`
- `engineering/evidence/operation-beta/WOP-MANAGED-HANDOFF-CONVERGENCE-ASSESSMENT.md`
- `engineering/evidence/operation-beta/CM-01-CM-06-CANONICAL-ZEUS-ROADMAP-INTEGRATION-ASSESSMENT.md`
- `engineering/evidence/operation-beta/EENS-CURRENT-STATE-AND-DEVELOPMENT-ROADMAP-ASSESSMENT.md`
- `engineering/evidence/operation-beta/EMP-CENTRALIZED-ENGINEERING-MANAGEMENT-PLATFORM-ASSESSMENT.md`
- `engineering/evidence/operation-beta/ZEUS-CM-EENS-EMP-INTEGRATED-ROADMAP-RECONCILIATION-ASSESSMENT.md`
- `docs/procedures/PROC-0009-ROADMAP_PLANNING_RECORDING_PROCEDURE.md`

## 3. Ownership model

| Concern | Canonical owner | Portfolio role |
|---|---|---|
| Mission facts, eligibility, and mission lifecycle | Mission authority / applicable Mission Contract | Dependency and readiness input |
| WOP contract and work-unit semantics | WOP authority and Zeus Stage 1 | Contract source for CM work |
| Engineering authority and execution | Zeus | Primary OA critical-path owner |
| Provider sandbox and technical permission | Provider/runtime | Security enforcement boundary |
| Events and notification delivery | EENS (`services/eens`) | Event record and delivery track |
| Engineering state and synchronization | EOS | External authoritative state/sync boundary |
| Portfolio coordination and operator projections | EMP / existing `engctl` interfaces | Centralized application track |
| Repository/project state | Project/repository owners and existing tooling | Reconciled input, not copied authority |
| Roadmap governance and publication | Engineering Governance | Review, qualification, and publication owner |

The portfolio roadmap owns cross-system sequencing only. It does not create a
second mission registry, WOP store, authority database, event store, provider
registry, execution monitor, acceptance system, or EOS authority.

## 4. Roadmap state model

Every portfolio item uses these planning fields:

```text
TRACK
ITEM_ID
OBJECTIVE
STATUS
DEPENDENCIES
BLOCKS
BLOCKED_BY
PARALLEL_ELIGIBILITY
AUTHORITY_SOURCE
ROADMAP_OWNER
NEXT_ACTION
IMPLEMENTATION_AUTHORIZED
```

Planning lifecycle values are:

```text
COMPLETE | ACTIVE | READY | PLANNED | BLOCKED | DEFERRED | SUPERSEDED
```

`READY` and `PLANNED` are planning states only. They never imply an approved
WOP, operator approval, execution authorization, provider invocation, or
repository mutation.

## 5. Tier 0 — historical P5-G6 capability baseline

| Track | Item | Status | Dependencies | Blocks | Parallel eligibility | Authority source | Next action |
|---|---|---|---|---|---|---|---|
| Zeus historical capability | `P5-G6` — Execution Monitoring Foundation | `ACCEPTED / PUBLISHED EVIDENCE; NO NATIVE BETA MISSION BINDING` | Historical P5 evidence | Supports later execution lifecycle | Reused by all downstream tracks | Zeus canonical roadmap and P5-G6 evidence | Preserve traceability; no rerun or mission inference |

P5-G6 is retained as an historical/evidence coordinate for the execution and
monitoring capability that was demonstrated and accepted. No native Operation
Beta mission binding is established by the P5 identifier. CM, EENS, and EMP
must reuse the verified capability where their contracts require it rather
than recreate it.

## 6. Tier 1 — Operation Beta current development path

Operation Beta is the current engineering context. The P5 identifiers below
remain unbound planning/capability coordinates in this portfolio candidate;
they are not native Beta missions and do not independently authorize,
select, admit, or execute work. Any future execution requires an authoritative
Beta mission/capability binding and separate authorization.

| Order | Item | Objective | Status | Depends on | Blocks | Parallel eligibility | Owner |
|---:|---|---|---|---|---|---|---|
| 1 | `P5-G7` — Controlled Pause / Resume | Historical/planning capability coordinate; future disposition unresolved | `UNBOUND / NOT_EXECUTABLE` | P5-G6 evidence; future Beta binding required | None established | Planning only | Zeus roadmap owner |
| 2 | `P5-G8` — Provider Failure Recovery | Historical/planning capability coordinate; future disposition unresolved | `UNBOUND / NOT_EXECUTABLE` | Future Beta binding required | None established | Planning only | Zeus roadmap owner |
| 3 | `P5-G9` — Execution Completion Foundation | Historical/planning capability coordinate; future disposition unresolved | `UNBOUND / NOT_EXECUTABLE` | Future Beta binding required | None established | Planning only | Zeus roadmap owner |
| 4 | `P5-G10` — Phase 5 Closeout | Historical/planning capability coordinate; future disposition unresolved | `UNBOUND / NOT_EXECUTABLE` | Future Beta binding required | None established | Planning only | Zeus roadmap owner |
| 5 | `Phase 6` — Execution Result Qualification | Qualify evidence/completion, obtain required operator decisions, and prepare reconciliation | `PLANNED` | Phase 5 closeout | Phase 7 | Supporting evidence work may parallelize | Zeus / qualification owners |
| 6 | `Phase 7` — Mission Qualification and Closeout | Determine contract satisfaction, reconcile controlled records/repository/EOS, and close | `PLANNED` | Phase 6 | Later portfolio expansion | No implicit publication | Zeus / governance / EOS owners |

Policy: `CM_BLOCKS_P5_G7=NO`, `CM_BLOCKS_P5_G8=NO`,
`EENS_BLOCKS_P5_G7=NO`, `EENS_BLOCKS_P5_G8=NO`, `EMP_BLOCKS_P5_G7=NO`, and
`EMP_BLOCKS_P5_G8=NO`.

## 7. Tier 2 — Operation Beta-supporting parallel tracks

These tracks may proceed only through separately authorized missions with
published inputs, isolated authority boundaries, and independent
qualification. Their inclusion does not alter the Zeus critical path.

### 7.1 Converged WOP / Managed Handoff (`CM`)

The former WOP-M and MH roadmaps are superseded as independent development
tracks. Managed Handoff is a subordinate execution work request within the WOP
execution contract; it is not a peer subsystem.

| Item | Objective | Status | Dependencies | Blocks | Parallel eligibility | Owner |
|---|---|---|---|---|---|---|
| `CM-01` | Converge WOP package/gate/execution contract and machine-readable work-unit semantics | `PLANNED / OB-SUPPORTING` | WOP-M1 convergence baseline | None established for current native Beta missions | Yes | WOP / Zeus Stage 1 |
| `CM-02` | Converge resolver, submission, admission, and eligibility paths using existing Zeus intake | `PLANNED / OB-SUPPORTING` | CM-01; current WOP/mission resolvers | None established for current native Beta missions | Yes | Zeus Stage 1 |

`CM-01 → CM-02` is the supporting Operation Beta portion. It must not create a
second handoff command family, authority store, or execution path.

### 7.2 EENS (`services/eens`)

EENS is durable engineering event-record and notification infrastructure. It
does not own mission, WOP, execution, acceptance, provider, project,
repository, or EOS authority.

| Item | Objective | Status | Dependencies | Blocks | Parallel eligibility | Owner |
|---|---|---|---|---|---|---|
| `EENS-A` | Stabilize event envelope/schema and source-bound identity | `PLANNED / OB-SUPPORTING` | Current EENS event model | None for current native Beta missions | Yes | EENS |
| `EENS-B` | Prove durable local persistence, idempotency, replay, and checkpoints | `PLANNED / OB-SUPPORTING` | EENS-A; current store/runtime | None for current native Beta missions | Yes | EENS |
| `EENS-C` | Add validated lifecycle producers and source/evidence locators | `PLANNED / OB-SUPPORTING` | EENS-A/B; stable Zeus event sources | None for current native Beta missions | Yes | EENS with Zeus adapters |
| `EENS-D` | Qualify notification routing and failure/retry behavior | `PLANNED / OB-SUPPORTING` | EENS-B; qualified adapter | None for current native Beta missions | Yes | EENS |

The Operation Beta-supporting EENS scope is bounded to validated local recording,
durability, idempotency, replay, checkpoints, and a qualified notification
adapter. EENS must not predefine managed-execution semantics that belong to CM.

### 7.3 Engineering Management Platform (`EMP`)

EMP is the centralized operator/control application over authoritative
subsystems. `engctl` remains a compatibility/low-level adapter; `empctl` is
not justified by this roadmap.

| Item | Objective | Status | Dependencies | Blocks | Parallel eligibility | Owner |
|---|---|---|---|---|---|---|
| `EMP-A` | Establish read-only federation and normalized project/portfolio views | `PLANNED / OB-SUPPORTING` | Existing JSON/native interfaces | None | Yes | EMP / `engctl` adapters |
| `EMP-B` | Expose read-only Zeus, mission, WOP, execution, repository, and EOS projections | `PLANNED / OB-SUPPORTING` | EMP-A; existing subsystem projections | None | Yes | EMP |

EMP-A/B may proceed without mature EENS live-event integration. They do not
mutate backend state directly and do not duplicate Zeus lifecycle logic.

## 8. Operation Beta reconciliation point

Operational Alpha is a historical complete/closed baseline, not the current
mission. Perform a portfolio reconciliation at the applicable Operation Beta
boundary before selecting later work. Resolve:

- actual Zeus OA capability and remaining execution gaps;
- CM-01/02 completion and remaining managed-work dependencies;
- EENS event-contract and delivery readiness;
- EMP foundation readiness;
- WOP-M1 deferred source/package generation alignment defect;
- provider/runtime limitations;
- qualification, controlled-document, repository, and EOS state;
- deferred and superseded planning records.

This reconciliation creates the next Operation Beta selection baseline. It
does not automatically activate any mission or bind an unbound P5 coordinate.

## 9. Tier 3 — Operation Beta follow-on dependency-driven convergence

The following is a provisional wave order. Independent missions may overlap
when their contracts prove the dependency is soft and their authority and
qualification boundaries do not collide.

### Wave 1 — execution contract convergence

`CM-03 → CM-04`

- `CM-03`: compose mission/WOP/gate authority into a subordinate work request
  using Zeus as execution owner.
- `CM-04`: translate authorized engineering actions into minimum provider
  permission profiles while retaining provider sandbox enforcement.

### Wave 2 — event convergence

`EENS-E → EENS-F → EENS-G`

- `EENS-E`: authenticated/reconnectable consumer interface for downstream
  projections.
- `EENS-F`: acknowledgement, multi-node delivery, retention, and EMP event
  integration.
- `EENS-G`: advanced qualification, portability, and mature platform
  integration.

These gates consume stabilized Zeus/CM event families. EENS remains an event
record/delivery owner, not a lifecycle authority.

### Wave 3 — execution/qualification convergence

`CM-05 → CM-06`

- `CM-05`: integrate existing monitoring, recovery, evidence, replay,
  reconciliation, and closeout owners; do not create a parallel monitor.
- `CM-06`: demonstrate an operator-submitted representative WOP managed by
  Zeus through the provider boundary with legitimate escalations only.

### Wave 4 — centralized management application

`EMP-C → EMP-D → EMP-E → EMP-F → EMP-G → EMP-H`

EMP progressively consumes stable Zeus, CM, EENS, EOS, project, repository,
node, and infrastructure interfaces. EMP live operation depends on EENS
consumer/event capabilities; read-only slices may arrive earlier.

## 10. Deferred and superseded work

| Work | Disposition | Reason / owner |
|---|---|---|
| WOP-M2..M7 | `SUPERSEDED` | Replaced by CM-01..CM-06; detailed WOP ownership remains in WOP/Zeus contracts |
| MH-01..MH-08 | `SUPERSEDED` | Managed Handoff is subordinate to WOP execution; no peer subsystem |
| WOP-M1 implementation gaps | `DEFERRED` | Source/package generation/version alignment requires separately authorized WOP work |
| `CM-03..CM-06` | `DEFERRED / POST-OA` | Depends on stable OA execution and managed-work contracts |
| `EENS-E..EENS-G` | `DEFERRED / POST-OA` | Depends on consumer, CM event, and multi-node maturity |
| `EMP-C..EMP-H` | `DEFERRED / POST-OA` | Depends on stable subsystem interfaces and EENS live integration |
| Broader node/infrastructure integration | `DEFERRED` | Future EMP/infrastructure owner contracts |
| Unpublished roadmap candidates | `DEFERRED / REVIEW_REQUIRED` | Must be reconciled through governance before controlling planning |

## 11. Portfolio relationship

```text
                         EMP
             centralized operator application
                       /   |   \
                    Zeus EENS  EOS
                 authority  events  state/sync
                    |
             WOP execution contract
                    |
          subordinate managed work request
                    |
          provider / Codex execution runtime
                    |
        monitoring / evidence / qualification
```

The portfolio roadmap sequences these owners; it does not merge their
authorities. Zeus composes engineering authority and controls execution. EENS
records and delivers events. EOS retains its existing engineering-state and
synchronization contract. EMP projects and routes state through canonical
interfaces.

## 12. Dependency and cycle validation rules

The intended acyclic relationship is:

```text
P5-G6
  → P5-G7 → P5-G8 → P5-G9 → P5-G10 → Phase 6 → Phase 7

WOP-M1
  → CM-01 → CM-02 → CM-03 → CM-04 → CM-05 → CM-06

EENS-A → EENS-B → EENS-C → EENS-D → EENS-E → EENS-F → EENS-G

EMP-A → EMP-B → EMP-C → EMP-D → EMP-E/EMP-F → EMP-G → EMP-H
```

Cross-track dependencies are deliberately limited:

- P5-G6 is reused by CM and downstream execution work.
- CM-01/02 may proceed alongside the Zeus OA path and do not block P5-G7/P5-G8.
- EENS-A..D may proceed alongside OA; EENS mature managed-execution events
  consume CM semantics but do not define them.
- EMP-A/B consume existing interfaces and do not require EENS live operation.
- CM-03/04 precede mature EENS execution-event work where event semantics
  depend on managed actions.
- EENS-E/F and stable CM interfaces precede EMP live/advanced operation.

No cycle is intended between Zeus, CM, EENS, and EMP. Any implementation
proposal that makes EENS or EMP a prerequisite for a future Beta mission or
for an unbound P5 coordinate must return to portfolio reconciliation with
evidence.

## 13. Future roadmap-recording actions

Before this record becomes the active authoritative portfolio roadmap,
Engineering Governance must:

1. resolve the permanent controlled-document/roadmap identity and registration
   relationship under PROC-0009, SPEC-0001, STD-0001, STD-0002, and DOC-0001;
2. review the scope and authority relationship to `OPERATION-BETA-ROADMAP.md`
   and the Zeus canonical roadmap;
3. qualify the dependency graph and supersession relationships;
4. publish the approved revision through the existing controlled lifecycle;
5. apply any declared EOS projection/synchronization boundary; and
6. verify the active portfolio projection without changing execution state.

Until those actions occur, this file is a persisted candidate planning record,
not a current execution-selection authority.

## 14. Machine-readable summary

```text
ROADMAP_RECONCILIATION_RESULT=RECORDED_CANDIDATE_PENDING_OPERATOR_REVIEW
PORTFOLIO_ROADMAP_OWNER=ENGINEERING_GOVERNANCE_FOR_CROSS_SYSTEM_PLANNING
OPERATIONAL_ALPHA_STATUS=COMPLETE_CLOSED
OPERATIONAL_ALPHA_CURRENT=NO
PRIMARY_CURRENT_MISSION=OPERATION_BETA
CURRENT_PLATFORM_CONTEXT=BETA-04
CURRENT_NATIVE_BETA_RECOMMENDATION=CAGF-01
CURRENT_ZEUS_GATE=UNRESOLVED_P5_NAMESPACE_NOT_NATIVE_BETA_AUTHORITY
OB_CRITICAL_PATH=UNRESOLVED_P5_COORDINATES_PENDING_BETA_BINDING
CM_SEQUENCE=CM-01->CM-02->CM-03->CM-04->CM-05->CM-06
EENS_SEQUENCE=EENS-A->EENS-B->EENS-C->EENS-D->EENS-E->EENS-F->EENS-G
EMP_SEQUENCE=EMP-A->EMP-B->EMP-C->EMP-D->EMP-E->EMP-F->EMP-G->EMP-H
OB_PARALLEL_SUPPORTING_WORK=CM-01/CM-02;EENS-A..D;EMP-A/EMP-B
OB_FOLLOW_ON_SEQUENCE=CM-03->CM-04;EENS-E..G;CM-05->CM-06;EMP-C..H
WOP_M_ROADMAP_DISPOSITION=SUPERSEDED_BY_CM_SEQUENCE
MH_ROADMAP_DISPOSITION=SUPERSEDED_BY_CM_SEQUENCE
ROADMAP_DEPENDENCY_VALIDATION=PASS_BY_CONSTRUCTION;NO_CYCLE_IDENTIFIED
DUPLICATE_ROADMAP_AUTHORITY=NO_NEW_ACTIVE_AUTHORITY_CREATED
CANONICAL_ZEUS_ROADMAP_CHANGED=NO
CONTROLLED_DOCUMENTS_CHANGED=YES_CANDIDATE_CORRECTED_NOT_REGISTERED_OR_PUBLISHED
ROADMAP_RECORDS_CREATED=1
ROADMAP_RECORDS_MODIFIED=0
IMPLEMENTATION_PERFORMED=NO
P5_G7_IMPLEMENTED=NO
CM_IMPLEMENTATION_PERFORMED=NO
EENS_IMPLEMENTATION_PERFORMED=NO
EMP_IMPLEMENTATION_PERFORMED=NO
WOP_IMPLEMENTATION_PERFORMED=NO
MISSION_STATE_MUTATION=NO
EXECUTION_STATE_MUTATION=NO
EOS_MUTATION=NO
CONTROLLED_DOCUMENT_VALIDATION=PENDING_GOVERNANCE_REGISTRATION;LOCAL_DIFF_CHECK_PASS
REGISTRY_VALIDATION=PASS
ZEUS_PLATFORM_VERIFICATION=PASS
EOS_VALIDATION=PASS_READ_ONLY
REPOSITORY_EOS_VALIDATION=PASS_READ_ONLY
GIT_DIFF_CHECK=PASS
COMMIT=NOT_PERFORMED
PUBLICATION=NOT_PERFORMED
PUSH=NOT_PERFORMED
EOS_SYNCHRONIZATION=NOT_PERFORMED
NEXT_AUTHORIZED_ACTION=OPERATOR_REVIEW_RECONCILED_PORTFOLIO_ROADMAP
STATUS=AWAITING_OPERATOR_REVIEW
```

## 15. Stop boundary

This record does not authorize P5-G7, CM, EENS, EMP, WOP, Managed Handoff, or
any other implementation. Stop for operator review.
