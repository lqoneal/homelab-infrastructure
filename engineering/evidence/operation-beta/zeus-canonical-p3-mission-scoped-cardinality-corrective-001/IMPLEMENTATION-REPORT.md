# Implementation Report

The corrective uses one shared mission-scoped contract in the existing P3
boundaries:

- `scripts/lib/emp/bootstrap_boundary.py` classifies P3 files against the
  selected admission transaction and reports current, historical, and invalid
  counts.
- `scripts/lib/emp/mission_admission_verification.py` applies the same scoped
  current-set contract and ignores unrelated historical downstream records.
- `scripts/lib/emp/canonical_lifecycle_resolver.py` selects the exact current
  P3 admission for the active P2 identity and rejects duplicate current
  candidates or a historical-only result.
- `scripts/tests/test-zeus-p3-mission-scoped-cardinality.py` covers current,
  historical, superseded/legacy, mismatch, zero-candidate, duplicate-current,
  and replay identity behavior.

The implementation is generic and does not hard-code the lifecycle mission.
It preserves the existing receipt-backed lifecycle owner and does not add a
parallel resolver or authority source.

No schema change was required. Current P3 cardinality and historical artifact
semantics were reconciled in:

- `engineering/docs/architecture/ZEUS-MISSION-PROJECTION-SPECIFICATION.md`
- `engineering/docs/architecture/ZEUS-WOP-SUBMISSION-PROCEDURE.md`
