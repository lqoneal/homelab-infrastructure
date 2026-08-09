# State Granularity Assessment

The canonical lifecycle state remains the P2/P3/P4-owned umbrella position
`AWAITING_EXECUTION_DISPATCH`. The subordinate provider/session/execution
projections carry finer-grained progress and do not override that owner.

`READINESS_GRANULARITY_CONTRACT=umbrella lifecycle readiness plus subordinate provider/session readiness`

`ELIGIBILITY_GRANULARITY_CONTRACT=canonical dispatch eligibility until downstream execution foundation is represented`

`NEXT_ACTION_CONTRACT=the receipt-backed subordinate transition is authoritative for the next actionable boundary`

After P5-G4/P5-G5, the subordinate state was
`READY_FOR_CONTROLLED_EXECUTION`, with next action
`BEGIN_CONTROLLED_MISSION_WORK`. This is intentional: execution-session
establishment is complete, but mission work remains a separate held boundary.
