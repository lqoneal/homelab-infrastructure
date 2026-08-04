# Hydration or Resolver Decision

Decision: shared canonical resolver with an in-memory projection. Stage 1
owns durable truth; runtime records remain compatibility projections. Durable
hydration is limited to the existing runtime writer and only when an execution
identity is already receipt-backed. This preserves the operator lifecycle and
prevents a missing projection from inventing authority.
