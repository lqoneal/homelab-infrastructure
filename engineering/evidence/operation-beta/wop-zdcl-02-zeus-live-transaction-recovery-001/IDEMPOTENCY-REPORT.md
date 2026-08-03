# Idempotency Report

Repeated resume preserves transaction, registration, provider, agent, and receipt identities. Once dispatch is verified, recovery performs no provider callback and returns `idempotent_recovery: true` with the same receipt projection.
