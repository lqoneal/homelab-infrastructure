# Execution State Machine

The canonical phases are persisted in `autonomous_delivery.PHASES`, from
`SOURCE_DISCOVERED` through `MISSION_CLOSEOUT`. A phase is not reported until
its prerequisite receipt-backed representation exists. Missing derived runtime
state is reconciled through `runtime_reconciliation`; immutable divergence and
authority boundaries fail closed.
