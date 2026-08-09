# Root-Cause Analysis

The prior `verify_current()` implementation enumerated reconciliation receipts
for the mission, filtered them by exact equality with the live publication
baseline, and required exactly one candidate. The immutable receipt recorded
`4305…`; after publication the live projection became `0e813…`, so the valid
historical receipt was filtered out and cardinality became zero.

This was a shared canonical P3/P4 resolver defect, not an invalid publication,
permission failure, or receipt corruption. The resolver incorrectly treated a
supplemental reconciliation receipt as the current-baseline authority.

The correction makes synchronized live Git/EOS projections authoritative for
the current baseline. Each matching reconciliation receipt is still verified
for digest, identity, repository binding, its own recorded lineage, and
ancestry to the live publication. A valid stale receipt is historical
supplemental evidence; a forged or contradictory receipt fails closed.
