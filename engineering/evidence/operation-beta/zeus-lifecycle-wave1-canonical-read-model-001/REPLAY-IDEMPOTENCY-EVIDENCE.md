# Replay and Idempotency Evidence

The exact mission snapshot command was run twice against the same P2 runtime.
The JSON projections were identical and the complete runtime file digest map
was unchanged. The six focused Wave 1 tests also verify repeated read
surfaces, receipt cardinality, and historical projection exclusion.

```text
REPLAY_IDEMPOTENCY=PASS
READ_ONLY_MUTATION_CHECK=PASS
DUPLICATE_SUBMISSION_CREATED=NO
DUPLICATE_MISSION_CREATED=NO
```

No receipt, request, admission, execution, or lifecycle state was created or
modified by a read-only command.
