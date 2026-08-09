# Root-Cause Analysis

Two independent steady-state assumptions invalidated the legitimate
publication transition. `repository_projection.py` treated every available
EOS mismatch as repository failure, while `canonical_baseline.py` required
`HEAD == origin/main` before admission provenance could be valid. Neither
resolver consulted the authoritative Zeus publication transaction and
milestone receipts.

P3 replay consumed that strict lineage result through
`mission_admission_verification.py` and `bootstrap_boundary.py`. The canonical
lifecycle resolver therefore returned `CANONICAL_P3_CHAIN_INVALID`.
Publication cohort and candidate revalidation then consumed the failed mission
projection and reported stale authority, creating the circular inability to
authorize the push that would restore remote parity.

The second post-commit defect was candidate revalidation against the mutable
working tree. Once a publication commit existed, frozen candidate bytes had to
be reproduced from the transaction commit tree, not rediscovered as still
unpublished working-tree paths.

The correction establishes one receipt-aware repository baseline classifier,
retains raw parity facts, and routes provenance, P3, cohort, candidate, and
publication status through that classification.

