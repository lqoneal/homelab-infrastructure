# Runtime Registration Validation Report

Repository validation returned:

```text
status: PASS
consumer_count: 17
production_count: 15
compatibility_count: 2
runtime_layer_count: 3
repeated_analysis_equal: true
```

The validator proves:

1. discovered consumers and registered consumers are equal;
2. only canonical layer identifiers 1, 2, and 3 are accepted;
3. actual imports exactly match each consumer's registered interfaces;
4. consumer identifiers are unique;
5. stale or missing implementation entries are rejected;
6. registry entries are deterministically ordered;
7. missing or invalid registration input fails closed.

The existing dependency validator also returned `PASS`, proving the registry
work did not alter the three-layer model or its downward dependency contract.
