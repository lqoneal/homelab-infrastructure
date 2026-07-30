# T02 Implementation Report

## Outcome

Progressive decision ownership is centralized in
`ProgressiveGateService`. The service façade also formalizes the complete T01
primitive set before further consumer migration.

## Architecture delta

Before T02:

```text
T01 free query functions --> progressive_oa record mechanics
progressive_oa.decide ----> independent decision orchestration
```

After T02:

```text
ProgressiveGateService
  +-- verification
  +-- receipt validation
  +-- predecessor and gate state
  +-- approve / decline / acceptance recording
  +-- receipt creation, persistence selection, replay, state transition

progressive_oa.decide --> compatibility delegation --> service
```

The receipt schema, locators, state schema, decision names, return tuple, and
exception visible to legacy callers are preserved. Durable-boundary
`OSError` propagation is also preserved for existing interruption recovery.

## API changes

The internal canonical API gains `ProgressiveGateService` and
`decision_service`. No CLI argument, output, exit-code, record-schema, or
operator workflow contract changes. Existing `progressive_oa.decide` and T01
module functions remain callable.

## Modified component inventory

| Component | Change |
|---|---|
| `scripts/lib/emp/progressive_gate.py` | Added the canonical façade and sole Progressive decision orchestration. |
| `scripts/lib/emp/progressive_oa.py` | Replaced decision implementation with an exception-compatible adapter. |
| `scripts/tests/test-progressive-gate-primitives.py` | Added service, approve, decline, duplicate, conflict, malformed-input, and delegation qualification. |
| `EVIDENCE/GATE-A/T02/*` | Added T02 specification and evidence reports. |

No CLI, PMCT, Agent Qualification, carry-forward, OA-02 lifecycle, Mission
Contract, ARS, EWI, execution runtime, or Gate B component was modified.

