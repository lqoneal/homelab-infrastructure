# Zeus Operational Gate Handler Framework

## Purpose and boundary

ZEUS-P2-009 separates execution orchestration from gate implementation.
`MissionExecutionRuntime` continues to own admission/WOP binding, state,
sequencing, checkpoints, evidence, waits, suspension, resume, cancellation, and
operational dispatch denial. `GateHandlerFramework` owns only discovery,
compatibility negotiation, bounded invocation, and the verification-first
handler contract.

The framework does not provide a production dispatcher. P2-010 adds the
operational-only artifact handler described in
`engineering/operations/zeus-operational-artifact-gate-handler.md`; the
existing reference handler remains non-mutating and qualification-only.

## Discovery and registration

Controlled implementations register in `HandlerRegistry`. Declarative
manifests are discovered from `engineering/handlers/*.yaml`.

Discovery never imports code named by a manifest. A manifest becomes usable
only when an already registered controlled implementation has an exactly
matching identity, semantic version, API version, modes, gates, capabilities,
and mutation declaration.

The stable API version is `zeus-gate-handler/1`. Required capabilities are:

- `verification-first`
- `deterministic`
- `idempotent`
- `restartable`
- `structured-evidence`
- `cancellation`

Negotiation requires a compatible mode, every requested gate, and all required
capabilities. No match fails closed.

## Execution contract

Every handler implements:

1. `verify_current(gate_id, context)`
2. `determine_required(gate_id, context, verification)`
3. `execute_required(gate_id, context, work)` when required
4. `verify_result(gate_id, context, result)`

The framework emits the complete handler trace in the gate result. If work is
already complete, execution is skipped and the result is
`PREVIOUSLY_SATISFIED`.

Execution context includes execution, mission, repository, and exact WOP
identity; a stable gate idempotency key; completed gates and checkpoints; retry
count; cancellation state; and invocation timestamp.

External-effect handlers must bind their own idempotency records to the stable
gate key. They must report artifact references rather than embedding mutable
artifacts in runtime state.

## Isolation, timeout, and failure behavior

Discovered handlers run in a bounded child process. Timeout terminates that
process and becomes a retryable structured `GATE_HANDLER_FAILURE`. Exceptions
return structured type/message diagnostics without corrupting the coordinator.

Cancellation between gates uses the Mission Execution Runtime's persistent
`Cancelled` state. The context exposes cancellation state for a future
cooperative operational handler. Mid-call cancellation transport is deferred
until a production handler and external-effect compensation contract are
separately designed; the current handler is non-mutating and safely
terminable.

The `LegacyHandlerAdapter` exists solely for backward-compatible injected test
handlers. It is non-isolated and cannot be discovered from a manifest or
negotiated for operational mode.

## Qualification handler

`zeus.qualification.reference` version `1.0.0` supports `EXECUTE_WORK` and
`VERIFY_COMPLETION`. It verifies repository/WOP context, determines required
work, records deterministic simulated results, verifies the result digest, and
reports `side_effects_performed: false`.

Its manifest is `engineering/handlers/qualification-handler.yaml`.

## Operational extension lifecycle

A future additional operational handler requires separate implementation
scope, controlled implementation registration, an exact compatible manifest,
deterministic idempotency and external checkpoint storage, timeout/cancellation
and compensation qualification, authentic commissioning, and an explicitly
enabled execution boundary unavailable from the current CLI.

Registration or discovery alone never enables dispatch.

## Diagnostics and evidence

Gate completion evidence contains handler identity/version, disposition,
verification-first trace, result verification, artifact references, and
side-effect declaration. Skips, retries, waits, failures, recovery, and
completion remain in the Mission Execution evidence chain and EENS projection.

## Controlled-document disposition

This guide documents a qualified extension framework. It does not authorize a
production handler, activation, dispatch, or execution.
