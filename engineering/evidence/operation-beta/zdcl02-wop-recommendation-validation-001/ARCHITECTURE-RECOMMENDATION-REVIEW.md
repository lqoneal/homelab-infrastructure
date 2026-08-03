# Architecture Recommendation Review

## Governing boundary

`ZEUS-DEVELOPMENT-CONTROL-LAYER-DIRECTION.md` makes ZDCL subordinate to
Engineering Governance, EOS, EMP, and EENS. `SPEC-0014` owns Operational Alpha
authority resolution and explicitly says observation, planning, or generated
views do not grant authority. `PROC-0001` owns the execution lifecycle;
`engineering/execution/execution-interface.yaml` routes existing owners.

## Dispositions

| Proposed capability | Disposition | Required boundary |
|---|---|---|
| Zeus lifecycle ownership | ACCEPT WITH MODIFICATION | Zeus orchestrates only the lifecycle already defined by the applicable controlled owner; it cannot approve or self-advance it. |
| Provider-neutral provider/agent abstraction | ACCEPT WITH MODIFICATION | Reuse the execution interface and existing capability contracts; no parallel provider registry or authority model. |
| Provider registration/discovery | ACCEPT WITH MODIFICATION | Registration is descriptive/qualified resource state; EMM/Governance remains authoritative for permission. |
| Capability qualification and deterministic selection | ACCEPT WITH MODIFICATION | Read-only selection/qualification must fail closed on ambiguity, stale data, or missing authority; selection cannot dispatch. |
| Non-live dispatch plan | ACCEPT WITH MODIFICATION | Produce an inspectable plan only; no launch, admission, or external effect. |
| Execution identity and receipt contracts | ACCEPT WITH MODIFICATION | Receipts are append-only facts from the producing component; Zeus verifies them and cannot forge provider facts. |
| Read-only inspection/verification | ACCEPT | Must not mutate runtime, EOS, EENS, EMM, or lifecycle state. |
| `engctl codex` adapter | ACCEPT WITH MODIFICATION | Compatibility adapter only; direct invocation is not authoritative and Codex is not the only provider. |
| Replay/forged-state safeguards | ACCEPT | Must bind identity, source digest, baseline, ordering, and producer; reject replay or forged receipts. |
| Live dispatch/autonomous selection | REJECT | Explicitly out of scope and prohibited by the WOP and current ZDCL direction. |
| New authority layer/registry/document class | REJECT | Violates existing ownership and the architectural burden-of-proof rule in SPEC-0014. |

## Complexity assessment

The proposal is directionally sound but risks duplicating provider registry,
execution identity, receipt, and metadata semantics already distributed across
EMM, EOS, EENS, and the Engineering Execution Interface. The revised design
must be a thin Zeus integration over those owners. Any new component must have
one producer, one schema owner, one locator, and an explicit compatibility
mapping.

## Result

Provider-neutral architecture is `ACCEPT WITH MODIFICATION`. It is not an
approval to implement or dispatch.
