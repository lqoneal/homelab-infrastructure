# Stage 1-to-Runtime Binding Trace

`execute-mission` calls the shared Stage 1 resolver with hydration enabled. When an execution argument is present, the resolver first selects the unique receipt-backed transaction whose Stage 1 `instance_id`, dispatch `instance_id`, or provider transaction binding matches it. It then delegates to the transaction-scoped reconciliation lock, extracts canonical `instance_id`, validates dispatch/provider bindings, discovers admission/execution/session projections, compares semantic identity, prepares derived projections, atomically installs them, and returns the same identity to status, session, start, and resume.

Direct runtime loading occurs only after this resolution.
