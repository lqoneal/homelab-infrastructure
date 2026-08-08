# Implementation Report

Implemented a generic P4 mission-scoped cardinality contract in the existing
bootstrap boundary and replay verifier.

Changed behavior:

1. `_scoped_bootstrap_cardinality` classifies current, historical, legacy,
   superseded, invalid, and ambiguous P4 artifacts.
2. Current cardinality is evaluated per complete P4 identity rather than per
   directory total.
3. Invalid identity-bearing P4 artifacts still fail closed.
4. The canonical lifecycle resolver selects P4 by the active P2/P3 Mission,
   WOP, submission, and admission chain.
5. Prohibited downstream checks are scoped to the requested current chain;
   historical Beta dispatch/provider-session records do not invalidate it.
6. Existing bootstrap transaction and all five artifact identities remain
   unchanged; no bootstrap was rerun to manufacture a replacement.

Runtime implementation files:

- `scripts/lib/emp/bootstrap_boundary.py`
- `scripts/lib/emp/bootstrap_verification.py`
- `scripts/lib/emp/canonical_lifecycle_resolver.py`

Focused regression coverage was added to
`scripts/tests/test-zeus-p4-g1-bootstrap-boundary.py`.
