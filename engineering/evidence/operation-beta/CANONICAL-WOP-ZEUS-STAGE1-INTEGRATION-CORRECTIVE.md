# Canonical WOP → Zeus Stage 1 Integration Corrective

`STATUS=AWAITING_OPERATOR_REVIEW`

## Scope

This bounded corrective adds read-only/native source handling and deterministic
Stage 1 adaptation for `canonical-wop-package/1`. It does not implement or
submit OB-CAGF-G01, create authority, or mutate mission, execution, runtime,
or EOS state.

## Implementation

- `scripts/lib/emp/wop_packaging.py` now explicitly classifies only YAML with
  `schema_version: canonical-wop-package/1` and a package identity mapping.
- The canonical validator runs before adaptation; invalid schema, integrity,
  identity, authority, extension, dependency, or cycle input fails closed.
- The adapter reuses the existing Stage 1 package-directory model and keeps
  canonical package, raw source, and derived Stage 1 tree digests distinct.
- Canonical identity, mission, gate, revision, baseline, requirement,
  recovery, publication, and non-authority declarations are retained in the
  Stage 1 metadata/manifest.
- `scripts/zeus` routes canonical YAML through an isolated temporary adapter
  for read-only `wop validate`, `inspect`, and `verify`. Canonical WOP IDs
  resolve to their unique canonical YAML source when supplied as a package
  directory identity.
- Governed `zeus submit` uses the same adapter and existing Stage 1 submit
  path; no submit was run against the real package in this corrective.

## Digest and ownership contract

The canonical package digest remains
`c7a90c8854c170474d21059463bda616b93cd1886ee372a2fa1c4ab4ebc1b85c`. The
raw YAML digest remains repository provenance
`70efd25355a8364dd748cbde9376fcf718d6a992f29fbbb982c54c67c539fac2`. An
adapted Stage 1 tree has its own derived identity. Stage 1 remains the sole
owner of registration, provenance, submission, admission, and lifecycle;
canonical projections remain non-authoritative.

## Verification

- Native `zeus wop validate`, `inspect`, and `verify` against the published
  canonical YAML: PASS, read-only, no traceability sidecar required.
- Canonical package tests: PASS, 7/7.
- Adapter integration tests: PASS, 5/5.
- WOP contract tests: PASS, 17/17.
- Stage 1 runtime tests: PASS, 7/7.
- Packaging tests: PASS, 9/9.
- Submission-boundary tests: PASS, 4/4.
- Admission tests: PASS, 13/13 and 9/9.
- Controlled-document validation: PASS.
- Registry, Zeus platform, Operation Beta, EOS, repository/EOS, and diff
  checks: PASS.
- Existing mission-oriented `test-zeus-wop-submission.py` remains failing in
  two unrelated cases (`MISSION_NOT_ELIGIBLE` expectation mismatch and a
  published-package result mismatch); no changes were made to that path.

No real WOP submission, admission, mission selection, execution, commit,
publication, push, or EOS synchronization was performed.
