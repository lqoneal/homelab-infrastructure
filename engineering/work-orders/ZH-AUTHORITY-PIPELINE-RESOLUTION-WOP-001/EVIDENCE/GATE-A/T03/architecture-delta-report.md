# T03 Architecture Delta Report

## Before T03

```text
oa02_lifecycle
  +-- GateApprovalService.configured
  +-- OA-01 binding and milestone validation
  +-- OA-02 candidate discovery
  +-- external verification-record interpretation
  +-- lifecycle rendering and snapshot persistence
```

The projection module directly implemented approval-evidence and candidate
resolution even though T01 and T02 had established canonical Progressive
authority.

## After T03

```text
Progressive Authority Primitives + Progressive Decision Authority
                         |
                         v
             ProgressiveGateService.gate_state
                         |
                         v
          ProgressiveLifecycleProjector (read-only)
                         |
                         v
            oa02_lifecycle compatibility view
```

Authority failures propagate through `ProgressiveLifecycleError`. Projection
consistency adds only read-model invariants: an accepted lifecycle must select
one canonical valid receipt, and a non-accepted lifecycle must select none.
The projector cannot decide or advance state.

## Frozen layers

T03 does not alter the T01/T02 implementation layers. SPEC-0012 1.1 records
them as `ARCHITECTURALLY FROZEN`; extension is permitted, but competing
authority implementations require an approved architectural decision.
