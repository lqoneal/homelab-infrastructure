# Authority-Operand Capture

Incorrect operand: `value.get("authority_snapshot_digest")` in `resolve_for_resume`.

Expected: `bd269d39d0ceddcab1d08b74a6d2d5ec0c28a20b0f82bc3444dc22c6e27d5b3d`.
Observed: `None`.

The corrective resolves the expected operand from receipt-backed Stage 1 evidence and treats a missing generic projection field as non-authoritative.

