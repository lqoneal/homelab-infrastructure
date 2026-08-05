# Publication Boundary Guard

`scripts/zeus-publication-boundary-guard` checks canonical repository identity,
attached branch, operation, target ref, origin presence, and push cleanliness.
It rejects prepublication commits on `main`, pushes to `main` without the
explicit governed publication authority marker, detached HEAD, and unexpected
refspecs. The guard is independent of session context.
