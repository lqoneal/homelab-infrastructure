# Authority Snapshot Reconciliation

Hydration does not fabricate an authority snapshot. A valid dispatch still requires one. An invalid historical dispatch without a snapshot is classified as reconcilable historical evidence; recovery preserves it, clears the active binding through the existing rollback path, and requires a fresh authoritative snapshot before redispatch.
