# Candidate Generation Inventory

1. Validate and project roadmap/readiness/blocker/prerequisite views from MKM,
   Capability Registry, EMM, PMCT, and gate inputs.
2. Generate executable gate manifests from qualified gate authority.
3. Generate controller machine views and human-readable projections from the
   same validated context.
4. Generate provenance manifests and reconciliation indexes.
5. Generate structured recommendation indexes only after recommendation object
   ownership and lifecycle are separately qualified.

Generation must be byte-stable, source-bound, version-bound, and fail closed.
It must not generate mission authority, capability identity, approvals,
lifecycle transitions, or publication decisions.
