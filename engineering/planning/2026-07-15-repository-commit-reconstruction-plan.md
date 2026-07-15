# Repository Commit Reconstruction Plan

Date: 2026-07-15
Status: Proposed for review
Authority: Codex Handoff Procedure — Repository Commit Classification and Commit Reconstruction Plan
Classification report: `engineering/planning/2026-07-15-repository-commit-classification-report.md`
Governing procedure: PROC-0001 Version 1.5

## Purpose and Safety Boundary

This record defines **how the approved Engineering History will be safely
created**. It authorizes no staging, commit, tag, push, milestone publication,
branch mutation, cherry-pick, or working-tree reconstruction.

The execution mission shall first protect the current worktree, use temporary
worktrees or temporary indexes for reconstructed intermediate revisions, and
compare every resulting tree against the expected objective. Direct editing of
the primary working tree to move backward through intermediate versions is not
the preferred method because multiple files contain successive objectives.

## Common Validation Gates

Before every commit: confirm repository identity, expected parent, clean
temporary reconstruction context, classified path set, no active Git operation,
and `git diff --check`. After every commit: inspect `git show --stat`, validate
the exact committed path set and message, run `git fsck --no-dangling
--no-reflogs`, and execute the objective-specific validation below. Stop on any
unexpected path, tree, dependency, validation result, or source-worktree drift.

## Per-Commit Reconstruction Plans

### 1. C01 — Generalize YAML front-matter repair

- Repository: Homelab
- Files: `scripts/bootstrap/repair_yaml_header.py`
- Method: whole-file staging in an isolated temporary worktree reconstructed
  from the current source blob.
- Validation: Python syntax; exercise missing-file and valid-header behavior on
  disposable test inputs; Homelab verification.
- Title: `refactor(tooling): generalize YAML front-matter repair`
- Message: `Replace template-specific header replacement with validated generic Markdown front-matter normalization.`
- Expected state: only the repair utility differs from `5f88299`; all other
  outstanding work remains outside the commit.

### 2. C02 — Permanent shared SSH-agent management

- Repository: Homelab
- Files: `scripts/engctl`, `scripts/lib/eos/context.sh`,
  `scripts/lib/eos/platform.sh`, `scripts/tests/test-eos-runtime.sh`, reconstructed
  INF-0001 Version 1.7, reconstructed PROJ-0001 Version 3.3.
- Method: temporary worktree with reconstructed intermediate controlled-document
  revisions; whole-file stage the four implementation paths and reconstructed
  documentation.
- Validation: Bash syntax, EOS runtime tests, `engctl ssh status`, `engctl ssh
  environment`, controlled-document validation, full Homelab verification.
- Title: `feat(platform): integrate shared SSH-agent management`
- Message: `Add stable per-login SSH-agent discovery, loading, diagnostics, resume qualification, tests, and authoritative architecture documentation.`
- Expected state: Engineering Platform SSH management is complete and documented;
  recovery and later governance/state changes remain absent.

### 3. C03 — Verified SprinterOS recovery baseline

- Repository: SprinterOS
- Files: reconstructed MILESTONE-0006 Version 1.0, HW-0001 1.3,
  AST-000001 1.1, INF-0001 1.3, PROJ-0001 2.3, SPRINT-1.1 1.3,
  DOC-0001 2.3, `scripts/validate_repository.py`, and MILESTONE-0005 1.1.
- Method: temporary worktree with reconstructed intermediate publication versions.
- Validation: `scripts/sprinterctl validate`, Python syntax, document relationship
  and index validation, exact committed path inspection.
- Title: `docs(recovery): record verified SprinterOS recovery baseline`
- Message: `Record the qualified whole-card image, dual verification evidence, update readiness, and deferred restoration boundary.`
- Expected state: recovery baseline and MILESTONE-0006 are authoritative; update,
  PROC-0003 migration, and case-study references remain absent.

### 4. C04 — Engineering Recovery Runbook publication

- Repository: Homelab
- Files: PROC-0003; reconstructed INF-0001 1.8, PROC-0001 1.2, DOC-0001 2.8.
- Method: temporary worktree and reconstructed intermediate revisions.
- Validation: controlled-document validation, bidirectional index relationships,
  full Homelab verification.
- Title: `docs(governance): publish Engineering Recovery Runbook`
- Message: `Establish PROC-0003 as the shared recovery acquisition, verification, preservation, cleanup, restoration-qualification, and evidence authority.`
- Expected state: Homelab owns the recovery procedure; freshness and commit
  governance remain absent.

### 5. C05 — SprinterOS recovery-authority migration

- Repository: SprinterOS
- Files: reconstructed INF-0001 1.4 and DOC-0001 2.4.
- Method: temporary worktree with two reconstructed document revisions.
- Validation: SprinterOS validation and direct verification that procedural
  duplication is replaced by the Homelab PROC-0003 reference.
- Title: `docs(recovery): migrate SprinterOS authority to PROC-0003`
- Message: `Reference the Homelab recovery runbook while retaining project-specific evidence, naming, retention, and acceptance constraints.`
- Expected state: no conflicting recovery authority exists.

### 6. C07 — Engineering State Freshness governance

- Repository: Homelab
- Files: STD-0004 Version 1.0; reconstructed DOC-0001 2.9 and PROC-0001 1.3;
  STD-0001 1.4, EOS-0003 1.1, EMP-0001 1.3, SPEC-0004 1.1.
- Method: temporary worktree with reconstructed original STD-0004 and
  intermediate DOC/PROC versions.
- Validation: controlled documents, lifecycle and relationship consistency,
  resume-source precedence review, full Homelab verification.
- Title: `docs(governance): establish Engineering State Freshness Standard`
- Message: `Publish STD-0004 and integrate freshness reconciliation into lifecycle, Work Initiation, EOS, EMP, and resume architecture.`
- Expected state: freshness governance exists at its original 1.0 boundary;
  classification and reconstruction additions remain absent.

### 7. C08-H — Homelab Engineering State reconciliation

- Repository: Homelab
- Files: reconstructed PROJ-0001 Version 3.4.
- Method: temporary worktree with one reconstructed document revision.
- Validation: Homelab validation; compare Project State with EOS-STATE 0.7 and
  the reconciliation checkpoint.
- Title: `docs(state): reconcile Homelab engineering baseline`
- Message: `Synchronize recovery, platform, SprinterOS update, active MMC investigation, current mission, and zero-unreconciled-milestone state.`
- Expected state: Homelab Project State matches the reconciled operational state.

### 8. C08-S — SprinterOS post-update reconciliation

- Repository: SprinterOS
- Files: reconstructed INF-0001 1.5, PROJ-0001 2.4, SPRINT-1.1 1.4,
  DOC-0001 2.5.
- Method: temporary worktree with reconstructed intermediate revisions.
- Validation: SprinterOS validation and comparison with Homelab Project State,
  EOS-STATE, and STD-0004 freshness boundary.
- Title: `docs(state): reconcile SprinterOS post-update baseline`
- Message: `Record the completed OS, firmware, EEPROM, and kernel update, successful local qualification, and active persistent MMC investigation.`
- Expected state: resume points only to the unresolved MMC investigation.

### 9. C09 — Raspberry Pi Recovery Case Study

- Repository: SprinterOS
- Files: REPORT-0002; final MILESTONE-0005 1.2, MILESTONE-0006 1.1,
  SPRINT-1.1 1.5, DOC-0001 2.6.
- Method: whole-file staging in a temporary worktree after commits 3, 5, and 8
  supply the correct intermediate parents.
- Validation: SprinterOS validation, relationship and index checks, evidence-only
  scope review.
- Title: `docs(evidence): publish Raspberry Pi recovery case study`
- Message: `Preserve the qualified recovery, update, post-update observations, lessons, and remaining MMC investigation without creating new procedure or fault conclusions.`
- Expected state: all current SprinterOS working-tree publications are represented.

### 10. C10 — Commit Classification governance

- Repository: Homelab
- Files: reconstructed STD-0004 1.1, PROC-0001 1.4, DOC-0001 2.10.
- Method: temporary worktree with reconstructed intermediate revisions derived
  from commit 6.
- Validation: Homelab validation; verify classification categories, one-objective
  rule, traceability, milestone rule, and distinct STD/PROC authority.
- Title: `docs(governance): establish Commit Classification procedure`
- Message: `Place mandatory classification after state reconciliation and govern logical boundaries, dependency order, traceability, and milestone isolation.`
- Expected state: classification is governed; reconstruction planning is not yet present.

### 11. C11 — Commit Reconstruction Planning governance

- Repository: Homelab
- Files: final STD-0004 1.2, PROC-0001 1.5, DOC-0001 2.11.
- Method: whole-file staging after commit 10 supplies the exact predecessor
  revisions; verify only the Version 1.2/1.5/2.11 deltas enter this commit.
- Validation: Homelab validation; verify lifecycle order, accepted reconstruction
  methods, execution gate, milestone sequence, and planning-artifact governance.
- Title: `docs(governance): establish Commit Reconstruction Planning`
- Message: `Add the governed reconstruction stage, safe reconstruction methods, execution prerequisites, and proportional persistent planning requirements.`
- Expected state: the current governing publications are fully represented.

### 12. C12 — Persistent commit planning records

- Repository: Homelab
- Files: this plan and the paired classification report.
- Method: whole-file staging after final review; update only review status or
  approved corrections before execution.
- Validation: Markdown inspection, cross-reference check, complete file-to-plan
  coverage, dependency graph review, Homelab verification.
- Title: `docs(planning): publish commit classification and reconstruction plan`
- Message: `Retain the first governed classification report and reconstruction plan for the multi-repository Engineering Platform Foundation history.`
- Expected state: every outstanding change has an authoritative reviewed execution plan.

## Milestone and Publication Sequence

After commits 1–12 pass their gates, perform a separate milestone qualification.
If approved, create a milestone-only commit with the recommended title:

`docs(milestone): publish Engineering Platform Foundation 1.0`

Create the annotated tag `engineering-platform-foundation-1.0` only after the
milestone commit validates and explicit tag authority is confirmed. Run
Homelab, controlled-document, relationship, Git integrity, EOS resume, and
cross-repository validation after tagging.

No push is currently authorized. A later push authority should push SprinterOS
commits in dependency order first where referenced by Homelab state, then push
Homelab commits and the annotated milestone tag. Revalidate local-to-upstream
commit ancestry immediately before any push.
