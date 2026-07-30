# T01 Primitive Interface Specification

## Scope

The canonical Progressive-only surface is
`scripts.lib.emp.progressive_gate`. It does not route commands, interpret
legacy text receipts, or alter operator workflows.

## Interfaces

| Interface | Contract |
|---|---|
| `verify(root, gate_id)` | Run the registered gate-specific verifier, then validate its repository-owned evidence and marker binding. Unsupported gates and any verifier error fail closed as `ProgressiveGateError`. |
| `verification_state(root, gate_id)` | Validate `VERIFICATION.json` and `VERIFIED`, including package, gate, evidence digest, and marker digest, and return their repository-qualified locators. |
| `validate_receipt(root, gate_id)` | Validate the state-selected receipt, content digest, package/gate/decision binding, package manifest binding, marker file digest, evidence/marker digests, supersedence, replay lifecycle, and predecessor chain. |
| `predecessor_state(root, gate_id)` | Resolve the immediate predecessor from the fixed Progressive gate sequence and require its canonical receipt. OA-01 returns `NOT_REQUIRED`. |
| `gate_state(root, gate_id=None)` | Return current gate, selected gate state, verification state, predecessor state, and receipt state from Progressive records only. |

All interfaces resolve `root`, require the Progressive package below that
root, return the qualified repository path and package identity, and perform
no writes except those performed by a gate-specific verifier invoked through
`verify`.

`verify` currently registers OA-01 through OA-05, the implemented Progressive
verifiers. OA-06 through OA-30 fail closed until their implementations exist.
The stable interface requires no architectural extension when those
implementations are registered.

## Determinism and replay

Queries are pure over repository bytes. Receipt selection comes only from
`runtime/state.json`; historical glob order cannot select authority. Repeated
validation returns equal results. A superseded, stale, unselected, malformed,
or state-inconsistent receipt is rejected.

## Compatibility

`progressive_oa.verify_receipt()` retains its existing signature and
`gate_id`/`receipt`/`integrity` response while delegating validation to the
canonical abstraction. Gate-specific verifier entry points remain callable
and all legacy interfaces remain present.
