# Identity Precedence

1. Stage 1 transaction `instance_id`.
2. Dispatch receipt `instance_id`, as an equality assertion.
3. Provider-selection transaction binding, as an equality assertion.
4. Valid derived runtime execution projection.
5. Native-session execution binding.
6. Operator-supplied execution argument, subject to exact equality.

Lower-precedence projections cannot override immutable Stage 1 identity.
