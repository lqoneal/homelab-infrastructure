# Zeus Execution Lifecycle State Machine

The canonical sequence is:

`SOURCE_DISCOVERED → SOURCE_VALIDATED → PACKAGE_PREPARED → PACKAGE_VERIFIED → PACKAGE_PROMOTED → REGISTERED → AUTHORIZED → ADMISSION_PREPARED → ADMISSION_PERSISTED → ADMISSION_VERIFIED → PROVIDER_SELECTED → DISPATCH_PREPARED → DISPATCH_PERSISTED → EXECUTION_PREPARED → EXECUTION_PERSISTED → EXECUTION_VERIFIED → PROVIDER_LAUNCH_REQUESTED → PROVIDER_LAUNCH_ACKNOWLEDGED → SESSION_PREPARED → SESSION_PERSISTED → EXECUTING → SUSPENDED/RESUMING → TERMINATING → COMPLETED → QUALIFIED → PUBLICATION_PREPARED → PUBLISHED → EOS_SYNCHRONIZED → CLOSED`.

The Stage 1 state `DISPATCHED` is not operationally complete until `mission-admissions/<admission-id>.json` and `mission-executions/<instance-id>.json` exist, validate their state digests, and are bound to the same receipt-backed transaction. `instance_id` is the canonical execution identity. Admission and execution projections are derived and repairable; immutable Stage 1 receipts are not.

Every transition has a previous state, new state, transaction, admission, execution, session, authority snapshot, repository baseline, package/source digests, provider/dispatch binding, persisted/verified artifacts, pre/post state digests, blockers, next action, and receipt. Illegal advancement is fail-closed.
