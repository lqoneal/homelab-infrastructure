# Hydration Persistence Trace

`hydrate=True` previously derived projections and used a two-file writer without a transaction lock, inventory, reconciliation receipt, native-session classification, or rollback. The shared reconciler now runs before direct loading for `start`, `status`, `session`, and `resume`.
