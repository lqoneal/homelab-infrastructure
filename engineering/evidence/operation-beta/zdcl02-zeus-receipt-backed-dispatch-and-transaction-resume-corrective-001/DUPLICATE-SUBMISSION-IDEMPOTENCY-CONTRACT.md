# Duplicate Submission and Resume Contract

`submit_development` derives a deterministic instance ID from mission, WOP, and package digest. A repeated identical submission returns that record with `idempotent_replay`; changed content is rejected. `zeus resume [IDENTIFIER]` resolves the existing record and advances only the next receipt-backed transition.
