# Blocker Lifecycle

The governed states are `DISCOVERED`, `VERIFIED`, `ACTIVE`, `RESOLVING`, `REVALIDATING`, `RESOLVED`, and `RETIRED`. Evidence-present blockers project through `VERIFIED` to `ACTIVE`; missing evidence remains `DISCOVERED` and cannot block publication. Re-evaluation is deterministic on every qualification decision and lifecycle transition.

The current qualification blockers are verified and active. They remain publication-blocking because their authoritative evidence still reports unresolved mandatory qualification conditions.
