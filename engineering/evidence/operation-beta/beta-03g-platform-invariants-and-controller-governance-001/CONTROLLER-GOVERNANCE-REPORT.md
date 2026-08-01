# Controller Governance Report

Controllers are governed as read-only projections. The Beta mission projection separates current admission, current execution, and historical records. Human and JSON forms use the same resolved object. Unknown, conflicting, stale, or multiple-current state fails closed.

The existing Beta controller boundary is the canonical resolver boundary; no second queue, lifecycle, admission, or execution authority was introduced.
