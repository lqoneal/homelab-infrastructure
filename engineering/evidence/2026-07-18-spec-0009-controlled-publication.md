# SPEC-0009 Controlled Publication Evidence

Date: 2026-07-18

Transaction: Handoff — Notification Service Controlled Publication

## Publication Boundary

Included paths:

- `docs/specifications/SPEC-0009-NOTIFICATION_SERVICE_SPECIFICATION.md`
- `docs/DOC-0001-REPOSITORY_DOCUMENT_INDEX.md`
- `engineering/evidence/2026-07-18-spec-0009-controlled-publication.md`

Excluded pre-existing working-tree paths:

- `scripts/lib/eos/codex.sh`
- `scripts/lib/eos/context.sh`
- `scripts/lib/eos/codex-report-qualify.sh`
- `scripts/tests/test-codex-notifications.sh`
- `scripts/tests/test-eos-runtime.sh`

## Identity and Baseline Inputs

- Assigned identity: `SPEC-0009`
- Initial version: `1.0`
- Lifecycle state: `Active`
- Owner: Engineering Platform
- Classification: Engineering Specification
- Approval authority: Engineering Governance
- Approval reference: Handoff — Notification Service Controlled Publication
- Publication date: 2026-07-18
- Parent repository baseline: `b54ca74`

## Publication Controls

- The qualified architecture is preserved.
- DOC-0001 registration is part of the same atomic publication boundary.
- All Deferred Execution items remain deferred.
- Publication creates no implementation authority.
- The publication commit is the immutable initial controlled baseline; its full
  object identifier is recorded in the qualified Completion Report produced
  after commit creation.

## Validation Record

The publication transaction requires, before commit:

- unique controlled identity and canonical placement;
- complete YAML metadata and valid relationships;
- DOC-0001 metadata, registration, and relationship consistency;
- controlled-document validation;
- whitespace validation;
- exact staged-path verification; and
- exclusion of all unrelated working-tree changes.

Post-commit verification requires the publication commit to contain exactly the
three included paths and requires the excluded paths to remain outside that
commit.
