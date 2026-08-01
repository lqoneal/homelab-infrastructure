# Submission Architecture Decision

Use one high-level operator entry point:

```text
zeus mission submit <MISSION_ID>
```

It is a resolver over the existing Stage 1 submission authority. When a
qualified package exists, it is reused and submitted through `Stage1Runtime`.
When no package exists, no package is fabricated and no placeholder approval
is inferred; the command returns a fail-closed missing-authority result.

The compatibility entry point remains:

```text
zeus submit <WOP_PACKAGE>
```

Admission and execution remain explicit:

```text
zeus admit-mission start ...
zeus execute-mission start --admission-id <ADMISSION_ID>
```

This preserves the existing authority boundaries and makes package resolution
the only newly simplified step.
