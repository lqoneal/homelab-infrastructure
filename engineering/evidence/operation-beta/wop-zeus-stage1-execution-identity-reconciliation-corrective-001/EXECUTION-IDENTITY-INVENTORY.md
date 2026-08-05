# Execution Identity Inventory

The authoritative target is Stage 1 transaction `ZEUS-DEVELOPMENT-5afc9959-aa8d-5dba-86b6-08a8721e1806`.

| Representation | Value | Role |
|---|---|---|
| Stage 1 `instance_id` | `ZEUS-DEVELOPMENT-5afc9959-aa8d-5dba-86b6-08a8721e1806` | Canonical execution identity |
| dispatch `instance_id` | same | Immutable dispatch assertion |
| provider-selection `transaction_id` | same | Immutable transaction binding |
| admission ID | `EMM-DEV-ADMISSION-21fbb4d8027dadc133d0cdab` | Admission identity, not execution identity |
| registration ID | `EMM-DEV-21fbb4d8027dadc133d0cdab` | Registration identity, not execution identity |
| runtime execution projection `execution_id` | same | Derived projection |
| native session ID | absent | No session was created or started |

The WOP ID, mission ID, package ID, receipt IDs, provider ID, and dispatch-plan digest are related bindings and are never execution substitutes.
