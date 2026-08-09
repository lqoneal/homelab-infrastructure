# Root-Cause Analysis

The existing provider-selection artifact was created at published baseline
`107a915e5e837699d723623cd9abe41da7642506`. After the legitimate descendant
publication to `e7e48ab6b523d94e73d40fb4311f86bc7118b0b1`, the canonical
resolver still required the artifact's recorded `current_published_baseline`
to equal the live baseline. That comparison rejected valid immutable
transition evidence and removed provider selection from the canonical read
model.

Call path:

`zeus mission <surface>` → `mission_verification_controller.verify()` →
`canonical_lifecycle_resolver.resolve()` → provider artifact discovery and
`_verify_set()` → strict `provider_anchor.current_published_baseline`
comparison.

The correction keeps mission/WOP/submission/admission/bootstrap/repository and
provenance scoping strict, but treats the provider artifact's recorded
published baseline as transition provenance. It validates that baseline and
the immutable provenance baseline are reachable Git ancestors of the live
HEAD/origin/EOS projection. Non-descendant, contradictory, forged, or
ambiguous state still fails closed.

