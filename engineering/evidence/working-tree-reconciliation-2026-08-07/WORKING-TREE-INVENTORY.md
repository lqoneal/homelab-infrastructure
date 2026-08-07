# Working-Tree Inventory and Starting Snapshot

## Baseline

- Repository root: `/data/engineering/repositories/homelab`
- Canonical remote: `origin git@github.com:lqoneal/homelab-infrastructure.git`
- Branch: `main`
- Starting HEAD: `e7e77eb16b6bb87a9370d611cdde881ce8cf3165`
- Starting `origin/main`: `e7e77eb16b6bb87a9370d611cdde881ce8cf3165`
- Starting HEAD/origin relationship: equal; fetch was attempted but failed because SSH denied access (`Permission denied (publickey)`)
- Starting EOS state: `/data/engineering/eos/state/EOS-STATE.md`, project `homelab`, commit `e7e77eb...`; EOS state validation PASS; sync-status `drifted (checkpoint 64394a57015f, repository e7e77eb16b6b)`
- No stash, reset, checkout, restore, clean, deletion, or synchronization was performed before this package.

## Starting counts

- Git porcelain-v2 entries: 72 (49 tracked modified entries plus 23 collapsed untracked directory entries)
- Expanded dirty regular files: 86
- Tracked modified: 49
- Tracked deleted: 0
- Staged: 0
- Untracked regular files: 37
- Untracked directories inventoried: 14

## Exact starting command outputs

### git status --porcelain=v2
```
1 .M N... 100644 100644 100644 7d1d67d8b7f0561c301a72b0b3043c85fb369e9b 7d1d67d8b7f0561c301a72b0b3043c85fb369e9b docs/architecture/ADR-0001-ZEUS-CANONICAL-ARCHITECTURE-DECISION.md
1 .M N... 100644 100644 100644 50709e6c96a2a9b47076b2b1679c5b121f7a87d7 50709e6c96a2a9b47076b2b1679c5b121f7a87d7 docs/emp/EMP-0001-ENGINEERING_MANAGEMENT_PLATFORM_ARCHITECTURE.md
1 .M N... 100644 100644 100644 b7ff61977bd252915d6397288bdc78236ae8dbd9 b7ff61977bd252915d6397288bdc78236ae8dbd9 docs/policies/POL-0001-ENGINEERING_GOVERNANCE_POLICY.md
1 .M N... 100644 100644 100644 70e8666b4af8b570aa1bccb762f932cdb3b3d7fa 70e8666b4af8b570aa1bccb762f932cdb3b3d7fa docs/procedures/PROC-0001-ENGINEERING_WORK_ORDER_EXECUTION_PROCEDURE.md
1 .M N... 100644 100644 100644 90e007e55d5a99bddd8f560432af2d3ee8c53498 90e007e55d5a99bddd8f560432af2d3ee8c53498 docs/procedures/PROC-0003-ENGINEERING_RECOVERY_RUNBOOK.md
1 .M N... 100644 100644 100644 e8e0debe9bd0ad070d634acc9eb6e7dec7ce709a e8e0debe9bd0ad070d634acc9eb6e7dec7ce709a docs/procedures/PROC-0005-CONTROLLED_DOCUMENT_PUBLICATION_PROCEDURE.md
1 .M N... 100644 100644 100644 9d9566581d90e32b1b5851ff9fb9f6318d001f4f 9d9566581d90e32b1b5851ff9fb9f6318d001f4f docs/procedures/PROC-0007-GOVERNANCE-STABILIZATION-PROCEDURE.md
1 .M N... 100644 100644 100644 2605ee40d719d5af63e1b254ba4ce8cffcc69b0e 2605ee40d719d5af63e1b254ba4ce8cffcc69b0e docs/procedures/PROC-0008-ENGINEERING_GOVERNANCE_DECISION_PROCEDURE.md
1 .M N... 100644 100644 100644 f5370790e5b04b62ab9961186dce89765168330d f5370790e5b04b62ab9961186dce89765168330d docs/specifications/SPEC-0001-CONTROLLED_DOCUMENT_MODEL.md
1 .M N... 100644 100644 100644 07ea6139be7fc3ca3225e0b4e7fb55dacccac517 07ea6139be7fc3ca3225e0b4e7fb55dacccac517 docs/specifications/SPEC-0002-ZEUS-CANONICAL-ARCHITECTURE-SPECIFICATION.md
1 .M N... 100644 100644 100644 63bc923ce57f6bf76760561fa03ea4900e63fbda 63bc923ce57f6bf76760561fa03ea4900e63fbda docs/specifications/SPEC-0005-ENGINEERING_CONTROL_FRAMEWORK.md
1 .M N... 100644 100644 100644 688b5a23e90e584e6e6a283fbf6e2bc74013618b 688b5a23e90e584e6e6a283fbf6e2bc74013618b docs/specifications/SPEC-0007-ENGINEERING-PLATFORM-CONSTRUCTION-SPECIFICATION.md
1 .M N... 100644 100644 100644 df04faa73f4293abe85c087c8782f7ef9ea649f2 df04faa73f4293abe85c087c8782f7ef9ea649f2 docs/specifications/SPEC-0010-ENGINEERING-KNOWLEDGE-REPOSITORY-ARCHITECTURE.md
1 .M N... 100644 100644 100644 4715a68a396c27aefa9c290987cb1e4ab8dede22 4715a68a396c27aefa9c290987cb1e4ab8dede22 docs/specifications/SPEC-0012-PRODUCTION-EXECUTION-FOUNDATION.md
1 .M N... 100644 100644 100644 922a2ffb0d9a57dd1a9c7dd59f59e9bac7a4a0ee 922a2ffb0d9a57dd1a9c7dd59f59e9bac7a4a0ee docs/specifications/SPEC-0014-OPERATIONAL-ALPHA-CONVERGENCE-AUTHORITY.md
1 .M N... 100644 100644 100644 5d5d9b6a2d8cd377b22c199597f9537001e4bada 5d5d9b6a2d8cd377b22c199597f9537001e4bada docs/standards/STD-0000-ENGINEERING_GOVERNANCE_DOCUMENTATION_ARCHITECTURE.md
1 .M N... 100644 100644 100644 b0e821a703522fbde3638be44f1da8a315884c64 b0e821a703522fbde3638be44f1da8a315884c64 docs/standards/STD-0001-ENGINEERING_DOCUMENT_LIFECYCLE_STANDARD.md
1 .M N... 100644 100644 100644 b3e93dba2a2e31787f586dd941da4a60657aaff3 b3e93dba2a2e31787f586dd941da4a60657aaff3 docs/standards/STD-0003-ENGINEERING_WORK_ORDER_STANDARD.md
1 .M N... 100644 100644 100644 fce2ba86ed38b6c16b4a8beda4b68f7b4177359c fce2ba86ed38b6c16b4a8beda4b68f7b4177359c engineering/admission/admission-record.schema.yaml
1 .M N... 100644 100644 100644 bc5d621977ec693a0fced177dc43e02351cb5801 bc5d621977ec693a0fced177dc43e02351cb5801 engineering/admission/wop-submission.schema.yaml
1 .M N... 100644 100644 100644 db0a336826e4bcec0d3171b6605b26106fdd036c db0a336826e4bcec0d3171b6605b26106fdd036c engineering/authority/manual-governance-wop-authority-policy.yaml
1 .M N... 100644 100644 100644 7e0392ebd87efa32596cc67b16a8072dd43de869 7e0392ebd87efa32596cc67b16a8072dd43de869 engineering/docs/architecture/OPERATION-BETA-CANONICAL-GATE-CATALOG.md
1 .M N... 100644 100644 100644 3c55fc8f16b8ba9500f658b7fdb1f70e194b707e 3c55fc8f16b8ba9500f658b7fdb1f70e194b707e engineering/docs/architecture/WOP-SCHEMA-AND-EXECUTION-INTERFACE.md
1 .M N... 100644 100644 100644 906c02b7b7da902bff25deb610f0c6065bafb074 906c02b7b7da902bff25deb610f0c6065bafb074 engineering/docs/operations/ZEUS-DEVELOPMENT-MODE.md
1 .M N... 100644 100644 100644 1d7ced0e781051fc3a23b89f96e69d2110befe76 1d7ced0e781051fc3a23b89f96e69d2110befe76 engineering/docs/operations/ZEUS-EXECUTION-LIFECYCLE-PROCEDURE.md
1 .M N... 100644 100644 100644 fd008c88eabbdef5d9a72793868c8e96b7a4b989 fd008c88eabbdef5d9a72793868c8e96b7a4b989 engineering/evidence/operation-beta/OPERATION-BETA-CANONICAL-GATE-CATALOG.yaml
1 .M N... 100644 100644 100644 9ba15427e9443f2d86f3ec2404ff8ba74e439bcc 9ba15427e9443f2d86f3ec2404ff8ba74e439bcc engineering/metadata/operational-alpha-emm.yaml
1 .M N... 100644 100644 100644 35b908a4f947b74f3f6d5a3524ce5b1ed57650d2 35b908a4f947b74f3f6d5a3524ce5b1ed57650d2 engineering/operations/authority-ownership-specification.md
1 .M N... 100644 100644 100644 6904650f1ab3ea9155d118e2d215939076c82902 6904650f1ab3ea9155d118e2d215939076c82902 engineering/operations/repository-authority-model.md
1 .M N... 100644 100644 100644 d36277672f2d5bade4939eb5adde01acf3ab1fcf d36277672f2d5bade4939eb5adde01acf3ab1fcf engineering/operations/zeus-mission-admission-runtime.md
1 .M N... 100644 100644 100644 0e73a7b4480febbf4b0f80fff42eda0001482806 0e73a7b4480febbf4b0f80fff42eda0001482806 engineering/operations/zeus-operational-alpha-progress.md
1 .M N... 100644 100644 100644 06857c7812e7c0147cf9e0112370b8dc6277332b 06857c7812e7c0147cf9e0112370b8dc6277332b engineering/operations/zeus-operational-runtime.md
1 .M N... 100644 100644 100644 9f3e0c0c8f60129292b4c7906078c3f656a766a7 9f3e0c0c8f60129292b4c7906078c3f656a766a7 engineering/operations/zeus-operator-interface.md
1 .M N... 100644 100644 100644 dae0b7275715d281d7a54e665c3260524db419ad dae0b7275715d281d7a54e665c3260524db419ad scripts/lib/emp/canonical_runtime_mission.py
1 .M N... 100644 100644 100644 14fe1a382bdfa3c4bc566dc78fbcc25f761dda96 14fe1a382bdfa3c4bc566dc78fbcc25f761dda96 scripts/lib/emp/codex_adapter.py
1 .M N... 100644 100644 100644 0588c53533861ac05c21194d001685ac046ac0dd 0588c53533861ac05c21194d001685ac046ac0dd scripts/lib/emp/execution_monitoring.py
1 .M N... 100644 100644 100644 27e49ddeae7d89e233e52e08b7ca04f1e7c66f39 27e49ddeae7d89e233e52e08b7ca04f1e7c66f39 scripts/lib/emp/mission_verification_controller.py
1 .M N... 100644 100644 100644 5c00e10a1d62c212b4cfc34ac92a71b805295a14 5c00e10a1d62c212b4cfc34ac92a71b805295a14 scripts/lib/emp/stage1_runtime.py
1 .M N... 100644 100644 100644 3c6b2fcd08e1340a593cc47cf7797ccc4c5ecc58 3c6b2fcd08e1340a593cc47cf7797ccc4c5ecc58 scripts/lib/emp/wop_admission.py
1 .M N... 100644 100644 100644 24907370e24d0c7215473aff806b5f30ea3b69cb 24907370e24d0c7215473aff806b5f30ea3b69cb scripts/lib/emp/wop_packaging.py
1 .M N... 100644 100644 100644 1b7a63285cb7fff925323cd32b563f9e40290227 1b7a63285cb7fff925323cd32b563f9e40290227 scripts/lib/emp/wop_schema.py
1 .M N... 100644 100644 100644 b6188c2e08c436e3c08be679a4cba30e89b8e01d b6188c2e08c436e3c08be679a4cba30e89b8e01d scripts/lib/eos/convergence_runtime.py
1 .M N... 100644 100644 100644 eec39c04536df4a0ab84a930e7788ac32952aac6 eec39c04536df4a0ab84a930e7788ac32952aac6 scripts/tests/test-convergence-runtime.py
1 .M N... 100644 100644 100644 a8b9118c2c946167075fc7f7826b0a472bd4d2a4 a8b9118c2c946167075fc7f7826b0a472bd4d2a4 scripts/tests/test-wop-admission.py
1 .M N... 100644 100644 100644 5649d8bbeb9debd68acb9c8f455e25ef725efbc2 5649d8bbeb9debd68acb9c8f455e25ef725efbc2 scripts/tests/test-zeus-development-mode-recovery.py
1 .M N... 100644 100644 100644 2dc23a0e2e60fcc7756314dbb73b7664cac60969 2dc23a0e2e60fcc7756314dbb73b7664cac60969 scripts/tests/test-zeus-p5-g5-execution-start.py
1 .M N... 100644 100644 100644 b1e53a86e0c111177ad8ad92b83ecea590a93634 b1e53a86e0c111177ad8ad92b83ecea590a93634 scripts/tests/test-zeus-p5-g6-codex-adapter.py
1 .M N... 100755 100755 100755 c273a374999402a10e326b9fc4bc7b08034346f4 c273a374999402a10e326b9fc4bc7b08034346f4 scripts/validate_controlled_documents.py
1 .M N... 100755 100755 100755 53c904183be69233e8ea574a685bac236a3b6ab3 53c904183be69233e8ea574a685bac236a3b6ab3 scripts/zeus
? docs/procedures/PROC-0009-ROADMAP_PLANNING_RECORDING_PROCEDURE.md
? engineering/docs/architecture/ZEUS-ROADMAP-INTEGRATION-ROADMAP.md
? engineering/evidence/2026-08-07-wop-submission-authority-convergence-001/
? engineering/evidence/operation-beta/CANONICAL-WOP-ZEUS-LIFECYCLE-INTEGRATION-ASSESSMENT.md
? engineering/evidence/operation-beta/CM-01-CM-06-CANONICAL-ZEUS-ROADMAP-INTEGRATION-ASSESSMENT.md
? engineering/evidence/operation-beta/EENS-CURRENT-STATE-AND-DEVELOPMENT-ROADMAP-ASSESSMENT.md
? engineering/evidence/operation-beta/EMP-CENTRALIZED-ENGINEERING-MANAGEMENT-PLATFORM-ASSESSMENT.md
? engineering/evidence/operation-beta/OB-CAGF-G01-IMPLEMENTATION-SPECIFICATION.md
? engineering/evidence/operation-beta/OPERATION-BETA-CONVERGENCE-AUTHORITY-AND-ROADMAP-RECONCILIATION.md
? engineering/evidence/operation-beta/OPERATION-BETA-INDEPENDENT-MISSION-AUTHORITY-AND-CONTROLLED-DOCUMENT-RECONCILIATION.md
? engineering/evidence/operation-beta/OPERATION-BETA-MISSION-CONVERGENCE-AND-EXECUTION-PATH-ASSESSMENT.md
? engineering/evidence/operation-beta/P5-G7-BETA-04-CAGF-01-AUTHORITATIVE-POSITION-AND-MISSION-ORDERING-ASSESSMENT.md
? engineering/evidence/operation-beta/WOP-MANAGED-HANDOFF-CONVERGENCE-ASSESSMENT.md
? engineering/evidence/operation-beta/ZEUS-CM-EENS-EMP-INTEGRATED-ROADMAP-RECONCILIATION-ASSESSMENT.md
? engineering/evidence/operation-beta/beta-test-runtime-source-corrective-001/
? engineering/evidence/operation-beta/phase-5-capability-reconciliation-001/
? engineering/evidence/operation-beta/roadmap-classification-recording-corrective-001/
? engineering/evidence/operation-beta/roadmap-procedure-maturity-inspection-001/
? engineering/evidence/operation-beta/roadmap-recording-procedure-evaluation-001/
? engineering/evidence/operation-beta/wop-contract-convergence-001/
? engineering/evidence/operation-beta/wop-package-maturity-assessment-001/
? engineering/work-orders/WOP-OB-CAGF-G01-CANONICAL-001/canonical-c7a90c8854c170474d210594/
? scripts/tests/test-wop-submission-authority-convergence.py
```

### git diff --stat
```
 ...DR-0001-ZEUS-CANONICAL-ARCHITECTURE-DECISION.md |   6 +-
 ...ENGINEERING_MANAGEMENT_PLATFORM_ARCHITECTURE.md |  10 +-
 .../POL-0001-ENGINEERING_GOVERNANCE_POLICY.md      |  18 ++--
 ...1-ENGINEERING_WORK_ORDER_EXECUTION_PROCEDURE.md |  44 ++++-----
 .../PROC-0003-ENGINEERING_RECOVERY_RUNBOOK.md      |   8 +-
 ...05-CONTROLLED_DOCUMENT_PUBLICATION_PROCEDURE.md |  27 +++---
 ...PROC-0007-GOVERNANCE-STABILIZATION-PROCEDURE.md |   4 +-
 ...08-ENGINEERING_GOVERNANCE_DECISION_PROCEDURE.md |   9 +-
 .../SPEC-0001-CONTROLLED_DOCUMENT_MODEL.md         |  15 +--
 ...02-ZEUS-CANONICAL-ARCHITECTURE-SPECIFICATION.md |  10 ++
 .../SPEC-0005-ENGINEERING_CONTROL_FRAMEWORK.md     |  19 ++--
 ...INEERING-PLATFORM-CONSTRUCTION-SPECIFICATION.md |  18 ++--
 ...NGINEERING-KNOWLEDGE-REPOSITORY-ARCHITECTURE.md |   6 +-
 .../SPEC-0012-PRODUCTION-EXECUTION-FOUNDATION.md   |  22 +++--
 ...0014-OPERATIONAL-ALPHA-CONVERGENCE-AUTHORITY.md |  68 +++++++------
 ...EERING_GOVERNANCE_DOCUMENTATION_ARCHITECTURE.md |  20 +++-
 ...0001-ENGINEERING_DOCUMENT_LIFECYCLE_STANDARD.md |   9 +-
 .../STD-0003-ENGINEERING_WORK_ORDER_STANDARD.md    |  37 ++++----
 engineering/admission/admission-record.schema.yaml |   1 -
 engineering/admission/wop-submission.schema.yaml   |  23 ++++-
 .../manual-governance-wop-authority-policy.yaml    |  37 +++++---
 .../OPERATION-BETA-CANONICAL-GATE-CATALOG.md       |  37 ++++++++
 .../WOP-SCHEMA-AND-EXECUTION-INTERFACE.md          |  24 +++--
 .../docs/operations/ZEUS-DEVELOPMENT-MODE.md       |  13 ++-
 .../ZEUS-EXECUTION-LIFECYCLE-PROCEDURE.md          |  18 +++-
 .../OPERATION-BETA-CANONICAL-GATE-CATALOG.yaml     |  24 ++---
 engineering/metadata/operational-alpha-emm.yaml    |   4 +-
 .../authority-ownership-specification.md           |  19 ++--
 .../operations/repository-authority-model.md       |   9 +-
 .../operations/zeus-mission-admission-runtime.md   |  27 +++---
 .../operations/zeus-operational-alpha-progress.md  |   4 +-
 engineering/operations/zeus-operational-runtime.md |  19 ++--
 engineering/operations/zeus-operator-interface.md  |   8 +-
 scripts/lib/emp/canonical_runtime_mission.py       |   3 +
 scripts/lib/emp/codex_adapter.py                   |  24 ++---
 scripts/lib/emp/execution_monitoring.py            |  12 +++
 scripts/lib/emp/mission_verification_controller.py |   3 +
 scripts/lib/emp/stage1_runtime.py                  |  29 +++---
 scripts/lib/emp/wop_admission.py                   |  32 ++++---
 scripts/lib/emp/wop_packaging.py                   |  24 ++---
 scripts/lib/emp/wop_schema.py                      |  17 ++--
 scripts/lib/eos/convergence_runtime.py             | 105 +++++++++++----------
 scripts/tests/test-convergence-runtime.py          |   8 +-
 scripts/tests/test-wop-admission.py                |   2 +-
 .../tests/test-zeus-development-mode-recovery.py   |  29 +++++-
 scripts/tests/test-zeus-p5-g5-execution-start.py   |  15 +++
 scripts/tests/test-zeus-p5-g6-codex-adapter.py     |   4 +-
 scripts/validate_controlled_documents.py           |   6 ++
 scripts/zeus                                       |  16 +++-
 49 files changed, 589 insertions(+), 357 deletions(-)
```

### git diff --name-status
```
M	docs/architecture/ADR-0001-ZEUS-CANONICAL-ARCHITECTURE-DECISION.md
M	docs/emp/EMP-0001-ENGINEERING_MANAGEMENT_PLATFORM_ARCHITECTURE.md
M	docs/policies/POL-0001-ENGINEERING_GOVERNANCE_POLICY.md
M	docs/procedures/PROC-0001-ENGINEERING_WORK_ORDER_EXECUTION_PROCEDURE.md
M	docs/procedures/PROC-0003-ENGINEERING_RECOVERY_RUNBOOK.md
M	docs/procedures/PROC-0005-CONTROLLED_DOCUMENT_PUBLICATION_PROCEDURE.md
M	docs/procedures/PROC-0007-GOVERNANCE-STABILIZATION-PROCEDURE.md
M	docs/procedures/PROC-0008-ENGINEERING_GOVERNANCE_DECISION_PROCEDURE.md
M	docs/specifications/SPEC-0001-CONTROLLED_DOCUMENT_MODEL.md
M	docs/specifications/SPEC-0002-ZEUS-CANONICAL-ARCHITECTURE-SPECIFICATION.md
M	docs/specifications/SPEC-0005-ENGINEERING_CONTROL_FRAMEWORK.md
M	docs/specifications/SPEC-0007-ENGINEERING-PLATFORM-CONSTRUCTION-SPECIFICATION.md
M	docs/specifications/SPEC-0010-ENGINEERING-KNOWLEDGE-REPOSITORY-ARCHITECTURE.md
M	docs/specifications/SPEC-0012-PRODUCTION-EXECUTION-FOUNDATION.md
M	docs/specifications/SPEC-0014-OPERATIONAL-ALPHA-CONVERGENCE-AUTHORITY.md
M	docs/standards/STD-0000-ENGINEERING_GOVERNANCE_DOCUMENTATION_ARCHITECTURE.md
M	docs/standards/STD-0001-ENGINEERING_DOCUMENT_LIFECYCLE_STANDARD.md
M	docs/standards/STD-0003-ENGINEERING_WORK_ORDER_STANDARD.md
M	engineering/admission/admission-record.schema.yaml
M	engineering/admission/wop-submission.schema.yaml
M	engineering/authority/manual-governance-wop-authority-policy.yaml
M	engineering/docs/architecture/OPERATION-BETA-CANONICAL-GATE-CATALOG.md
M	engineering/docs/architecture/WOP-SCHEMA-AND-EXECUTION-INTERFACE.md
M	engineering/docs/operations/ZEUS-DEVELOPMENT-MODE.md
M	engineering/docs/operations/ZEUS-EXECUTION-LIFECYCLE-PROCEDURE.md
M	engineering/evidence/operation-beta/OPERATION-BETA-CANONICAL-GATE-CATALOG.yaml
M	engineering/metadata/operational-alpha-emm.yaml
M	engineering/operations/authority-ownership-specification.md
M	engineering/operations/repository-authority-model.md
M	engineering/operations/zeus-mission-admission-runtime.md
M	engineering/operations/zeus-operational-alpha-progress.md
M	engineering/operations/zeus-operational-runtime.md
M	engineering/operations/zeus-operator-interface.md
M	scripts/lib/emp/canonical_runtime_mission.py
M	scripts/lib/emp/codex_adapter.py
M	scripts/lib/emp/execution_monitoring.py
M	scripts/lib/emp/mission_verification_controller.py
M	scripts/lib/emp/stage1_runtime.py
M	scripts/lib/emp/wop_admission.py
M	scripts/lib/emp/wop_packaging.py
M	scripts/lib/emp/wop_schema.py
M	scripts/lib/eos/convergence_runtime.py
M	scripts/tests/test-convergence-runtime.py
M	scripts/tests/test-wop-admission.py
M	scripts/tests/test-zeus-development-mode-recovery.py
M	scripts/tests/test-zeus-p5-g5-execution-start.py
M	scripts/tests/test-zeus-p5-g6-codex-adapter.py
M	scripts/validate_controlled_documents.py
M	scripts/zeus
```

### git diff --numstat
```
3	3	docs/architecture/ADR-0001-ZEUS-CANONICAL-ARCHITECTURE-DECISION.md
6	4	docs/emp/EMP-0001-ENGINEERING_MANAGEMENT_PLATFORM_ARCHITECTURE.md
9	9	docs/policies/POL-0001-ENGINEERING_GOVERNANCE_POLICY.md
22	22	docs/procedures/PROC-0001-ENGINEERING_WORK_ORDER_EXECUTION_PROCEDURE.md
5	3	docs/procedures/PROC-0003-ENGINEERING_RECOVERY_RUNBOOK.md
16	11	docs/procedures/PROC-0005-CONTROLLED_DOCUMENT_PUBLICATION_PROCEDURE.md
3	1	docs/procedures/PROC-0007-GOVERNANCE-STABILIZATION-PROCEDURE.md
5	4	docs/procedures/PROC-0008-ENGINEERING_GOVERNANCE_DECISION_PROCEDURE.md
9	6	docs/specifications/SPEC-0001-CONTROLLED_DOCUMENT_MODEL.md
10	0	docs/specifications/SPEC-0002-ZEUS-CANONICAL-ARCHITECTURE-SPECIFICATION.md
11	8	docs/specifications/SPEC-0005-ENGINEERING_CONTROL_FRAMEWORK.md
12	6	docs/specifications/SPEC-0007-ENGINEERING-PLATFORM-CONSTRUCTION-SPECIFICATION.md
4	2	docs/specifications/SPEC-0010-ENGINEERING-KNOWLEDGE-REPOSITORY-ARCHITECTURE.md
13	9	docs/specifications/SPEC-0012-PRODUCTION-EXECUTION-FOUNDATION.md
33	35	docs/specifications/SPEC-0014-OPERATIONAL-ALPHA-CONVERGENCE-AUTHORITY.md
16	4	docs/standards/STD-0000-ENGINEERING_GOVERNANCE_DOCUMENTATION_ARCHITECTURE.md
7	2	docs/standards/STD-0001-ENGINEERING_DOCUMENT_LIFECYCLE_STANDARD.md
19	18	docs/standards/STD-0003-ENGINEERING_WORK_ORDER_STANDARD.md
0	1	engineering/admission/admission-record.schema.yaml
19	4	engineering/admission/wop-submission.schema.yaml
23	14	engineering/authority/manual-governance-wop-authority-policy.yaml
37	0	engineering/docs/architecture/OPERATION-BETA-CANONICAL-GATE-CATALOG.md
14	10	engineering/docs/architecture/WOP-SCHEMA-AND-EXECUTION-INTERFACE.md
8	5	engineering/docs/operations/ZEUS-DEVELOPMENT-MODE.md
17	1	engineering/docs/operations/ZEUS-EXECUTION-LIFECYCLE-PROCEDURE.md
12	12	engineering/evidence/operation-beta/OPERATION-BETA-CANONICAL-GATE-CATALOG.yaml
2	2	engineering/metadata/operational-alpha-emm.yaml
10	9	engineering/operations/authority-ownership-specification.md
5	4	engineering/operations/repository-authority-model.md
14	13	engineering/operations/zeus-mission-admission-runtime.md
3	1	engineering/operations/zeus-operational-alpha-progress.md
9	10	engineering/operations/zeus-operational-runtime.md
4	4	engineering/operations/zeus-operator-interface.md
3	0	scripts/lib/emp/canonical_runtime_mission.py
10	14	scripts/lib/emp/codex_adapter.py
12	0	scripts/lib/emp/execution_monitoring.py
3	0	scripts/lib/emp/mission_verification_controller.py
17	12	scripts/lib/emp/stage1_runtime.py
21	11	scripts/lib/emp/wop_admission.py
10	14	scripts/lib/emp/wop_packaging.py
10	7	scripts/lib/emp/wop_schema.py
53	52	scripts/lib/eos/convergence_runtime.py
4	4	scripts/tests/test-convergence-runtime.py
1	1	scripts/tests/test-wop-admission.py
28	1	scripts/tests/test-zeus-development-mode-recovery.py
15	0	scripts/tests/test-zeus-p5-g5-execution-start.py
2	2	scripts/tests/test-zeus-p5-g6-codex-adapter.py
6	0	scripts/validate_controlled_documents.py
14	2	scripts/zeus
```

### git diff --cached --name-status
```
(empty)
```

### git ls-files --others --exclude-standard
```
docs/procedures/PROC-0009-ROADMAP_PLANNING_RECORDING_PROCEDURE.md
engineering/docs/architecture/ZEUS-ROADMAP-INTEGRATION-ROADMAP.md
engineering/evidence/2026-08-07-wop-submission-authority-convergence-001/AUTHORITY-MODEL-BEFORE-AFTER.md
engineering/evidence/2026-08-07-wop-submission-authority-convergence-001/COMPLETION-REPORT.md
engineering/evidence/2026-08-07-wop-submission-authority-convergence-001/CONTROLLED-DOCUMENT-INVENTORY.md
engineering/evidence/2026-08-07-wop-submission-authority-convergence-001/NEGATIVE-TESTS.md
engineering/evidence/2026-08-07-wop-submission-authority-convergence-001/PUBLICATION-CANDIDATE-MANIFEST.md
engineering/evidence/2026-08-07-wop-submission-authority-convergence-001/RUNTIME-ENFORCEMENT-CHANGES.md
engineering/evidence/2026-08-07-wop-submission-authority-convergence-001/STARTING-BASELINE.md
engineering/evidence/2026-08-07-wop-submission-authority-convergence-001/VALIDATION-OUTPUT.md
engineering/evidence/2026-08-07-wop-submission-authority-convergence-001/ZEUS-NATIVE-VERIFICATION.md
engineering/evidence/operation-beta/CANONICAL-WOP-ZEUS-LIFECYCLE-INTEGRATION-ASSESSMENT.md
engineering/evidence/operation-beta/CM-01-CM-06-CANONICAL-ZEUS-ROADMAP-INTEGRATION-ASSESSMENT.md
engineering/evidence/operation-beta/EENS-CURRENT-STATE-AND-DEVELOPMENT-ROADMAP-ASSESSMENT.md
engineering/evidence/operation-beta/EMP-CENTRALIZED-ENGINEERING-MANAGEMENT-PLATFORM-ASSESSMENT.md
engineering/evidence/operation-beta/OB-CAGF-G01-IMPLEMENTATION-SPECIFICATION.md
engineering/evidence/operation-beta/OPERATION-BETA-CONVERGENCE-AUTHORITY-AND-ROADMAP-RECONCILIATION.md
engineering/evidence/operation-beta/OPERATION-BETA-INDEPENDENT-MISSION-AUTHORITY-AND-CONTROLLED-DOCUMENT-RECONCILIATION.md
engineering/evidence/operation-beta/OPERATION-BETA-MISSION-CONVERGENCE-AND-EXECUTION-PATH-ASSESSMENT.md
engineering/evidence/operation-beta/P5-G7-BETA-04-CAGF-01-AUTHORITATIVE-POSITION-AND-MISSION-ORDERING-ASSESSMENT.md
engineering/evidence/operation-beta/WOP-MANAGED-HANDOFF-CONVERGENCE-ASSESSMENT.md
engineering/evidence/operation-beta/ZEUS-CM-EENS-EMP-INTEGRATED-ROADMAP-RECONCILIATION-ASSESSMENT.md
engineering/evidence/operation-beta/beta-test-runtime-source-corrective-001/CORRECTIVE-RECORD.md
engineering/evidence/operation-beta/phase-5-capability-reconciliation-001/PHASE-5-CAPABILITY-RECONCILIATION-REPORT.md
engineering/evidence/operation-beta/roadmap-classification-recording-corrective-001/PROC-0009-REPOSITORY-RECONCILIATION-REPORT.md
engineering/evidence/operation-beta/roadmap-classification-recording-corrective-001/ROADMAP-CLASSIFICATION-RECORDING-CORRECTIVE-COMPLETION-REPORT.md
engineering/evidence/operation-beta/roadmap-procedure-maturity-inspection-001/ROADMAP-PROCEDURE-MATURITY-INSPECTION-REPORT.md
engineering/evidence/operation-beta/roadmap-recording-procedure-evaluation-001/ROADMAP-RECORDING-PROCEDURE-EVALUATION-REPORT.md
engineering/evidence/operation-beta/wop-contract-convergence-001/WOP-M1-CANONICAL-CONTRACT-CONVERGENCE-COMPLETION-REPORT.md
engineering/evidence/operation-beta/wop-package-maturity-assessment-001/WOP-PACKAGE-MATURITY-ASSESSMENT.md
engineering/work-orders/WOP-OB-CAGF-G01-CANONICAL-001/canonical-c7a90c8854c170474d210594/bootstrap.md
engineering/work-orders/WOP-OB-CAGF-G01-CANONICAL-001/canonical-c7a90c8854c170474d210594/gates.yaml
engineering/work-orders/WOP-OB-CAGF-G01-CANONICAL-001/canonical-c7a90c8854c170474d210594/manifests/immutable-manifest.yaml
engineering/work-orders/WOP-OB-CAGF-G01-CANONICAL-001/canonical-c7a90c8854c170474d210594/mission.yaml
engineering/work-orders/WOP-OB-CAGF-G01-CANONICAL-001/canonical-c7a90c8854c170474d210594/roadmap.md
engineering/work-orders/WOP-OB-CAGF-G01-CANONICAL-001/canonical-c7a90c8854c170474d210594/source-wop.yaml
scripts/tests/test-wop-submission-authority-convergence.py
```

## SHA-256 for every starting untracked regular file

```
d4b8c9761570ad50cb031deb2d283fc49df47c5b3c9cb6ea087c6a21d781f1d0  docs/procedures/PROC-0009-ROADMAP_PLANNING_RECORDING_PROCEDURE.md
76fa9728c65515fef51ee3b9eba3426ffc951466fb93a741ed700686b8346ae4  engineering/docs/architecture/ZEUS-ROADMAP-INTEGRATION-ROADMAP.md
302a2007e24d50899d18a754334a37fc1c773f82ff50af95789a4c32cd716a3b  engineering/evidence/2026-08-07-wop-submission-authority-convergence-001/AUTHORITY-MODEL-BEFORE-AFTER.md
a9232b40d2765d53d21be576f8eddc4cec209d184eafd66022afc532b098e7ce  engineering/evidence/2026-08-07-wop-submission-authority-convergence-001/COMPLETION-REPORT.md
a9e7555a10f3a240018d754d5ba2ab52bcb76adb8378dddeb95f52e4ec8945cd  engineering/evidence/2026-08-07-wop-submission-authority-convergence-001/CONTROLLED-DOCUMENT-INVENTORY.md
9d0b717f4cabefb4943f586dcc2e94c26249c296ebb3a6629f04870e9e101834  engineering/evidence/2026-08-07-wop-submission-authority-convergence-001/NEGATIVE-TESTS.md
35ec8ad89ffcbc9fdd73d6c837933438381f17831889c557fc5ee0926b9aedec  engineering/evidence/2026-08-07-wop-submission-authority-convergence-001/PUBLICATION-CANDIDATE-MANIFEST.md
5b24128d4fb3fe558297a7bf43fa5d46a5ac1cd1a49fc02454fb945fc229ad4f  engineering/evidence/2026-08-07-wop-submission-authority-convergence-001/RUNTIME-ENFORCEMENT-CHANGES.md
3e21a589bb7d6247b262c5195184fc01cc4956919323e67bef2a73dc92673fb0  engineering/evidence/2026-08-07-wop-submission-authority-convergence-001/STARTING-BASELINE.md
9b2301f532e697dda729ae5ec82f0227746931d1fb3d5b5e6ba0a0aed9612b86  engineering/evidence/2026-08-07-wop-submission-authority-convergence-001/VALIDATION-OUTPUT.md
e616c818fd3afa9c560f604a673792b6f24c292e9771ccf02392ca9d39baa1ca  engineering/evidence/2026-08-07-wop-submission-authority-convergence-001/ZEUS-NATIVE-VERIFICATION.md
fcaf070993cdc997d270549868696a9fe404c998ca8889ee5baa1838da496a38  engineering/evidence/operation-beta/CANONICAL-WOP-ZEUS-LIFECYCLE-INTEGRATION-ASSESSMENT.md
9bc3258becb05f8cd3fab8ead8747eaf9daba7d388345ff1df716621b5799f64  engineering/evidence/operation-beta/CM-01-CM-06-CANONICAL-ZEUS-ROADMAP-INTEGRATION-ASSESSMENT.md
0cb6b290be7b7fe0d4bc37e11bd505cefc65798adb658be7b5af13cc9699c623  engineering/evidence/operation-beta/EENS-CURRENT-STATE-AND-DEVELOPMENT-ROADMAP-ASSESSMENT.md
e27257f171a12198223de93a4f98134dd89b101cb0d8b9da898f1c665d5d4898  engineering/evidence/operation-beta/EMP-CENTRALIZED-ENGINEERING-MANAGEMENT-PLATFORM-ASSESSMENT.md
4f829260b54cfe0e41d0e9136d6d2c9ce64a8d290cb103b7c64e1703fc4f1aed  engineering/evidence/operation-beta/OB-CAGF-G01-IMPLEMENTATION-SPECIFICATION.md
3144e0bda9269c9263f6b80a40699ffd467bfaa60eb8775bfa032b8afdd0568e  engineering/evidence/operation-beta/OPERATION-BETA-CONVERGENCE-AUTHORITY-AND-ROADMAP-RECONCILIATION.md
73813a38750ad069857bb356e8011e2b9e0af5b21bb08961f9de83965f8fd9d6  engineering/evidence/operation-beta/OPERATION-BETA-INDEPENDENT-MISSION-AUTHORITY-AND-CONTROLLED-DOCUMENT-RECONCILIATION.md
7f6e3be7756619bd0cb6acb0a5c20d5211898a6e7adf058212a1452126fdc7f5  engineering/evidence/operation-beta/OPERATION-BETA-MISSION-CONVERGENCE-AND-EXECUTION-PATH-ASSESSMENT.md
26184b7d8858ae8af6992c2173d49db6b09be411cc11fd080bcd85af160fd97e  engineering/evidence/operation-beta/P5-G7-BETA-04-CAGF-01-AUTHORITATIVE-POSITION-AND-MISSION-ORDERING-ASSESSMENT.md
b50864dfffb27e1f1968ce9e27282f15f694bbd4b6ad81ba96d077da7af5c4d7  engineering/evidence/operation-beta/WOP-MANAGED-HANDOFF-CONVERGENCE-ASSESSMENT.md
93c571584c9a045b3a7d8c9ffeed6935afb3bff48d368a5748f4f3b450e08a51  engineering/evidence/operation-beta/ZEUS-CM-EENS-EMP-INTEGRATED-ROADMAP-RECONCILIATION-ASSESSMENT.md
6722af88019ced642865201035ab3d2004a8ab9dfe648a51fce00fe3614987b9  engineering/evidence/operation-beta/beta-test-runtime-source-corrective-001/CORRECTIVE-RECORD.md
f5df7a39be487226dd1ff5a3fbb1be798ab04d88192cb626a1da00b5173db9e0  engineering/evidence/operation-beta/phase-5-capability-reconciliation-001/PHASE-5-CAPABILITY-RECONCILIATION-REPORT.md
80186f004cabdab7e084e5af5afbbf61a41c0c497aa747cd3ef24fcc3e1e94cd  engineering/evidence/operation-beta/roadmap-classification-recording-corrective-001/PROC-0009-REPOSITORY-RECONCILIATION-REPORT.md
e767d35706dc96ef3051fb7468ddbb81315f02b055427349fb754f1c885d5635  engineering/evidence/operation-beta/roadmap-classification-recording-corrective-001/ROADMAP-CLASSIFICATION-RECORDING-CORRECTIVE-COMPLETION-REPORT.md
04a0e6eb0704a08a06c538cf9f5c13c33710bee5fcc2a9dedbde2e3882f7cdc6  engineering/evidence/operation-beta/roadmap-procedure-maturity-inspection-001/ROADMAP-PROCEDURE-MATURITY-INSPECTION-REPORT.md
c30f12644307b5f233a862a2760eb22a44eed5fd6c7f1978d6a5cb20b1f74770  engineering/evidence/operation-beta/roadmap-recording-procedure-evaluation-001/ROADMAP-RECORDING-PROCEDURE-EVALUATION-REPORT.md
9fa2b914febd6f586dac73b6c9e765978fff4a6bf72bb2d4526c56c554b39a35  engineering/evidence/operation-beta/wop-contract-convergence-001/WOP-M1-CANONICAL-CONTRACT-CONVERGENCE-COMPLETION-REPORT.md
b86f2123365e7c3a5a58f0570322bc8a305848bc683412ffe2d3f53bf0cc2805  engineering/evidence/operation-beta/wop-package-maturity-assessment-001/WOP-PACKAGE-MATURITY-ASSESSMENT.md
d17a909946af415d3161fad69a0d71ed7482d99a11f2916a08c9d913e51f7150  engineering/work-orders/WOP-OB-CAGF-G01-CANONICAL-001/canonical-c7a90c8854c170474d210594/bootstrap.md
403ec5f754b2f85afcd8f1081de69d129d77c51dfbea4e1739f42f992e553b59  engineering/work-orders/WOP-OB-CAGF-G01-CANONICAL-001/canonical-c7a90c8854c170474d210594/gates.yaml
159b9a812106f86b8d884dacf81b9742aac6697339a7171ad7cfeafbc3976194  engineering/work-orders/WOP-OB-CAGF-G01-CANONICAL-001/canonical-c7a90c8854c170474d210594/manifests/immutable-manifest.yaml
632e15bcc343cbbbd769006ddd7b60342700aaa319f88b3996b02615ed2aaab2  engineering/work-orders/WOP-OB-CAGF-G01-CANONICAL-001/canonical-c7a90c8854c170474d210594/mission.yaml
df27952c8ea3ef1a06c9c7163c9df490026c018a46aeb88550d941bc1344e425  engineering/work-orders/WOP-OB-CAGF-G01-CANONICAL-001/canonical-c7a90c8854c170474d210594/roadmap.md
70efd25355a8364dd748cbde9376fcf718d6a992f29fbbb982c54c67c539fac2  engineering/work-orders/WOP-OB-CAGF-G01-CANONICAL-001/canonical-c7a90c8854c170474d210594/source-wop.yaml
4c761b779267d05c16e3396c0c75707e98a82cd1a2729fed214020322b119ed2  scripts/tests/test-wop-submission-authority-convergence.py
```

## Starting untracked directory inventory

- `docs/procedures` — entries: docs/procedures/PROC-0009-ROADMAP_PLANNING_RECORDING_PROCEDURE.md
- `engineering/docs/architecture` — entries: engineering/docs/architecture/ZEUS-ROADMAP-INTEGRATION-ROADMAP.md
- `engineering/evidence/2026-08-07-wop-submission-authority-convergence-001` — entries: engineering/evidence/2026-08-07-wop-submission-authority-convergence-001/AUTHORITY-MODEL-BEFORE-AFTER.md, engineering/evidence/2026-08-07-wop-submission-authority-convergence-001/COMPLETION-REPORT.md, engineering/evidence/2026-08-07-wop-submission-authority-convergence-001/CONTROLLED-DOCUMENT-INVENTORY.md, engineering/evidence/2026-08-07-wop-submission-authority-convergence-001/NEGATIVE-TESTS.md, engineering/evidence/2026-08-07-wop-submission-authority-convergence-001/PUBLICATION-CANDIDATE-MANIFEST.md, engineering/evidence/2026-08-07-wop-submission-authority-convergence-001/RUNTIME-ENFORCEMENT-CHANGES.md, engineering/evidence/2026-08-07-wop-submission-authority-convergence-001/STARTING-BASELINE.md, engineering/evidence/2026-08-07-wop-submission-authority-convergence-001/VALIDATION-OUTPUT.md, engineering/evidence/2026-08-07-wop-submission-authority-convergence-001/ZEUS-NATIVE-VERIFICATION.md
- `engineering/evidence/operation-beta` — entries: engineering/evidence/operation-beta/CANONICAL-WOP-ZEUS-LIFECYCLE-INTEGRATION-ASSESSMENT.md, engineering/evidence/operation-beta/CM-01-CM-06-CANONICAL-ZEUS-ROADMAP-INTEGRATION-ASSESSMENT.md, engineering/evidence/operation-beta/EENS-CURRENT-STATE-AND-DEVELOPMENT-ROADMAP-ASSESSMENT.md, engineering/evidence/operation-beta/EMP-CENTRALIZED-ENGINEERING-MANAGEMENT-PLATFORM-ASSESSMENT.md, engineering/evidence/operation-beta/OB-CAGF-G01-IMPLEMENTATION-SPECIFICATION.md, engineering/evidence/operation-beta/OPERATION-BETA-CONVERGENCE-AUTHORITY-AND-ROADMAP-RECONCILIATION.md, engineering/evidence/operation-beta/OPERATION-BETA-INDEPENDENT-MISSION-AUTHORITY-AND-CONTROLLED-DOCUMENT-RECONCILIATION.md, engineering/evidence/operation-beta/OPERATION-BETA-MISSION-CONVERGENCE-AND-EXECUTION-PATH-ASSESSMENT.md, engineering/evidence/operation-beta/P5-G7-BETA-04-CAGF-01-AUTHORITATIVE-POSITION-AND-MISSION-ORDERING-ASSESSMENT.md, engineering/evidence/operation-beta/WOP-MANAGED-HANDOFF-CONVERGENCE-ASSESSMENT.md, engineering/evidence/operation-beta/ZEUS-CM-EENS-EMP-INTEGRATED-ROADMAP-RECONCILIATION-ASSESSMENT.md
- `engineering/evidence/operation-beta/beta-test-runtime-source-corrective-001` — entries: engineering/evidence/operation-beta/beta-test-runtime-source-corrective-001/CORRECTIVE-RECORD.md
- `engineering/evidence/operation-beta/phase-5-capability-reconciliation-001` — entries: engineering/evidence/operation-beta/phase-5-capability-reconciliation-001/PHASE-5-CAPABILITY-RECONCILIATION-REPORT.md
- `engineering/evidence/operation-beta/roadmap-classification-recording-corrective-001` — entries: engineering/evidence/operation-beta/roadmap-classification-recording-corrective-001/PROC-0009-REPOSITORY-RECONCILIATION-REPORT.md, engineering/evidence/operation-beta/roadmap-classification-recording-corrective-001/ROADMAP-CLASSIFICATION-RECORDING-CORRECTIVE-COMPLETION-REPORT.md
- `engineering/evidence/operation-beta/roadmap-procedure-maturity-inspection-001` — entries: engineering/evidence/operation-beta/roadmap-procedure-maturity-inspection-001/ROADMAP-PROCEDURE-MATURITY-INSPECTION-REPORT.md
- `engineering/evidence/operation-beta/roadmap-recording-procedure-evaluation-001` — entries: engineering/evidence/operation-beta/roadmap-recording-procedure-evaluation-001/ROADMAP-RECORDING-PROCEDURE-EVALUATION-REPORT.md
- `engineering/evidence/operation-beta/wop-contract-convergence-001` — entries: engineering/evidence/operation-beta/wop-contract-convergence-001/WOP-M1-CANONICAL-CONTRACT-CONVERGENCE-COMPLETION-REPORT.md
- `engineering/evidence/operation-beta/wop-package-maturity-assessment-001` — entries: engineering/evidence/operation-beta/wop-package-maturity-assessment-001/WOP-PACKAGE-MATURITY-ASSESSMENT.md
- `engineering/work-orders/WOP-OB-CAGF-G01-CANONICAL-001/canonical-c7a90c8854c170474d210594` — entries: engineering/work-orders/WOP-OB-CAGF-G01-CANONICAL-001/canonical-c7a90c8854c170474d210594/bootstrap.md, engineering/work-orders/WOP-OB-CAGF-G01-CANONICAL-001/canonical-c7a90c8854c170474d210594/gates.yaml, engineering/work-orders/WOP-OB-CAGF-G01-CANONICAL-001/canonical-c7a90c8854c170474d210594/mission.yaml, engineering/work-orders/WOP-OB-CAGF-G01-CANONICAL-001/canonical-c7a90c8854c170474d210594/roadmap.md, engineering/work-orders/WOP-OB-CAGF-G01-CANONICAL-001/canonical-c7a90c8854c170474d210594/source-wop.yaml
- `engineering/work-orders/WOP-OB-CAGF-G01-CANONICAL-001/canonical-c7a90c8854c170474d210594/manifests` — entries: engineering/work-orders/WOP-OB-CAGF-G01-CANONICAL-001/canonical-c7a90c8854c170474d210594/manifests/immutable-manifest.yaml
- `scripts/tests` — entries: scripts/tests/test-wop-submission-authority-convergence.py

## Reconciliation package accounting

The five files in this directory were created after the starting snapshot as the
required Phase 8 reconciliation record. They are included exactly once in
`PATH-DISPOSITION.csv`, then will be published as a separate bounded cleanup
record. They are not included in the starting counts above.

## Candidate isolation

- Authority candidate paths listed by manifest: 41
- Authority candidate evidence files under the manifest directory: 9
- Total Class A paths: 50
- Overlap paths requiring exact hunk review: `engineering/admission/wop-submission.schema.yaml`, `engineering/authority/manual-governance-wop-authority-policy.yaml`, `engineering/docs/operations/ZEUS-DEVELOPMENT-MODE.md`, `engineering/docs/operations/ZEUS-EXECUTION-LIFECYCLE-PROCEDURE.md`, `scripts/tests/test-zeus-development-mode-recovery.py`
- Unrelated overlap: no mixed semantic hunk was identified in review; all current hunks in those five paths are authority-convergence edits, but they will be staged with exact-hunk application.
- Manifest equivalence: PASS for the 41 listed paths plus all 9 files in the candidate evidence directory; no non-A path is admitted to Class A.

## Initial validation observations

- `git diff --check`: PASS per candidate evidence.
- Controlled-document validation: repository baseline checks PASS; candidate full run reported 3902 PASS / 105 pre-existing or unrelated failures.
- Semantic, registry, assurance, synchronization, Zeus platform, and integrated failures are classified in candidate `VALIDATION-OUTPUT.md` and `COMPLETION-REPORT.md`.
- Zeus doctor: READY; current platform mission/context is Operation Beta / CAGF-01; no execution started.
