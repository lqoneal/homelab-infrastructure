# Architecture Report

The Mission Knowledge Model is the single current Operational Alpha mission
projection. It validates its EMM entity, roadmap provenance, and Capability
Registry before resolving lifecycle, dependencies, readiness, blockers, and
current mission state. Zeus controllers are read-only projections.

The superseded Progressive and PMCT stores remain available only to explicit
historical gate and compatibility services. They cannot select the active
mission, determine current lifecycle, or supply next-action state.

The reconciled current state is OA-01 through OA-14 `COMPLETED`, OA-15
`CURRENT`, OA-16 through OA-30 `STAGED`; OA-15 is blocked only by missing
`ZEUS-OA-CAP-014`.
