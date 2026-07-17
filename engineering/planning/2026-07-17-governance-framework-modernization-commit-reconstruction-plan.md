# Governance Framework Modernization Commit Reconstruction Plan

Date: 2026-07-17

Authority: EGR-000002 and EWO-000018

## Approved Method

Use explicit path staging from the existing working tree. Do not use bulk
staging. Compare the staged path list against the classified publication set
and the EWO-000017 exclusion list before commit.

Shared records are staged as complete reconciled publications because their
current revisions deliberately preserve EWO-000017 context and add EWO-000018
authority. The registry regression fixture is staged only because the published
registry would otherwise fail deterministic platform validation.

The EWO-000017 controlled Work Order is staged as the required authority and
relationship target for the reconciled index, Project State, registry, and
EGR-000002. Its notification runtime paths remain excluded.

## Pre-Commit Gates

1. Controlled-document validator passes.
2. Work Registry schema and regression tests pass.
3. Governance hierarchy has no cycle.
4. Exact `Completion Report` headings and mandatory Governance Conformance
   Review requirements are discoverable from repository governance.
5. `git diff --check` passes.
6. Staged paths contain no excluded notification runtime path.
7. Staged diff contains no secret or live-acceptance material.
8. Commit message matches the classification report.

## Expected Post-Commit State

The governance publication is committed and EWO-000017 runtime work remains
unstaged and uncommitted. The repository is intentionally modified under the
EGR-000002 exception rather than falsely reported clean. EOS is refreshed and
a post-publication checkpoint records the exact boundary. No tag or push occurs.
