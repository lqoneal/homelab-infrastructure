# Recurrence Prevention Tests

`scripts/tests/test-publication-boundary-guard.py` passes four assertions:
candidate commit allowed, clean candidate push allowed, unauthorized `main`
push rejected, and a publication marker cannot bypass the verified-branch
requirement. No test grants authority from a session or WOP identifier.
