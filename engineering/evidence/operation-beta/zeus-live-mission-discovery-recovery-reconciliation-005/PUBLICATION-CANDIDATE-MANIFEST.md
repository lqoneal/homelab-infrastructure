# Publication Candidate Manifest

## Corrective hunks

- `scripts/lib/emp/canonical_lifecycle_resolver.py` — canonical P2 submitted
  mission index (file is an existing untracked Wave 1 candidate; preserve the
  prior candidate content and include this additive function).
- `scripts/lib/emp/canonical_mission_lifecycle.py` — merge canonical submitted
  missions into the existing planning list.
- `scripts/zeus` — non-legacy mission requests fail closed through the
  canonical resolver instead of OA selectors.
- `scripts/tests/test-zeus-wave1-canonical-read-model.py` — live list and
  missing-current-mission regression coverage.
- `scripts/tests/test-zeus-development-mode-recovery.py` — clean isolated
  repository fixture for receiptless-dispatch recovery proof.
- `engineering/docs/architecture/ZEUS-MISSION-PROJECTION-SPECIFICATION.md`
- `engineering/docs/architecture/ZEUS-STAGE1-RUNTIME.md`
- `engineering/docs/cli/ZEUS-USER-GUIDE.md`
- `engineering/docs/operations/ZEUS-DEVELOPMENT-MODE.md`

## New evidence

This directory is the bounded evidence package for the corrective.

All other modified and untracked paths shown by `git status --short` are
pre-existing or belong to prior corrective candidates and remain preserved;
they are not staged by this handoff.
