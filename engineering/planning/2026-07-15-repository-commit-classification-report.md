# Repository Commit Classification Report

Date: 2026-07-15
Status: Proposed for review
Authority: Codex Handoff Procedure — Repository Commit Classification and Commit Reconstruction Plan
Governing procedure: PROC-0001 Version 1.5
Engineering State: Reconciled under STD-0004 through the SprinterOS post-update qualification boundary

## Purpose

This persistent planning record defines **what Engineering History should
exist** for every outstanding Homelab and SprinterOS repository change. It
authorizes no staging, commit, tag, push, milestone publication, or
implementation.

## Repository Baseline

| Repository | Branch and HEAD | Observed state |
| --- | --- | --- |
| Homelab | `main` at `5f8829962d22d3cc233e02765a83ed004fd344ab` | 13 modified and 2 untracked paths before this planning mission |
| SprinterOS | `main` at `8921ed9` | 8 modified and 2 untracked paths; three commits ahead of `origin/main` |

EOS-STATE Version 0.7 and the active 2026-07-15 Engineering State
Reconciliation checkpoint agree that the Engineering Platform is operational,
recovery is qualified, zero milestones remain unreconciled, and the current
engineering investigation is persistent SprinterOS MMC storage I/O errors.

## Complete File Classification

| Repository | Path | Class | Objective | Purpose and dependency |
| --- | --- | --- | --- | --- |
| Homelab | `scripts/bootstrap/repair_yaml_header.py` | Tooling; Refactor; Bug Fix | C01 | Generalize YAML front-matter repair; independent pre-existing tooling change. |
| Homelab | `scripts/engctl` | Engineering Platform; Implementation | C02 | Add shared SSH-agent controller commands and resolved launcher path. |
| Homelab | `scripts/lib/eos/context.sh` | Engineering Platform; Implementation | C02 | Add stable socket, status, environment, loading, and operational reporting. |
| Homelab | `scripts/lib/eos/platform.sh` | Engineering Platform; Implementation | C02 | Integrate SSH-agent state with platform qualification. |
| Homelab | `scripts/tests/test-eos-runtime.sh` | Engineering Platform; Validation | C02 | Validate SSH-agent and controller integration. |
| Homelab | `docs/infrastructure/INF-0001-INFRASTRUCTURE_BASELINE.md` | Infrastructure; Documentation; Recovery | C02, C04 | Version 1.7 documents SSH architecture; Version 1.8 establishes PROC-0003 recovery authority. |
| Homelab | `docs/project/PROJ-0001-PROJECT_STATE.md` | Documentation; Engineering State | C02, C08 | Version 3.3 records SSH completion; Version 3.4 records reconciled recovery and MMC state. |
| Homelab | `docs/procedures/PROC-0003-ENGINEERING_RECOVERY_RUNBOOK.md` | Procedures; Recovery; Governance | C04 | Publish the authoritative recovery workflow after qualified recovery evidence. |
| Homelab | `docs/standards/STD-0004-ENGINEERING_STATE_FRESHNESS_STANDARD.md` | Standards; Governance | C07, C10, C11 | Version 1.0 establishes freshness; 1.1 adds classification; 1.2 adds reconstruction planning. |
| Homelab | `docs/procedures/PROC-0001-ENGINEERING_WORK_ORDER_EXECUTION_PROCEDURE.md` | Procedures; Governance | C04, C07, C10, C11 | Versions 1.2 through 1.5 integrate recovery, freshness, classification, and reconstruction planning. |
| Homelab | `docs/DOC-0001-REPOSITORY_DOCUMENT_INDEX.md` | Governance; Documentation | C04, C07, C10, C11 | Versions 2.8 through 2.11 register recovery, freshness, classification, and reconstruction workflow. |
| Homelab | `docs/standards/STD-0001-ENGINEERING_DOCUMENT_LIFECYCLE_STANDARD.md` | Standards; Governance | C07 | Distinguish controlled-document lifecycle from STD-0004 operational lifecycle. |
| Homelab | `docs/eos/EOS-0003-OPERATIONAL_PERSISTENCE_PROFILE.md` | Engineering Platform; Documentation | C07 | Apply freshness and authoritative-state precedence to EOS checkpoints. |
| Homelab | `docs/emp/EMP-0001-ENGINEERING_MANAGEMENT_PLATFORM_ARCHITECTURE.md` | Engineering Platform; Documentation | C07 | Apply freshness boundaries to EMP/EOS context. |
| Homelab | `docs/specifications/SPEC-0004-ENGINEERING_CONTEXT_RECONSTRUCTION_SERVICE.md` | Standards; Documentation | C07 | Require current authoritative resume sources and stale-objective rejection. |
| Homelab | `engineering/planning/2026-07-15-repository-commit-classification-report.md` | Governance; Engineering Evidence; Documentation | C12 | Persistent classification record required by PROC-0001. |
| Homelab | `engineering/planning/2026-07-15-repository-commit-reconstruction-plan.md` | Governance; Engineering Evidence; Documentation | C12 | Persistent reconstruction and execution plan required by PROC-0001. |
| SprinterOS | `docs/journal/milestones/2026-07-15-verified-recovery-baseline-recorded.md` | Recovery; Engineering Evidence; Milestone | C03, C09 | MILESTONE-0006 Version 1.0 records recovery; 1.1 links REPORT-0002. |
| SprinterOS | `docs/hardware/HW-0001-master-hardware-register.md` | Infrastructure; Recovery; Documentation | C03 | Record the protected recovery baseline. |
| SprinterOS | `docs/hardware/assets/AST-000001-atreides.md` | Infrastructure; Recovery; Documentation | C03 | Record image size, destination, and deferred restoration. |
| SprinterOS | `scripts/validate_repository.py` | Tooling; Validation | C03 | Validate MILESTONE-0006 and restoration boundary. |
| SprinterOS | `docs/infrastructure/INF-0001-INFRASTRUCTURE_BASELINE.md` | Infrastructure; Recovery; Documentation | C03, C05, C08 | Versions 1.3, 1.4, and 1.5 record recovery, authority migration, and post-update state. |
| SprinterOS | `docs/project/PROJ-0001-PROJECT_STATE.md` | Documentation; Engineering State | C03, C08 | Versions 2.3 and 2.4 record recovery readiness and reconciled MMC investigation. |
| SprinterOS | `docs/sprints/SPRINT-1.1.md` | Documentation; Engineering State; Evidence | C03, C08, C09 | Versions 1.3 through 1.5 record recovery, reconciliation, and REPORT-0002. |
| SprinterOS | `docs/DOC-0001-REPOSITORY_DOCUMENT_INDEX.md` | Governance; Documentation | C03, C05, C08, C09 | Versions 2.3 through 2.6 register each successive objective. |
| SprinterOS | `docs/journal/milestones/2026-07-14-raspberry-pi-platform-qualified.md` | Engineering Evidence; Milestone | C03, C09 | Version 1.1 links the recovery successor; 1.2 links the case study. |
| SprinterOS | `docs/reports/REPORT-0002-RASPBERRY_PI_RECOVERY_CASE_STUDY.md` | Engineering Evidence; Documentation | C09 | Preserve qualified recovery, update, and investigation history. |

No renamed or deleted paths were observed.

## Proposed Engineering Change Sets

| ID | Engineering objective | Repository | Primary classification | Proposed boundary |
| --- | --- | --- | --- | --- |
| C01 | Generalize YAML front-matter repair | Homelab | Tooling; Refactor; Bug Fix | One independent tooling commit. |
| C02 | Implement and document permanent shared SSH-agent management | Homelab | Engineering Platform; Infrastructure | Implementation, tests, INF-0001 1.7, and PROJ-0001 3.3. |
| C03 | Record the verified SprinterOS recovery baseline | SprinterOS | Recovery; Evidence; Milestone | MILESTONE-0006 1.0 and recovery-state publications. |
| C04 | Publish the Homelab Engineering Recovery Runbook | Homelab | Procedures; Recovery; Governance | PROC-0003, INF-0001 1.8, PROC-0001 1.2, DOC-0001 2.8. |
| C05 | Migrate SprinterOS recovery authority to PROC-0003 | SprinterOS | Recovery; Documentation | INF-0001 1.4 and DOC-0001 2.4. |
| C07 | Establish Engineering State Freshness governance | Homelab | Standards; Governance | STD-0004 1.0 and related lifecycle, EOS, EMP, resume, initiation, and index revisions. |
| C08-H | Reconcile Homelab Engineering State | Homelab | Documentation; Engineering State | PROJ-0001 3.4. |
| C08-S | Reconcile SprinterOS post-update state | SprinterOS | Documentation; Engineering State | INF-0001 1.5, PROJ-0001 2.4, SPRINT-1.1 1.4, DOC-0001 2.5. |
| C09 | Publish the Raspberry Pi Recovery Case Study | SprinterOS | Engineering Evidence; Documentation | REPORT-0002 and its milestone, sprint, and index relationships. |
| C10 | Establish Commit Classification governance | Homelab | Procedures; Standards; Governance | STD-0004 1.1, PROC-0001 1.4, DOC-0001 2.10. |
| C11 | Establish Commit Reconstruction Planning governance | Homelab | Procedures; Standards; Governance | STD-0004 1.2, PROC-0001 1.5, DOC-0001 2.11. |
| C12 | Publish repository commit planning records | Homelab | Governance; Engineering Evidence | This report and the paired reconstruction plan. |

C06 is intentionally unused so the identifiers preserve the earlier planning
analysis without renumbering later reviewed objectives.

## Dependency Order

```text
C01 (independent)
C02 ───────────────────────────────────────────────┐
C03 → C04 → C05                                    │
C03 → C07 → C08-H                                  │
             └──→ C08-S → C09                      │
C02, C04, C07, C08-H, C08-S, C09 → C10 → C11 → C12
                                                     ↓
                                  Engineering Platform Foundation milestone
```

C04 follows C03 because PROC-0003 incorporates the qualified recovery lessons.
C05 requires the Homelab PROC-0003 authority. C08 requires STD-0004. C09
requires reconciled state. C10 and C11 document governance learned after the
first classification exercise. C12 requires both procedures.

## Milestone Determination

Engineering Platform Foundation milestone prerequisites are fully identified
and reconstructable without a catch-all commit. Publication remains prohibited
until all approved prerequisite commits execute and validate. The milestone
record and tag shall be separate from implementation, governance, recovery,
evidence, and planning commits.
