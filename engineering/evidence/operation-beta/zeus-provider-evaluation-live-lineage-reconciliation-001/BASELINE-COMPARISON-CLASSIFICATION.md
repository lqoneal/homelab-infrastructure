# Baseline Comparison Classification

| Comparison | Classification | Contract |
|---|---|---|
| HEAD vs origin/main vs EOS | `LEGITIMATE_STRICT_EQUALITY` | Must agree for the live publication projection |
| provider recorded baseline vs live baseline | `PROVENANCE_COMPARISON` | Recorded baseline must be an ancestor of live baseline |
| lifecycle provenance baseline vs live baseline | `PROVENANCE_COMPARISON` | Immutable provenance must be an ancestor of live baseline |
| provider identity vs registry | `LIVE_PROJECTION_COMPARISON` | Provider comes from the qualified live registry |
| provider selection artifact digest | `IMMUTABLE_RECEIPT_INTEGRITY` | Digest must reproduce exactly |
| old exact provider baseline == current HEAD requirement | `OBSOLETE_CURRENT_STATE_AUTHORITY` | Removed from current provider projection |

Verified ancestry:

`7f77dfdc4eb98d7eb8cbcb4a837a6cf0b3505a5c` →
`107a915e5e837699d723623cd9abe41da7642506` →
`e7e48ab6b523d94e73d40fb4311f86bc7118b0b1`.

