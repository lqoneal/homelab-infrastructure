# Selection Policy Assessment

## Finding

The candidate resolver is mission/WOP scoped but not publication-boundary scoped.
It selects every source classified `QUALIFIED_UNPUBLISHED` for the active
Mission/WOP and unions their path claims. This is deterministic, but not
sufficiently authoritative for shared files.

## Evidence

- 19 source manifests are selected.
- All 19 bind to the same Mission and WOP.
- 14 frozen paths have multiple source claims.
- The manifests describe shared files as hunk-scoped, but the frozen candidate
  stores path membership only.
- No selected source exposes a non-empty publication cohort, gate, or candidate
  intent.
- The current transaction nevertheless reports no blocker and
  `PREPUBLICATION_VERIFIED`.

## Required canonical model

Extend the existing Mission/WOP/publication authority model with a persisted
publication unit/cohort or equivalent hunk-level inclusion authority. A shared
path must be eligible only when its exact content authority is unambiguous.
Absent that authority, native classification must fail closed with a precise
blocker and preserve the immutable transaction for operator review.

The bounded corrective requires that boundary for overlapping current claims.
It accepts disjoint claims and claims sharing one explicit cohort, and fails
closed for the observed 14 overlaps. This preserves deterministic replay and
the frozen transaction while exposing the missing authority through the native
inspect/status/mission-publication projections. It does not invent a cohort or
modify the frozen transaction.

Implementation:

- `scripts/lib/emp/publication_candidate_authority.py`
- `scripts/lib/emp/publication_transaction.py`
- `scripts/tests/test-zeus-publication-candidate-authority.py`

Qualification: candidate-authority `7/7` and publication-transaction `5/5`.
