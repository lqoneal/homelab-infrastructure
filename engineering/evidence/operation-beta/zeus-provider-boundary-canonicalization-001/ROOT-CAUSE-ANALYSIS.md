# Provider Boundary Canonicalization — Root Cause

The current provider path had two independent defects. The CLI rejected any
mission that did not begin with the historical `MISSION-BETA-` prefix before
consulting the canonical mission projection. The provider-session validator
then treated any dispatch in the runtime as a contradiction, even when it was
an immutable record for another mission.

The corrective removes the prefix guard from the current path and scopes
provider/session validation to the requested mission and its authoritative
identity chain. Historical records remain untouched and are excluded from
current cardinality. A malformed or orphaned target record still fails closed.

The provider-selection transaction was then projected through the shared
canonical lifecycle resolver. All mission-native surfaces now agree on the
provider-selected boundary without creating dispatch, session, invocation,
or execution state.
