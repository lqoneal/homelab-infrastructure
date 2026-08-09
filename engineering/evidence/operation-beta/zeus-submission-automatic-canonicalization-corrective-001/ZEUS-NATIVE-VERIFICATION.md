# Zeus-Native Verification

With the isolated runtime selected, the following commands all resolved the same mission without mutation:

```text
zeus mission show ZEUS-EXECUTION-LIFECYCLE-COMPLETION-01 --json
zeus mission state ZEUS-EXECUTION-LIFECYCLE-COMPLETION-01 --json
zeus mission authority ZEUS-EXECUTION-LIFECYCLE-COMPLETION-01 --json
zeus mission blockers ZEUS-EXECUTION-LIFECYCLE-COMPLETION-01 --json
zeus mission next ZEUS-EXECUTION-LIFECYCLE-COMPLETION-01 --json
zeus mission snapshot ZEUS-EXECUTION-LIFECYCLE-COMPLETION-01 --json
zeus mission verify ZEUS-EXECUTION-LIFECYCLE-COMPLETION-01 --json
```

All returned `result=PASS`, `lifecycle_state=ADMISSION_REQUESTED`, the correct WOP identity, operator-submitted-WOP authority, no blockers, and `EVALUATE_MISSION_ADMISSION` as the next action. The snapshot reports `WOP_PUBLISHED=NO` and `WOP_SUBMITTED=YES`; no admission, provider, session, dispatch, or execution identity was present.
