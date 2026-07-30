# Zeus Architecture Baseline Mission Contract — Lifecycle Reconciliation

Date: 2026-07-30

Execution classification: Direct non-EWO contract preparation and validation

Proposed mission:
`ZEUS-ARCHITECTURE-BASELINE-COMPLETION-001`

Proposed contract:
`MC-ZEUS-ARCHITECTURE-BASELINE-COMPLETION-001`

## Authority boundary

This reconciliation prepares a non-authorizing candidate Mission Contract. It
does not claim Engineering Governance, Mission Admission, Mission Activation,
controlled-document approval, freeze, publication, persistence, or lifecycle
transition authority.

No Project State, Work Registry, active Mission Contract, active mission,
controlled phase, roadmap, Runtime, Progressive state, or EOS state was
changed.

## Authoritative lifecycle procedure

The controlling sources are:

- `POL-0001`, Temporary Mission Admission and Activation Directive;
- `PROC-0001`, Mission Admission and Activation Candidate;
- `STD-0003`, Repository Mission Contract;
- `engineering/mission-contracts/mission-contract.schema.yaml`; and
- `scripts/lib/eos/mission_activation.py`.

Together they establish:

1. Engineering Governance alone owns Mission Admission and Mission Activation.
2. Admission records intent but does not create execution authority.
3. Activation is a separate decision and transaction.
4. Direct candidate-to-active mutation is prohibited.
5. Activation must leave exactly one active Mission Contract.
6. The activation transaction reconciles the selected contract, its existing
   Work Registry item, Project State, activation evidence, and derived EOS
   state.
7. An execution agent cannot independently admit, revoke, or activate a
   mission.

## Current active authority

The repository currently resolves exactly one active Mission Contract:

```text
Contract: MC-MISSION-CONTRACT-PUBLICATION-001
Mission: MISSION-CONTRACT-PUBLICATION-001
WOP: GH-ZEUS-OA-PROGRESSIVE-001
Registry binding: EMP-WORK-GH-ZEUS-OA-PROGRESSIVE-001
Lifecycle: active
```

The proposed architecture contract remains `candidate` and grants no
transactional authority.

## Replacement and supersedence analysis

The Mission Contract schema permits:

```text
active -> suspended | completed | revoked | expired | superseded
suspended -> active | revoked | expired
candidate -> active | invalid
```

The activation service rejects a candidate while any other contract remains
`active`. It does not mutate or supersede the predecessor contract as part of
the candidate activation transaction.

Consequences:

- `active -> suspended` is reversible and represents pausing the current
  authority, but it does not satisfy literal supersedence.
- `active -> superseded` is terminal and satisfies the requested disposition,
  but it must occur before candidate activation and cannot be rolled back by
  the current activation transaction.
- atomic “supersede predecessor upon successor activation” is not implemented.

The candidate records the requested predecessor and supersedence intent, but
that metadata is not an executable lifecycle transition. Engineering
Governance must choose an authorized predecessor disposition or separately
authorize a lifecycle implementation change before activation.

## Standby lifecycle reconciliation

`Standby` is not a valid state in any controlling Mission Contract or Work
Registry Mission state set. The existing model requires a layer-specific
projection:

| Layer | Valid standby-equivalent state | Rationale |
|---|---|---|
| Governance state | remains `Admitted` or `Activated` | execution suspension does not reinterpret Governance intent |
| Mission Contract | `suspended` | reversible non-active authority state |
| Execution state | `Suspended` | execution is paused without Governance-state change |
| Work Registry Mission | `blocked` | Mission states do not define `deferred`; the architecture prerequisite is the blocker |
| Work Registry Work Item | `deferred` | explicit resumable planning deferral; requires an active Deferral object |

This mapping is a proposed reconciliation rule. It was not applied. Other
missions already in non-active `proposed`, `authorized`, `blocked`,
`completed`, or `cancelled` states do not require a synthetic Standby
transition.

## Proposed phase identifiers

The candidate reserves registry-conformant identifiers without creating Work
Registry Phase objects:

| Sequence | Proposed phase identifier | Supplied target |
|---|---|---|
| I | `EMP-PHASE-ZEUS-ARCHITECTURE-BASELINE-01-ARCH-0001` | ARCH-0001 |
| II | `EMP-PHASE-ZEUS-ARCHITECTURE-BASELINE-02-ADR-0001` | ADR-0001 |
| III | `EMP-PHASE-ZEUS-ARCHITECTURE-BASELINE-03-ADR-0001` | ADR-0001 |
| IV | `EMP-PHASE-ZEUS-ARCHITECTURE-BASELINE-04-SPEC-0002` | SPEC-0002 |
| V | `EMP-PHASE-ZEUS-ARCHITECTURE-BASELINE-05-OA-ROADMAP` | Operational Alpha Roadmap |

Phase II and Phase III both target ADR-0001 exactly as supplied. Their distinct
engineering purposes, entry criteria, and exit criteria are not defined. The
unique identifiers prevent collision but do not resolve that semantic
duplication. Engineering Governance must clarify or confirm it before
activation.

## Admission sequencing conflict

The admission implementation requires all of the following before it can
return `ADMIT`:

- a candidate Mission Contract;
- an Active WOP whose work item matches the contract;
- an attributable approval binding the mission and contract;
- exactly one existing Work Registry item in `ready` or `active`;
- matching registry scope; and
- satisfied dependencies.

The requested sequencing prohibits Work Registry reconciliation until after
successful admission. Therefore the current admission implementation cannot
admit this new mission under the requested ordering: the required registry
binding cannot exist before admission, while admission cannot succeed without
it.

No Work Registry item, phase, dependency, or deferral was created.

## Lifecycle disposition

```text
CONTRACT PREPARED: YES
CONTRACT LIFECYCLE: candidate
CONTRACT SCHEMA VALID: YES
MISSION ADMISSION: DENIED
MISSION ACTIVATION: NOT ATTEMPTED
PREDECESSOR DISPOSITION: NOT PERFORMED
PROJECT / REGISTRY RECONCILIATION: NOT PERFORMED
```

