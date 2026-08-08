# Recovery-Test Reconciliation

The failing test was first observed as `UNCOMMITTED_WORKING_TREE_DRIFT` because
`Stage1Runtime._resolve_baseline_transition()` correctly inspected the real
repository and found preserved dirty candidate work. That environmental error
preceded the receiptless-dispatch semantic check.

The test now creates a clean `git clone --no-local` fixture in a temporary
directory and runs the same transaction against the isolated repository. The
actual intended behavior is proven:

1. A `DISPATCHED` record with an invalid/missing authority binding is not
   treated as authoritative dispatch.
2. Historical invalid dispatch evidence is preserved.
3. The invalid dispatch receipt is removed from the current chain.
4. State returns to `AWAITING_EXECUTION_DISPATCH` with `pending_phase=DISPATCHED`.
5. A fresh authority snapshot is required before redispatch.
6. No execution identity or mission work is created.

`test_receiptless_dispatched_state_rolls_back_on_resume` passes in the clean
fixture. The real dirty checkout remains untouched and is not classified as a
GAP-008 semantic failure.
