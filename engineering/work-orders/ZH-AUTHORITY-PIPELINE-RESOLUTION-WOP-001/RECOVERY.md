# Interruption Recovery

Run package verification, repository identity verification, and a comparison
of current HEAD/status against `STATE.json`. Verify every completed operation
from its evidence rather than repeating it. Resume at `next_operation`.

If HEAD moved or the pre-existing working tree changed outside recorded WOP
effects, stop and record a conflict. If a temporary-file write failed, retain
the last validated atomic target and remove/quarantine only the bounded
temporary file. If an append-only effect occurred, never delete it; record the
irreversible boundary and reconcile forward. If REAC validity or authority is
lost, clear no evidence and stop fail-closed.

