# Digest Role Classification

| Digest | Semantic role | Validation |
|---|---|---|
| Stage 1 package digest | Immutable promoted package identity | Record cross-checked with package, registration, and dispatch receipts |
| Source digest | Submitted WOP source identity | Compared only with source lineage |
| Submission digest | Canonical WOP projection identity | Recomputed by `submission_digest` validation |
| Execution projection digest | Serialized execution projection identity | State-integrity validation only |
| Runtime state digest | Serialized runtime state identity | Runtime store integrity validation only |

Only the first role is used for package identity. Source, submission,
projection, and runtime-state digests are never compared to it.
