# Authority Snapshot Redispatch Contract

Redispatch requires a complete immutable snapshot bound to transaction, WOP, package, repository baseline, protected baselines, effect profile, governance authority, and provider qualification. Recovery clears the stale binding; the next Zeus resume creates a fresh snapshot. Any missing or conflicting authority fails as `AUTHORITY_CHAIN_INTEGRITY_FAILURE` before dispatch.
