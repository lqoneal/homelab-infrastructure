# Runtime Divergence Report

| ID | Severity | Divergence | Corrective recommendation |
| --- | --- | --- | --- |
| CERT-001 | Blocking | Operational admission resolves legacy authority bundle | Migrate admission resolution to ConvergenceRuntime and bind receipt to admission state |
| CERT-002 | Blocking | Operational WOP generation resolves legacy authority bundle | Generate WOP only from a resolved SPEC-0014 receipt |
| CERT-003 | Blocking | Convergence envelope is not the gate-handler operational context | Define/adapt the convergence execution context and qualify handler consumption |
