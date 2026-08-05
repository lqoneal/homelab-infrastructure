# Atomic Execution Rebinding

Admission supersession and execution rebinding use the existing atomic JSON update mechanism. Existing valid projections are reused; conflicting or unsafe partial projections fail closed. Hydration accepts an already-valid reconciled admission only after state-digest and identity validation before installing its missing execution projection.

