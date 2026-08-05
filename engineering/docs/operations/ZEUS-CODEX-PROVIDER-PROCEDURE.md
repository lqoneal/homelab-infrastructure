# Zeus Codex Provider Procedure

The normal governed workflow is `zeus submit <authorized-wop>`. Provider
inspection uses `zeus provider list`, `zeus provider capabilities`, and
`zeus provider status <execution>`. Execution inspection and control use
`zeus execution show|session|stop|resume <execution>`.

Zeus creates the context envelope and invokes `engctl codex --context-file`
internally. Direct `engctl codex` use is low-level only and is not evidence of
governed mission execution. A missing qualified provider, malformed envelope,
ambiguous ownership, unavailable process identity, or publication-boundary
request stops fail closed.
