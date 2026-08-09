# Baseline Provenance Model

## Two distinct baselines

`RECEIPT_PROVENANCE_BASELINE` is the immutable repository commit against which
the lifecycle receipt was created and qualified:

`7f77dfdc4eb98d7eb8cbcb4a837a6cf0b3505a5c`

`CURRENT_PUBLISHED_BASELINE` is the current live synchronized repository/EOS
commit:

`4305b95216ca4022e176e00922ecb50fae318dec`

They are not interchangeable. The reconciliation receipt records both plus
live `HEAD`, `origin/main`, EOS baseline, repository identity, predecessor
receipt identities, lifecycle state, and the lineage result.

## Lineage contract

The current repository must be on `main`, `HEAD == origin/main`, and equal the
current published target. The provenance commit must be reachable and an
ancestor of that target. Equal commits resolve as `IDENTICAL`; a legitimate
descendant resolves as `ANCESTOR`. Missing, unreachable, unrelated,
non-descendant, repository-mismatched, forged, or ambiguous evidence fails
closed.

The durable reconciliation receipt is deterministically identified from the
live repository identity, mission/WOP and predecessor receipt identities,
provenance baseline, and current publication baseline. Exact replay finds the
same immutable file and digest.

Historical receipts remain append-only evidence. They are never selected as
current authority merely because they are present on disk, and they do not
count as competing current baseline candidates after canonical identity and
lineage scoping.

