# Session Requirement Ledger

This gate carries forward the prior lifecycle ledgers and records the active
requirements for the current handoff.

| ID | Requirement | Status | Verification |
|---|---|---|---|
| R01 | Submitted WOP is sole authority; no new authority artifact | SATISFIED | WOP digest and receipt bindings |
| R02 | Preserve dirty/unrelated work; no stage/commit/publish/push/EOS | SATISFIED | Git inventory and final index/validation |
| R03 | Verify live mission, provider, dispatch, session, and repository boundary before mutation | SATISFIED | STARTING-STATE and native commands |
| R04 | Invoke only canonical `provider-invocation create` | SATISFIED | Invocation receipt and command output |
| R05 | Provider identity is live-registry-derived and mission-scoped | SATISFIED | Provider selection and invocation bindings |
| R06 | Provider invocation replay is idempotent | SATISFIED | Same invocation ID/digests on replay |
| R07 | Follow only Zeus-reported next action | SATISFIED | Native projection changed to `START_EXECUTION` |
| R08 | Establish only the canonical idle execution session | SATISFIED | P5-G5 receipt and execution-session artifact |
| R09 | Execution-session replay creates no duplicate | SATISFIED | Same execution/session IDs on replay |
| R10 | Stop before controlled mission work | SATISFIED | `BEGIN_CONTROLLED_MISSION_WORK` stop boundary; no work receipt |
| R11 | Reconcile directly affected docs and roadmap | SATISFIED | Reconciliation and roadmap artifacts |
| R12 | Run focused/regression/full validations | SATISFIED | Validation report; unrelated failures classified |
| R13 | Zeus-native surfaces independently agree | SATISFIED | Native verification artifact |
| R14 | Carry forward Live Projection First, immutable provenance, and fail-closed rules | SATISFIED | Runtime bindings, docs, and tests |
| R15 | Do not begin GAP-009, Wave 3 E2E recovery, CAGF-01, or later work | SATISFIED | Stop boundary and final audit |

Downstream mission-work, monitoring, qualification, publication, EOS
synchronization, closeout, and CAGF-01 requirements are explicitly
`UNVERIFIED_BY_STOP_BOUNDARY`, not silently omitted.

`UNMAPPED_ACTIVE_REQUIREMENTS=0`

`UNEXPLAINED_SKIPPED_REQUIREMENTS=0`

`ALL_OPERATOR_SUBMISSIONS_ACCOUNTED_FOR=YES`
