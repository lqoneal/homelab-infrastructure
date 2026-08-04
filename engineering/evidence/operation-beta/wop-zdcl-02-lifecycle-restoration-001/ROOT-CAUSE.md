# Root Cause

The first failing decision was publication-baseline verification in
`Stage1Runtime._resolve_baseline_transition`. It required the immutable ZDCL
publication receipt's `resulting_main` to equal the current clean `main` HEAD.

The receipt correctly binds the hydration publication at `f95b691`; later
documentation-only publications advanced `main` to `b500329`. The resolver
therefore stopped before recovery-baseline binding, authority snapshot
restoration, provider selection, and dispatch preparation.

Classification: `IMPLEMENTATION_DEFECT` — exact-equality handling did not model
an authorized documentation/evidence-only descendant after the bound
publication.
