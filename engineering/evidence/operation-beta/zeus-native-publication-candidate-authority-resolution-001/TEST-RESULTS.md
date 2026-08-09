# Test results

Focused candidate-authority tests cover one source, multiple-source union,
dependency inclusion, historical exclusion, already-published exclusion,
conflicting claims, missing paths, deterministic replay, and exact
source-to-path traceability.

Results:

- candidate authority tests: PASS (5/5);
- native publication transaction tests: PASS (5/5);
- repository projection tests: PASS (9/9);
- Python compilation: PASS;
- deterministic prepare replay: PASS; same publication identity and candidate
  digest;
- stale candidate handling: PASS; the pre-report transaction was preserved as
  `STALE_CLASSIFICATION` and superseded by a new deterministic transaction.
- mission publication projection: PASS; failed historical transactions do not
  override the single active transaction, while multiple active transactions
  remain fail-closed.
