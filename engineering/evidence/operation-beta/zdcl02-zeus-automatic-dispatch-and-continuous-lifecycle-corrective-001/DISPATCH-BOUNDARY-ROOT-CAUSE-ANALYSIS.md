# Dispatch Boundary Root Cause Analysis

The CLI constructed `Stage1Runtime` without an execution executor, so the
existing lifecycle intentionally stopped after admission. The corrective
injects the canonical automatic resolver while retaining the safe blocked
result when no qualified agent exists.
