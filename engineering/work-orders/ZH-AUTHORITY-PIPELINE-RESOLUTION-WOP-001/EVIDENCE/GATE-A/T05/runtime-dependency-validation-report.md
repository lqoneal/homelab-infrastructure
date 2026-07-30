# T05 Runtime Dependency Validation Report

Command:

```text
python3 -m unittest scripts/tests/test-progressive-runtime-dependencies.py
```

Result: 7 tests passed.

The suite proves the repository graph and negatively injects each prohibited
condition into an isolated fixture:

1. runtime compatibility leakage fails closed;
2. an upward Layer 1/2 to Layer 3 edge fails closed;
3. a runtime cycle fails closed;
4. a foundational runtime/compatibility back-edge fails closed;
5. duplicate projection authority fails closed; and
6. missing validation inputs fail closed.

The positive graph result is deterministic and contains only the permitted
Layer 3 to Layer 1/2 edge. The validator parses repository source rather than
importing runtime modules, so validation cannot mutate runtime state.

