# Authority Chain Verification

The immutable authority snapshot is digest-checked and bound to WOP, package, repository, protected baselines, and approval state. A dispatched record without a valid snapshot terminates with `AUTHORITY_CHAIN_INTEGRITY_FAILURE`. Historical pre-dispatch receipt bindings remain preserved during invalid-dispatch reconciliation.
