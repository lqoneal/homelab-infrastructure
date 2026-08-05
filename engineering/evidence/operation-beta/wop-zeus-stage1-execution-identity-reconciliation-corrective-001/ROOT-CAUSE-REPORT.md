# Root Cause Report

The first failing point was transaction selection in the shared Stage 1/runtime boundary. When only an execution argument was supplied, resolution selected the first active receipt-backed transaction (`530c…`) rather than matching the requested execution to Stage 1 `instance_id` (`5afc…`). The subsequent comparison therefore produced `UNVERIFIABLE_RECORD: requested execution conflicts with Stage 1 receipt` for a valid request.

The corrective makes `instance_id` canonical, validates dispatch/provider bindings against it, and repairs only derived projections with the same transaction binding.
