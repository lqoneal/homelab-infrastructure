# Publication Candidate Manifest

No files are staged. The exact corrective candidate paths are the following;
the operator must review hunks in paths marked `OVERLAP` because those files
also contained pre-existing dirty work.

## Candidate paths

- `docs/architecture/ADR-0001-ZEUS-CANONICAL-ARCHITECTURE-DECISION.md`
- `docs/emp/EMP-0001-ENGINEERING_MANAGEMENT_PLATFORM_ARCHITECTURE.md`
- `docs/policies/POL-0001-ENGINEERING_GOVERNANCE_POLICY.md`
- `docs/procedures/PROC-0001-ENGINEERING_WORK_ORDER_EXECUTION_PROCEDURE.md`
- `docs/procedures/PROC-0003-ENGINEERING_RECOVERY_RUNBOOK.md`
- `docs/procedures/PROC-0005-CONTROLLED_DOCUMENT_PUBLICATION_PROCEDURE.md`
- `docs/procedures/PROC-0007-GOVERNANCE-STABILIZATION-PROCEDURE.md`
- `docs/procedures/PROC-0008-ENGINEERING_GOVERNANCE_DECISION_PROCEDURE.md`
- `docs/specifications/SPEC-0001-CONTROLLED_DOCUMENT_MODEL.md`
- `docs/specifications/SPEC-0002-ZEUS-CANONICAL-ARCHITECTURE-SPECIFICATION.md`
- `docs/specifications/SPEC-0005-ENGINEERING_CONTROL_FRAMEWORK.md`
- `docs/specifications/SPEC-0007-ENGINEERING-PLATFORM-CONSTRUCTION-SPECIFICATION.md`
- `docs/specifications/SPEC-0010-ENGINEERING-KNOWLEDGE-REPOSITORY-ARCHITECTURE.md`
- `docs/specifications/SPEC-0012-PRODUCTION-EXECUTION-FOUNDATION.md`
- `docs/specifications/SPEC-0014-OPERATIONAL-ALPHA-CONVERGENCE-AUTHORITY.md`
- `docs/standards/STD-0000-ENGINEERING_GOVERNANCE_DOCUMENTATION_ARCHITECTURE.md`
- `docs/standards/STD-0001-ENGINEERING_DOCUMENT_LIFECYCLE_STANDARD.md`
- `docs/standards/STD-0003-ENGINEERING_WORK_ORDER_STANDARD.md`
- `engineering/admission/wop-submission.schema.yaml` (OVERLAP)
- `engineering/authority/manual-governance-wop-authority-policy.yaml` (OVERLAP)
- `engineering/docs/architecture/WOP-SCHEMA-AND-EXECUTION-INTERFACE.md`
- `engineering/docs/operations/ZEUS-DEVELOPMENT-MODE.md` (OVERLAP)
- `engineering/docs/operations/ZEUS-EXECUTION-LIFECYCLE-PROCEDURE.md` (OVERLAP)
- `engineering/metadata/operational-alpha-emm.yaml`
- `engineering/operations/authority-ownership-specification.md`
- `engineering/operations/repository-authority-model.md`
- `engineering/operations/zeus-mission-admission-runtime.md`
- `engineering/operations/zeus-operational-alpha-progress.md`
- `engineering/operations/zeus-operational-runtime.md`
- `engineering/operations/zeus-operator-interface.md`
- `scripts/lib/emp/codex_adapter.py`
- `scripts/lib/emp/stage1_runtime.py`
- `scripts/lib/emp/wop_admission.py`
- `scripts/lib/emp/wop_packaging.py`
- `scripts/lib/emp/wop_schema.py`
- `scripts/lib/eos/convergence_runtime.py`
- `scripts/tests/test-convergence-runtime.py`
- `scripts/tests/test-wop-admission.py`
- `scripts/tests/test-wop-submission-authority-convergence.py`
- `scripts/tests/test-zeus-development-mode-recovery.py` (OVERLAP)
- `scripts/tests/test-zeus-p5-g6-codex-adapter.py`
- this evidence directory and its files

## Publication commands

Do not use `git add -A`. After operator review, stage exactly the reviewed
candidate paths/hunks through the canonical repository publication procedure,
run its required validation and publication review, then commit/push only
under that procedure. EOS synchronization remains a separate explicit action
after publication and is not authorized by this bootstrap session.
