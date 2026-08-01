# Canonical WOP Schema Decision

Published Beta WOPs use the semantic mission-bound reference as canonical
identity. UUID WOP references remain backward-compatible legacy identities for
standalone historical packages. No silent conversion or replacement occurs.

`approval.authority`, `approval.reference`, and lifecycle authorization are
required and resolve from the mission contract or authoritative approval
record. `approval.date` is optional because the ZDCL-01 authority does not
publish one. If supplied, it must be ISO-8601. Missing optional data is omitted,
never serialized as `None` or a placeholder.

Package qualification, submission, admission, and execution now consume the
same canonical submission validation rules. Execution may recheck freshness,
digest, repository, baseline, and approval state, but may not introduce hidden
required fields.
