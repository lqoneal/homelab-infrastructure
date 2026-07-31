# Execution Contract Certification Report

`OPERATIONAL-ALPHA-EXECUTION-CONTRACT@1.0` is indexed as an authoritative EMM
entity with a source digest. `ConvergenceRuntime.execution_contract()` checks
its identity, revision, classification, baseline, lifecycle, and
`OperationalGatePlan` resolution type.

For a resolved authority flow, context assembly requires exactly one
authoritative EMM `OperationalGatePlan` matching the Implementation WOP and
revision. It validates baseline, binding, active lifecycle, source digest, and
handler payload. The runtime then invokes the handler context service, which
validates all gate actions and context digest. It cannot derive a plan from a
WOP or runtime assumption.

Focused tests demonstrate both outcomes: no EMM plan raises a deterministic
error; a correctly indexed, active test plan produces a handler-valid context.
