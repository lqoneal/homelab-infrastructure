# Execution-Session Contract

Canonical command:

`scripts/zeus execution-start create ZEUS-EXECUTION-LIFECYCLE-COMPLETION-01 --json`

This P5-G5 foundation transition consumes the acknowledged provider
invocation and creates one identity-bound idle execution session. It binds the
Mission ID, WOP ID, submission, admission, bootstrap, dispatch, provider,
provider session, provider invocation, repository identity, and live baseline.

`EXECUTION_ID=EXECUTION-START-03e0a183-23a4-5dc7-b6dc-bc62c1a9a1ae`

`EXECUTION_SESSION_ID=EXECUTION-SESSION-13637768-524b-5587-8d01-1cce5f301b80`

`EXECUTION_ADAPTER_MODE=QUALIFICATION_ADAPTER`

The transition reported `READY_FOR_CONTROLLED_EXECUTION` and next action
`BEGIN_CONTROLLED_MISSION_WORK`. Its foundation `execution_started` field is
true, but `mission_work_started=false`, `repository_work_started=false`,
`execution_monitoring_active=false`, and no real provider process or work unit
was launched. The second create invocation returned the same execution and
session identities with `duplicate_execution_start=IDEMPOTENT`.
