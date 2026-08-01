# OA-20 Dependency Analysis

The previous circularity was caused by MKM assigning the outcome capability as the prerequisite. The corrected semantics are:

* OA-19 produces CAP-018.
* OA-20 consumes operational CAP-018 and produces CAP-019.
* OA-21 consumes CAP-019 and produces CAP-020.

Readiness therefore requires OA-19 completion, repository/EOS convergence, and CAP-018 operational status. CAP-019 remains unavailable until OA-20 qualification. This preserves fail-closed readiness without blocking the mission on its own outcome.

