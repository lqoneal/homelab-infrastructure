# Zeus Autonomous Execution State Machine

The lifecycle states are source discovery and validation, package creation and verification, registration, authority resolution, admission persistence and verification, provider selection, dispatch, execution and session persistence, monitoring, diagnosis, correction, reconciliation, resume, qualification, publication preparation and approval, publication, EOS synchronization, canonical reconciliation, mission activation, closeout, and archive.

State is derived from immutable receipts first. A transition is durable only after its derived projection and lifecycle snapshot are atomically written and reloaded. Publication and destructive actions remain approval-gated where policy requires.

The state machine permits repeated gate and transaction transitions inside one
authorized execution envelope. After each completed transition, successor
authority is re-evaluated from the authoritative projection. The machine stops
only at a policy-required decision, unresolved or failed authority or
qualification, an explicit authority ceiling, a protected publication/EOS
boundary, or terminal state. Resume starts at the first incomplete transition
and never reruns a completed gate or duplicates a completed effect.
