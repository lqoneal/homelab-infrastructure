# Controlled Document Reconciliation

The canonical publication procedure and Zeus user guide now define
`PREPUBLICATION_VERIFIED` as a persisted receipt-backed milestone, identify
`verify-pre` and its compatibility spelling, and state the ordered reload
boundary before staging authority.

The mission projection specification now forbids read models from outrunning
durable publication state. Development Mode records the same fail-closed and
idempotent behavior. These changes preserve the existing publication cohort
and candidate authority model: those projections can block a transition but
cannot grant or advance publication state.

Historical completion evidence was inspected but not rewritten.

