# Reconciliation Plan

## Pre-mutation gate

- Starting expanded dirty paths: 86.
- Class A: 50; Class B: 0; Class C: 36; Class D: 0; Class E: 0; Class F: 0.
- Phase 8 reconciliation files: 5 additional paths, each classified once in the CSV.
- Initial unclassified paths: 0.
- Initial unresolved paths: 0.
- No deletion action is authorized.

## Execution order

1. Apply exact-hunk isolation for Group A and stage the 50 manifest-equivalent paths.
2. Run candidate-scope, diff-check, controlled-document, focused semantic, registry, and Zeus publication preflight checks.
3. Commit Group A as one bounded publication. Push is blocked until remote SSH credentials are available; do not claim publication to origin.
4. Fetch and verify parity again. EOS synchronization is not run while the EOS manifest drift remains read-only/unresolved and no explicit sync boundary has been authorized.
5. Publish the five reconciliation records as a separate bounded cleanup-evidence commit.
6. Do not publish Class C groups: their reports explicitly say COMMIT=NOT_PERFORMED/PUBLICATION=NOT_PERFORMED or awaiting operator review, and the user instruction prohibits mixing them merely to clean the tree.
7. Recompute inventory after each transaction. Preserve the remaining Class C files; no D/E deletion is safe.

## Clean-tree qualification

A clean tree cannot be reached within the established authority boundaries without
publishing or discarding Class C artifacts that are explicitly pending their
own lifecycle. Discarding them is prohibited. Therefore the final state may
remain dirty with Class C preserved; this is a preservation blocker, not an
unresolved provenance blocker. Implementation readiness is BLOCKED until the
owning authorities qualify/publish or otherwise disposition those 36 follow-on
paths.

## Validation commands after bounded transactions

`git diff --check`; `scripts/validate_controlled_documents.py`;
`scripts/engctl validate homelab`; `scripts/engctl registry validate`;
`scripts/engctl eos sync-validate homelab`; `scripts/engctl platform validate homelab`;
`scripts/zeus platform verify`; `scripts/zeus status`; `scripts/zeus doctor`;
Operation Beta verification; EOS validation; repository/EOS parity; integrated validation.

CAGF-01 execution is explicitly not authorized by this cleanup and will not start.
