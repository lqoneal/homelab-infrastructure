# Progressive OA Interruption and Recovery

Stop immediately on interruption, stale/revoked authority, invalid evidence,
reconciliation conflict, rejection, or verification failure. Preserve every
partial artifact and record the active gate as `INTERRUPTED`, `FAILED`, or
`REJECTED`; never infer completion.

Re-run package integrity, repository identity, authority, EOS synchronization,
state, and evidence checks. Resolve the first incomplete durable operation from
the append-only manifest. Resume only that operation with the same package,
gate, execution, and idempotency identity. Verify no duplicate event, evidence,
receipt, transition, approval, dispatch, or completion record.

If engineering change is required, instantiate `templates/corrective-work.yaml`
and obtain separate authority. A recovery record permits restoration of
already-authorized state only; it does not authorize redesign or corrective
implementation.
