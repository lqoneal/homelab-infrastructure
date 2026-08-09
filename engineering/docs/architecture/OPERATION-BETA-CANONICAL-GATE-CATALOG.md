# Operation Beta Canonical Gate Catalog

**Status:** Planning candidate; pending operator review and governed publication
**Operation:** OPERATION-BETA
**Published baseline:** f65fa1bb5b445e6ca44330020808b193437190a2
**Authority:** None. Missions, WOPs, approvals, admissions, and execution records remain authoritative.
**Machine-readable companion:** ../evidence/operation-beta/OPERATION-BETA-CANONICAL-GATE-CATALOG.yaml

## Purpose and semantic boundary

This catalog decomposes the unified Canonical Zeus Development Roadmap into
capability gates. It is a planning candidate, not a mission queue and not a
source of authority. Historical qualification satisfies a gate only when the
scope and evidence match; it is reused, not rerun or rebound.

Mission authority is independent. Dependencies in the catalog are technical
capability, interface, data, artifact, qualification, environment, resource,
integration, publication-baseline, or safety dependencies only. Roadmap order,
recommendation, selection, operation membership, and completion of another
mission do not authorize a mission.

The companion YAML is the machine-actionable record. Every gate contains:
GATE_ID, CAPABILITY_FAMILY, TITLE, CANONICAL_OWNER, OBJECTIVE, SCOPE,
ENTRY_CONDITIONS, REQUIRED_TECHNICAL_INPUTS, TECHNICAL_DEPENDENCIES,
PARALLELISM_CONSTRAINTS, INTERFACES_PRODUCED, CONSUMERS,
IMPLEMENTATION_REQUIREMENTS, PROHIBITED_SCOPE, VERIFICATION_REQUIREMENTS,
ZEUS_NATIVE_VERIFICATION, EVIDENCE_REQUIREMENTS, QUALIFICATION_REQUIREMENTS,
EXIT_CRITERIA, FAILURE_BEHAVIOR, REPLAY_IDEMPOTENCY_REQUIREMENTS,
COMPLETION_STATE, and ROADMAP_REQUIREMENTS_SATISFIED.

## Gate inventory

| Gate | Family | Disposition | Parallelism | Traceability |
| --- | --- | --- | --- | --- |
| OB-ZEUS-G00 | Zeus/ZDCL | HISTORICAL_ALREADY_SATISFIED | Historical | P5-G1..G5; ZDCL-01 |
| OB-ZEUS-G01 | Zeus/ZDCL | COMPLETE | Sequential technical dependency | P5-G6..G8 |
| OB-ZEUS-G02 | Zeus/ZDCL | NEW_UNSATISFIED | Sequential technical dependency | P5-G9..G10; Phases 6..7 |
| OB-CAGF-G01 | CAGF | NEW_UNSATISFIED | Ready for parallel implementation | CAGF source/projection |
| OB-EPE-G01 | EPE | BLOCKED_BY_MISSING_TECHNICAL_INPUT | Sequential technical dependency | EPE-01..05 |
| OB-CM-G01..G03 | CM | NEW_UNSATISFIED | Interface/dependency bounded | CM-01..06 |
| OB-EENS-G01 | EENS | PARTIALLY_SATISFIED | Parallel after interface freeze | EENS-A..C |
| OB-EENS-G02 | EENS | NEW_UNSATISFIED | Parallel after interface freeze | EENS-D..G |
| OB-EMP-G01 | EMP | PARTIALLY_SATISFIED | Parallel after interface freeze | EMP-A..D |
| OB-EMP-G02 | EMP | NEW_UNSATISFIED | Parallel after interface freeze | EMP-E..H |
| OB-ARCH-G01 | Roadmap/architecture | NEW_UNSATISFIED | Parallel after interface freeze | Roadmap model/provenance |
| OB-ARCH-G02 | Roadmap/architecture | PLANNING_ONLY_NOT_YET_GATE_READY | Sequential | Progress/drift/remaining plan |
| OB-IQ-G01 | Integrated qualification | BLOCKED_BY_MISSING_TECHNICAL_INPUT | Sequential | Integrated lifecycle/evidence |
| OB-IQ-G02 | Integrated qualification | BLOCKED_BY_MISSING_TECHNICAL_INPUT | Sequential | Completion/publication/repository/EOS |

## Lifecycle WOP crosswalk

The companion YAML owns the deterministic projection crosswalk for the active
lifecycle WOP. It grants no mission or execution authority.

| WOP gate | Local objective | Operation Beta representation | Meaning |
| --- | --- | --- | --- |
| 1 | `LIFECYCLE-AUTHORITY-CONVERGENCE` | `OB-ARCH-G01` | Bounded projection/roadmap convergence corrective; status `OPERATOR_REVIEW` |
| 4 | `CONTROLLED-EXECUTION-AND-RECOVERY` | `OB-ZEUS-G01` | Current intended lifecycle capability position at `READY_FOR_CONTROLLED_EXECUTION`; work held |

Gate 1 corrective work does not move the receipt-backed mission backward from
Gate 4. Gate 4 execution, monitoring, and recovery expansion remain outside
this convergence handoff.

The lifecycle-gate convergence assessment at
`engineering/evidence/operation-beta/ob-zeus-g01-lifecycle-gate-convergence-and-residual-assessment-001/`
reconciles the published P5-G6 monitoring acceptance, the published and
qualified Wave 3 recovery contract, later provider/session recovery
correctives, and current Zeus-native projections. It finds no remaining G01
implementation residual. Formal closure remains pending governed publication
of this catalog reconciliation. The current Codex native-thread persistence
defect is a deferred execution-runtime instance and does not invalidate the
qualified fail-closed G01 recovery capability.

## Capability-level dependency graph

    OB-ZEUS-G00 -> OB-ZEUS-G01 -> OB-ZEUS-G02
    OB-ZEUS-G00 -> OB-CM-G01 -> OB-CM-G02 -> OB-CM-G03
    OB-ZEUS-G00 -> OB-EENS-G01 -> OB-EENS-G02
    OB-ZEUS-G00 -> OB-EMP-G01 -> OB-EMP-G02
    OB-ZEUS-G00 -> OB-ARCH-G01 -> OB-ARCH-G02
    OB-CAGF-G01 -> QUALIFIED_CANONICAL_SOURCE_PROJECTION -> OB-EPE-G01
    Upstream family gates -> OB-IQ-G01 -> OB-IQ-G02

CAGF-01 is the preferred producer of QUALIFIED_CANONICAL_SOURCE_PROJECTION,
not the source of EPE authority. An equivalent qualified producer may satisfy
that technical input where governed records permit it.

## OB-CAGF-G01 bounded implementation clarification

`OB-CAGF-G01` is limited to one bounded reference projection family exercised
end-to-end. Its implementation contract is not authorization to implement the
broader CAGF-01 through CAGF-05 capability set. The broader CAGF roadmap remains
future staged development and is satisfied only by separately scoped gates.

The reference family shall make the existing Operation Beta mission/readiness
projection source-bound and deterministic. It may consume the existing Mission
Knowledge Model, Capability Registry, EMM, PMCT/gate authority, Engineering
Governance, repository identity/baseline, and EOS records, but none of those
owners is replaced. The generated projection is disposable derived output and
never becomes authority.

The bounded contract is:

```text
canonical owners
  -> one declared source contract
  -> normalized, source-bound inputs and stable digests
  -> identity/dependency/cycle/stale/conflict validation
  -> deterministic projection generation
  -> bounded Operation Beta mission/readiness projection
  -> immutable provenance/publication manifest
  -> byte-stability and replay qualification
  -> fail-closed publication boundary
  -> Zeus-native verification
```

The gate must preserve independent mission authority. Technical or capability
dependencies remain permitted; mission-to-mission authority dependencies,
synthetic Mission Contracts, new WOPs, execution, and broad CAGF artifact
generation remain prohibited. Existing repository identity, Mission
Contract/WOP resolution, receipt-backed lifecycle projections, drift detection,
replay/idempotency, and Zeus verification capabilities are reused rather than
rebuilt.

## Convergence points

| Shared capability | Canonical owner | Consumers | Duplicate implementation avoided |
| --- | --- | --- | --- |
| Canonical source and deterministic projection | CAGF/source owners | Zeus, EPE, CM, EMP, roadmap | Competing source registries/projections |
| Contract, resolver, admission, work-unit interface | CM/Zeus boundary | Zeus, EPE, WOP, providers | Parallel WOP/resolver/authority engines |
| Events, replay, notification projections | EENS | Zeus, CM, EMP, evidence | Competing event stores/notification paths |
| Management projections/action routing | EMP over canonical owners | Zeus/operator views | Second mission/portfolio/state authority |
| Integrated qualification/reconciliation | PMCT/Governance with Zeus/EOS | All families | Duplicate completion/closeout systems |

## Execution path and completion

1. Reuse OB-ZEUS-G00 and completed OB-ZEUS-G01; do not rerun accepted P5-G6
   or qualified P5-G7/P5-G8 work.
2. On the active Zeus lifecycle track, publish the G01 reconciliation and then
   begin OB-ZEUS-G02 under its own authority. CAGF-01 remains deferred while
   lifecycle completion is the selected engineering focus.
3. After interface freeze, plan OB-CM-G01, OB-EENS-G01, OB-EMP-G01,
   and OB-ARCH-G01 in parallel where their own authority and qualification
   controls permit.
4. Advance dependent CM, EENS, EMP, Zeus, and roadmap gates; qualify
   OB-EPE-G01 when its capability input exists.
5. Run OB-IQ-G01, then OB-IQ-G02.

Operation Beta completion requires every non-superseded gate to be qualified,
all capability dependencies and interfaces satisfied, integrated
mission/WOP/execution/evidence/approval/recovery/publication/repository/EOS
behavior passing, Zeus-native independent verification, and no required
capability remaining planning-only or unresolved.

This candidate does not select CAGF-01, create a WOP, or authorize any gate.
