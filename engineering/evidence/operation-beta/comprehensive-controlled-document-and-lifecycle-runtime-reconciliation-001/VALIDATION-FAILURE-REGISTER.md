# Validation Failure Register

## Initial findings

The initial semantic-all run reported 93 findings. They were generated `roadmap.md` and legacy `immutable-wop.yaml` files beneath package/evidence trees, not current controlled documents. They were classified `HISTORICAL_ONLY` / `CONFORMANT_FALSE_POSITIVE` for the default aggregate profile. They remain individually inspectable and were not rewritten.

One assurance property, `EP-EMP-PROGRESS-DEVIATION-TRACEABILITY`, used an old literal pattern (`deviation|branch`) that did not match the current deterministic normalized/recommendation implementation. It was corrected to test the current semantic behavior.

## Final results

- `python3 scripts/validate_controlled_documents.py`: PASS.
- `python3 scripts/validate_controlled_documents.py --semantic-all`: PASS, 3805 checks, 0 failures.
- `... --assurance-only`: PASS.
- `... --conformance`: PASS.
- `... --implementation-coverage`: PASS.
- semantic-profile regression tests: PASS, 9 tests.
- synchronization validation reports candidate drift from unrelated dirty work and is not a normative-document contradiction; see `CONFLICT-REGISTER`.

No current normative validation failure remains unexplained.

