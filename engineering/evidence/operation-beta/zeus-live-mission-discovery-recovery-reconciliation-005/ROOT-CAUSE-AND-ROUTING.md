# Discovery Defect and Routing Reconciliation

## Root cause

`canonical_lifecycle_resolver.resolve()` already resolved the lifecycle mission
from the P2 submission receipt, but the live `mission list` path called the
legacy `canonical_mission_lifecycle.mission_list()` implementation, which only
merged Operation Beta planning entries and the historical STOPQ reconciliation.
It never indexed canonical P2 receipts.

When a requested non-OA mission was absent from the selected runtime, the CLI
also allowed the request to fall through to generic legacy Mission Knowledge /
assurance handling. That produced OA-01-specific selector errors instead of a
canonical `MISSION_NOT_FOUND` result.

## Corrective

- Added a read-only `submitted_missions()` index to the canonical lifecycle
  resolver.
- Merged that index into the existing mission list without deleting the
  Operation Beta planning projection.
- Added explicit non-legacy fail-closed return behavior in `scripts/zeus`.
- Preserved historical OA and Operation Beta compatibility routes.
- Added list, missing-evidence, identity, replay, and isolation regression
  coverage.

No Mission Contract, admission, bootstrap, provider, session, execution, or
lifecycle progression record was manufactured.
