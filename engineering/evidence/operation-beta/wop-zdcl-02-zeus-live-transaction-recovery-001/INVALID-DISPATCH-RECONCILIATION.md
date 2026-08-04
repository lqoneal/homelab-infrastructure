# Invalid Dispatch Reconciliation

An invalid dispatch is retained in evidence with its digest and reason. The active dispatch binding is cleared, the lifecycle returns to `AWAITING_EXECUTION_DISPATCH`, and the next canonical resume creates a fresh authority snapshot before redispatch. No execution receipt is fabricated.
