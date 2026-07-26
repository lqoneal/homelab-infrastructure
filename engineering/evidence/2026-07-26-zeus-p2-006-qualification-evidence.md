# ZEUS-P2-006 Owner Enrollment Toolkit Qualification Evidence

Date: 2026-07-26
Baseline: `5ebaa32` plus ZEUS-P2-002 through P2-005 working-tree state
Result: PASS — toolkit qualified; no production enrollment or activation

## Qualified capabilities

- OpenSSH public-key parsing and SHA-256 fingerprinting.
- Explicit owner/principal/authorization enrollment requests.
- Detached SSH authorization verification in the
  `zeus-owner-enrollment` namespace.
- Create/update lifecycle for enrollment, rotation, suspension, and retirement.
- Registry digest validation and immutable identity history.
- Candidate-only owner trust policy and allowed-signers compilation.
- Unsigned record-specific publication templates.
- Canonical unsigned envelope preparation with deterministic ID and digest.
- Governance approval payload validation without decision generation.
- Commissioning diagnostics separated by enrollment, signature, approval,
  publication-set, source-record, and activation blockers.

## Security evidence

Qualification proves:

- private-key input is rejected;
- the toolkit has no key-generation or envelope-signing operation;
- unsigned, tampered, incorrectly authorized, or wrong-owner requests fail;
- every enrollment lifecycle action requires a fresh external signature;
- trust compilation fails until all eight designated owners are active;
- compiled trust output is marked `candidate_only` and is not installed;
- Governance approval templates contain no decision;
- an incomplete approval payload is rejected;
- a complete owner-supplied approval payload is validated and wrapped without
  adding a signature; and
- all production configuration switches remain false.

Ephemeral qualification keys and isolated policies/registries are destroyed
after each test and are never promoted.

## Production status

`scripts/authority-ownerctl status` reports zero active enrollments and eight
missing owners. `scripts/authority-publishctl status` now distinguishes:

- unconfigured enrollment root;
- missing owner enrollments;
- missing compiled trust principals and keys;
- missing unsigned publication envelopes;
- missing detached signatures;
- missing Governance approval publication;
- empty operational collections; and
- inactive authority source.

The P2-005 commissioning work item remains blocked on genuine external owner
artifacts, not missing software capability.

## Focused commands

```text
python3 scripts/tests/test-owner-enrollment.py
python3 scripts/tests/test-authority-publication.py
python3 scripts/tests/test-authority-resolution-runtime.py
python3 scripts/tests/test-emp-registry.py
scripts/authority-ownerctl status
scripts/authority-publishctl status
```

Aggregate repository results are recorded in the completion report.
