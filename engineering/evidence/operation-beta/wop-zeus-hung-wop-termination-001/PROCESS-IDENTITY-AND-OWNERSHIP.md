# Process Identity and Ownership

Termination requires the session-bound process PID, process-group ID, process
session ID, and recorded process start time where available. Zeus verifies the
current process group and start time and rejects missing, mismatched, or
self-owned process groups. Child cleanup is achieved only through the proven
execution process group; unrelated groups are never matched or signaled.
