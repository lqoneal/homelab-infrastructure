# Session Requirement Ledger

This corrective carries forward the prior accumulated session ledger and
retains the prior eight downstream unverified groups; those groups remain
blocked by this handoff's explicit stop boundary. No earlier requirement is
deleted or silently replaced.

| ID | Active requirement | Status | Evidence |
|---|---|---|---|
| R001 | Submitted-WOP authority; no second generic authority | SATISFIED | Native authority projection |
| R002 | Live Projection First | SATISFIED | Runtime implementation and native verification |
| R003 | Hardcoding Last Resort | SATISFIED | Source search and implementation report |
| R004 | Immutable P2/P3/P4/provider receipts | SATISFIED | Artifact digest comparison |
| R005 | Provenance baseline distinct from live baseline | SATISFIED | Provenance model and ancestry tests |
| R006 | Arbitrary descendant publication support | SATISFIED | Multi-publication and N+1 tests |
| R007 | Fail closed on non-descendant/identity/digest ambiguity | SATISFIED | Negative tests and resolver contract |
| R008 | Current mission-scoped provider selection | SATISFIED | Boundary tests and native projection |
| R009 | Provider identity from live registry | SATISFIED | Registry qualification evidence |
| R010 | Zeus status reconciliation | SATISFIED | `zeus status --json` canonical lifecycle fields |
| R011 | Direct controlled-document reconciliation | SATISFIED | Reconciliation report and validators |
| R012 | Existing provider selection reused before replay | SATISFIED | Native provider verification |
| R013 | Safe idempotent provider replay | SATISFIED | `duplicate_provider_selection=IDEMPOTENT` |
| R014 | Stop before dispatch/session/invocation/execution | SATISFIED | Target artifact inventory |
| R015 | Prior provider-boundary downstream requirements | BLOCKED | Explicit stop boundary; retained from prior ledger |
| R016 | Current provider-lineage corrective | SATISFIED | This evidence package |

The prior ledger's eight downstream groups are not silently skipped: dispatch,
provider/session/invocation, execution start, real work, monitoring/checkpoint,
and downstream completion groups remain unverified because this corrective
prohibits them.

