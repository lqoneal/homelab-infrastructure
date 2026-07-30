# T02 Decision Service Specification

## Canonical interface

`scripts.lib.emp.progressive_gate.ProgressiveGateService` is the supported
Progressive authority façade. It is repository-bound at construction and
encapsulates:

| Method | Contract |
|---|---|
| `verify` | Dispatch canonical gate verification and validate its binding. |
| `verification_state` | Query the integrity-valid verification record. |
| `validate_receipt` | Validate the state-selected acceptance receipt. |
| `predecessor_state` | Prove the immediate Progressive predecessor. |
| `gate_state` | Query aggregate Progressive gate state. |
| `approve` / `record_acceptance` | Persist or replay an `ACCEPTED` decision. |
| `decline` | Persist or replay a `REJECTED` decision. |
| `decide` | Validated common decision primitive; rejects all other values. |

`decision_service(root)` is a construction helper. Module-level T01 query
functions and `progressive_oa.decide` remain compatibility surfaces, not
additional decision implementations.

## Persistence contract

Decision receipts use the existing schema version 2 format, canonical JSON
digest, filenames, manifest/marker/evidence bindings, and atomic exclusive
creation. State is written only after receipt persistence and validation.
Acceptance advances exactly one gate. Rejection retains the active gate,
clears `acceptance_receipt`, and records `STOPPED_FAIL_CLOSED`.

An accepted replay is authoritative only when selected by runtime state and
when lifecycle, operator, marker, evidence, manifest, digest, and
supersedence checks pass. An interrupted acceptance recovers exactly one
valid persisted receipt. Multiple recoverable receipts fail closed.

A rejected replay requires the deterministic `rejected.json` identity and
revalidates content integrity and all current evidence bindings before it is
returned. A different operator or tampered receipt is a conflict.

## Decision flow

```text
caller
  |
  v
ProgressiveGateService.decide
  |
  +-- validate repository, gate, decision, active state, operator
  +-- validate VERIFIED + VERIFICATION.json (+ OA-02 boundary when applicable)
  |
  +-- existing current decision? --> validate integrity/bindings --> replay
  |
  +-- create canonical receipt --> persist exclusively --> validate
  |                                                    |
  +----------------------------------------------------+
                                                       v
                                               persist runtime state
```

## Fail-closed flow

```text
malformed / stale / conflicting / superseded / ambiguous
                         |
                         v
              ProgressiveGateError
                         |
                         v
             no lifecycle advancement
```

