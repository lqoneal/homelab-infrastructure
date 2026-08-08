# GAP-006 Qualification — Canonical Next Action

`GAP_006_IMPLEMENTED=YES`

For the canonical P2 lifecycle state, the resolver derives rather than
blindly trusts:

```text
ADMISSION_REQUESTED -> EVALUATE_MISSION_ADMISSION
```

A receipt that declares another next action is rejected with
`CANONICAL_NEXT_ACTION_CONTRADICTION`. All affected Zeus-native surfaces
return the same next action and blockers. Exact replay returns the same
projection without mutation.

`CANONICAL_NEXT_ACTION_RESOLUTION=PASS`
