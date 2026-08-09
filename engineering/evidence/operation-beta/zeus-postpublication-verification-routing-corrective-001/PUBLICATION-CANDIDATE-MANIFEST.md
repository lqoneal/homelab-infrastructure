# Publication Candidate Manifest

Candidate: Zeus postpublication verification routing corrective

Mission: `ZEUS-EXECUTION-LIFECYCLE-COMPLETION-01`

WOP: `WOP-ZEUS-EXECUTION-LIFECYCLE-COMPLETION-001`

Scope: expose the existing authoritative `VERIFY_POSTPUBLICATION_STATE`
transition through the canonical Zeus CLI and document/test that contract.

## Exact candidate paths

- `scripts/zeus`
- `scripts/tests/test-zeus-postpublication-verification-routing.py`
- `engineering/docs/cli/ZEUS-USER-GUIDE.md`
- `engineering/docs/operations/ZEUS-EXECUTION-LIFECYCLE-PROCEDURE.md`
- `engineering/evidence/operation-beta/zeus-postpublication-verification-routing-corrective-001/COMPLETION-EVIDENCE.md`
- `engineering/evidence/operation-beta/zeus-postpublication-verification-routing-corrective-001/PUBLICATION-CANDIDATE-MANIFEST.md`

## Authority and validation

The transaction owner remains `scripts/lib/emp/publication_transaction.py`;
the corrective does not create or modify a second lifecycle mechanism. The
canonical command is:

```text
scripts/zeus publication verify-post <PUBLICATION_ID> --json
```

Focused and directly affected regression results, live recovery output, final
state, next action, and blockers are recorded in
`COMPLETION-EVIDENCE.md`. Unrelated dirty worktree content is outside this
candidate.
