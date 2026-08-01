# Zeus Operation Beta Controller Integration

Status: published controller integration for `OB-PLAN-v1.0.0`
Operation: `OPERATION-BETA`
Production baseline: `OA-v1.0.0` (immutable)
Development baseline: `OB-PLAN-v1.0.0`

## Authority and projection boundary

Zeus provides read-only projections for Operation Beta. The published Beta
roadmap is the planning source; the Mission Knowledge Model, Capability
Registry, EMM, PMCT/gate authority, EOS, Engineering Governance, EMP, and EENS
retain the ownership assigned by the Beta authority model. This controller
does not persist mission state, allocate capability identifiers, or advance a
lifecycle.

The controller recognizes the `ZDCL`, `CAGF`, and `EPE` mission families and
exposes operation, family, and mission views. Derived metrics carry the
source baseline and are recomputed on every request.

## Required integrity checks

Beta verification fails closed when a controlled source is absent, the
roadmap order or root is invalid, either `OA-v1.0.0` or `OB-PLAN-v1.0.0` is
missing, the pillar model is incomplete, or production/development identity
cannot be distinguished. Unknown mission families and orphan mission IDs are
errors, not empty projections.

## CLI contract

```text
zeus operation show BETA
zeus operation status BETA
zeus operation roadmap BETA
zeus operation metrics BETA
zeus operation health BETA
zeus operation verify BETA
zeus operation next-action BETA

zeus mission list
zeus mission completed
zeus mission history
zeus mission archive
zeus mission roadmap ZDCL
zeus mission roadmap CAGF
zeus mission roadmap EPE
zeus mission status <MISSION_ID>
zeus mission readiness <MISSION_ID>
zeus mission blockers <MISSION_ID>
zeus mission prerequisites <MISSION_ID>
zeus mission dependencies <MISSION_ID>
zeus mission metrics <MISSION_ID>
zeus mission verify <MISSION_ID>
```

Alpha inspection commands remain available through their existing
Mission Knowledge Model projections. Beta output never substitutes for Alpha
production state, and Alpha history is not treated as Beta authority.

The default mission list is the active Beta development view. Completed Alpha
missions are historical projections and are exposed only by the completed,
history, or archive views.

Mission queue inspection remains on the existing EMP/Zeus orchestration and
Mission Knowledge Model path. It is a read-only projection and does not create
a parallel queue, scheduler, admission store, or lifecycle authority. See
`ZEUS-MISSION-QUEUE-AND-SCHEDULING.md` for the ownership and fail-closed
contract.

## Metrics

Operation and mission metrics are derived from the roadmap cards and current
published baselines. They include lifecycle counts, progress views, critical
path, dependency/authority/controller/roadmap health, promotion readiness,
unresolved recommendations, and production/development divergence. The
metrics are not stored as authority and cannot repair a source conflict.

## Next action

The published BETA-00 assessment and roadmap identify `ZDCL-01` as the first
implementation candidate. The controller reports that recommendation as a
projection only; a separately authorized and resolved WOP remains required.
