# Mission Projection Reconciliation Report

Status: QUALIFIED

The Beta mission resolver now produces one read-only projection containing
`current_admission`, `current_execution`, `historical_admissions`, and
`historical_executions`. `ZDCL-01` resolves to the fresh admission
`MISSION-ADMISSION-e8a3b130-f4b6-50d0-9bf4-21b1a2c5cefd`, no current execution,
and one cancelled historical execution.

The cancelled execution is no longer selected by recency and is exposed only
by the explicit mission history view.
