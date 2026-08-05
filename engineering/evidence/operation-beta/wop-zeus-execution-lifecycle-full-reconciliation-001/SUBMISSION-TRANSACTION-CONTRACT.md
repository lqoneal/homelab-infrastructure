# Submission Transaction Contract

Validation and package acceptance precede mutation. A dispatch receipt is accepted only after provider-selection and authority bindings validate. The shared reconciliation transaction atomically installs and verifies admission and execution projections. Failure is persisted as `BLOCKED` with `EXECUTION_PERSISTED` pending and a resumable next action; no successful `DISPATCHED` response is returned without verified projections.
