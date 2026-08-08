# Changed-File Manifest

## Wave 1 files

| File | Change | Dirty-file overlap |
|---|---|---|
| `scripts/lib/emp/submission_boundary.py` | Receipt-backed canonical P2 read model and common projections | Pre-existing modified file; publish only the `mission_view()` Wave 1 hunks |
| `scripts/zeus` | Route P2 `readiness` and `eligibility` actions through the canonical read model | Pre-existing modified file; publish only the action-set hunk |
| `engineering/docs/architecture/ZEUS-MISSION-PROJECTION-SPECIFICATION.md` | Documents P2 `ADMISSION_REQUESTED` projection and canonical next action | New Wave 1 controlled-document hunk |
| `scripts/tests/test-zeus-wave1-canonical-read-model.py` | Focused positive, negative, replay, historical, and non-mutation tests | New Wave 1 test |
| `engineering/planning/ZEUS-LIFECYCLE-GAP-REMEDIATION-PLAN-001.md` | Marks GAP-001 and GAP-006 `QUALIFIED` | Planning-state hunk from prior planning candidate |
| `engineering/evidence/operation-beta/zeus-lifecycle-wave1-canonical-read-model-001/` | This evidence package | New Wave 1 evidence |

All other dirty tracked and untracked paths are preserved and excluded from
this candidate.
