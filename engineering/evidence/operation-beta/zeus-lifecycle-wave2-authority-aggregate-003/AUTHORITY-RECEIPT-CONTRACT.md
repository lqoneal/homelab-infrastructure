# Canonical Authority Receipt Contract

`ZEUS-CANONICAL-AUTHORITY-RECEIPT/1` is a read-only adapter over existing
receipt families. It recognizes:

- `CANONICAL`: P2 authority envelope with operator-submitted-WOP authority,
  explicit approval state, and `generic_second_approval_required=false`;
- `STAGE1_LEGACY`: digest-verified Stage 1 authority snapshot;
- `AUTONOMOUS_LEGACY`: digest-verified autonomous authority snapshot;
- explicit `*_UNVERIFIED` legacy compatibility classes when historical input
  contains only an opaque digest or legacy authorization receipt.

Canonical evidence is never manufactured. Missing canonical authority,
identity mismatch, digest mismatch, duplicate canonical candidates, and
semantic contradiction fail closed. Legacy evidence remains immutable and is
classified rather than silently treated as canonical. Autonomous lifecycle
and dispatch validation now pass through this boundary while preserving their
existing compatibility behavior.

The current mission resolves from the P2 receipt as `CANONICAL`; no legacy
authority record is allowed to override it.
