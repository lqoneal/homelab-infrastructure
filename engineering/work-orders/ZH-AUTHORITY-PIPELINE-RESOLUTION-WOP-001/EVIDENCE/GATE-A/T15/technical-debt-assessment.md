# T15 Technical Debt Assessment

Date: 2026-07-29

Disposition: ACCEPTED WITH BOUNDED REDUCTION

The principal duplication is registry loading, ordered-string validation,
digest comparison, and temporary-fixture construction across the eight
accepted validators. Refactoring those internals now would enlarge regression
risk and obscure proof that accepted validator behavior is unchanged.

T15 therefore centralizes orchestration, registry fingerprinting,
controlled-document checks, canonical chain reporting, and qualification
fingerprinting in one internal consolidation validator. Per-layer semantic
logic remains with its accepted owner. A later behavior-preserving cleanup may
extract JSON loading and ordering helpers after snapshotting each validator's
errors and result schema. Documentation duplication is bounded by keeping the
normative baseline in SPEC-0012 and discovery metadata in DOC-0001.
