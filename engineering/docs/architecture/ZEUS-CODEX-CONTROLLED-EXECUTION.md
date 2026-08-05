# Zeus-Controlled Codex Execution

ZDCL-02 uses `zeus submit <authorized-wop>` as the governed entry point. Zeus
resolves authority and constructs a versioned machine context envelope before
calling the low-level `engctl codex` provider service. The envelope is passed
by `ZEUS_CODEX_CONTEXT_FILE` and `ZEUS_CODEX_CONTEXT_JSON`; its digest binds
transaction, WOP, mission, mode, effect profile, repository, branch, and
protected baselines.

`engctl codex` remains a platform component, not a governed operator workflow.
It accepts the Zeus envelope, rejects invalid schema or digest context, and
does not create authority. The wrapper owns process-group supervision,
idempotent session identity, stop, interruption recovery, receipts, and the
EENS event contract. Publication and protected-branch changes remain gated by
Zeus authority.
