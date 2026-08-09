# Zeus-Native Verification

The following surfaces all returned `RC=0` and `result=PASS` after the final
transition:

`mission show`, `mission state`, `mission authority`, `mission blockers`,
`mission readiness`, `mission eligibility`, `mission next`, and
`mission snapshot` for `ZEUS-EXECUTION-LIFECYCLE-COMPLETION-01`.

The shared values were:

```text
MISSION_ID=ZEUS-EXECUTION-LIFECYCLE-COMPLETION-01
WOP_ID=WOP-ZEUS-EXECUTION-LIFECYCLE-COMPLETION-001
PROVIDER_ID=zeus-local-loneal-01
DISPATCH_ID=DISPATCH-18865edc-5878-57c0-ae43-c697f01e3325
PROVIDER_SESSION_ID=PROVIDER-SESSION-309031db-d38a-5bf9-8db3-b871ed2ddfd1
PROVIDER_INVOCATION_ID=PROVIDER-INVOCATION-ccbf4655-b0f4-57b2-8a1a-3fea9a3d88f9
EXECUTION_ID=EXECUTION-START-03e0a183-23a4-5dc7-b6dc-bc62c1a9a1ae
EXECUTION_SESSION_ID=EXECUTION-SESSION-13637768-524b-5587-8d01-1cce5f301b80
MISSION_STATE=AWAITING_EXECUTION_DISPATCH
NEXT_AUTHORIZED_ACTION=BEGIN_CONTROLLED_MISSION_WORK
BLOCKERS=[]
MISSION_WORK_STARTED=NO
```

`zeus status --json`, `provider-invocation verify`, and `execution-start
verify` agreed with the mission-native projection.
