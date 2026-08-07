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
next eligible roadmap mission, but requires its own separately published and
authorized WOP before submission or admission.

| Order | Mission | Scope | Depends on | Exit boundary |
| ---: | --- | --- | --- | --- |
| 0 | `BETA-00` | Engineering Platform assessment, reconciliation, backlog, and sequencing | OA frozen baseline | Assessment and roadmap qualified |
| 1 | `ZDCL-01` | First qualified ZDCL foundation increment | BETA-00; approved ZDCL contract | Foundation qualified and published |
| 2 | `ZDCL-02..n` | Session, context, workspace, approval, evidence, event, qualification, publication, and distributed increments | Prior qualified ZDCL increment | Each separately qualified |
| 3 | `CAGF-01` | Canonical source ownership and deterministic projection foundation | BETA-00; ZDCL context contract as applicable | Generator contract qualified |
| 4 | `CAGF-02..n` | Identity validation, generation, reconciliation, qualification, and publication integration | Prior qualified CAGF increment | Each separately qualified |
| 5 | `EPE-01` | Executable mission contracts and task/state execution foundation | BETA-00; applicable ZDCL/CAGF outputs | Phase 1 contract qualified |
| 6 | `EPE-02..n` | Transactions, ledger, dependency-aware validation, recommendations, EMP/EENS, and distributed evolution | Prior qualified EPE increment | Each separately qualified |

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
