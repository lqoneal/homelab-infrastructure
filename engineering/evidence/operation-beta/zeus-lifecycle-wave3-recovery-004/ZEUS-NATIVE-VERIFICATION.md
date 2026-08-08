# Zeus-Native Verification

```text
ZEUS_RUNTIME_ROOT=/tmp/zeus-submission-canonicalization-4lKCNq scripts/zeus mission recovery ZEUS-EXECUTION-LIFECYCLE-COMPLETION-01 --json
ZEUS_RUNTIME_ROOT=/tmp/zeus-submission-canonicalization-4lKCNq scripts/zeus mission aggregate ZEUS-EXECUTION-LIFECYCLE-COMPLETION-01 --json
```

Both returned `PASS`, `read_only=true`, the canonical mission/WOP identity,
`ADMISSION_REQUESTED`, `EVALUATE_MISSION_ADMISSION`,
`recovery_state=NOT_STARTED`, `monitoring_state=NOT_STARTED`,
`resume_eligibility=NOT_AVAILABLE`, and no recovery records. The aggregate
reported `current_execution_readiness=NOT_AVAILABLE` and
`historical_session_execution_leak=NONE`. Repeated inspection returned the
same projection and did not change the runtime tree.
