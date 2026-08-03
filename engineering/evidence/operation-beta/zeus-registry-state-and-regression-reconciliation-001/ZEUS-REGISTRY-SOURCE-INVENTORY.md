# Zeus Registry Source Inventory

| Source | Owner | Classification | Validation |
|---|---|---|---|
| `engineering/capabilities/operational-alpha-capability-registry.yaml` | Engineering Governance / EMM | authoritative capability registry | `capability_registry.verify` |
| `engineering/dispatch/execution-agent-registry.json` | Engineering Governance / Zeus execution registry | controlled candidate registry | `production_execution.load_registry` |
| `engineering/registry/work-registry.yaml` | Engineering management | authoritative work registry | `scripts/engctl registry validate` |
| `engineering/missions/operational-alpha-mission-knowledge.yaml` | Engineering Governance | authoritative mission knowledge | mission-knowledge resolver |
| `engineering/operations/zeus-operational-alpha-progress.md` plus EMM-resolved WOP | Engineering Governance | current OA projection inputs | `operational_alpha_status.resolve` |
| `.zeus/runtime/agents` and Stage 1 runtime | Zeus runtime | derived/append-only runtime evidence | runtime validators |
| `scripts/tests/fixtures/oa05-capability-state.json` | qualification | frozen historical fixture only | OA-05 regression tests |

Tests do not make a source authoritative.
