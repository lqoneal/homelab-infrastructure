# Timeout and Escalation

Provider adapters own bounded launch timeout reporting. Exhaustion produces `LAUNCH_FAILED` with `PROVIDER_LAUNCH_RETRY_EXHAUSTED`; no operator dispatch command is synthesized and no launch is acknowledged after timeout.
