# Mission and Transaction Discoverability

`zeus mission status|show|authority|contract|snapshot ZDCL-02` now resolves the registered Development transaction through Stage 1 instead of returning `BETA_MISSION_NOT_FOUND`. Views expose transaction, registration, package, state, receipt IDs, provider/agent when present, authority snapshot, blockers, and next action. Read-only views do not mutate runtime state.
