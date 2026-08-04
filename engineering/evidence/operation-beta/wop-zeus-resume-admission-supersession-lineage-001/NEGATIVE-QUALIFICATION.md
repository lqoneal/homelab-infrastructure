# Negative Qualification

PASS for disposable rejection of:

- unrelated requested admission;
- missing successor / broken `superseded_by` link;
- source digest mismatch;
- circular or multiple successor lineage (covered by the shared supersession contract);
- stale, dirty, or unpublished execution environment (strict resume mode).

All failures occur before runtime state mutation.
