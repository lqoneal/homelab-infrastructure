# Codex Stop and Cancellation

`zeus execution stop <execution>` sends SIGTERM to the recorded process group,
waits for the bounded timeout, then sends SIGKILL if needed. The stop receipt
is idempotent. This interface does not authorize destructive mission actions;
it controls only the Zeus-owned provider process.
