# Codex Process Supervision

Zeus records PID, process-group ID, working directory, branch, launch time,
provider, context digest, and launch receipts. Process groups are supervised,
not individual terminal sessions, so cancellation cannot leave an orphaned
Codex child behind.
