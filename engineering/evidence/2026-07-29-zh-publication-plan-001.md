# ZH Publication and Commit Plan 001

Date: 2026-07-29  
Reconciled by: `ZH-PUBLICATION-PLAN-RECONCILIATION-001`  
Disposition: `RECONCILED — PUBLICATION PAUSED AFTER PU-01`

## Authoritative baseline

- Repository: `/data/engineering/repositories/homelab`
- Completed commit: PU-01 at `a85893930e83c2a0579e465f4951499965441f11`
- Upstream: `origin/main`, local ahead 1 / behind 0 at reconciliation
- EOS: `EXPECTED_PUBLICATION_DRIFT`; synchronization prohibited before the boundary after PU-08
- Machine-readable plan: `engineering/evidence/2026-07-29-zh-publication-plan-001.json`
- Digest/membership manifest: `engineering/evidence/2026-07-29-zh-publication-plan-reconciliation-001-manifest.json`

## Required sequence

```text
PU-01 (completed) -> PU-01A -> PU-02 -> PU-03 -> PU-04 -> PU-05 -> PU-06 -> PU-07 -> PU-08
  -> Synchronization Boundary -> PU-09 -> Final Validation Boundary -> Push
```

PU-01A is the dedicated prerequisite protocol unit. PU-02 through PU-08 retain their previously approved membership and commit messages. PU-09 is narrowed to the two historical audit artifacts because the authoritative plan and reconciliation evidence must publish in PU-01A before resumed execution.

## Publication units

### PU-01 — docs(governance): publish mission lifecycle baseline

Status: completed. Dependencies: none. Risk: high.

Publish the coordinated governance baseline, index, milestone, and documentation qualifications that define mission initiation, admission, stabilization, and authority restoration.

Published paths (15; historical PU-01 membership, not candidate assignments):

- `docs/DOC-0001-REPOSITORY_DOCUMENT_INDEX.md`
- `docs/charters/CHAR-0001-ENGINEERING_CHARTER.md`
- `docs/edr/EDR-0002-ENGINEERING_AUTHORITY_MODEL.md`
- `docs/genesis/GEN-0001-GENESIS_GOVERNANCE_RECORD.md`
- `docs/policies/POL-0001-ENGINEERING_GOVERNANCE_POLICY.md`
- `docs/procedures/PROC-0001-ENGINEERING_WORK_ORDER_EXECUTION_PROCEDURE.md`
- `docs/procedures/PROC-0002-ENGINEERING_GOVERNANCE_RESOLUTION_PROCEDURE.md`
- `docs/procedures/PROC-0007-GOVERNANCE-STABILIZATION-PROCEDURE.md`
- `docs/project/milestones/2026-07-29-operational-alpha-governance-baseline-1.0.md`
- `docs/specifications/SPEC-0005-ENGINEERING_CONTROL_FRAMEWORK.md`
- `docs/specifications/SPEC-0011-PRODUCTION-AUTHORITY-RESTORATION-SPECIFICATION.md`
- `engineering/evidence/2026-07-29-zh-gov-mission-lifecycle-002-corrective-handoff.md`
- `scripts/tests/test-governance-baseline-documentation.py`
- `scripts/tests/test-governance-bootstrap-documentation.py`
- `scripts/tests/test-governance-mission-admission-documentation.py`

Validation:

- `python3 scripts/validate_controlled_documents.py`
- `python3 scripts/tests/test-governance-baseline-documentation.py`
- `python3 scripts/tests/test-governance-bootstrap-documentation.py`
- `python3 scripts/tests/test-governance-mission-admission-documentation.py`
- `git diff --check`

Prepared commit message:

```text
docs(governance): publish mission lifecycle baseline

Publish the coordinated governance baseline, index, milestone, and documentation qualifications that define mission initiation, admission, stabilization, and authority restoration.

Engineering rationale: preserve ZH-GOV-MISSION-LIFECYCLE-002, Operational Alpha Governance Baseline 1.0 as a reviewable publication boundary without partial lifecycle state or rewritten evidence.

Validation: python3 scripts/validate_controlled_documents.py; python3 scripts/tests/test-governance-baseline-documentation.py; python3 scripts/tests/test-governance-bootstrap-documentation.py; python3 scripts/tests/test-governance-mission-admission-documentation.py; git diff --check.
Affected OA gates: OA-01 through OA-30 governance envelope; no gate transition.
Related investigations: none.
Controlled-document impact: Updates CHAR-0001, POL-0001, EDR-0002, GEN-0001, PROC-0001/0002/0007, SPEC-0005/0011, DOC-0001, and adds the baseline milestone.
```

### PU-01A — docs(platform): publish corrected EOS publication protocol

Status: planned. Dependencies: PU-01. Risk: high.

Publish the coordinated repository-authoritative EOS protocol correction, stop/reconciliation evidence, and authoritative regenerated publication plan as the prerequisite for resumed execution.

Paths (14):

- `docs/DOC-0001-REPOSITORY_DOCUMENT_INDEX.md`
- `docs/eos/EOS-0003-OPERATIONAL_PERSISTENCE_PROFILE.md`
- `docs/procedures/PROC-0001-ENGINEERING_WORK_ORDER_EXECUTION_PROCEDURE.md`
- `docs/procedures/PROC-0005-CONTROLLED_DOCUMENT_PUBLICATION_PROCEDURE.md`
- `docs/standards/STD-0004-ENGINEERING_STATE_FRESHNESS_STANDARD.md`
- `engineering/evidence/2026-07-29-zh-publication-protocol-correction-001-change-matrix.md`
- `engineering/evidence/2026-07-29-zh-publication-protocol-correction-001.md`
- `engineering/evidence/2026-07-29-zh-publication-resume-002.md`
- `engineering/evidence/2026-07-29-zh-publication-plan-reconciliation-001.md`
- `engineering/evidence/2026-07-29-zh-publication-plan-reconciliation-001-change-matrix.md`
- `engineering/evidence/2026-07-29-zh-publication-plan-reconciliation-001-manifest.json`
- `engineering/evidence/2026-07-29-zh-publication-plan-001.md`
- `engineering/evidence/2026-07-29-zh-publication-plan-001.json`
- `engineering/operations/repository-eos-synchronization.md`

Validation:

- `python3 scripts/validate_controlled_documents.py`
- `python3 scripts/tests/test-governance-baseline-documentation.py`
- `python3 -m json.tool engineering/evidence/2026-07-29-zh-publication-plan-001.json`
- `python3 -m json.tool engineering/evidence/2026-07-29-zh-publication-plan-reconciliation-001-manifest.json`
- `verify exact PU-01A staged path set and manifest digests`
- `git diff --check`

Prepared commit message:

```text
docs(platform): publish corrected EOS publication protocol

Publish the coordinated repository-authoritative EOS protocol correction, stop/reconciliation evidence, and authoritative regenerated publication plan as the prerequisite for resumed execution.

Engineering rationale: preserve ZH-PUBLICATION-PROTOCOL-CORRECTION-001, ZH-PUBLICATION-RESUME-002, and ZH-PUBLICATION-PLAN-RECONCILIATION-001 as one reviewable governing boundary before runtime publication resumes.

Validation: python3 scripts/validate_controlled_documents.py; python3 scripts/tests/test-governance-baseline-documentation.py; parse and verify publication JSON/manifest; verify exact staged paths and digests; git diff --check.
Affected OA gates: No gate transition.
Related investigations: EOS Publication Contract investigation.
Controlled-document impact: Updates DOC-0001, PROC-0001/0005, STD-0004, EOS-0003, and the operational synchronization procedure.
```

### PU-02 — feat(zeus): implement cumulative OA-01 through OA-05 runtime

Status: planned. Dependencies: PU-01A. Risk: high.

Publish the indivisible cumulative Zeus implementation: operational context, authority, discovery, resolution, Stage 1 staging, CLI, PMCT contracts, package metadata, documentation, and regressions.

Paths (49):

- `engineering/docs/architecture/ZEUS-STAGE1-RUNTIME.md`
- `engineering/docs/cli/ZEUS-USER-GUIDE.md`
- `engineering/execution/execution-interface.yaml`
- `engineering/operations/authority-ownership-specification.md`
- `engineering/operations/zeus-mission-admission-runtime.md`
- `engineering/operations/zeus-mission-execution-runtime.md`
- `engineering/operations/zeus-oa01-mission-verification.md`
- `engineering/operations/zeus-operational-runtime.md`
- `engineering/operations/zeus-operator-interface.md`
- `engineering/tests/zeus-operational-alpha/PMCT-CAPABILITY-MATRIX.yaml`
- `engineering/tests/zeus-operational-alpha/PMCT-CONTRACT.md`
- `engineering/tests/zeus-operational-alpha/tests/test-result-model.py`
- `engineering/tests/zeus-operational-alpha/tests/test-state-protection.py`
- `engineering/tests/zeus-operational-alpha/tests/test_discovery.py`
- `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/MANIFEST.sha256`
- `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/gates/OA-05/implementation.md`
- `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/gates/OA-05/verification.md`
- `scripts/lib/emp/controlled_mission_authority.py`
- `scripts/lib/emp/mission_contract_discovery.py`
- `scripts/lib/emp/mission_resolution.py`
- `scripts/lib/emp/oa01_gate_verification.py`
- `scripts/lib/emp/oa01_implementation.py`
- `scripts/lib/emp/oa01_verification.py`
- `scripts/lib/emp/oa02_gate_verification.py`
- `scripts/lib/emp/oa02_implementation.py`
- `scripts/lib/emp/oa03_gate_verification.py`
- `scripts/lib/emp/oa03_implementation.py`
- `scripts/lib/emp/oa04_gate_verification.py`
- `scripts/lib/emp/oa04_implementation.py`
- `scripts/lib/emp/oa05_gate_verification.py`
- `scripts/lib/emp/oa05_implementation.py`
- `scripts/lib/emp/progressive_oa.py`
- `scripts/lib/emp/project_operational_context.py`
- `scripts/lib/emp/stage1_runtime.py`
- `scripts/tests/test-zeus-mission-count-status.py`
- `scripts/tests/test-zeus-oa01-implementation.py`
- `scripts/tests/test-zeus-oa01-verification.py`
- `scripts/tests/test-zeus-oa02-controlled-authority.py`
- `scripts/tests/test-zeus-oa02-lifecycle.py`
- `scripts/tests/test-zeus-oa03-mission-contract-discovery.py`
- `scripts/tests/test-zeus-oa04-context-reconstruction.py`
- `scripts/tests/test-zeus-oa04-mission-resolution.py`
- `scripts/tests/test-zeus-oa05-mission-staging.py`
- `scripts/tests/test-zeus-progressive-oa.py`
- `scripts/tests/test-zeus-stage1-runtime.py`
- `scripts/tests/test_discovery.py`
- `scripts/verify.sh`
- `scripts/zeus`
- `services/eens/README.md`

Validation:

- `bash engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/verify-package.sh`
- `python3 scripts/tests/test-zeus-progressive-oa.py`
- `python3 scripts/tests/test-zeus-stage1-runtime.py`
- `python3 scripts/tests/test-zeus-oa05-mission-staging.py`
- `python3 scripts/tests/test-zeus-mission-count-status.py`
- `python3 -m py_compile <affected modules>`
- `git diff --check`

Prepared commit message:

```text
feat(zeus): implement cumulative OA-01 through OA-05 runtime

Publish the indivisible cumulative Zeus implementation: operational context, authority, discovery, resolution, Stage 1 staging, CLI, PMCT contracts, package metadata, documentation, and regressions.

Engineering rationale: preserve REBUILD-ZEUS-OA-PROGRESSIVE-WOP-001, ZH-OA01-IMPLEMENTATION-003, ZH-OA02-CONTROLLED-MISSION-AUTHORITY-001, ZH-OA03-MISSION-CONTRACT-DISCOVERY-001, ZH-OA04-MISSION-RESOLUTION-001, ZH-OA05-MISSION-STAGING-001, ZH-OA05-MISSION-COUNT-INVESTIGATION-001, ZH-001 Stage 1 as a reviewable publication boundary without partial lifecycle state or rewritten evidence.

Validation: bash engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/verify-package.sh; python3 scripts/tests/test-zeus-progressive-oa.py; python3 scripts/tests/test-zeus-stage1-runtime.py; python3 scripts/tests/test-zeus-oa05-mission-staging.py; python3 scripts/tests/test-zeus-mission-count-status.py; python3 -m py_compile <affected modules>; git diff --check.
Affected OA gates: Implements and verifies OA-01 through OA-05; leaves acceptance projection unpublished.
Related investigations: ZH-OA05-MISSION-COUNT-INVESTIGATION-001.
Controlled-document impact: No controlled-document lifecycle mutation; implements PU-01 contracts and updates operational/package documentation.
```

### PU-03 — docs(oa): preserve OA-01 acceptance evidence

Status: planned. Dependencies: PU-02. Risk: medium.

Publish OA-01 implementation, verification attempts, corrective completion, accepted receipt, qualification, and admission-initiation evidence as an immutable set.

Paths (12):

- `engineering/evidence/2026-07-29-zh-oa01-implementation-003.md`
- `engineering/evidence/2026-07-29-zh-oa01-qualification-002.md`
- `engineering/evidence/2026-07-29-zh-zeus-oa-admission-001-work-initiation.md`
- `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/decisions/OA-01/accepted.json`
- `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/evidence/OA-01/IMPLEMENTATION.json`
- `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/evidence/OA-01/VERIFICATION.json`
- `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/evidence/OA-01/VERIFIED`
- `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/evidence/OA-01/ZH-OA01-VERIFICATION-CORRECTIVE-004-COMPLETION.md`
- `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/evidence/OA-01/attempts/0c721f239604ca12d5d59af0db2c857b097b8cbdec44c045f36058d790b13c91/VERIFICATION.json`
- `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/evidence/OA-01/attempts/0c721f239604ca12d5d59af0db2c857b097b8cbdec44c045f36058d790b13c91/VERIFIED`
- `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/evidence/OA-01/attempts/a337b7ade99bb67790d51e0bc09a07777ae06096454540af005adb99dfa4024d/VERIFICATION.json`
- `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/evidence/OA-01/attempts/a337b7ade99bb67790d51e0bc09a07777ae06096454540af005adb99dfa4024d/VERIFIED`

Validation:

- `scripts/zeus gate receipt OA-01`
- `JSON parse and digest review of OA-01 evidence`
- `git diff --check`

Prepared commit message:

```text
docs(oa): preserve OA-01 acceptance evidence

Publish OA-01 implementation, verification attempts, corrective completion, accepted receipt, qualification, and admission-initiation evidence as an immutable set.

Engineering rationale: preserve ZH-OA01-IMPLEMENTATION-003, ZH-OA01-QUALIFICATION-002, ZH-OA01-VERIFICATION-CORRECTIVE-004, ZH-ZEUS-OA-ADMISSION-001 as a reviewable publication boundary without partial lifecycle state or rewritten evidence.

Validation: scripts/zeus gate receipt OA-01; JSON parse and digest review of OA-01 evidence; git diff --check.
Affected OA gates: OA-01 evidence only; acceptance already occurred.
Related investigations: none.
Controlled-document impact: Evidence-only; no controlled-document revision.
```

### PU-04 — docs(oa): preserve OA-02 acceptance evidence

Status: planned. Dependencies: PU-03. Risk: medium.

Publish OA-02 controlled-mission-authority implementation and verification history together with its accepted receipt.

Paths (8):

- `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/decisions/OA-02/accepted.json`
- `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/evidence/OA-02/IMPLEMENTATION.json`
- `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/evidence/OA-02/VERIFICATION.json`
- `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/evidence/OA-02/VERIFIED`
- `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/evidence/OA-02/ZH-OA02-CONTROLLED-MISSION-AUTHORITY-001-COMPLETION.md`
- `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/evidence/OA-02/attempts/2fe7fb97fab8e62a70167a71048cf35de1080fc11b9a6a44f43d5cbcaa9ac92d/IMPLEMENTATION.json`
- `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/evidence/OA-02/attempts/af955eb13c8a91130651c74ca91f6e8cbd6a44ca814926c0ca2f06d1856f5f7d/VERIFICATION.json`
- `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/evidence/OA-02/attempts/af955eb13c8a91130651c74ca91f6e8cbd6a44ca814926c0ca2f06d1856f5f7d/VERIFIED`

Validation:

- `scripts/zeus gate receipt OA-02`
- `JSON parse and digest review of OA-02 evidence`
- `git diff --check`

Prepared commit message:

```text
docs(oa): preserve OA-02 acceptance evidence

Publish OA-02 controlled-mission-authority implementation and verification history together with its accepted receipt.

Engineering rationale: preserve ZH-OA02-CONTROLLED-MISSION-AUTHORITY-001 as a reviewable publication boundary without partial lifecycle state or rewritten evidence.

Validation: scripts/zeus gate receipt OA-02; JSON parse and digest review of OA-02 evidence; git diff --check.
Affected OA gates: OA-02 evidence only; depends on OA-01 history.
Related investigations: none.
Controlled-document impact: Evidence-only; no controlled-document revision.
```

### PU-05 — docs(oa): preserve OA-03 acceptance evidence

Status: planned. Dependencies: PU-04. Risk: medium.

Publish OA-03 mission-contract-discovery implementation, verification, completion report, and accepted receipt.

Paths (7):

- `engineering/evidence/2026-07-29-zh-oa03-mission-contract-discovery-001-completion-report.md`
- `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/decisions/OA-03/accepted.json`
- `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/evidence/OA-03/IMPLEMENTATION.json`
- `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/evidence/OA-03/VERIFICATION.json`
- `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/evidence/OA-03/VERIFIED`
- `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/evidence/OA-03/attempts/d87249a0cc7e04fa895a696a801da5bfe41b04e3b08b04c844ded6890db7237a/VERIFICATION.json`
- `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/evidence/OA-03/attempts/d87249a0cc7e04fa895a696a801da5bfe41b04e3b08b04c844ded6890db7237a/VERIFIED`

Validation:

- `scripts/zeus gate receipt OA-03`
- `JSON parse and digest review of OA-03 evidence`
- `git diff --check`

Prepared commit message:

```text
docs(oa): preserve OA-03 acceptance evidence

Publish OA-03 mission-contract-discovery implementation, verification, completion report, and accepted receipt.

Engineering rationale: preserve ZH-OA03-MISSION-CONTRACT-DISCOVERY-001 as a reviewable publication boundary without partial lifecycle state or rewritten evidence.

Validation: scripts/zeus gate receipt OA-03; JSON parse and digest review of OA-03 evidence; git diff --check.
Affected OA gates: OA-03 evidence only; depends on OA-01 and OA-02 history.
Related investigations: none.
Controlled-document impact: Evidence-only; no controlled-document revision.
```

### PU-06 — docs(oa): preserve OA-04 corrected acceptance chain

Status: planned. Dependencies: PU-05. Risk: high.

Publish OA-04 mission-resolution evidence, all attempts, original and corrected receipts, and explicit supersedence without rewriting history.

Paths (23):

- `engineering/evidence/2026-07-29-zh-oa04-acceptance-replay-corrective-001.md`
- `engineering/evidence/2026-07-29-zh-oa04-contract-conformance-review-001.md`
- `engineering/evidence/2026-07-29-zh-oa04-mission-resolution-001-completion-report.md`
- `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/decisions/OA-04/accepted-59cbfe3e60b09f1483fe165276f3b247577ccc83bcd084ea212fa78689f972c0.json`
- `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/decisions/OA-04/accepted.json`
- `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/decisions/OA-04/superseded-by-contract-correction.json`
- `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/evidence/OA-04/IMPLEMENTATION.json`
- `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/evidence/OA-04/VERIFICATION.json`
- `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/evidence/OA-04/VERIFIED`
- `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/evidence/OA-04/attempts/0b538ce2262bf9a7a33a88e47ebd12b48becfc0a675701fb72e96a5679225e55/VERIFICATION.json`
- `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/evidence/OA-04/attempts/0b538ce2262bf9a7a33a88e47ebd12b48becfc0a675701fb72e96a5679225e55/VERIFIED`
- `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/evidence/OA-04/attempts/1734b9295a029c9ecddb6440cd86d1faf7aee7af1d2269d33180876e0a188b87/VERIFICATION.json`
- `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/evidence/OA-04/attempts/1734b9295a029c9ecddb6440cd86d1faf7aee7af1d2269d33180876e0a188b87/VERIFIED`
- `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/evidence/OA-04/attempts/23cc5af0c6b56b31f1fb92108cac3150fb4d58578f1f148d8e534b9c2335565a/VERIFICATION.json`
- `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/evidence/OA-04/attempts/23cc5af0c6b56b31f1fb92108cac3150fb4d58578f1f148d8e534b9c2335565a/VERIFIED`
- `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/evidence/OA-04/attempts/37cd9ee4f0e0e9a4d91d3289d2a4694ef5da9474dc979293673e9aa68353d7c0/VERIFICATION.json`
- `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/evidence/OA-04/attempts/37cd9ee4f0e0e9a4d91d3289d2a4694ef5da9474dc979293673e9aa68353d7c0/VERIFIED`
- `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/evidence/OA-04/attempts/8996960699a4970b2fda196eecc043ddcda1608ffd3321ee90531cc5c55091e3/VERIFICATION.json`
- `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/evidence/OA-04/attempts/8996960699a4970b2fda196eecc043ddcda1608ffd3321ee90531cc5c55091e3/VERIFIED`
- `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/evidence/OA-04/attempts/95d3457565ff128521e19305444a1e80613598c9a9f51a715eb4ed9d81f03c6f/IMPLEMENTATION.json`
- `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/evidence/OA-04/attempts/cdbf93a74bc687fa622dbea84b011f37d5b0879d95523c7f5c473663cf92deee/IMPLEMENTATION.json`
- `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/evidence/OA-04/attempts/dbbab47a902ee5c431bfd824ef1ead1a9d423e377f3443b258a80724314e97d3/VERIFICATION.json`
- `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/evidence/OA-04/attempts/dbbab47a902ee5c431bfd824ef1ead1a9d423e377f3443b258a80724314e97d3/VERIFIED`

Validation:

- `scripts/zeus gate receipt OA-04`
- `Verify original/corrected receipt and supersedence linkage`
- `JSON parse and digest review of OA-04 evidence`
- `git diff --check`

Prepared commit message:

```text
docs(oa): preserve OA-04 corrected acceptance chain

Publish OA-04 mission-resolution evidence, all attempts, original and corrected receipts, and explicit supersedence without rewriting history.

Engineering rationale: preserve ZH-OA04-MISSION-RESOLUTION-001, ZH-OA04-ACCEPTANCE-REPLAY-CORRECTIVE-001, ZH-OA04-CONTRACT-CONFORMANCE-REVIEW-001 as a reviewable publication boundary without partial lifecycle state or rewritten evidence.

Validation: scripts/zeus gate receipt OA-04; Verify original/corrected receipt and supersedence linkage; JSON parse and digest review of OA-04 evidence; git diff --check.
Affected OA gates: OA-04 corrected evidence chain only.
Related investigations: none.
Controlled-document impact: Evidence-only; supersedence record is additive and immutable.
```

### PU-07 — docs(oa): preserve OA-05 staging acceptance evidence

Status: planned. Dependencies: PU-06. Risk: medium.

Publish OA-05 staging and mission-count investigation evidence, Stage 1 completion record, attempts, and accepted receipt.

Paths (10):

- `engineering/evidence/2026-07-28-zeus-operational-alpha-stage1-completion-report.md`
- `engineering/evidence/2026-07-29-zh-oa05-contract-conformance-review-001.md`
- `engineering/evidence/2026-07-29-zh-oa05-mission-count-investigation-001.md`
- `engineering/evidence/2026-07-29-zh-oa05-mission-staging-001-completion-report.md`
- `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/decisions/OA-05/accepted-31c196a0ef998f1e9cc59988eac81eaa015d134bf1a1ee1a9d15cb401d274be9.json`
- `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/evidence/OA-05/IMPLEMENTATION.json`
- `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/evidence/OA-05/VERIFICATION.json`
- `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/evidence/OA-05/VERIFIED`
- `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/evidence/OA-05/attempts/1c96738d313cb6f3759be8f3c62e44da199bc85cd3b1aec61918964ad639fa62/VERIFICATION.json`
- `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/evidence/OA-05/attempts/1c96738d313cb6f3759be8f3c62e44da199bc85cd3b1aec61918964ad639fa62/VERIFIED`

Validation:

- `scripts/zeus gate receipt OA-05`
- `python3 scripts/tests/test-zeus-mission-count-status.py`
- `JSON parse and digest review of OA-05 evidence`
- `git diff --check`

Prepared commit message:

```text
docs(oa): preserve OA-05 staging acceptance evidence

Publish OA-05 staging and mission-count investigation evidence, Stage 1 completion record, attempts, and accepted receipt.

Engineering rationale: preserve ZH-OA05-MISSION-STAGING-001, ZH-OA05-MISSION-COUNT-INVESTIGATION-001, ZH-001 Stage 1 as a reviewable publication boundary without partial lifecycle state or rewritten evidence.

Validation: scripts/zeus gate receipt OA-05; python3 scripts/tests/test-zeus-mission-count-status.py; JSON parse and digest review of OA-05 evidence; git diff --check.
Affected OA gates: OA-05 evidence only; OA-06 remains pending.
Related investigations: ZH-OA05-MISSION-COUNT-INVESTIGATION-001.
Controlled-document impact: Evidence-only; no controlled-document revision.
```

### PU-08 — chore(zeus): reconcile OA-06 pending state projection

Status: planned. Dependencies: PU-01, PU-02, PU-03, PU-04, PU-05, PU-06, PU-07. Risk: high.

Atomically publish Project State, Work Registry revision 85, OA progress, runtime state, and their count-sensitive regressions after all accepted receipts exist.

Paths (6):

- `docs/project/PROJ-0001-PROJECT_STATE.md`
- `engineering/operations/zeus-operational-alpha-progress.md`
- `engineering/registry/work-registry.yaml`
- `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/state.json`
- `scripts/tests/test-emp-registry.py`
- `scripts/tests/test-zeus-mission-assurance.py`

Validation:

- `scripts/zeus status --json`
- `scripts/engctl registry validate`
- `scripts/engctl eos sync-validate homelab`
- `scripts/engctl platform validate homelab`
- `python3 scripts/tests/test-emp-registry.py`
- `python3 scripts/tests/test-zeus-mission-assurance.py`
- `bash scripts/verify.sh`
- `git diff --check`

Prepared commit message:

```text
chore(zeus): reconcile OA-06 pending state projection

Atomically publish Project State, Work Registry revision 85, OA progress, runtime state, and their count-sensitive regressions after all accepted receipts exist.

Engineering rationale: preserve Progressive OA state reconciliation, ZH-OA05-MISSION-COUNT-INVESTIGATION-001 as a reviewable publication boundary without partial lifecycle state or rewritten evidence.

Validation: scripts/zeus status --json; scripts/engctl registry validate; scripts/engctl eos sync-validate homelab; scripts/engctl platform validate homelab; python3 scripts/tests/test-emp-registry.py; python3 scripts/tests/test-zeus-mission-assurance.py; bash scripts/verify.sh; git diff --check.
Affected OA gates: Projects OA-01..OA-05 ACCEPTED and OA-06 PENDING; performs no transition.
Related investigations: ZH-OA05-MISSION-COUNT-INVESTIGATION-001.
Controlled-document impact: Updates PROJ-0001 state projection; registry/progress/runtime/test paths must publish together.
```

### PU-09 — docs(evidence): preserve working-tree reconciliation audit

Status: planned. Dependencies: PU-08. Risk: low.

Publish the historical working-tree reconciliation report and its original digest inventory after the candidate they describe has been published and synchronized.

Paths (2):

- `engineering/evidence/2026-07-29-zh-working-tree-reconciliation-001.md`
- `engineering/evidence/2026-07-29-zh-working-tree-reconciliation-001-inventory.json`

Validation:

- `python3 -m json.tool engineering/evidence/2026-07-29-zh-working-tree-reconciliation-001-inventory.json`
- `verify historical inventory internal consistency`
- `git diff --check`

Prepared commit message:

```text
docs(evidence): preserve working-tree reconciliation audit

Publish the historical working-tree reconciliation report and its original digest inventory after the candidate they describe has been published and synchronized.

Engineering rationale: preserve ZH-WORKING-TREE-RECONCILIATION-001 as an independently reviewable historical audit boundary.

Validation: parse the historical inventory; verify its internal consistency; git diff --check.
Affected OA gates: No gate impact.
Related investigations: none.
Controlled-document impact: Evidence-only; no controlled-document revision.
```

## Boundary validation

- Initial Validation Boundary: before PU-01A; verify exact manifest membership/digests, repository health, registry, package applicability, empty index, and read-only EOS comparison.
- Publication Boundaries: validate and commit only the exact unit path set; classify intermediate EOS differences as `EXPECTED_PUBLICATION_DRIFT` when repository evidence supports it.
- Synchronization Boundary: after PU-08 only; require separate synchronization authority and prerequisites, then verify exact EOS projection/runtime.
- Final Validation Boundary: after PU-09; run the corrected procedure’s complete repository, registry, package, diff, EOS, and integrated-platform checks.

Any content, HEAD, upstream, receipt, lifecycle, or digest movement invalidates this plan and requires re-initiation. No Operational Alpha declaration or baseline freeze is included.
