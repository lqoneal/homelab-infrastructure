# Authority Model Before and After

## Before

The runtime and documents treated the normal chain as an Authority Record or
manual-governance delegation, then EMM/Implementation WOP resolution, with
separate approval and execution authority checks. The direct symptoms were
`AUTHORITY_RECORD_REQUIRED`, generic `OPERATOR_APPROVAL_REQUIRED`, separate
corrective/implementation/execution language, and managed writable-session
provisioning blocked behind the redundant authority model.

## After

```text
operator-submitted WOP
  -> WOP schema, identity, integrity, and scope validation
  -> admission / lifecycle resolution where applicable
  -> mission, repository, baseline, dependency, provider, and session binding
  -> writable managed execution context
  -> execute only the submitted WOP scope
```

The WOP is the authority boundary. A second generic corrective,
implementation, execution, secondary-work, or redundant operator-approval
grant is not required. An approval remains required when and only when the
submitted WOP declares that approval gate. An Authority Record or other
record remains valid when a separate domain contract uses it as an identity or
safety prerequisite, but it is not a generic operator authorization.
