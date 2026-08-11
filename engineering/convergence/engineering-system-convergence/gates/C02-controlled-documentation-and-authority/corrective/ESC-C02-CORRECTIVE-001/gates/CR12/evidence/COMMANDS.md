# CR12 Command Record

Corrective: ESC-C02-CORRECTIVE-001
Item: CR12 — Define Interruption and Replay
Captured: 2026-08-10T08:45:03Z

CR12 verified the frozen execution position, protected history, target-artifact
non-conflict, and CR07-CR11 design dependencies before creating the required
design artifact.

Zeus-native roadmap capability was checked before repository fallback.

CR12 defined deterministic interruption classification, exact replay identity,
idempotent replay, fail-closed conflicting replay, explicit mutation authority,
and read-only resume/status behavior.

No controller or engctl implementation was changed.

CR13 was not executed.
