# Operation Beta — Mission Roadmap

Status: published planning roadmap; BETA-04 active mission baseline
Authority: `engineering/docs/operations/OPERATION-BETA-CHARTER.md`
Baseline input: Operational Alpha frozen baseline `OA-v1.0.0`
Design constitution: `engineering/docs/architecture/ENGINEERING-PLATFORM-DESIGN-PRINCIPLES.md`

## Sequence

The published current mission is `BETA-04`, recorded by
`engineering/missions/operation-beta-current.yaml` and
`engineering/authority/operation-beta-beta04-activation.yaml`. It is a bounded
platform-readiness and controller-reconciliation mission and does not authorize
capability implementation.

`ZDCL-01` completed independent qualification and explicit operator acceptance;
its sealed completion record is `engineering/mission-completions/ZDCL-01.yaml`.
It remains discoverable through completed and history views. `CAGF-01` is the
native Beta catalog recommendation, but the current primary cross-cutting
engineering mission is lifecycle completion as recorded below. CAGF-01's
recommendation remains advisory and its submission/admission is deferred
until lifecycle completion is independently qualified and closed. CAGF-01
still requires its own separately published and authorized WOP.

| Order | Mission | Scope | Depends on | Exit boundary |
| ---: | --- | --- | --- | --- |
| 0 | `BETA-00` | Engineering Platform assessment, reconciliation, backlog, and sequencing | OA frozen baseline | Assessment and roadmap qualified |
| 1 | `ZDCL-01` | First qualified ZDCL foundation increment | BETA-00; approved ZDCL contract | Foundation qualified and published |
| 2 | `ZDCL-02..n` | Session, context, workspace, approval, evidence, event, qualification, publication, and distributed increments | Prior qualified ZDCL increment | Each separately qualified |
| 3 | `CAGF-01` | Canonical source ownership and deterministic projection foundation | BETA-00; ZDCL context contract as applicable | Generator contract qualified |
| 4 | `CAGF-02..n` | Identity validation, generation, reconciliation, qualification, and publication integration | Prior qualified CAGF increment | Each separately qualified |
| 5 | `EPE-01` | Executable mission contracts and task/state execution foundation | BETA-00; applicable ZDCL/CAGF outputs | Phase 1 contract qualified |
| 6 | `EPE-02..n` | Transactions, ledger, dependency-aware validation, recommendations, EMP/EENS, and distributed evolution | Prior qualified EPE increment | Each separately qualified |

## Current Zeus lifecycle-completion track

The current primary engineering mission is
`ZEUS_EXECUTION_LIFECYCLE_COMPLETION`, represented by
`ZEUS-EXECUTION-LIFECYCLE-COMPLETION-01` and
`WOP-ZEUS-EXECUTION-LIFECYCLE-COMPLETION-001`. Its submitted lifecycle
state is `READY_FOR_CONTROLLED_EXECUTION`; the receipt-backed dispatch,
provider-session, provider-invocation, and execution-start chain is current,
and mission work remains
intentionally held. The mission's authoritative investigation identified twelve active
lifecycle gaps. Their durable implementation plan is recorded in
`engineering/planning/ZEUS-LIFECYCLE-GAP-REMEDIATION-PLAN-001.md` and the
supporting evidence package
`engineering/evidence/operation-beta/zeus-lifecycle-gap-roadmap-persistence-001/`.

The lifecycle remediation is dependency-ordered through canonical state
ownership, dispatch/provider/session convergence, monitoring and recovery,
independent evidence and qualification, publication/EOS synchronization,
closeout, and final end-to-end proof. The planning record does not authorize
runtime implementation or lifecycle advancement. `CAGF-01` remains deferred
behind independently qualified and closed lifecycle completion; its identity
binding corrective remains preserved as separate candidate work.

| Planning item | Status | Dependency / boundary |
| --- | --- | --- |
| `ZEUS-EXECUTION-LIFECYCLE-COMPLETION-01` | `READY_FOR_CONTROLLED_EXECUTION / WORK_HELD` | Submitted WOP; receipt-backed dispatch, provider session, provider invocation, and idle execution session established; stop before `BEGIN_CONTROLLED_MISSION_WORK` |
| `GAP-001..GAP-003, GAP-005, GAP-008..GAP-012` | `OPEN / IMPLEMENTATION_PLANNED` | See the durable plan and dependency graph; later gaps remain incomplete |
| `GAP-004, GAP-007` | `OPERATIONALLY_PROVEN_THROUGH_EXECUTION_SESSION` | One current dispatch, provider session, provider acknowledgement, and idle execution session verified and replayed idempotently; Wave 7 aggregate expansion remains separate |
| `CAGF-01` | `DEFERRED` | Must not advance from its separate identity-binding candidate until lifecycle completion is qualified and closed |

This section records current planning state and does not replace mission,
WOP, admission, execution, publication, or EOS authority.

The live Operation Beta projection consumes the canonical submitted-mission
index and resolver. Its current coordinates are:

```text
CURRENT_OPERATION=OPERATION-BETA
CURRENT_EXECUTABLE_MISSION=ZEUS-EXECUTION-LIFECYCLE-COMPLETION-01
CURRENT_WOP=WOP-ZEUS-EXECUTION-LIFECYCLE-COMPLETION-001
CURRENT_LIFECYCLE_STATE=READY_FOR_CONTROLLED_EXECUTION
CURRENT_GATE_MAPPING=WOP_GATE_4_CONTROLLED-EXECUTION-AND-RECOVERY/OB-ZEUS-G01
MISSION_WORK_STARTED=false
REPOSITORY_WORK_STARTED=false
LIFECYCLE_NEXT_ACTION=BEGIN_CONTROLLED_MISSION_WORK
FUTURE_RECOMMENDED_MISSION=CAGF-01
```

Any older statement that reports no current executable mission, or treats
`CAGF-01` as current execution, is a superseded point-in-time planning
projection. It remains historical evidence and cannot override the live
receipt chain.

The rows express recommended order, not implementation authority. Parallel work is allowed only where a future mission contract proves that its inputs are published, qualified, and independent.

## Mission availability and ordering semantics

This roadmap may expose multiple available or eligible missions at the same
time. A roadmap row or arrow expresses planning and organizational order; it
does not by itself create a dependency, selection, authorization, or execution
requirement. A mission becomes required to precede another only when an
authoritative mission contract, prerequisite, dependency, authority condition,
resource constraint, or safety boundary establishes that relationship.

`AVAILABLE`, `ELIGIBLE`, `RECOMMENDED`, `SELECTED`, `AUTHORIZED`, `ACTIVE`,
`BLOCKED`, and `DEFERRED` are distinct states. In particular, a recommendation
is advisory and does not constitute selection or execution authority. An
operator or Zeus may select an alternate mission only when it is independently
eligible and the applicable authority and admission requirements are met.
Runtime/resource concurrency constraints are separate from mission eligibility
and do not convert an advisory roadmap sequence into a global strict order.

## Promotion gates

Every increment must resolve its objective, verify its authority and baseline,
implement only its scope, qualify independently, reconcile canonical records,
obtain the governed publication decision, merge, synchronize EOS, validate the
Engineering Platform, and issue a completion receipt. A working tree,
generated projection, or local EOS state is not a published capability.

## Production and development states

`OA-v1.0.0` is the immutable production baseline. Beta work is a separate
development state with candidate, qualified, published, and superseded or
rolled-back outcomes. Development state must not replace Alpha tags, canonical
`main`, or synchronized production EOS. Rollback preserves evidence and
returns to the last qualified checkpoint or Alpha baseline.

## Parallelism and scope

The apparent pillar branches are not implicit concurrency permission. A mission
contract must prove published independent inputs and non-overlapping authority
and qualification boundaries; otherwise the listed order applies. This roadmap
does not allocate capability IDs, advance lifecycle, authorize runtime changes,
or replace the canonical owners in the authority model.

## Pillar work breakdown

### ZDCL

1. Native session launcher and identity.
2. Session classification and effect profile.
3. Mission/WOP resolution and immutable engineering context.
4. Repository and EOS qualification.
5. Durable session persistence and interruption recovery.
6. Controlled workspaces and approval enforcement.
7. Evidence/EENS and qualification integration.
8. Publication integration and distributed qualified agents.
9. Exclusive engineering execution control.

### CAGF

1. Canonical owner inventory and source contracts.
2. Stable input/digest model and deterministic generator contract.
3. Identity, dependency, cycle, and stale-source validation.
4. PMCT, gates, controllers, readiness, blockers, prerequisites, and operational metadata projections.
5. Continuous qualification, publication manifests, and safe migration away from manually maintained duplicates.

### EPE

1. Executable mission contracts.
2. Deterministic task graphs.
3. State-based skip/resume semantics.
4. Mission transactions.
5. Append-only execution ledger and projections.
6. Dependency-aware validation with policy-complete publication checks.
7. Structured recommendation lifecycle.
8. Responsibility separation and EMP/EENS integration.

## Readiness and sequencing rules

- A mission may consume only published, qualified predecessor outputs.
- A documented direction is not an operational capability.
- Conflicting authority, stale digests, missing ownership, or ambiguous scope fail closed and become reconciliation work.
- Historical Operational Alpha artifacts remain evidence and do not become Beta authority.
- No mission may advance a later pillar phase without its predecessor's qualified boundary.

### Admission freshness

- Admission identity includes the resolved submission and current Development
  repository baseline.
- A baseline change makes an admission stale for execution and requires a
  replacement admission; the historical admission and execution remain
  immutable evidence.
- Replacement admissions must carry explicit supersession lineage and may
  reuse the existing authoritative submission and published WOP.
