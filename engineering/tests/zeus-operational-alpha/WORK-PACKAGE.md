# ZEUS-P2-020 PMCT Implementation Work Package

## Execution and integrity

Preflight requires repository
`/data/engineering/repositories/homelab` at starting baseline
`1015ff709656a59e096f1e4b6107f9fa17371e5f`. Apply through the reviewed
repository patch and regenerate only the locked matrix/gate wrappers with
`tools/generate-controlled-assets.py`. Verify the generated diff before commit.

Verification:

```bash
python3 -m unittest discover engineering/tests/zeus-operational-alpha/tests
for file in engineering/tests/zeus-operational-alpha/**/*.sh; do bash -n "$file"; done
engineering/tests/zeus-operational-alpha/bin/pmct inspect
engineering/tests/zeus-operational-alpha/bin/pmct run OA-01
```

The PMCT runtime preserves authoritative engineering, repository, and
operational decision state while creating test evidence and allowing only
explicitly documented bounded presentation telemetry. Rollback before commit
removes only P2-020 files; after commit, use a normal reviewed revert commit.
Never reset or delete the unrelated unsigned P2-019 package.

Interruption leaves a run without `COMPLETE`; preserve it and rerun the gate.
Resume means a new unique run, not editing prior evidence. Controlled
reconciliation updates the PMCT state, Project State, Work Registry, roadmap,
progress/resume tracker, and completion report after validation.

A PMCT `PASS` records only the Codex demonstration result. The next gate
remains blocked until independent operator verification succeeds and an
operator acceptance receipt is recorded and reconciled.
