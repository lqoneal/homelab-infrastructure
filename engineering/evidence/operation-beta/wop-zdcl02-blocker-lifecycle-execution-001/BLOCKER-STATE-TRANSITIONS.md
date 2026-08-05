# Blocker State Transitions

Allowed edges are `DISCOVERED→VERIFIED→ACTIVE→RESOLVING→REVALIDATING`, followed by `ACTIVE` when unresolved or `RESOLVED→RETIRED` after verified corrective completion. Direct skips are rejected.
