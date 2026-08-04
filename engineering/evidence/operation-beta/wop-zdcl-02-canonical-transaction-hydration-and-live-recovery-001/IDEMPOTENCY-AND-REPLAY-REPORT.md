# Idempotency and Replay Report

Hydration is deterministic and idempotent: repeated resume derives the same fields and receipt ID list. A valid dispatch is not reissued. An invalid dispatch is reconciled once by its historical dispatch digest.
