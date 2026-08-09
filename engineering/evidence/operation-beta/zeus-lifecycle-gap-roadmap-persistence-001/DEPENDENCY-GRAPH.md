# Dependency Graph

```text
P2 submission identity and receipts
        |
        +--> GAP-001 canonical mission discovery
        |
        +--> GAP-006 canonical next-action resolver
                    |
                    +--> GAP-002 integrated receipt-backed transition resolver
                                  |
                 +----------------+----------------+
                 |                                 |
          GAP-004 authority adapter          GAP-007 native aggregate view
                 |
              GAP-008 interruption/checkpoint/resume
                 |
              GAP-009 evidence and independent qualification
                 |
          +------+----------------+
          |                       |
      GAP-011 candidate       GAP-012 sync drift
          +------+----------------+
                 |
              GAP-003 publication/EOS receipt bridge
                 |
              GAP-005 canonical closeout
                 |
              GAP-010 legacy-only fallback cleanup
                 |
          final real filesystem/Git/EOS/provider E2E proof
```

## Dependency decisions

- `GAP-001` and `GAP-006` are the first independent unit because both are
  read-only resolution contracts over existing P2 identity and do not require
  admission or provider mutation.
- `GAP-002` must follow them: a transition resolver cannot safely own the
  chain until discovery and next-action authority are singular.
- `GAP-004`, `GAP-007`, and `GAP-008` depend on a stable canonical chain and
  identity-preserving provider/session contracts.
- `GAP-009` depends on real mission-work and recovery receipts; qualification
  must not certify a projection-only execution.
- `GAP-011` and `GAP-012` are publication prerequisites/supporting controls;
  `GAP-003` cannot be proven until exact candidate isolation and sync drift
  semantics are deterministic.
- `GAP-005` is last among substantive runtime corrections because closeout
  must consume the converged publication, sync, evidence, and execution
  chain.
- `GAP-010` is compatibility-only and may be scheduled with Wave 1 only if it
  remains explicitly legacy-only; it is not a prerequisite for execution.
- Final E2E proof is a qualification dependency on all implementation waves,
  not a substitute for any focused gap correction.

No dependency grants authority or changes the parent mission state.
