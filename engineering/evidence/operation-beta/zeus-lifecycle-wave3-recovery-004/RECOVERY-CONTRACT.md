# GAP-008 Recovery Contract

Contract: `ZEUS-CANONICAL-RECOVERY/1`

The immutable envelope types are:

* `RECOVERY_CHECKPOINT`: mission, WOP, execution, provider, session,
  repository identity/baseline, source digest, lifecycle position, evidence
  position, and completed/current work units.
* `RECOVERY_INTERRUPTION_RECEIPT`: one checkpoint, deterministic cause,
  observed provider/session process state, heartbeat result, and
  repository-mutation/lifecycle-receipt ordering.
* `RECOVERY_RESUME_REQUEST`: the existing execution identity, completed work
  to skip, and duplicate-execution prevention.

Records use create-only immutable writes and deterministic UUIDv5 identities.
Exact replay returns the original record with `IDEMPOTENT`; divergent replay
fails with `RECOVERY_REPLAY_DIVERGED`. The structural schema is
`engineering/oversight/recovery-contract.schema.yaml`; runtime verification is
in `scripts/lib/emp/canonical_recovery.py`.

Recovery cannot advance canonical lifecycle state. Before execution the native
view reports `NOT_STARTED`; process/session/heartbeat liveness is observational.
Missing, stale, forged, digest-invalid, identity-conflicting, or multiple
checkpoints fail closed.
