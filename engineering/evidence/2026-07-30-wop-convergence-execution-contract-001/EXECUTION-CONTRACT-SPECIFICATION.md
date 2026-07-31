# Execution Contract Specification

| Item | Definition |
| --- | --- |
| Contract identity | `OPERATIONAL-ALPHA-EXECUTION-CONTRACT@1.0` |
| Authoritative source | `engineering/execution/operational-alpha-execution-contract.yaml` |
| Index | `OPERATIONAL-ALPHA-EMM@1.1`, entity `OperationalExecutionContract` |
| Gate-plan identity | `OperationalGatePlan/<Implementation WOP id>/<Implementation WOP revision>` |
| Gate-plan source | Exact EMM entity source; one YAML record per plan revision |
| Required plan binding | Baseline, WOP id/revision, active lifecycle, source digest, and handler-compatible `gate_plan` payload |
| Derived consumer | `OperationalExecutionContextService` through `ConvergenceRuntime.operational_execution_context` |
| Absence result | `PRECONDITION_FAILED` before gate-handler invocation |
| Invalid or mismatched result | `INTEGRITY_FAILURE` before gate-handler invocation |

The handler payload must be a mapping with `gates`. Each gate has nonempty actions and declared dependencies. Every action has a unique identifier, supported action type, safe relative artifact path, and the required content digest. These are validation requirements, not pre-authored OA-01 implementation content.

The contract is represented in SPEC-0014@1.1 and the execution interface. Runtime assembly is read-only with respect to all authoritative inputs.
