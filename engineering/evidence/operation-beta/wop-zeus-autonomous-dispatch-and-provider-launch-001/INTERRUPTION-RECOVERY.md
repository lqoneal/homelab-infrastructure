# Interruption Recovery

The launch journal is replay-safe. A pre-acknowledgment interruption remains retryable; a verified `EXECUTING` record is reused. Conflicting launch IDs fail closed.
