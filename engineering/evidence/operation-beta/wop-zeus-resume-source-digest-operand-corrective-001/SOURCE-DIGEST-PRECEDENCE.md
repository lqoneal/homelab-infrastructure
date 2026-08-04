# Source Digest Precedence

1. `receipts.validation.source_digest`
2. Stage 1 transaction `source_digest`
3. Stage 1-specific admission/projection fields such as
   `stage1_source_digest` and `source_binding.source_digest`
4. Generic `source_digest`, only when present and equal

Receipt and transaction values are cross-checked when both exist. Generic
absence is permitted only because the canonical Stage 1 source binding is
present; conflicting present values fail closed.
