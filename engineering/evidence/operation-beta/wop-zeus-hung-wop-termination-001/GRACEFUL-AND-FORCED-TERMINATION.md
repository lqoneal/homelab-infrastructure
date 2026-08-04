# Graceful and Forced Termination

The control sequence is `EXECUTING -> STOP_REQUESTED -> TERMINATING ->
INTERRUPTED`. SIGTERM is sent first. After the bounded timeout, SIGKILL is
sent only to the verified process group. A surviving target produces
`TERMINATION_FAILED` with exact process diagnostics and preserves the evidence
already recorded.
