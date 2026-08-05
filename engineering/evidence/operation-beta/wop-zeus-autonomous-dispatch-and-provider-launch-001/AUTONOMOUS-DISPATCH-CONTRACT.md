# Autonomous Dispatch Contract

Dispatch is authorized only by the immutable Stage 1 chain. The controller derives one launch ID from transaction, dispatch receipt digest, and provider. Missing or conflicting bindings fail closed; successful replay returns the existing terminal launch.
