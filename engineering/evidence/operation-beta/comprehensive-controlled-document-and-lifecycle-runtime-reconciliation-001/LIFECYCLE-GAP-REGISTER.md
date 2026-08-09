# Lifecycle Gap Register

| ID | Severity | Scope | Finding | Recommended remediation |
|---|---|---|---|---|
| GAP-001 | HIGH | BLOCKS_INDEPENDENT_VERIFICATION | P2 target discovery depends on selected runtime root; default surfaces do not expose it when the contract is absent | Canonical runtime resolver and explicit P2/P3/P4 discovery tests |
| GAP-002 | HIGH | BLOCKS_LIFECYCLE_EXECUTION, BLOCKS_INDEPENDENT_VERIFICATION | P2/P3/P4/Stage1/provider chain lacks one integrated mission-native transition resolver | Make receipt chain canonical; subordinate projections only |
| GAP-003 | HIGH | BLOCKS_PUBLICATION | Publication/EOS mutation and mission receipts are not proven as one authoritative chain | Add bounded publication/sync receipt bridge with external mutation authority |
| GAP-004 | HIGH | BLOCKS_SAFE_RECOVERY | Autonomous resolver and Stage1 fixtures require incompatible authority receipt contracts | Define canonical adapter or unified receipt contract; fail closed on ambiguity |
| GAP-005 | HIGH | BLOCKS_CLOSEOUT | Canonical reconciliation closeout and legacy Beta closeout are duplicative | Retain legacy read-only compatibility; unify terminal predicate |
| GAP-006 | HIGH | BLOCKS_INDEPENDENT_VERIFICATION | Mission verification controller and current projection disagree on next action | One canonical next-action resolver and migration tests |
| GAP-007 | MEDIUM | BLOCKS_INDEPENDENT_VERIFICATION | No single native surface covers provider/session/process/monitor/evidence lifecycle | Add mission-native read-only aggregate view |
| GAP-008 | MEDIUM | BLOCKS_SAFE_RECOVERY | Recovery failure modes lack end-to-end proof | Add deterministic interruption/checkpoint/resume scenarios |
| GAP-009 | MEDIUM | BLOCKS_INDEPENDENT_VERIFICATION | Qualification chain is component-tested, not real-mission independently proven | Bind qualification to receipt/evidence manifest chain |
| GAP-010 | LOW | TECHNICAL_DEBT | Historical default mission identity remains in generic Codex compatibility fallback | Make fallback explicitly legacy-only |
| GAP-011 | MEDIUM | BLOCKS_PUBLICATION | Candidate scope verifier cannot accept the entire dirty worktree | Publish only exact isolated corrective hunks |
| GAP-012 | LOW | TECHNICAL_DEBT | Layered validators report candidate drift under synchronization mode | Keep baseline fingerprints immutable; qualify exact candidate |

All findings are classified. No substantive runtime remediation was implemented.

