# Validation Output

## Passing focused qualification

- `test-convergence-runtime.py`: 11 passed.
- `test-wop-admission.py`: 13 passed.
- `test-wop-submission-authority-convergence.py`: 5 passed.
- `test-zeus-p5-g6-codex-adapter.py`: 25 passed, 1 skipped.
- WOP packaging: 9 passed.
- WOP authoring: 11 passed.
- Canonical WOP Stage 1 integration: 5 passed.
- Registry validation: PASS; 87 objects.
- Operation Beta authority status: PASS; authority digest validation PASS.
- Zeus-native submitted-WOP resolution: PASS; see
  `ZEUS-NATIVE-VERIFICATION.md`.

## Read-only qualification results requiring classification

- Controlled-document full run: exit 1, 3902 checks passed and 105 failed.
  Failures are pre-existing semantic gaps in historical/untracked roadmaps,
  fixtures, and legacy WOP packages, plus declared synchronization and
  assurance failures; none is an authority-convergence document failure.
- Individual changed-document semantic checks: several exit 1 because the
  repository’s existing semantic profiles lack required sections/concepts or
  do not resolve profiles; the exact failing concepts are retained in the
  command output and are unrelated to the authority wording change.
- `scripts/engctl eos sync-validate homelab`: FAIL, canonical
  `/data/engineering/eos/state/EOS-MANIFEST.md` drift. No synchronization was
  performed.
- `scripts/zeus platform verify --json`: FAIL only on the same manifest
  consistency/synchronization defect; repository, baseline parity, registry,
  runtime, WOP schema, and validator checks pass.
- Broader lifecycle/provider tests that mutate the default runtime were
  blocked by the sandbox’s read-only `/home/loneal/.local/state` runtime; this
  is environmental and not a corrective implementation failure.
- `git diff --check`: PASS.
