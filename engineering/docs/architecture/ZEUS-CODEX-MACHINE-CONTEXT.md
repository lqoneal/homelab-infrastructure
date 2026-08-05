# Zeus Codex Machine Context Contract

Schema version `1` is an object with `transaction_id`, `wop_id`, `mission_id`,
`execution_mode`, `effect_profile`, `governance_authority`, `repository`,
`branch`, `protected_baselines`, `mission_contract`, and `context_digest`.

The digest is SHA-256 over the canonical JSON object excluding no fields. A
provider must consume the envelope as data and must not substitute a prose
instruction or infer missing authority. Repository, branch, effect profile,
and protected-baseline changes fail closed.
