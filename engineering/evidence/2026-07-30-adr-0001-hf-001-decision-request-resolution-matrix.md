# ADR-0001-HF-001 Decision Request Resolution Matrix

Date: 2026-07-30

Execution classification: direct non-EWO controlled-document development.
This evidence does not approve, activate, persist, publish, or implement
ADR-0001.

## Baseline

| Item | Value |
|---|---|
| Repository | `git@github.com:lqoneal/homelab-infrastructure.git` |
| Repository root | `/data/engineering/repositories/homelab` |
| Branch | `main` |
| HEAD | `d0861dc62b8199de03230152c4ed3cfb687dd9a7` |
| Assessment baseline | `ARCH-0001@1.6` |
| Assessment SHA-256 | `a3965a1797d049ca2dc5d8a1d408556ad187d7aa49c4645d73eb52163ac0d9dd` |
| ADR predecessor | `ADR-0001@1.2` |
| ADR predecessor SHA-256 | `4ff5840585dca0d940d742fd7bdb6099d43542d219d98b03c06317ca3adc4f24` |
| ADR produced | `ADR-0001@1.3` |
| ADR produced SHA-256 | `bc3749695802757f346ba8c144c7331dbc9cdac931d0a39157066c4df68997c3` |

## Resolution Matrix

Every resolution section contains an architectural decision, rationale,
alternatives considered, rejected alternatives, affected subsystems,
authoritative owners, lifecycle impacts, implementation constraints, backward
compatibility impacts, and a Future Implementation traceability target.

| Decision Request | Architectural resolution | ADR section and decisions | Primary owner or component | Future implementation | Result |
|---|---|---|---|---|---|
| ARCH-DR-001 | Governance Authority Record is sole mission authority; EMP derives immutable Mission Contract | §14.1; ADR-D-001, ADR-D-008, ADR-D-015 | Governance, ADR-C-002 through ADR-C-004 | ADR-FI-001 | RESOLVED |
| ARCH-DR-002 | Authority Resolution Service produces the only canonical REAC | §14.2; ADR-D-003, ADR-D-004 | ADR-C-006 | ADR-FI-003 | RESOLVED |
| ARCH-DR-003 | Zeus EWI emits the sole terminal `ALLOW`, `DENY`, or `STOP` | §14.3; ADR-D-006 | ADR-C-008 | ADR-FI-005 | RESOLVED |
| ARCH-DR-004 | PMA is monotonic narrow-only and never initiates | §14.4; ADR-D-005 | ADR-C-007 | ADR-FI-004 | RESOLVED |
| ARCH-DR-005 | Graph is offline; compatibility is syntax-only; legacy paths are bounded; no compatibility authorizes | §14.5; ADR-D-012 | ADR-C-014 | ADR-FI-011, ADR-FI-015 | RESOLVED |
| ARCH-DR-006 | Governance, authority predicate, planning, execution, document, publication, and synchronization states remain orthogonal | §14.6; ADR-D-008, ADR-D-015 | owner matrix §8; lifecycle matrix §18 | ADR-FI-006 | RESOLVED |
| ARCH-DR-007 | Publication establishes the source baseline before separate directional EOS synchronization | §14.7; ADR-D-010 | ADR-C-011, ADR-C-013 | ADR-FI-007 | RESOLVED |
| ARCH-DR-008 | `engineering/execution/missions/` is a generated EMP discovery projection, then retired | §14.8; ADR-D-001, ADR-D-012 | ADR-C-003, ADR-C-004, ADR-C-014 | ADR-FI-008 | RESOLVED |
| ARCH-DR-009 | Cleanliness and remote freshness use deterministic phase-specific policy | §14.9; ADR-D-003, ADR-D-004, ADR-D-006 | repository observation, ADR-C-006, ADR-C-008, ADR-C-013 | ADR-FI-009, ADR-FI-015 | RESOLVED |
| ARCH-DR-010 | Authorization Bundle is a typed carrier selected by exact family, generation, applicability, and owner facts; never authority | §14.10; ADR-D-003, ADR-D-004, ADR-D-012 | source publishers and ADR-C-006 | ADR-FI-003 | RESOLVED |
| ARCH-DR-011 | Ten non-substitutable typed receipt classes have distinct owners and subjects | §14.11; ADR-D-002, ADR-D-009 | emitting decision owner | ADR-FI-002, ADR-FI-010 | RESOLVED |
| ARCH-DR-012 | PMCT has no standalone operational role; only pure predicates may remain behind canonical interfaces | §14.12; ADR-D-005, ADR-D-012 | canonical caller; ADR-C-014 for migration | ADR-FI-011 | RESOLVED |
| ARCH-DR-013 | EENS owns durable events, replay, checkpoints, and notification delivery; HNS expansion is deferred | §14.13; ADR-D-011 | ADR-C-012 | ADR-FI-012 | RESOLVED |
| ARCH-DR-014 | Authority publication generations are selected by exact rule-driven applicability; ambiguity stops | §14.14; ADR-D-003, ADR-D-004, ADR-D-012 | source owner and ADR-C-006 | ADR-FI-003 | RESOLVED |
| ARCH-DR-015 | Cutover requires clean, reachability, replay, recovery, and negative-authorizer evidence with a bounded rollback rule | §14.15; ADR-D-012 and §10 | independent qualification and ADR-C-008 | ADR-FI-015 | RESOLVED |
| ARCH-DR-016 | WOP, mission Runtime, and Stage 1 admissions have distinct subjects, owners, and receipts | §14.16; ADR-D-002, ADR-D-004, ADR-D-006 | ADR-C-005 and ADR-C-008 | ADR-FI-010 | RESOLVED |
| ARCH-DR-017 | Standard execution contains no Execution Grant or post-WOP authority object | §14.17; ADR-D-013 | Governance and ADR-C-008 | ADR-FI-005 | RESOLVED |
| ARCH-DR-018 | Typed generalized resource claims, containment, conflict, leases, and fencing cover all resource types | §14.18; ADR-D-014 | Authority Record, WOP, ADR-C-009 | ADR-FI-013 | RESOLVED |
| ARCH-DR-019 | Governance, EMP, Zeus, WOP, qualification, EENS, and EOS have explicit required and prohibited responsibilities | §14.19; ADR-D-006, ADR-D-007, ADR-D-011, ADR-D-015 | ADR-C-001 through ADR-C-014 | ADR-FI-016 | RESOLVED |
| ARCH-DR-020 | Bound attempts, proven checkpoints, effect fencing, revalidation, atomic reservation, and quorum-safe leases govern recovery and scale | §14.20; ADR-D-007, ADR-D-008, ADR-D-016 | ADR-C-008, ADR-C-009, ADR-C-011 | ADR-FI-014 | RESOLVED |

## Coverage Result

- Decision Requests inventoried from ARCH-0001: 20.
- Decision Request resolution sections: 20.
- Missing resolutions: 0.
- Duplicate resolution owners: 0.
- Resolutions dependent on unstated downstream specification content: 0.
- Architectural questions required for Operational Alpha left open: 0.

Result: PASS.
