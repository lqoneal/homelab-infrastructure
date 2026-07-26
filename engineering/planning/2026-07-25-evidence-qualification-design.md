# EMP Evidence Package Qualification

Date: 2026-07-25
Status: Independent qualification implementation
Mission: Zeus Operational Alpha Mission L

## Boundary and separation

Execution agents produce artifact bytes, assemble an Evidence Package and sign
its checksum. Zeus receives the immutable package, independently verifies the
artifact bytes and package bindings, evaluates the WOP-bound qualification
contract, and issues an immutable Qualification Report.

The subsystem does not execute or dispatch work, approve execution, select or
complete missions, close WOPs, update Project State or Work Registry records,
modify controlled documents, or perform engineering reconciliation.

## Evidence Package

An Evidence Package (EP) binds:

- assignment, execution session, mission and WOP identities;
- repository and baseline identities;
- execution-agent identity;
- deterministically ordered evidence manifest and artifact digest map;
- required and produced evidence declarations;
- completion metadata and package timestamp;
- deterministic UUIDv5 package identity, SHA-256 checksum and signature
  interface.

Manifest entries identify artifact identity/type/producer/digest,
WOP-objective relationship, verification-requirement relationship, and
required/optional classification. Artifact bytes remain separate inputs so
Zeus recomputes their digests rather than trusting agent declarations.

## Qualification contract

The evaluation contract binds the WOP, mission, assignment, repository and
baseline. It declares required, expected and prohibited evidence, required
verification steps, and the evidence needed for each WOP objective.

The execution agent cannot change this contract. Completion assertions never
substitute for artifacts or a completed Mission K session projection.

## Decisions

Every evaluation returns exactly one terminal decision:

- `PASS`: all integrity, completion, evidence, verification and objective
  requirements succeed.
- `FAIL`: verifiable evidence violates a prohibited-evidence rule or conflicts
  with the completed execution-state requirement.
- `INCOMPLETE`: the package is trustworthy but required evidence,
  verification steps or objective support is missing.
- `UNVERIFIABLE`: package/signature/artifact integrity, declarations or
  identity bindings cannot be verified.

Unexpected evidence is retained in the report. It does not silently satisfy a
requirement.

## Determinism and history

The immutable report includes its package identity, decision, sorted reason
codes, missing/unexpected evidence, integrity matrix, completeness evaluation,
qualified/unqualified objectives, package timestamp, deterministic UUIDv5
qualification identity and SHA-256 digest.

Identical canonical inputs produce byte-identical reports. Qualification
history is append-only and permits repeated qualification only when every
retained report for an EP is canonical-data identical. Restart replay validates
each report and preserves the original result.
