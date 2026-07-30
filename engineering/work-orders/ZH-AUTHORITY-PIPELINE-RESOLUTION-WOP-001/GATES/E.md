# Gate E — Authority Integration

Implement indexed discovery, ARS REAC creation/validation, REAC-consuming PMA,
orchestrating EWI, one Initiation Decision Record, shadow-only compatibility,
and read-only diagnostics. Exit with exactly one production allow path.
Rollback disables the new path and leaves initiation blocked; it may not
reactivate a parallel allow path.

