# Provider-Evaluation Verification

## Canonical path discovered

The supported provider-selection controller is the P5-G1 path:

```text
scripts/zeus provider candidates <MISSION_ID> --json
scripts/zeus provider select <MISSION_ID>
scripts/zeus provider verify <MISSION_ID> --json
```

The shared implementation is `scripts/lib/emp/provider_selection.py`.
The execution-agent registry contains one active, qualified, repository-scoped
candidate: `zeus-local-loneal-01`. No provider identity was selected or
persisted during this handoff.

## Fail-closed result

The user-facing route rejects the lifecycle mission before reaching the shared
controller:

```text
scripts/zeus provider select ZEUS-EXECUTION-LIFECYCLE-COMPLETION-01 --json
RC=78
MISSION_NOT_CANONICAL: provider selection requires a canonical Beta mission
```

The guard is an obsolete hardcoded `MISSION-BETA-*` selector in `scripts/zeus`.
It conflicts with the live receipt-backed canonical mission identity
`ZEUS-EXECUTION-LIFECYCLE-COMPLETION-01`.

The shared verifier also cannot safely proceed. It delegates to the older
`mission_verification_controller`, which reports:

```text
provider_session: FAIL
DISPATCH_CROSS_MISSION: published dispatch does not belong to the requested mission
```

This is a second integration defect in the provider boundary: preserved
cross-mission historical dispatch/session projection is treated as a current
provider-session failure instead of being excluded by canonical mission
scoping. The canonical mission-native resolver itself remains `PASS`.

## Boundary decision

Provider evaluation was not attempted. No provider-selection artifact was
created. No dispatch, provider session, invocation, execution session,
execution, or mission-work transition was attempted. The handoff stopped at
the first new fail-closed lifecycle defect as required.

