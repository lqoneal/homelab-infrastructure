# Idempotency Verification

The canonical recovery test proves schema migration followed by repeated `resume` without new receipts. The duplicate-dispatch test proves a verified dispatch does not invoke the executor again. Protected baseline tags and transaction identity remain unchanged.
