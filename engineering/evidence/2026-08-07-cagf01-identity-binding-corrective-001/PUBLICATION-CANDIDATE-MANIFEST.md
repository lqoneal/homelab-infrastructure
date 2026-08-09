# CAGF-01 Identity Binding Corrective — Publication Candidate

The candidate is prepared but not staged, committed, pushed, submitted,
admitted, or executed.

## New or corrective paths

- `engineering/work-orders/WOP-OB-CAGF-G01-CANONICAL-001/revisions/2/canonical-wop-package.yaml`
- `engineering/work-orders/WOP-OB-CAGF-G01-CANONICAL-001/canonical-79a9fb9ce9017eb66322bbdc/`
- `engineering/evidence/2026-08-07-cagf01-identity-binding-corrective-001/`
- `scripts/lib/emp/managed_handoff.py`
- `scripts/lib/emp/mission_submission.py`
- `scripts/lib/emp/wop_packaging.py`
- `scripts/lib/eos/operational_beta.py`
- `scripts/lib/wop/canonical_package.py`
- `scripts/tests/test-cagf01-identity-binding-corrective.py`
- `scripts/tests/test-zeus-beta-controller.py`
- `engineering/validation/controlled-document-semantic-profiles.yaml`

## Overlap requiring operator hunk review

- `scripts/validate_controlled_documents.py` — pre-existing Class-C changes
  retained; canonical-package semantic-profile additions are in scope.

## Preserved historical and unrelated paths

- `engineering/work-orders/WOP-OB-CAGF-G01-CANONICAL-001/canonical-wop-package.yaml`
  remains byte-identical revision 1 evidence.
- `engineering/work-orders/WOP-OB-CAGF-G01-CANONICAL-001/canonical-c7a90c8854c170474d210594/`
  remains unchanged historical Stage-1 evidence.
- All other pre-existing modified and untracked Class-C artifacts observed at
  the starting baseline remain present and were not reset or removed.

## Publication boundary

Operator review and canonical publication are still required. The next
authorized lifecycle action after publication review is:

`OPERATOR_REVIEW_AND_PUBLISH_CAGF01_IDENTITY_BINDING_CORRECTIVE`
