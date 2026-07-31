# WOP-EMM-ROADMAP-GOVERNANCE-RECONCILIATION-001

## Architecture Responsibility Matrix

Authority was resolved from the published chain `ARCH-0001 → ADR-0001 →
SPEC-0002` and the adopted `ZEUS-OA-ROADMAP-002` implementation. No session
marker was treated as authority.

| Responsibility | Single owner | Consumer / boundary | Evidence of ownership |
|---|---|---|---|
| Roadmap intent, sequence, and objectives | Engineering Governance through `ZEUS-OA-ROADMAP-002` | EMM | EMM `MissionRoadmap` entity and controlled roadmap |
| Roadmap source binding and drift detection | EMM | `zeus mission roadmap --verify` | EMM-bound `MissionRoadmap` source/digest resolution |
| Roadmap qualification determination | PROC-0006 | PROC-0001 and mission admission | PROC-0006 independent qualification contract |
| Mission Knowledge Model reconciliation | EMM-bound mission knowledge service | Zeus projections | `scripts/lib/eos/mission_knowledge.py` |
| EMM synchronization and reconciliation | EOS/EMM directional synchronization boundary | runtime projections | ADR-0001 synchronization ownership and EOS validation |
| Work Initiation qualification and routing | PROC-0001 | execution lifecycle | PROC-0001 Mission-Assurance and Work Initiation sections |
| Read-only roadmap presentation | Zeus | operators | `zeus mission roadmap` projection |

The existing architecture therefore already provides both owners. No separate
roadmap monitor or second qualification authority was introduced. The prior
roadmap verifier was reconciled to resolve the EMM `MissionRoadmap` entity and
its exact source digest before comparing Mission Knowledge Model provenance.
