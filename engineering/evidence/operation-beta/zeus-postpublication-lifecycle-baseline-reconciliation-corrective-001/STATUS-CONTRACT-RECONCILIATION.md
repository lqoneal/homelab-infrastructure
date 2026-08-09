# Zeus Status Contract Reconciliation

The prior status failures were split into two classes.

1. The current status path could enter the historical OA assembler when a
   testing/engineering state was present. That assembler required
   `authority/active-publication.json` and OA-01 selectors, which are not
   prerequisites for current canonical P2/P3/P4 lifecycle status.
2. The associated tests asserted the superseded OA-rich status shape rather
   than the current Operation Beta planning plus canonical lifecycle contract.

The current path now emits Operation Beta authority data together with a
`canonical_lifecycle` live projection, `current_state_authority`, and
canonical mission/state/next fields. It does not use an OA pointer to discover
or authorize the lifecycle mission. OA fields remain explicitly labeled
compatibility-only. The operator-interface tests were updated to assert this
current contract; the focused suite passes.

`zeus status` still reports the Beta planning next action for the planning
domain. It separately exposes the canonical lifecycle mission and its
receipt-backed next action, so the two projections are not conflated.

