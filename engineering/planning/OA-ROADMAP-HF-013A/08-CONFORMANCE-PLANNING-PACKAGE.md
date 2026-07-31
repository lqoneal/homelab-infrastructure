# Conformance Planning Package

| Suite | Fixtures and datasets | Pass/fail criteria | Required evidence |
| --- | --- | --- | --- |
| Metadata | valid, missing, conflicting, superseded, migrated EMM fixtures | one canonical resolution; invalid facts fail closed | inputs, resolver result, diagnostics |
| Synchronization | source, stale projection, retry, interrupted checkpoint datasets | directional, idempotent projection; no source overwrite | checkpoints, drift class, reconciliation result |
| Interface Contract | eight HF-011 interface request/response/error fixtures | pre/postconditions and error semantics match contract | versioned exchange transcript |
| Capability | one fixture for each HF-008 capability | consumes/produces only declared metadata | capability trace and evidence |
| Generated Artifact | fixed metadata and expected artifact digests | same input gives same output; output is non-authoritative | metadata/generator/artifact digests |
| Engineering Information API | version and compatibility fixtures | stable logical interface and fail-closed incompatibility | API result and compatibility decision |
| Qualification | passing, failing, incomplete evidence fixtures | deterministic pass/fail and attributable result | qualification report and evidence index |
| End-to-End Operational Alpha | governance-to-closeout metadata fixture | locked lifecycle order, no cycles/dead ends/owner conflict | gate trace, projections, qualification evidence |

Suites are specifications. No executable tests, runtime fixtures, or production
data are created by this package. Each future implementation shall materialize
the listed fixtures under separate authorization and retain the stated evidence.
