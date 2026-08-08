# Controlled-Document Reconciliation

Current P3 semantics were added to the mission projection specification and
WOP submission procedure. They define:

- append-only historical artifact preservation;
- mission/WOP/submission-scoped current cardinality;
- exactly one current canonical set;
- zero-current and ambiguous-current fail-closed behavior;
- deterministic replay identity;
- historical and legacy evidence exclusion from current authority.

The submitted-WOP authority model, machine-readable WOP guidance, explicit
in-WOP approval enforcement, and canonical receipt-backed lifecycle ownership
were preserved. No historical evidence or completed WOP was rewritten.

Controlled-document conformance and semantic checks passed with zero current
failures. No schema or validator suppression was introduced.
