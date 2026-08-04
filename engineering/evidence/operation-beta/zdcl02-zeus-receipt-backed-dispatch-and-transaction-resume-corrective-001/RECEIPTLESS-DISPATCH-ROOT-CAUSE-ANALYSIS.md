# Receiptless Dispatch Root Cause

The prior dispatcher emitted a minimal agent assignment and the lifecycle controller treated its presence as sufficient for `DISPATCHED`. The corrective now validates a complete dispatch receipt and freezes authority before provider selection. A receiptless or incomplete dispatch is classified as `RECEIPT_INTEGRITY_FAILURE` and is recoverable to `AWAITING_EXECUTION_DISPATCH` without fabricating evidence.
