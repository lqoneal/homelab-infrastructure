# Dispatch and Execution-Start Assessment

The documented contract distinguishes admission, dispatch, provider launch, session materialization, and execution start. `DISPATCHED` is intended to be receipt-backed and bound to admission/execution projections; execution start requires an actual execution session.

P2 submission was independently verified only through `ADMISSION_REQUESTED`. P3/P4 and provider execution boundaries have component tests but no fresh end-to-end target-mission proof. Therefore dispatch/execution-start convergence is `UNPROVEN`, not treated as implemented merely because modules exist.

