# Test Results

Focused suite:

```text
PYTHONPATH=. python3 scripts/tests/test-zeus-repository-projection.py
.........
Ran 9 tests in 0.624s
OK
```

Covered cases include clean state, tracked dirty state, staged state,
untracked names containing spaces and tabs, HEAD/origin mismatch, descendant
and non-descendant refs, detached HEAD, missing origin, invalid repository,
EOS mismatch, deterministic replay, JSON serialization, and read-only CLI
behavior.

The current active mission was verified separately through all eight native
mission surfaces. No provider dispatch, invocation, session creation,
execution start, mission work, CAGF-01, publication, push, or EOS
synchronization was performed by this task.

Additional regression classification:

- Provider live-lineage regression: PASS (3/3).
- P5-G2 dispatch foundation: PASS (3/3).
- P5-G1 legacy fixture: FAIL on its pre-existing expectation that the already
  qualified lifecycle provider-selection artifact does not exist; its
  read-only snapshot assertion also observes fixture/runtime drift. This is
  not a repository-projection failure.
- P5-G3 legacy tamper fixture: BLOCKED before assertion because the governed
  durable runtime is read-only in this environment (`Errno 30`).
- Mission-verification controller fixture: BLOCKED during setup by
  `ENOSPC` while copying the 6.3G durable runtime into the 4G `/tmp`
  filesystem. No assertion reached the new projection code.

The direct projection suite and the live eight-surface Zeus verification are
the independent acceptance evidence for this corrective. The legacy failures
remain explicitly classified and were not weakened or silently absorbed.
