# Authoritative Runtime Source Map

The authoritative Development source is the receipt-backed Stage 1 record at
`.zeus/runtime/stage1/missions/<transaction>.json`. Its admission, authority,
dispatch, provider, and downstream receipt identities own runtime authority.
`mission-admissions` and `mission-executions` are derived projections.

The corrective adds `stage1_execution_resolution.py`, which validates the
Stage 1 digest and receipt chain, derives a read-only admission projection,
and reuses any existing execution projection. It creates no transaction,
receipt, provider selection, or authority snapshot.
