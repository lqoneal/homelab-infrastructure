# Zeus Controller MKM Reconciliation

Work order: `WOP-ZEUS-CONTROLLER-MKM-RECONCILIATION-001`
Mission: `EMP-MISSION-ZEUS-OPERATIONAL-ALPHA`

## Responsibility matrix

| Controller family | Active resolver | Authoritative source | Compatibility boundary |
| --- | --- | --- | --- |
| `mission list`, `roadmap`, `portfolio`, `queue`, `health` | `mission_knowledge` | Mission Knowledge Model, EMM-bound roadmap and Capability Registry | None |
| `mission state`, `show`, `eligibility`, `readiness`, `explain`, `blockers`, `prerequisites`, `dependency-graph`, `synchronization`, `snapshot`, `next`, `recommend` | `mission_knowledge` | Mission Knowledge Model and EMM-bound Capability Registry | None |
| `next-action` | `mission_knowledge.next_action` | Mission Knowledge Model | Direct `resolve_next_action()` fallback is fixture/historical compatibility only |
| `dispatch status`, `dispatch verify` | `mission_knowledge.dispatch_verification` | Mission Knowledge Model and qualified capability projection | No legacy selection |
| `orchestrate status`, `orchestrate verify` | `mission_knowledge.orchestration_verification` | Mission Knowledge Model and qualified capability projection | No legacy selection |
| `gate`, PMCT, progressive lifecycle commands | Explicit legacy handlers | Historical gate evidence and explicit compatibility interfaces | Never an active mission projection |

All active controllers use the shared presentation contract: human-readable by
default, deterministic JSON with `--verify`, and structured JSON with `--json`.
