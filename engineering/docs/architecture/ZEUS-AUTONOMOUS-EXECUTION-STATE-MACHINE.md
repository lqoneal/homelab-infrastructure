# Zeus Autonomous Execution State Machine

The lifecycle states are source discovery and validation, package creation and verification, registration, authority resolution, admission persistence and verification, provider selection, dispatch, execution and session persistence, monitoring, diagnosis, correction, reconciliation, resume, qualification, publication preparation and approval, publication, EOS synchronization, canonical reconciliation, mission activation, closeout, and archive.

State is derived from immutable receipts first. A transition is durable only after its derived projection and lifecycle snapshot are atomically written and reloaded. Publication and destructive actions remain approval-gated where policy requires.
