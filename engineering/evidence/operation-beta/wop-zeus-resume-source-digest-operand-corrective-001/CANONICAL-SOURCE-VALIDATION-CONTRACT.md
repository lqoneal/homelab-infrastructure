# Canonical Source Validation Contract

The Stage 1 validation receipt is authoritative, with the transaction source
digest as the required fallback. Both are cross-checked when present. The
resolved value is then compared against present admission and execution source
bindings. Missing generic fields are tolerated only when canonical Stage 1
source identity is valid; missing canonical identity, conflicting values, or
untraceable provenance fail closed.

Package, submission, projection, and runtime-state digests retain independent
validation contracts.
