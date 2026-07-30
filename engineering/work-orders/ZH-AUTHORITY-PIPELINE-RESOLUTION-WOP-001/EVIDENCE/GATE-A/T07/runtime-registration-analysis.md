# Runtime Registration Analysis

AST-based deterministic discovery scans Python modules under `scripts/lib` and
recognizes only the four registered runtime-facing interfaces:

- canonical: `progressive_gate`, `progressive_lifecycle`;
- compatibility: `progressive_oa`, `oa02_lifecycle`.

Canonical runtime-internal Layer 3 to Layer 2/1 consumption is governed by the
dependency contract and excluded from the consumer registry. Tests and
validators are qualification infrastructure and are also excluded.

Discovery found 17 external runtime consumers:

- 15 production consumers;
- 2 compatibility consumers (`progressive_oa` and `oa02_lifecycle`).

Production consumers currently use registered compatibility interfaces.
Compatibility consumers use canonical runtime interfaces. For every entry the
validator requires actual imports to equal declared interfaces and requires
the declared layers to equal the layers exposed by those interfaces. This
detects unregistered consumption, bypass, stale registration, and repository
drift without inspecting runtime behavior or changing call paths.

Two consecutive analyses returned structurally equal results.
