# Result and Evidence Contract

Every gate has fixed `RESULT.yaml` and `evidence/` locations. Pending gates do
not receive placeholder results. A gate is complete only when `STATE.yaml`
lists it complete, its definition has the same terminal status, a schema-valid
result records that exact status, its evidence list is non-empty, and every
referenced evidence path exists and passes applicable integrity bindings.

Results record starting state, findings, issues, authority conflicts,
redundancies, simplification candidates, artifacts, evidence, criterion-level
results, blockers, disposition, and next action. Detailed artifacts remain in
the gate evidence tree; the result is the durable executive record. A result
file alone never advances state.
