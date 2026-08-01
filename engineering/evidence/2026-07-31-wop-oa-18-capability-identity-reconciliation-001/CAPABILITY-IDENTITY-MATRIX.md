# OA-18 Capability Identity Matrix

| Source | Capability ID | Name | Binding/result |
|---|---|---|---|
| Mission Contract / gate specification | CAP-017 binding resolved from gate capability name | Approval Enforcement During Execution | PASS |
| Roadmap OA-18 | CAP-017 by reconciled controlled identity | Approval Enforcement During Execution | PASS |
| OA-18 gate definition | CAP-017 binding | Approval Enforcement During Execution | PASS |
| Mission Knowledge Model | ZEUS-OA-CAP-017 | Approval Enforcement During Execution | PASS |
| Capability Registry rev. 1.8 | ZEUS-OA-CAP-017 | Approval Enforcement During Execution | PASS |
| EMM rev. 3.0 | Capability Registry and Mission Knowledge bindings | Approval Enforcement During Execution | PASS |
| Zeus projections | ZEUS-OA-CAP-017 | Approval Enforcement During Execution | PASS |

## Capability contract

- Description: pause protected actions for valid operator approval; reject
  invalid, stale, ambiguous, unauthorized, and replayed approvals; fail closed.
- Acceptance: positive, negative, replay, interruption, recovery, cumulative
  regression, append-only evidence, and valid operator receipt.
- Dependencies: CAP-016 and the Mission Knowledge Model.
- EMM entity: `CapabilityRegistry/OPERATIONAL-ALPHA-CAPABILITY-REGISTRY`, rev. 1.8.
- Mission Knowledge Model: `OA-18`, rev. 3.0.
- Registry status: planned and unavailable until implementation qualification.
