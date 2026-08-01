# Canonical Authority Generation Framework — Published Engineering Direction

Status: published engineering direction; planned framework; implementation deferred through OA-30
Authority boundary: generated artifacts remain subordinate to their canonical owners

## Purpose

The Canonical Authority Generation Framework (CAGF) is the planned engineering
architecture for eliminating drift between canonical authority and derived
operational artifacts. CAGF will transform validated canonical records into
deterministic projections and will continuously qualify those projections.

CAGF will not create mission authority, capability authority, lifecycle
transitions, approvals, or implementation scope. Generation is a projection
operation, not an authorization operation.

## Authority ownership

| Artifact or fact | Canonical owner | Derived consumers |
| --- | --- | --- |
| Mission sequence, objectives, dependencies, readiness inputs | Mission Knowledge Model | Roadmap and mission controllers |
| Capability identity and operational state | Capability Registry | Capability and mission projections |
| Authority bindings and drift status | EMM | Verification and reconciliation views |
| Qualification contract and gate semantics | PMCT / controlled gate authority | Executable gates and qualification tools |
| Executable gate definition | Controlled gate authority | Gate runner projection |
| Controller presentation | Shared controller projection contract | Human, `--verify`, and `--json` views |
| EOS engineering state | EOS | Platform and synchronization checks |

Each generated artifact carries a source reference, source revision or digest,
generator identity, generation timestamp, and qualification result. A source
conflict or unverifiable digest fails closed and blocks publication of the
affected projection.

## Planned generated artifacts

CAGF is intended to generate, deterministically:

- PMCT capability and gate projections;
- executable gate definitions;
- mission roadmap, readiness, blocker, prerequisite, and next-action views;
- capability projections and operational metadata;
- controller projections and structured verification views;
- provenance manifests and reconciliation evidence indexes.

Generated artifacts are disposable projections. They must not be edited to
change authority. A required semantic change is made at the canonical owner,
then regenerated and requalified.

## Generation contract

The future framework shall:

1. resolve canonical sources in a declared authority order;
2. validate schemas and cross-source identity bindings;
3. reject disagreement, missing source data, stale digests, and cycles;
4. produce byte-stable output for identical inputs and generator versions;
5. emit a manifest binding every output to its sources;
6. qualify outputs before publication or operational consumption;
7. preserve prior published projections as immutable evidence.

The framework must not silently repair source conflicts. Reconciliation is a
controlled engineering action followed by regeneration and qualification.

## Progressive direction

The planned migration is: inventory and ownership map; canonical source
contracts; deterministic single-artifact generation; cross-artifact identity
validation; continuous qualification; controlled publication integration; and
eventual removal of manually maintained duplicate projections where safe.

The work will be introduced incrementally during later authorized Operational
Alpha gates. No CAGF generator, source rewrite, runtime integration, or
lifecycle change is implemented by this publication.

## Relationship to ZDCL

ZDCL will consume qualified generated context and projections. CAGF will
generate projections from canonical authority. Neither subsystem supersedes
Engineering Governance, EOS, EMP, EENS, the Mission Knowledge Model, or the
Capability Registry.

## Deferred status

CAGF remains a planned engineering direction through OA-30. After OA-30
acceptance, its first implementation contract is governed by
`engineering/docs/architecture/ENGINEERING-PLATFORM-EVOLUTION-PHASE-1.md` and
requires a separately authorized work order. Implementation is explicitly
deferred by this document; ownership, deterministic-generation requirements,
and the future qualification boundary remain unchanged.
