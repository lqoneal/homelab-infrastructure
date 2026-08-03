# Idempotency and Replay Report

Repeated identical submission resolves the same transaction, registration, and package. Repeated invalid-dispatch reconciliation preserves one historical evidence entry and one recovery receipt; unchanged state is byte-stable. Dispatch selection remains deterministic by qualified agent ID.
