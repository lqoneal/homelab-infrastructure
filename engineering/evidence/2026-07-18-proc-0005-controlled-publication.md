# PROC-0005 Controlled Publication and Governance Baseline Evidence

Date: 2026-07-18

Transaction: Handoff — Controlled Document Publication Procedure Controlled Publication

## Publication Boundary

Included paths:

- `docs/procedures/PROC-0005-CONTROLLED_DOCUMENT_PUBLICATION_PROCEDURE.md`
- `docs/DOC-0001-REPOSITORY_DOCUMENT_INDEX.md`
- `engineering/evidence/2026-07-18-proc-0005-controlled-publication.md`

Excluded pre-existing working-tree paths:

- `scripts/lib/eos/codex.sh`
- `scripts/lib/eos/context.sh`
- `scripts/lib/eos/codex-report-qualify.sh`
- `scripts/tests/test-codex-notifications.sh`
- `scripts/tests/test-eos-runtime.sh`

## Qualified Content

- Reviewed planning-draft SHA-256:
  `eab22db371205d39836b5da9313864043ffdf8606cbf3aa46ea79f0a7738caef`
- Publication representation changes are limited to controlled metadata,
  canonical identity and placement, Active-publication wording, adoption text,
  and Revision History.
- The six-stage lifecycle, authority model, evidence model, publication
  controls, proportional application, Governance boundaries, and informative
  automation appendix are preserved.

## Controlled Identity

- Document identifier: `PROC-0005`
- Title: Controlled Document Publication Procedure
- Version: `1.0`
- Lifecycle state: `Active`
- Owner: Engineering Governance
- Classification: Engineering Procedure
- Approval authority: Engineering Governance
- Approval reference: Handoff — Controlled Document Publication Procedure
  Controlled Publication
- Publication date: 2026-07-18
- Parent repository baseline:
  `4fa62ae9642443ac2831fa7565e5b4d802f8d674`

## Initial Governance Baseline

`PROC-0005` Version 1.0 is the initial governance baseline for the reusable
Controlled Document Publication Procedure.

Governing standards and representation:

- STD-0000 — Engineering Documentation Standard
- STD-0001 — Engineering Document Lifecycle Standard
- STD-0002 — Engineering Document Persistence Standard
- SPEC-0001 — Controlled Document Representation Specification

Intended document classes:

- specifications;
- standards;
- policies;
- procedures;
- Engineering Decision Records; and
- other controlled classes permitted by their class-specific governance.

Intended consumers:

- document authors and technical reviewers;
- Engineering Governance and delegated Publication Authorities;
- repository custodians and Publication Executors;
- PROC-0001-governed publication work;
- PROC-0002 specialized EGR publication;
- PROC-0004 handoff construction for publication missions;
- future work-initiation and publication-planning guidance; and
- separately authorized future publication automation.

Specialized procedures supplement this baseline and are not replaced by it.
The informative automation appendix creates no authority.

## Immutable Baseline Treatment

The atomic publication commit containing this evidence record is the immutable
initial baseline. Its full commit object identifier and the immutable PROC-0005
blob identifier are resolved and recorded in the qualified Completion Report
after commit creation. This avoids an impossible self-referential commit hash
inside the commit whose identity it records.

## Required Verification

Before persistence:

- validate controlled identity, metadata, lifecycle, relationships, canonical
  placement, DOC-0001 synchronization, and complete publication content;
- verify the staged path set equals the three included paths exactly;
- verify all excluded paths remain unstaged; and
- run whitespace and repository validation.

After persistence:

- verify the publication commit contains exactly the three included paths;
- resolve the full commit and procedure blob identifiers;
- rerun controlled-document and repository-integrity validation; and
- confirm excluded changes remain outside the publication commit.

Publication creates no automation or downstream implementation authority.
