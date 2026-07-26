# Engineering Work Initiation Authorization Enforcement

Date: 2026-07-25
Status: Enforcement Mode implementation
Mission: Zeus Operational Alpha Mission H Revision 2

## Decision routing

Engineering Work Initiation still runs the legacy qualification for comparison
and rollback evidence. In the default `enforcement` mode, only the Zeus
Authority/WOP decision controls the qualification return status. Zeus denial,
missing inputs, invalid configuration or ADR persistence failure returns 77 and
fails closed. A legacy allow cannot override it. A Zeus allow remains an
authorization decision only; it does not execute or dispatch a WOP.

## Rollback

`EOS_AUTHORIZATION_MODE=rollback` restores the legacy result as the routing
decision while continuing Zeus evaluation and ADR generation. Rollback is
explicit, observable in ADR schema version 2 and regression tested. Historical
`shadow` mode remains available for diagnostic compatibility but is not the
operational default.

## Context trust boundary

Enforcement compares the supplied WOP evaluation repository and baseline with
the repository identity and HEAD observed by Work Initiation. Repository or
resume state cannot supply authority, and disagreement with the WOP context
fails closed as `EXECUTION_CONTEXT_MISMATCH`.

## ADR versioning

Mission G ADR schema version 1 is unchanged, preserving byte reproduction of
the retained qualification package. Enforcement and rollback generate schema
version 2 records adding enforcement mode, authoritative decision source,
legacy comparison result and rollback status. These fields participate in the
deterministic decision digest.

## Separation from execution

No execution-session constructor, WOP dispatcher, live lease acquisition,
effect executor or autonomous loop is introduced. Authorization ends with a
decision record and process status.
