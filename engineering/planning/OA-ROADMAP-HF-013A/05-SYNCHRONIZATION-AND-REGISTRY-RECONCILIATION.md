# Synchronization and Registry Reconciliation

## Directional reconciliation

| Source | Derived destination | Trigger | Owner | Verification | Result |
| --- | --- | --- | --- | --- | --- |
| baseline registry | DOC-0001 and controlled cross references | successful publication validation | repository owner | baseline identifier and paths resolve | completed in repository |
| HF source package | baseline registry | publication finalization | architecture owner | all HF-005–HF-012 packages listed | completed in repository |
| repository baseline | EOS projection | separately authorized post-publication synchronization | EOS owner | exact baseline locator comparison | `SYNCHRONIZATION_REQUIRED`; no runtime write performed |
| repository baseline | project/runtime management views | separately authorized projection | respective owner | authoritative locator reconciliation | planning handoff only |

Repository records are authoritative. Derived state shall never overwrite the
baseline registry or controlled documents. The final validation report records
the repository result and the deferred runtime synchronization handoff.

## Drift and recovery

A derived consumer that does not resolve the published baseline identifier is
in `SYNCHRONIZATION_REQUIRED`, not authoritative-source failure. The owner
shall stop dependent implementation activity, reconcile from the repository
locator, retain evidence, and re-run its exact read-only verification. No
automatic retry may create or alter authoritative facts.
