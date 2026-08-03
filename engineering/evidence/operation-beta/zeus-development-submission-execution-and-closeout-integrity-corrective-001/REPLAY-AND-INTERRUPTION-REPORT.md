# Replay and Interruption Report

Repeated submission of an unchanged Development package resolves the same
instance and package digest and returns `idempotent_replay: true`. The
receipt map is not duplicated.

The prior `interrupt_after` compatibility option cannot advance an unsupported
phase. With no executor, both initial submission and replay remain at
`AWAITING_EXECUTION_DISPATCH`; resume retains the same lifecycle identity,
receipt set, and exact next action.

Source changes after an accepted pending submission require explicit
supersession and are rejected before a second lifecycle is created.
