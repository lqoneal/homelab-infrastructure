# BETA-02 Defect and Qualification Report

## Confirmed defect

The default `zeus mission list` path called the Operational Alpha Mission
Knowledge Model inventory and therefore showed only completed OA missions.

## Correction

The default list now projects active Beta work. Explicit completed/history/
archive views retain completed Alpha history. Beta explain and queue views now
include the authoritative fields required for operator and machine consumers.

## Qualification

Coverage includes active-list filtering, history availability, Beta explain,
queue scope, human/JSON semantic invariants, repeated deterministic reads,
unknown mission/family failure, and preservation of Alpha tags and state.
