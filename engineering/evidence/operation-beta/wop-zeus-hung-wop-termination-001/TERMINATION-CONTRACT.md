# Termination Contract

`scripts/zeus stop <mission>` is exceptional execution control. It resolves
one unambiguous execution, verifies the exact recorded PID/process-group
identity, requests SIGTERM, escalates to SIGKILL after a bounded timeout, and
records an immutable `EXECUTION_TERMINATION` receipt. Success leaves execution
and session state `INTERRUPTED`; the next action is `scripts/zeus resume
<mission>`.

It never creates authority, cancels a mission, replaces a transaction, or
targets processes by command name.
