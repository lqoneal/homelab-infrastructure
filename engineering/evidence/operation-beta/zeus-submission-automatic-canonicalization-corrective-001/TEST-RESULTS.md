# Test Results

Focused command:

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  scripts/tests/test-zeus-submission-automatic-canonicalization.py \
  scripts/tests/test-zeus-p1-g1-authoring.py \
  scripts/tests/test-zeus-p2-g1-submission-boundary.py \
  scripts/tests/test-wop-submission-authority-convergence.py \
  scripts/tests/test-wop-admission.py
```

Result: `31 tests`, `OK`.

Coverage includes first/replay canonicalization, source byte preservation, conflicting and stale provenance, repository-option routing, generic approval rejection, explicit legacy classification, P2 idempotency, authority projection, native mission views, P1 authoring, P2 boundary, admission, and explicit in-WOP approval behavior.

