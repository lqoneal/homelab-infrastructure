# T03 Lifecycle Projection Specification

## Interface

`ProgressiveLifecycleProjector(root, service=None).project(gate_id)` returns:

| Field | Source |
| --- | --- |
| package, repository, gate, current gate | Canonical gate-state query |
| gate, verification, predecessor, receipt states | `ProgressiveGateService.gate_state` |
| receipt | Canonically validated state-selected receipt, or null |
| lifecycle state | Deterministic mapping from canonical gate and verification state |
| next action | Deterministic projection label with no side effect |

`project(root, gate_id)` is the convenience entry point.

## Deterministic mapping

| Canonical condition | Lifecycle projection | Next action |
| --- | --- | --- |
| gate accepted with valid receipt | `ACCEPTED` | `COMPLETE` |
| gate rejected | `REJECTED` | `CORRECT_OR_RECOVER_<gate>` |
| verification valid, decision absent | `VERIFIED_AWAITING_OPERATOR_ACCEPTANCE` | `DECIDE_<gate>` |
| failed or interrupted | `BLOCKED` | `CORRECT_OR_RECOVER_<gate>` |
| otherwise | `AWAITING_VERIFICATION` | `VERIFY_<gate>` |

## Consistency and failure

The projection fails closed when canonical authority reports stale, invalid,
conflicting, superseded, or replay-inconsistent state. It also rejects:

- an accepted gate without a canonical valid receipt; and
- a non-accepted gate that selects an acceptance receipt.

The projection has no write method. OA-02 compatibility may persist a
digest-protected projection snapshot, explicitly classified as a projection.
That snapshot is never consumed as a Progressive verification marker,
acceptance receipt, or decision.
