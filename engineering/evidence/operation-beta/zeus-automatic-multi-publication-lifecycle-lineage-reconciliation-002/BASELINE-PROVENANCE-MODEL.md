# Baseline Provenance Model

`RECEIPT_PROVENANCE_BASELINE` is immutable transition provenance. It is not a
freeze on the repository and is never rewritten.

`CURRENT_PUBLISHED_BASELINE` is resolved live from `HEAD`, `origin/main`, EOS,
and repository identity. Validity requires parity among those projections and
Git ancestry from immutable provenance to the live baseline.

The model is therefore:

```text
immutable receipt provenance
  -> verified publication ancestry (zero or more descendants)
  -> synchronized live HEAD/origin/EOS baseline
```

Reconciliation receipts record historical transition evidence. They are
optional for routine descendant publication and cannot replace live current
authority. Identity mismatch, rewritten/non-descendant history, parity
conflict, forged evidence, and ambiguity fail closed.
