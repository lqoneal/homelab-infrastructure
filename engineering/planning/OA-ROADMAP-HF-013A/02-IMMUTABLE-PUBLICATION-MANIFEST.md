# Immutable Publication Manifest — OA-IMPLEMENTATION-BASELINE-1.0

Transaction identifier: `OA-HF-013A-PUB-001`

Authority: `OA-ROADMAP-HF-013A`

Starting repository baseline: `7e3bf67345e53591036aa0ca103f78aa9844f93c`

Publication operation: local atomic Git commits and annotated baseline tag;
remote publication is not authorized by this manifest.

## Included publication content

1. `engineering/planning/OA-ROADMAP-HF-005/**`
2. `engineering/planning/OA-ROADMAP-HF-006/**`
3. `engineering/planning/OA-ROADMAP-HF-007/**`
4. `engineering/planning/OA-ROADMAP-HF-008/**`
5. `engineering/planning/OA-ROADMAP-HF-009/**`
6. `engineering/planning/OA-ROADMAP-HF-010/**`
7. `engineering/planning/OA-ROADMAP-HF-011/**`
8. `engineering/planning/OA-ROADMAP-HF-012/**`
9. `engineering/planning/OA-ROADMAP-HF-013A/**`
10. `engineering/registry/architecture-baselines/OA-IMPLEMENTATION-BASELINE-1.0.yaml`
11. `docs/project/milestones/2026-07-30-operational-alpha-implementation-baseline-1.0.md`
12. `docs/DOC-0001-REPOSITORY_DOCUMENT_INDEX.md`
13. `docs/project/PHASE-0001-ZEUS-OPERATIONAL-ALPHA-AUTHORITY.md`
14. `docs/project/PROJ-0001-PROJECT_STATE.md`
15. `engineering/evidence/2026-07-30-oa-hf-013a/**`

The exact staged-path proof, commit locators, and frozen digests are appended
in the publication validation report before transaction finalization. No glob
is used for staging; the directory notation above is an inventory shorthand
only, and the final staged-path list is authoritative.

## Explicit exclusions

| Path or set | Reason | Disposition |
| --- | --- | --- |
| `docs/architecture/AQR-0001-ARCHITECTURE-QUALIFICATION-REPORT.md` | pre-existing user-owned Draft revision | preserved and excluded; no overwrite or lifecycle claim |
| `engineering/evidence/2026-07-30-aqr-0001-hf-002-*` | pre-existing user-owned qualification outputs | preserved and excluded |
| `engineering/planning/OA-ROADMAP-HF-001/**` through `OA-ROADMAP-HF-004/**` | pre-existing adjacent planning work outside HF-013A scope | preserved and excluded |
| every other pre-existing working-tree deviation | unrelated or not explicitly authorized publication content | preserved and excluded |

## Boundaries and stop conditions

- Initial validation: repository identity, initial commit, status inventory,
  document references, and whitespace validation.
- Publication: exact included paths only; no unrelated staging, cleanup, or
  refactoring.
- Synchronization: repository-controlled registry and cross-reference updates
  only. EOS runtime mutation is not performed; it is recorded as a directional
  `SYNCHRONIZATION_REQUIRED` handoff to its owner.
- Stop on a dirty included path not created by this transaction, failed
  validation, unexpected staged path, or conflict with the excluded AQR work.
