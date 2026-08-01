# BETA-01 CLI Integration Report

The authoritative command mapping is:

```text
zeus submit <WOP_PACKAGE>
zeus missions list
zeus missions select
zeus mission queue list
zeus mission queue show <MISSION_ID>
zeus mission queue next
zeus mission queue blockers
zeus mission queue history
zeus admit-mission start ...
zeus execute-mission start --admission-id <ADMISSION_ID>
```

The queue subcommands are read-only projections. Existing submission,
selection, admission, and execution commands remain the authoritative
mutation boundaries.
