---
document_id: WOP-RUNTIME-BASELINE-PUBLICATION-001-PUBLICATION-BOUNDARY
status: Approved
date: 2026-07-30
scope: ZEUS-CONVERGENCE-RUNTIME-BASELINE-1.0 publication boundary
---

# Publication Boundary Manifest

## Initial validation boundary

- Repository: `REPOSITORY-HOMELAB`
- Starting commit: `1454917f3e314ef847db8467c7b84a529dcc3d2d`
- Target branch: `main`
- Target identifier: `ZEUS-CONVERGENCE-RUNTIME-BASELINE-1.0`
- Intended immutable tag: `ZEUS-CONVERGENCE-RUNTIME-BASELINE-1.0`
- EOS boundary: read-only verification only; no EOS synchronization is part of this publication.

## Included publication content

The following modified paths are frozen as the certified convergence-runtime baseline. Directory entries include every file beneath them.

- `docs/DOC-0001-REPOSITORY_DOCUMENT_INDEX.md`
- `docs/project/PROJ-0001-PROJECT_STATE.md`
- `docs/project/milestones/2026-07-30-operational-alpha-convergence-runtime-closeout.md`
- `docs/specifications/SPEC-0014-OPERATIONAL-ALPHA-CONVERGENCE-AUTHORITY.md`
- `engineering/execution/execution-interface.yaml`
- `engineering/execution/operational-alpha-execution-contract.yaml`
- `engineering/metadata/`
- `engineering/registry/architecture-baselines/OA-IMPLEMENTATION-BASELINE-1.0.yaml`
- `engineering/registry/runtime-baselines/`
- `engineering/evidence/2026-07-30-wop-convergence-closeout-001/`
- `engineering/evidence/2026-07-30-wop-convergence-execution-contract-001/`
- `engineering/evidence/2026-07-30-wop-convergence-execution-migration-001/`
- `engineering/evidence/2026-07-30-wop-convergence-implementation-001/`
- `engineering/evidence/2026-07-30-wop-convergence-operational-integration-001/`
- `engineering/evidence/2026-07-30-wop-runtime-certification-001/`
- `engineering/evidence/2026-07-30-wop-runtime-certification-002/`
- `engineering/evidence/2026-07-30-wop-runtime-qualification-001/`
- `engineering/evidence/2026-07-30-wop-runtime-requalification-001/`
- `scripts/lib/emp/mission_admission_runtime.py`
- `scripts/lib/eos/convergence_runtime.py`
- `scripts/lib/eos/execution_interface.py`
- `scripts/lib/eos/state_sync.py`
- `scripts/tests/test-convergence-runtime.py`
- `scripts/tests/test-engineering-execution-interface.py`
- `scripts/tests/test-mission-admission-runtime.py`
- `scripts/tests/test-mission-execution-runtime.py`
- `scripts/tests/test-operational-gate-handler.py`
- `scripts/tests/test-zeus-mission-assurance.py`
- `scripts/zeus`

## Explicitly excluded paths

These changes are unrelated to the certified convergence-runtime baseline and remain uncommitted and unmodified by this publication.

| Scope | Disposition rationale |
| --- | --- |
| `AQR-0001` revision and its HF-002 evidence | Independent architecture-qualification re-execution against repository commit `7e3bf673...`; it explicitly retains Draft/Pending promotion status and is not a runtime contract, runtime certification, or runtime-baseline record. |
| OA-ROADMAP-HF-001 through HF-004 | Proposal-local roadmap and adoption-planning artifacts. The runtime baseline is governed by the already adopted `OA-IMPLEMENTATION-BASELINE-1.0`, `SPEC-0014@1.1`, EMM, and the final runtime certification, not these unpublished predecessor proposal directories. |
| OA-01 controlled requirements reassessment | Read-only downstream gate-readiness evidence against `OA-IMPLEMENTATION-BASELINE-1.0`; it neither implements nor certifies the Zeus convergence runtime. |

- `docs/architecture/AQR-0001-ARCHITECTURE-QUALIFICATION-REPORT.md`
- `engineering/evidence/2026-07-30-aqr-0001-hf-002-architecture-qualification-matrix.md`
- `engineering/evidence/2026-07-30-aqr-0001-hf-002-architecture-readiness-report.md`
- `engineering/evidence/2026-07-30-aqr-0001-hf-002-change-summary.md`
- `engineering/evidence/2026-07-30-aqr-0001-hf-002-independent-qualification-report.md`
- `engineering/evidence/2026-07-30-aqr-0001-hf-002-repository-convergence-qualification-matrix.md`
- `engineering/evidence/2026-07-30-aqr-0001-hf-002-validation.md`
- `engineering/evidence/2026-07-30-wop-oa-01-000/OA-01-CONTROLLED-REQUIREMENTS-REASSESSMENT.md`
- `engineering/planning/OA-ROADMAP-HF-001/`
- `engineering/planning/OA-ROADMAP-HF-002/`
- `engineering/planning/OA-ROADMAP-HF-003/`
- `engineering/planning/OA-ROADMAP-HF-004/`

## Stop conditions

Stop publication if the staged boundary contains an excluded path, validation fails, the remote branch advances, or the immutable tag resolves to a different commit from the frozen baseline commit.
