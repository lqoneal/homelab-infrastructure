# Publication Candidate Manifest

Publication was not performed. The candidate consists of these corrective
files/hunks:

- `scripts/lib/emp/bootstrap_boundary.py` — generic P4 classification and
  scoped cardinality validation.
- `scripts/lib/emp/bootstrap_verification.py` — scoped replay cardinality and
  current-chain downstream validation.
- `scripts/lib/emp/canonical_lifecycle_resolver.py` — mission/WOP/submission/
  admission-scoped P4 selection.
- `scripts/tests/test-zeus-p4-g1-bootstrap-boundary.py` — P4 historical,
  duplicate, current-downstream, and replay coverage.
- `engineering/docs/architecture/ZEUS-MISSION-PROJECTION-SPECIFICATION.md`
- `engineering/docs/architecture/ZEUS-WOP-SUBMISSION-PROCEDURE.md`
- `engineering/docs/operations/ZEUS-DEVELOPMENT-MODE.md`
- This evidence directory.

The listed runtime, test, and documentation files already contained unrelated
pre-existing changes in the working tree. Publication must isolate the P4
hunks from those changes; no file was staged. All other dirty tracked and
untracked paths remain preserved and are outside this candidate.
