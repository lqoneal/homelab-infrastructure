# T03 APPR Controlled Document Revision

## Selected authoritative documents

1. `docs/specifications/SPEC-0012-PRODUCTION-EXECUTION-FOUNDATION.md`
   was revised from 1.0 to 1.1. It was selected because it is Active,
   `source_of_truth: true`, indexed, owned by Lawrence O'Neal in the Execution
   Authority domain, and already specifies production verification, decision,
   persistence, replay, and lifecycle enforcement.
2. `docs/DOC-0001-REPOSITORY_DOCUMENT_INDEX.md` was revised from 2.59 to
   2.60 because it is the authoritative controlled-document index and must
   record the SPEC-0012 revision.

SPEC-0012 now freezes:

- Progressive Authority Primitives as exclusive verification, receipt
  validation, predecessor-resolution, and gate-query authority;
- `ProgressiveGateService` as the canonical façade and exclusive Progressive
  approval, rejection, persistence, acceptance, replay, receipt-generation,
  and supersedence authority;
- `progressive_oa` as a compatibility boundary;
- lifecycle projections as fail-closed read models rather than authority
  owners; and
- the future rule to consume canonical layers and avoid competing
  implementations.

## Candidates not modified

| Candidate | Reason not selected |
| --- | --- |
| `engineering/operations/authority-ownership-specification.md` | An authoritative human production-ownership note, but not registered as a controlled document in DOC-0001 and not the implementation-mechanics owner. |
| `engineering/planning/ZH-AUTHORITY-PIPELINE-INTEGRATION-PLANNING-001/01-authority-pipeline-specification.md` | Explicitly a planning proposal and explicitly not an authority artifact. |
| `engineering/docs/architecture/ZEUS-CONTROLLED-DOCUMENTATION-ARCHITECTURE.md` | Explicitly proposed, uncontrolled, unapproved, and non-authoritative. |
| `docs/project/PHASE-0001-ZEUS-OPERATIONAL-ALPHA-AUTHORITY.md` | Controls mission identity, scope, and sequencing; it expressly does not own runtime implementation mechanics. |
| `engineering/operations/zeus-operational-runtime.md` | Operational guidance subordinate to SPEC-0012, not an indexed controlled source of truth for this architecture. |

No new controlled document was created.

## Validation

`python3 scripts/validate_controlled_documents.py` passed all 2,647 checks.
