# Deterministic WOP Convergence-Binding Generation Recommendation

## Recommendation

Generate convergence bindings only from validated canonical records. A
binding generator must never infer a WOP, substitute an admitted package, or
repair an authority conflict.

## Canonical inputs

- Mission Knowledge Model mission identity, objective, lifecycle, and
  capability prerequisites/outcome.
- Immutable WOP package identity, revision, digest, scope, and admission.
- Gate definition and controlled procedure references.
- Repository identity, exact published baseline, branch, and working-tree
  qualification.
- EMM authority binding and digest state.
- Execution identity and qualified-agent record.

## Binding contract

The generated record should bind mission ID, WOP ID and digest, gate ID,
repository identity, published baseline, execution identity, authority source,
capability prerequisite and outcome, qualified agent, lifecycle state, source
digests, generator identity/version, and generation timestamp.

## Validation rules

Reject missing records, stale digests, mismatched repository or baseline,
unadmitted or superseded WOPs, invalid capability state, ambiguous agents,
cycles, and any source disagreement. Identical canonical inputs and generator
version must produce byte-stable output. Publication must occur only after
independent validation and controlled admission.

## Ownership and integration

The Mission Knowledge Model owns mission semantics; the WOP admission system
owns package admission; EOS owns repository and engineering state; EMM owns
binding/drift detection; the Capability Registry owns capability state; ZDCL
consumes the binding for session control; and CAGF may later generate derived
binding inputs and projections. None of these consumers may originate
authority.

## Publication sequence

Resolve canonical inputs, validate and digest them, generate the binding,
independently validate it, publish the immutable evidence, admit the WOP, then
run the OA-21 verifier. Any failure stops before execution or lifecycle
mutation.

## Status

This is a design recommendation only. No binding-generation framework was
implemented by this reconciliation.
