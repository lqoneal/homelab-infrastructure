# Adoption Evidence

Dry-run:

```text
scripts/zeus runtime adopt --source /tmp/zeus-submission-canonicalization-4lKCNq --dry-run --json
```

Result: `PASS`

- Adoption ID: `89e798494d51bd803d8d1201`
- Mission: `ZEUS-EXECUTION-LIFECYCLE-COMPLETION-01`
- Submission: `SUBMISSION-a2c024ce-077a-5d70-bb1d-067e056e5a23`
- Durable manifest: `canonical-submission-adoption.json`

The real adoption completed with `ADOPTED_CANONICAL_SUBMISSION`; replay
completed with `ALREADY_ADOPTED` and the same adoption ID. An equivalent copy
of the transaction runtime also replayed as `ALREADY_ADOPTED`.

The durable runtime contains both the historical Beta P2 record and the new
lifecycle P2 record. It contains no lifecycle admission or execution receipt.
The lifecycle receipt preserves the source digest, WOP identity, Mission
identity, repository fingerprint, submission digest, and receipt digest.
