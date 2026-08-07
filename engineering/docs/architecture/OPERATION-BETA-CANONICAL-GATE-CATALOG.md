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
| OB-ZEUS-G01 | Zeus/ZDCL | PARTIALLY_SATISFIED | Sequential technical dependency | P5-G6..G8 |
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

## Convergence points

| Shared capability | Canonical owner | Consumers | Duplicate implementation avoided |
| --- | --- | --- | --- |
| Canonical source and deterministic projection | CAGF/source owners | Zeus, EPE, CM, EMP, roadmap | Competing source registries/projections |
| Contract, resolver, admission, work-unit interface | CM/Zeus boundary | Zeus, EPE, WOP, providers | Parallel WOP/resolver/authority engines |
| Events, replay, notification projections | EENS | Zeus, CM, EMP, evidence | Competing event stores/notification paths |
| Management projections/action routing | EMP over canonical owners | Zeus/operator views | Second mission/portfolio/state authority |
| Integrated qualification/reconciliation | PMCT/Governance with Zeus/EOS | All families | Duplicate completion/closeout systems |

## Execution path and completion

1. Reuse OB-ZEUS-G00; do not rerun accepted P5-G6 work.
2. The first unsatisfied technical gate is OB-CAGF-G01.
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
