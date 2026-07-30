# SPEC-0002 HF-001 Prioritized Repository Convergence Backlog

Date: 2026-07-30

Source: AQR-0001 Draft 1.1 Repository Convergence Qualification

Repository determination: `NOT CONVERGED`

This backlog is observational planning evidence. It does not authorize
cleanup, deletion, staging, commit, publication, synchronization, lifecycle
transition, or promotion.

## P0 — Establish owner-bounded candidate groups

### RC-BL-001 — Freeze a new inventory observation before convergence

- **Finding:** AQR-RCF-001.
- **Scope:** Regenerate the complete file-level status after separately
  authorized convergence begins and bind HEAD, branch, upstream, index, and
  timestamp.
- **Completion evidence:** immutable pre-action inventory, counts, and digest.

### RC-BL-002 — Partition deviations by information owner

- **Findings:** AQR-RCF-002, AQR-RCF-003.
- **Scope:** Assign every deviation to one owner-approved controlled-document,
  implementation, evidence, registry/state, Runtime, WOP/mission,
  publication, synchronization, archive/history, generated/temporary, or
  compatibility candidate group.
- **Constraint:** No path may belong to two writable candidate groups.
- **Completion evidence:** exact non-overlapping include/exclude manifests,
  owner acknowledgements, dependency edges, and zero orphan paths.

### RC-BL-003 — Reconcile controlled-document candidates

- **Criteria:** AQR-RCQ-003, AQR-RCQ-006.
- **Scope:** Verify revision lineage, lifecycle, registration, relationships,
  superior-record conformance, and candidate grouping for every changed
  controlled record.
- **Completion evidence:** per-document change matrix, current DOC-0001
  registration, validator output, semantic review, and owner disposition.

### RC-BL-004 — Reconcile evidence and historical retention

- **Criteria:** AQR-RCQ-004, AQR-RCQ-007.
- **Scope:** Bind every evidence/review/archive artifact to its producer,
  subject, provenance, integrity, retention class, and candidate group.
- **Constraint:** Historical/archive bytes remain immutable. Status or filename
  alone cannot authorize deletion.
- **Completion evidence:** evidence manifest, hashes, provenance, retention
  route, archive verification, and orphan-free subject mapping.

### RC-BL-005 — Reconcile registries, state, missions, and projections

- **Criterion:** AQR-RCQ-005.
- **Scope:** Compare Project State, Work Registry, Mission Contracts,
  activation requests, execution-mission projections, WOP state, Progressive
  decision/evidence state, publication records, and EOS projections to their
  named owners.
- **Constraint:** Do not select newest timestamp or reverse-synchronize a
  projection into its source.
- **Completion evidence:** owner matrix, drift classification, authorized
  direction, before/after identities, and unresolved blocker register.

## P1 — Qualify disposition safety

### RC-BL-006 — Classify generated and temporary artifacts

- **Criteria:** AQR-RCQ-002, AQR-RCQ-007.
- **Scope:** Confirm which caches, Runtime outputs, generated matrices,
  manifests, observations, and environment-local files are reproducible,
  retainable, ignored, published, or excluded.
- **Completion evidence:** generation contract, source inputs, reproducibility
  result, ignore/publication policy, and owner decision.

### RC-BL-007 — Resolve duplicate, compatibility, obsolete, and superseded candidates

- **Finding:** AQR-RCF-004.
- **Scope:** For every candidate duplicate or superseded/obsolete name, prove
  canonical owner, consumers, production reachability, recovery dependency,
  historical value, and preservation requirements.
- **Constraint:** No deletion or retirement without consumer-complete and
  recovery evidence.
- **Completion evidence:** consumer inventory, call graph, comparison tests,
  retirement or retention decision, archive digest, and rollback boundary.

### RC-BL-008 — Reconcile implementation and test cohorts

- **Criteria:** AQR-RCQ-006, AQR-RCQ-009.
- **Scope:** Group Runtime libraries, scripts, tests, schemas, service
  documentation, and generated architecture metadata into independently
  reviewable implementation candidates.
- **Completion evidence:** scope manifest, test/evidence binding, unrelated
  exclusions, dependency graph, and owner acceptance.

## P1 — Establish a clean exact candidate

### RC-BL-009 — Reach zero unexplained deviation

- **Criteria:** AQR-RCQ-008, AQR-RCQ-009.
- **Scope:** Complete authorized retain/include/exclude/split/archive/generate/
  ignore/retire dispositions until every deviation is explained and each
  intended candidate can be isolated exactly.
- **Completion evidence:** zero orphan deviations, empty unauthorized staging,
  exact candidate manifests, and clean or intentionally bounded status.

### RC-BL-010 — Freeze and persist the architecture candidate

- **Criteria:** AQR-RCQ-009, AQR-RCQ-010, AQR-QC-014.
- **Scope:** Under separate authority, freeze the exact ARCH/ADR/SPEC/AQR,
  DOC-0001, and qualification-evidence boundary and persist it through its
  controlled publication owner.
- **Completion evidence:** exact paths, digests, dependency order, immutable
  locator, publication receipt, and persistence verification.

### RC-BL-011 — Prove clean reconstruction and formal qualification

- **Criteria:** AQR-RCQ-010, AQR-QC-014.
- **Scope:** Reconstruct the immutable candidate from a clean checkout, repeat
  deterministic validation, and execute independent qualification under a
  frozen authorized PROC-0006 invocation.
- **Completion evidence:** matching digests, validator outputs, frozen
  qualification contract, independent result, findings, and recommendation.

## P2 — Framework maintainability

### RC-BL-012 — Add an AQR semantic profile

- **Finding:** AQR-F-006.
- **Scope:** Under separate authority, add an additive semantic profile for
  architecture and repository convergence qualification content.
- **Completion evidence:** controlled profile revision, tests, coverage,
  qualification, and publication.

## Dependency order

```text
RC-BL-001
    ↓
RC-BL-002
    ├──> RC-BL-003
    ├──> RC-BL-004
    ├──> RC-BL-005
    ├──> RC-BL-006
    ├──> RC-BL-007
    └──> RC-BL-008
             ↓
          RC-BL-009
             ↓
          RC-BL-010
             ↓
          RC-BL-011

RC-BL-012 may proceed independently under separate authority.
```
