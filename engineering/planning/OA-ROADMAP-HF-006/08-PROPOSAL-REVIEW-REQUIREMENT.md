# Proposal Review Requirement: Information and Synchronization Architecture

Status: `PROPOSED — NON-AUTHORITATIVE`

Any future roadmap proposal that introduces or changes a document, report,
registry, dashboard, matrix, lifecycle model, engineering state, or metadata
shall include an information-and-synchronization section before review.

| Required declaration | Minimum content |
|---|---|
| authoritative source | one fact owner, stable identity, schema/revision |
| artifact classification | Authoritative, Derived, Runtime, or Historical |
| synchronization architecture | sources, targets, direction, mechanism, owner, trigger, freshness |
| verification method | provenance/digest and semantic predicate |
| drift detection | measurable stale, missing, mismatched, or conflicting condition |
| reconciliation and recovery | owner-routed correction, rebuild/replay, fail-safe state |
| public verification | intended canonical Zeus command or justified non-Zeus interface |
| generated-content boundary | authored metadata versus generated representation |

Review is incomplete when any declaration is absent, assigns multiple writers
to one fact, permits reverse synchronization from a derived view, or lacks a
safe response to drift. The reviewer records the disposition as incomplete;
this requirement itself does not approve, reject, or modify controlled work.
