# Roadmap Persistence Contract

`roadmap.yaml` is the canonical program index. It fixes roadmap identity,
version, program, repository/preservation bindings, state and manifest paths,
and ordered C00-C20 gate/result locators. Each indexed `GATE.yaml` is the sole
full execution definition for that gate; `ROADMAP.md` is only a compact review
projection.

Gate definitions are repository-relative, ordered, schema-validated, unique,
dependency-resolved, and immutable historical inputs once completed. The
preservation reference is `REFERENCE_ONLY`. Roadmap approval or next-gate
selection never grants implementation, publication, provider, or EOS authority.

The EMM binding manifest binds every definition, Project State, and completed
result. Any unbound required source or digest drift fails closed.
