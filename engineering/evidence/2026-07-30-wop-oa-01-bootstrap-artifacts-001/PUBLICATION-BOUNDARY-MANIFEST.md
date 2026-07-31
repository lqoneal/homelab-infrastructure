---
document_id: WOP-OA-01-BOOTSTRAP-PUBLICATION-001-PUBLICATION-BOUNDARY
status: Approved
date: 2026-07-30
scope: OA-01 manual-governance bootstrap authority publication boundary
---

# Publication Boundary Manifest

## Frozen publication boundary

- Repository: `REPOSITORY-HOMELAB`
- Starting commit: `a7d8e6bafab6c25bb007096167e9f4847308edd4`
- Target branch: `main`
- Publication marker: `OA-01-BOOTSTRAP-AUTHORITY-ARTIFACTS-1.0`
- Runtime baseline preserved: `ZEUS-CONVERGENCE-RUNTIME-BASELINE-1.0@5decaed25c8e3489b49f7dcb032eb27ffd7c783e`
- Lifecycle effect: `NONE`

## Included publication content

The following paths, and only the listed `scripts/zeus` bootstrap-action hunks,
are required for deterministic resolution of the published OA-01 bootstrap
authority artifacts.

- `docs/policies/POL-0001-ENGINEERING_GOVERNANCE_POLICY.md`
- `docs/procedures/PROC-0001-ENGINEERING_WORK_ORDER_EXECUTION_PROCEDURE.md`
- `docs/specifications/SPEC-0014-OPERATIONAL-ALPHA-CONVERGENCE-AUTHORITY.md`
- `docs/standards/STD-0003-ENGINEERING_WORK_ORDER_STANDARD.md`
- `engineering/authority/manual-governance-wop-authority-policy.yaml`
- `engineering/execution/execution-interface.yaml`
- `engineering/execution/bootstrap-gate-actions/OA-01-BOOTSTRAP-GATE-ACTIONS.yaml`
- `engineering/metadata/operational-alpha-emm.yaml`
- `engineering/work-orders/OA-01-ROOT-ADMISSION-001/immutable-wop.yaml`
- `scripts/lib/eos/convergence_runtime.py`
- `scripts/tests/test-convergence-runtime.py`
- `scripts/zeus` — `execution bootstrap-actions` interface only
- `engineering/evidence/2026-07-30-wop-oa-01-bootstrap-artifacts-001/`

The included content establishes a bounded manual-governance root authority,
the exact EMM registrations, and a handler-validated bootstrap action payload.
It does not create an Authority Record, Operational Gate Plan, activation, or
execution state.

## Explicit exclusions

The following changes are not part of this publication and remain uncommitted:

- `docs/architecture/AQR-0001-ARCHITECTURE-QUALIFICATION-REPORT.md`
- `engineering/evidence/2026-07-30-aqr-0001-hf-002-*`
- `engineering/evidence/2026-07-30-wop-oa-01-000/`
- `engineering/planning/OA-ROADMAP-HF-001/` through `OA-ROADMAP-HF-004/`
- `engineering/evidence/2026-07-30-wop-oa-state-reconciliation-001/`
- `engineering/evidence/2026-07-30-wop-runtime-status-resolution-001/`
- `scripts/lib/eos/operational_alpha_status.py`
- `scripts/lib/eos/state_sync.py`
- `scripts/tests/test-operational-alpha-status.py`
- `scripts/zeus` current-status resolver hunks

These are separate qualification, planning, reassessment, or status-resolution
work. They do not establish the bootstrap-authority artifact contract.

## Stop conditions

Stop publication if a staged path is absent from the inclusion list, an
exclusion is staged, source-digest validation fails, the immutable runtime tag
does not resolve to `5decaed25c8e3489b49f7dcb032eb27ffd7c783e`, or `main`
advances before publication.
