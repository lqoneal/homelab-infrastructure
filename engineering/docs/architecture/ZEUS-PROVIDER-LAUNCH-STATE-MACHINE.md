# Zeus Provider Launch State Machine

`DISPATCHED → LAUNCH_PREPARED → LAUNCH_REQUESTED → PROVIDER_STARTING → PROVIDER_ACKNOWLEDGED → SESSION_MATERIALIZED → SESSION_VERIFIED → EXECUTING`.

Failure states are `LAUNCH_BLOCKED`, `LAUNCH_RETRYING`, `LAUNCH_FAILED`, `ROLLBACK_REQUIRED`, and `TERMINATED`. A launch is replayed by its deterministic launch identity; a healthy terminal record is never started twice. Retry is bounded. Failover requires explicit WOP policy, unchanged effect profile, and another qualified provider.
