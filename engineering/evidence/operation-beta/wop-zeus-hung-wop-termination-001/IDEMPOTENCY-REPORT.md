# Idempotency Report

The first successful stop creates one deterministic termination receipt and
one interrupted lifecycle transition. Repeated stop resolves the same
execution and reports `ALREADY_STOPPED`; it does not signal a process, append a
second termination receipt, or alter identity.
