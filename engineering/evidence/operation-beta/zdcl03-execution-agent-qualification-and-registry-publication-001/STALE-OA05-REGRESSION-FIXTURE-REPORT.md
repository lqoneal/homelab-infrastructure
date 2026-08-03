# Stale OA-05 Regression Fixture Report

The test `scripts/tests/test-zeus-oa05-capability-registry.py` is not valid against
the current published Operational Alpha state.

Observed stale assertions:

- expected active gate: `OA-06`
- actual active gate: `OA-08`
- expected capability count: `5`
- actual capability count: `30`

Disposition:

- This is a pre-existing stale test-fixture defect.
- Current Operational Alpha state and the capability registry shall not be
  modified to satisfy obsolete assertions.
- The test is reconciled by the registry-state corrective: live assertions now
  validate current authoritative invariants, while historical OA-05 values are
  isolated in `scripts/tests/fixtures/oa05-capability-state.json`.
