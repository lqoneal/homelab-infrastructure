# Root-Cause Analysis

## Finding

The postpublication failure was a baseline-policy defect in the shared P3
validation path. Admission and bootstrap receipts recorded the immutable
repository baseline `7f77dfdc4eb98d7eb8cbcb4a837a6cf0b3505a5c`, but the
repository had subsequently advanced legitimately to
`4305b95216ca4022e176e00922ecb50fae318dec` and EOS was synchronized to that
same descendant. The old validation required the receipt baseline to equal
the current HEAD, so the canonical P3 chain failed closed even though the
publication was a valid descendant.

The failure was not caused by a permission decision, missing WOP authority,
P3/P4 cardinality, or provider state. It occurred in the shared admission
baseline validation consumed by the canonical lifecycle resolver.

## Corrective ownership

`scripts/lib/eos/canonical_baseline.py` now owns generic provenance-lineage
validation. `bootstrap_boundary.py` and
`mission_admission_verification.py` consume that shared contract. The
canonical lifecycle resolver validates the durable current reconciliation
receipt after P3/P4 resolution. `scripts/zeus publication reconcile` is the
user-facing bounded reconciliation operation.

No historical P2/P3/P4 receipt was rewritten. The durable reconciliation
receipt is a current derived artifact and does not replace the original
receipt provenance.

