# Routing Analysis

```text
zeus submit SOURCE
  -> resolve source
  -> classify current authored / promotable Development / explicit legacy
  -> verify or derive Phase-1 provenance
  -> common submit_wop_boundary()
  -> one submission receipt + one admission request
  -> ADMISSION_REQUESTED
```

Current authored sources use existing provenance verification. Promotable Markdown/TXT sources use `wop_canonicalization.canonicalize()`, which emits the adjacent immutable sidecar without changing source bytes. Existing Stage 1 package directories remain on the legacy compatibility path. `--repository` is validated repository context and no longer selects legacy routing.

