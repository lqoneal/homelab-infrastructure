# Submission to Execution Schema Map

The authoritative source is `scripts/lib/emp/wop_schema.py`, consumed by source extraction, `wop lint`, `wop validate`, packaging, Stage 1 resolution, and `VALIDATE_WOP` admission validation.

| Contract area | Source field | Package projection | Execution field |
|---|---|---|---|
| Approval | `approval_authorized_lifecycle_state` | `approval.authorized_lifecycle_state` | `approval.authorized_lifecycle_state` |
| References | `authoritative_references` | `authoritative_references` | `authoritative_references` |
| Runtime authority | `execution_package_authority_node_id` | `execution_package_references.authority_node_id` | same |
| Runtime decision | `execution_package_authorization_decision_record` | `execution_package_references.authorization_decision_record` | same |
| Sections | `sections_*` | `sections.*` | `sections.*` |

The first loss was the legacy projection in `wop_packaging.package`, which serialized only mission scalars. The corrective projects the complete contract and uses the same admission validator at execution.
