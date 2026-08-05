# Zeus Autonomous Dispatch and Provider Launch

After a receipt-backed `DISPATCHED` state, Zeus owns the provider-launch boundary. The shared lifecycle resolver validates immutable dispatch and provider-selection receipts, derives one deterministic launch identity, invokes only the configured qualified provider adapter, verifies process and health acknowledgment, materializes one session, and then exposes `EXECUTING`.

An absent adapter, invalid acknowledgment, conflicting ownership, exhausted retry policy, or failed session persistence is fail-closed. Zeus never fabricates an acknowledgment, changes Stage 1 receipts, or creates authority. Launch state is journaled atomically under the selected runtime and keyed by Stage 1 transaction plus dispatch receipt digest.

The default prepublication path records `PROVIDER_LAUNCH_ADAPTER_UNAVAILABLE`; actual launch requires an explicitly configured provider adapter and a separately authorized post-publication execution context.
