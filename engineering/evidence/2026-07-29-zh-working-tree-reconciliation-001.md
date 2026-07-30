# ZH Working-Tree Reconciliation 001

Date: 2026-07-29  
Handoff: `ZH-WORKING-TREE-RECONCILIATION-001`  
Disposition: `RECONCILED — PRESERVATION CANDIDATE READY FOR HUMAN COMMIT REVIEW`

## 1. Engineering Work Initiation

| Item | Result |
| --- | --- |
| Repository root / identity | `/data/engineering/repositories/homelab`; remote `git@github.com:lqoneal/homelab-infrastructure.git` |
| Branch / upstream | `main` / `origin/main`; ahead 0, behind 0 |
| HEAD | `f79462bd837df51f12a103f2ebc69a071c27f45d` |
| Qualified baseline provenance | Progressive WOP baseline `bcdd0b1a19045654d470bc65383c05a976bae2a6` is an ancestor of HEAD; package at HEAD verifies. The older publication contract baseline `d25d144...` is superseded by the completed publication sequence through HEAD. |
| Project State | `PROJ-0001@9.9`; Zeus Operational Alpha; OA-06 pending |
| Progressive package | `GH-ZEUS-OA-PROGRESSIVE-001`; 30 unique cumulative gates; integrity PASS |
| Accepted receipts | OA-01, OA-02, OA-03, OA-04, OA-05 each integrity PASS |
| Repository health | PASS; modified state explicitly preserved |
| Work Registry | revision 85; 85 objects; schema, hierarchy, state, dependency, and authority validation PASS |
| EOS | repository projection validates; synchronization validation PASS; checkpoint status reports drift from `bcdd0b1a...` to repository HEAD, expected after subsequent committed publication history |
| Infrastructure baseline | `/data/engineering` EOS workspace present; repository, state, checkpoints, staging, tools, and storage usable. Independent verifier reported only optional missing workspace directories and ended with 0 warnings / 0 failures. |
| Mission/execution authority | Active repository record names the already-published `MISSION-CONTRACT-PUBLICATION-001`; repository log proves its publication/closeout sequence is at HEAD. This handoff is separate, narrower reconciliation authority and grants no commit/push or lifecycle mutation. |
| Unauthorized execution | No live Stage 1 mission records; mission count 0; no submission, dispatch, mission execution, OA declaration, or baseline freeze observed or performed. |
| Preservation | Pre-change binary tracked diff, porcelain-v2 status, untracked list, and 130-file SHA-256 inventory captured at `/tmp/zh-reconcile-before.aUVhD7`. |

`engctl execution snapshot --mission GH-ZEUS-OA-PROGRESSIVE-001` returned exit 78 because no repository Mission Contract is keyed by that WOP ID. Direct read-only contract resolution found the stale active publication contract described above. This discrepancy did not authorize or cause any mutation.

## 2. Inventory and classification

Initiation contained 130 changed files: 36 tracked modifications and 94 untracked files; zero staged, deleted, renamed, or copied paths. Git's compact status groups untracked directories and therefore reported 83 status entries. The machine-readable companion expands every directory to repository-relative file paths.

| Category | Count | Disposition |
| --- | ---: | --- |
| A. Legitimate tracked modification | 36 | Retain in authoritative path |
| B. Legitimate new repository file | 33 | Retain in authoritative path for human staging/commit decision |
| C–D. Runtime/cache transient | 0 | None present in Git inventory |
| E. Historical evidence immutable | 61 | Protect and retain unchanged |
| F–I. Duplicate/misplaced/deleted/superseded | 0 | No corrective move/removal/restoration justified |
| J. Unresolved | 0 | No path-level disposition blocker |

No content-identical changed file exists elsewhere in the repository. No ignored configuration captured either highlighted untracked file. No working-tree path was moved, restored, removed, or content-edited; consequently every before/after digest is identical.

## 3. Provenance and highlighted untracked source analysis

`scripts/lib/emp/stage1_runtime.py` is a legitimate new repository source file at the authoritative EMP runtime path. It has no HEAD or historical Git object and no identical/alternate copy. `scripts/zeus` imports it directly; Stage 1, OA-05 staging, and mission-count tests depend on it; architecture, CLI, Project State, OA evidence, and the Stage 1 completion report name that exact path. Its provenance is the ZH-001 Stage 1 implementation, with structural count hardening from `ZH-OA05-MISSION-COUNT-INVESTIGATION-001`. Disposition: Category B, retain.

`scripts/tests/test-zeus-mission-count-status.py` is a legitimate new focused regression test at the repository's authoritative CLI-test path. It has no HEAD/history object, ignore match, duplicate, or generated-source marker. The mission-count investigation records its seven-test result, and it imports the production Stage 1 module. Disposition: Category B, retain.

The current validations depend on both exact paths. Retaining the source merely because tests import it was not the basis for disposition: architecture ownership, production CLI import, persisted OA verification evidence, documentation, and completion/investigation provenance independently establish authority.

## 4. Historical evidence protection

All accepted decision receipts and OA runtime verification records are untracked Category E artifacts and were left byte-for-byte unchanged. Historical completion, qualification, corrective, supersedence, admission, and investigation evidence was likewise protected. The package manifest and OA-05 implementation/verification changes are internally consistent and package verification passes. No evidence showed an unauthorized rewrite of a historical receipt; no historical artifact was normalized into current evidence.

## 5. Actions performed

- Captured a verified pre-action inventory and hashes outside the repository.
- Expanded all compact untracked directory entries into 130 file-level records.
- Compared changed-file SHA-256 values against every non-cache repository file; found zero identical alternates.
- Checked Git history, ignore rules, imports, execution references, documentation, tests, package evidence, and provenance for the two highlighted paths.
- Retained every legitimate source, test, controlled record, runtime record, and historical evidence file in its authoritative location.
- Added only this report and its machine-readable companion.

Actions intentionally not performed: no restore, reset, clean, removal, relocation, staging, commit, push, OA verification that writes evidence, gate acceptance/advancement, mission submission, dispatch, execution, Operational Alpha declaration, or baseline freeze. Project State, Registry, OA progress, and EOS source records were already mutually consistent and were not changed by this reconciliation.

## 6. Before/after digest disposition

Every one of the 130 initiation paths has `sha256_before == sha256_after` in the JSON inventory. No move, restoration, or removal occurred, so there is no destructive before/after action table. The report and JSON are new reconciliation evidence; the JSON self-entry uses a null `sha256_after` because embedding its own digest would be self-referential.

## 7. Validation results

| Validation | Applicability | Result |
| --- | --- | --- |
| `zeus status --json` | Applicable | PASS: OA-01..OA-05 accepted; OA-06 pending; mission count 0 |
| OA-01..OA-05 receipts | Applicable | PASS each |
| Current OA-06 verification | Intentionally not run | The only unambiguously discovered command can persist verification evidence; lifecycle mutation/evidence regeneration was outside reconciliation need. OA-06 remains pending. |
| Mission-count status | Applicable | PASS, 7 tests |
| Stage 1 runtime | Applicable | PASS, 7 tests |
| OA-05 mission staging | Applicable | PASS, 12 tests |
| Progressive OA | Applicable | PASS, 17 tests |
| Progressive package verification | Applicable | PASS, 30 gates |
| Controlled documents | Applicable | PASS, 2,641 checks |
| Repository health | Applicable | PASS, modified candidate preserved |
| Work Registry | Applicable | PASS, revision 85 / 85 objects |
| EOS synchronization validation | Applicable | PASS |
| Integrated platform validation | Applicable | PASS through repository, synchronization, EOS runtime, and integrated platform layers |
| Independent `scripts/verify.sh` | Applicable | PASS, 20 checks, 0 warnings, 0 failures |
| Python compilation | Applicable | PASS for affected EMP/Zeus modules |
| `git diff --check` | Applicable | PASS |

## 8. Lifecycle and execution state before/after

Before and after are identical: OA-01 through OA-05 `ACCEPTED`; OA-06 sole active gate `PENDING`; OA-07 through OA-30 `PENDING`; live mission count 0; declaration authorization false. No live mission submission, dispatch, mission execution, Operational Alpha declaration, or baseline freeze occurred.

## 9. Remaining risks and recommended commit grouping

The remaining risk is operational metadata ambiguity: `mission-contractctl resolve` still reports the prior publication contract active even though repository history contains its publication and bootstrap-closeout commits. This reconciliation did not amend that record because doing so is outside the requested path inventory and could rewrite authority history. Human review should decide whether a separate, explicitly authorized closeout reconciliation is needed.

Recommended commit groups, without staging or committing:

1. Governance baseline controlled documents and their documentation tests.
2. Progressive OA core/package, gate contracts, runtime state, and immutable gate evidence.
3. OA-01 through OA-04 implementations, focused tests, and completion/corrective evidence.
4. Stage 1/OA-05 mission staging, mission-count hardening, architecture/CLI documentation, tests, Project State/Registry/progress reconciliation, and OA-05 evidence.
5. OA-06 development artifacts, separated from accepted-gate evidence.
6. This working-tree reconciliation report and inventory.

Historical receipts should remain byte-identical and be reviewed as evidence, not squashed or regenerated. Commit grouping must be reviewed against dependency ordering so no group temporarily breaks package or controlled-document validation.

## 10. Final disposition

`RECONCILED — PRESERVATION CANDIDATE READY FOR HUMAN REVIEW AND COMMIT DECISION.` Every initiation path is classified; no duplicate, misplaced file, accidental deletion, transient artifact, or unresolved Category J item was found. The repository is intentionally still dirty because legitimate work has not been committed and this handoff forbids committing.

## Appendix A — Path-by-path classification

| Path | Git | Tracked | Category | Action |
| --- | --- | --- | --- | --- |
| `docs/DOC-0001-REPOSITORY_DOCUMENT_INDEX.md` | `M` | yes | A | retain in place |
| `docs/charters/CHAR-0001-ENGINEERING_CHARTER.md` | `M` | yes | A | retain in place |
| `docs/edr/EDR-0002-ENGINEERING_AUTHORITY_MODEL.md` | `M` | yes | A | retain in place |
| `docs/genesis/GEN-0001-GENESIS_GOVERNANCE_RECORD.md` | `M` | yes | A | retain in place |
| `docs/policies/POL-0001-ENGINEERING_GOVERNANCE_POLICY.md` | `M` | yes | A | retain in place |
| `docs/procedures/PROC-0001-ENGINEERING_WORK_ORDER_EXECUTION_PROCEDURE.md` | `M` | yes | A | retain in place |
| `docs/procedures/PROC-0002-ENGINEERING_GOVERNANCE_RESOLUTION_PROCEDURE.md` | `M` | yes | A | retain in place |
| `docs/procedures/PROC-0007-GOVERNANCE-STABILIZATION-PROCEDURE.md` | `M` | yes | A | retain in place |
| `docs/project/PROJ-0001-PROJECT_STATE.md` | `M` | yes | A | retain in place |
| `docs/project/milestones/2026-07-29-operational-alpha-governance-baseline-1.0.md` | `??` | no | B | retain in place |
| `docs/specifications/SPEC-0005-ENGINEERING_CONTROL_FRAMEWORK.md` | `M` | yes | A | retain in place |
| `docs/specifications/SPEC-0011-PRODUCTION-AUTHORITY-RESTORATION-SPECIFICATION.md` | `M` | yes | A | retain in place |
| `engineering/docs/architecture/ZEUS-STAGE1-RUNTIME.md` | `??` | no | B | retain in place |
| `engineering/docs/cli/ZEUS-USER-GUIDE.md` | `M` | yes | A | retain in place |
| `engineering/evidence/2026-07-28-zeus-operational-alpha-stage1-completion-report.md` | `??` | no | E | retain in place |
| `engineering/evidence/2026-07-29-zh-gov-mission-lifecycle-002-corrective-handoff.md` | `??` | no | E | retain in place |
| `engineering/evidence/2026-07-29-zh-oa01-implementation-003.md` | `??` | no | E | retain in place |
| `engineering/evidence/2026-07-29-zh-oa01-qualification-002.md` | `??` | no | E | retain in place |
| `engineering/evidence/2026-07-29-zh-oa03-mission-contract-discovery-001-completion-report.md` | `??` | no | E | retain in place |
| `engineering/evidence/2026-07-29-zh-oa04-acceptance-replay-corrective-001.md` | `??` | no | E | retain in place |
| `engineering/evidence/2026-07-29-zh-oa04-contract-conformance-review-001.md` | `??` | no | E | retain in place |
| `engineering/evidence/2026-07-29-zh-oa04-mission-resolution-001-completion-report.md` | `??` | no | E | retain in place |
| `engineering/evidence/2026-07-29-zh-oa05-contract-conformance-review-001.md` | `??` | no | E | retain in place |
| `engineering/evidence/2026-07-29-zh-oa05-mission-count-investigation-001.md` | `??` | no | E | retain in place |
| `engineering/evidence/2026-07-29-zh-oa05-mission-staging-001-completion-report.md` | `??` | no | E | retain in place |
| `engineering/evidence/2026-07-29-zh-zeus-oa-admission-001-work-initiation.md` | `??` | no | E | retain in place |
| `engineering/execution/execution-interface.yaml` | `M` | yes | A | retain in place |
| `engineering/operations/authority-ownership-specification.md` | `M` | yes | A | retain in place |
| `engineering/operations/zeus-mission-admission-runtime.md` | `M` | yes | A | retain in place |
| `engineering/operations/zeus-mission-execution-runtime.md` | `M` | yes | A | retain in place |
| `engineering/operations/zeus-oa01-mission-verification.md` | `??` | no | B | retain in place |
| `engineering/operations/zeus-operational-alpha-progress.md` | `M` | yes | A | retain in place |
| `engineering/operations/zeus-operational-runtime.md` | `M` | yes | A | retain in place |
| `engineering/operations/zeus-operator-interface.md` | `M` | yes | A | retain in place |
| `engineering/registry/work-registry.yaml` | `M` | yes | A | retain in place |
| `engineering/tests/zeus-operational-alpha/PMCT-CAPABILITY-MATRIX.yaml` | `M` | yes | A | retain in place |
| `engineering/tests/zeus-operational-alpha/PMCT-CONTRACT.md` | `M` | yes | A | retain in place |
| `engineering/tests/zeus-operational-alpha/tests/test-result-model.py` | `M` | yes | A | retain in place |
| `engineering/tests/zeus-operational-alpha/tests/test-state-protection.py` | `M` | yes | A | retain in place |
| `engineering/tests/zeus-operational-alpha/tests/test_discovery.py` | `??` | no | B | retain in place |
| `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/MANIFEST.sha256` | `M` | yes | A | retain in place |
| `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/gates/OA-05/implementation.md` | `M` | yes | A | retain in place |
| `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/gates/OA-05/verification.md` | `M` | yes | A | retain in place |
| `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/decisions/OA-01/accepted.json` | `??` | no | E | retain in place |
| `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/decisions/OA-02/accepted.json` | `??` | no | E | retain in place |
| `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/decisions/OA-03/accepted.json` | `??` | no | E | retain in place |
| `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/decisions/OA-04/accepted-59cbfe3e60b09f1483fe165276f3b247577ccc83bcd084ea212fa78689f972c0.json` | `??` | no | E | retain in place |
| `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/decisions/OA-04/accepted.json` | `??` | no | E | retain in place |
| `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/decisions/OA-04/superseded-by-contract-correction.json` | `??` | no | E | retain in place |
| `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/decisions/OA-05/accepted-31c196a0ef998f1e9cc59988eac81eaa015d134bf1a1ee1a9d15cb401d274be9.json` | `??` | no | E | retain in place |
| `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/evidence/OA-01/IMPLEMENTATION.json` | `??` | no | E | retain in place |
| `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/evidence/OA-01/VERIFICATION.json` | `??` | no | E | retain in place |
| `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/evidence/OA-01/VERIFIED` | `??` | no | E | retain in place |
| `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/evidence/OA-01/ZH-OA01-VERIFICATION-CORRECTIVE-004-COMPLETION.md` | `??` | no | E | retain in place |
| `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/evidence/OA-01/attempts/0c721f239604ca12d5d59af0db2c857b097b8cbdec44c045f36058d790b13c91/VERIFICATION.json` | `??` | no | E | retain in place |
| `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/evidence/OA-01/attempts/0c721f239604ca12d5d59af0db2c857b097b8cbdec44c045f36058d790b13c91/VERIFIED` | `??` | no | E | retain in place |
| `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/evidence/OA-01/attempts/a337b7ade99bb67790d51e0bc09a07777ae06096454540af005adb99dfa4024d/VERIFICATION.json` | `??` | no | E | retain in place |
| `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/evidence/OA-01/attempts/a337b7ade99bb67790d51e0bc09a07777ae06096454540af005adb99dfa4024d/VERIFIED` | `??` | no | E | retain in place |
| `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/evidence/OA-02/IMPLEMENTATION.json` | `??` | no | E | retain in place |
| `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/evidence/OA-02/VERIFICATION.json` | `??` | no | E | retain in place |
| `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/evidence/OA-02/VERIFIED` | `??` | no | E | retain in place |
| `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/evidence/OA-02/ZH-OA02-CONTROLLED-MISSION-AUTHORITY-001-COMPLETION.md` | `??` | no | E | retain in place |
| `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/evidence/OA-02/attempts/2fe7fb97fab8e62a70167a71048cf35de1080fc11b9a6a44f43d5cbcaa9ac92d/IMPLEMENTATION.json` | `??` | no | E | retain in place |
| `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/evidence/OA-02/attempts/af955eb13c8a91130651c74ca91f6e8cbd6a44ca814926c0ca2f06d1856f5f7d/VERIFICATION.json` | `??` | no | E | retain in place |
| `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/evidence/OA-02/attempts/af955eb13c8a91130651c74ca91f6e8cbd6a44ca814926c0ca2f06d1856f5f7d/VERIFIED` | `??` | no | E | retain in place |
| `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/evidence/OA-03/IMPLEMENTATION.json` | `??` | no | E | retain in place |
| `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/evidence/OA-03/VERIFICATION.json` | `??` | no | E | retain in place |
| `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/evidence/OA-03/VERIFIED` | `??` | no | E | retain in place |
| `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/evidence/OA-03/attempts/d87249a0cc7e04fa895a696a801da5bfe41b04e3b08b04c844ded6890db7237a/VERIFICATION.json` | `??` | no | E | retain in place |
| `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/evidence/OA-03/attempts/d87249a0cc7e04fa895a696a801da5bfe41b04e3b08b04c844ded6890db7237a/VERIFIED` | `??` | no | E | retain in place |
| `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/evidence/OA-04/IMPLEMENTATION.json` | `??` | no | E | retain in place |
| `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/evidence/OA-04/VERIFICATION.json` | `??` | no | E | retain in place |
| `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/evidence/OA-04/VERIFIED` | `??` | no | E | retain in place |
| `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/evidence/OA-04/attempts/0b538ce2262bf9a7a33a88e47ebd12b48becfc0a675701fb72e96a5679225e55/VERIFICATION.json` | `??` | no | E | retain in place |
| `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/evidence/OA-04/attempts/0b538ce2262bf9a7a33a88e47ebd12b48becfc0a675701fb72e96a5679225e55/VERIFIED` | `??` | no | E | retain in place |
| `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/evidence/OA-04/attempts/1734b9295a029c9ecddb6440cd86d1faf7aee7af1d2269d33180876e0a188b87/VERIFICATION.json` | `??` | no | E | retain in place |
| `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/evidence/OA-04/attempts/1734b9295a029c9ecddb6440cd86d1faf7aee7af1d2269d33180876e0a188b87/VERIFIED` | `??` | no | E | retain in place |
| `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/evidence/OA-04/attempts/23cc5af0c6b56b31f1fb92108cac3150fb4d58578f1f148d8e534b9c2335565a/VERIFICATION.json` | `??` | no | E | retain in place |
| `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/evidence/OA-04/attempts/23cc5af0c6b56b31f1fb92108cac3150fb4d58578f1f148d8e534b9c2335565a/VERIFIED` | `??` | no | E | retain in place |
| `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/evidence/OA-04/attempts/37cd9ee4f0e0e9a4d91d3289d2a4694ef5da9474dc979293673e9aa68353d7c0/VERIFICATION.json` | `??` | no | E | retain in place |
| `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/evidence/OA-04/attempts/37cd9ee4f0e0e9a4d91d3289d2a4694ef5da9474dc979293673e9aa68353d7c0/VERIFIED` | `??` | no | E | retain in place |
| `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/evidence/OA-04/attempts/8996960699a4970b2fda196eecc043ddcda1608ffd3321ee90531cc5c55091e3/VERIFICATION.json` | `??` | no | E | retain in place |
| `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/evidence/OA-04/attempts/8996960699a4970b2fda196eecc043ddcda1608ffd3321ee90531cc5c55091e3/VERIFIED` | `??` | no | E | retain in place |
| `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/evidence/OA-04/attempts/95d3457565ff128521e19305444a1e80613598c9a9f51a715eb4ed9d81f03c6f/IMPLEMENTATION.json` | `??` | no | E | retain in place |
| `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/evidence/OA-04/attempts/cdbf93a74bc687fa622dbea84b011f37d5b0879d95523c7f5c473663cf92deee/IMPLEMENTATION.json` | `??` | no | E | retain in place |
| `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/evidence/OA-04/attempts/dbbab47a902ee5c431bfd824ef1ead1a9d423e377f3443b258a80724314e97d3/VERIFICATION.json` | `??` | no | E | retain in place |
| `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/evidence/OA-04/attempts/dbbab47a902ee5c431bfd824ef1ead1a9d423e377f3443b258a80724314e97d3/VERIFIED` | `??` | no | E | retain in place |
| `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/evidence/OA-05/IMPLEMENTATION.json` | `??` | no | E | retain in place |
| `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/evidence/OA-05/VERIFICATION.json` | `??` | no | E | retain in place |
| `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/evidence/OA-05/VERIFIED` | `??` | no | E | retain in place |
| `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/evidence/OA-05/attempts/1c96738d313cb6f3759be8f3c62e44da199bc85cd3b1aec61918964ad639fa62/VERIFICATION.json` | `??` | no | E | retain in place |
| `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/evidence/OA-05/attempts/1c96738d313cb6f3759be8f3c62e44da199bc85cd3b1aec61918964ad639fa62/VERIFIED` | `??` | no | E | retain in place |
| `engineering/work-orders/GH-ZEUS-OA-PROGRESSIVE-001/runtime/state.json` | `M` | yes | A | retain in place |
| `scripts/lib/emp/controlled_mission_authority.py` | `??` | no | B | retain in place |
| `scripts/lib/emp/mission_contract_discovery.py` | `??` | no | B | retain in place |
| `scripts/lib/emp/mission_resolution.py` | `??` | no | B | retain in place |
| `scripts/lib/emp/oa01_gate_verification.py` | `??` | no | B | retain in place |
| `scripts/lib/emp/oa01_implementation.py` | `??` | no | B | retain in place |
| `scripts/lib/emp/oa01_verification.py` | `??` | no | B | retain in place |
| `scripts/lib/emp/oa02_gate_verification.py` | `??` | no | B | retain in place |
| `scripts/lib/emp/oa02_implementation.py` | `??` | no | B | retain in place |
| `scripts/lib/emp/oa03_gate_verification.py` | `??` | no | B | retain in place |
| `scripts/lib/emp/oa03_implementation.py` | `??` | no | B | retain in place |
| `scripts/lib/emp/oa04_gate_verification.py` | `??` | no | B | retain in place |
| `scripts/lib/emp/oa04_implementation.py` | `??` | no | B | retain in place |
| `scripts/lib/emp/oa05_gate_verification.py` | `??` | no | B | retain in place |
| `scripts/lib/emp/oa05_implementation.py` | `??` | no | B | retain in place |
| `scripts/lib/emp/progressive_oa.py` | `M` | yes | A | retain in place |
| `scripts/lib/emp/project_operational_context.py` | `??` | no | B | retain in place |
| `scripts/lib/emp/stage1_runtime.py` | `??` | no | B | retain in place |
| `scripts/tests/test-emp-registry.py` | `M` | yes | A | retain in place |
| `scripts/tests/test-governance-baseline-documentation.py` | `??` | no | B | retain in place |
| `scripts/tests/test-governance-bootstrap-documentation.py` | `??` | no | B | retain in place |
| `scripts/tests/test-governance-mission-admission-documentation.py` | `??` | no | B | retain in place |
| `scripts/tests/test-zeus-mission-assurance.py` | `M` | yes | A | retain in place |
| `scripts/tests/test-zeus-mission-count-status.py` | `??` | no | B | retain in place |
| `scripts/tests/test-zeus-oa01-implementation.py` | `??` | no | B | retain in place |
| `scripts/tests/test-zeus-oa01-verification.py` | `??` | no | B | retain in place |
| `scripts/tests/test-zeus-oa02-controlled-authority.py` | `??` | no | B | retain in place |
| `scripts/tests/test-zeus-oa02-lifecycle.py` | `M` | yes | A | retain in place |
| `scripts/tests/test-zeus-oa03-mission-contract-discovery.py` | `??` | no | B | retain in place |
| `scripts/tests/test-zeus-oa04-context-reconstruction.py` | `??` | no | B | retain in place |
| `scripts/tests/test-zeus-oa04-mission-resolution.py` | `??` | no | B | retain in place |
| `scripts/tests/test-zeus-oa05-mission-staging.py` | `??` | no | B | retain in place |
| `scripts/tests/test-zeus-progressive-oa.py` | `M` | yes | A | retain in place |
| `scripts/tests/test-zeus-stage1-runtime.py` | `??` | no | B | retain in place |
| `scripts/tests/test_discovery.py` | `??` | no | B | retain in place |
| `scripts/verify.sh` | `M` | yes | A | retain in place |
| `scripts/zeus` | `M` | yes | A | retain in place |
| `services/eens/README.md` | `M` | yes | A | retain in place |
