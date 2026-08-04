# Regression Test Report

Hydration and canonical recovery tests passed, including legacy projection hydration, invalid dispatch without an authority snapshot, digest verification, migration, idempotency, replay protection, provider preservation, lifecycle continuity, and no-fabrication behavior. `git diff --check` passed.

One unrelated published-main CLI regression expects the historical doctor label `READY_FOR_REVIEW`; the current command returns `READY`. No hydration or recovery behavior was changed for that test.
