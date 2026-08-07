# Controlled-Document Semantic Inventory

## Current roots inspected

- Architecture: `docs/architecture/ADR-0001`, `ARCH-0001`, `AQR-0001`.
- EDR: `docs/edr/EDR-0002`, `EDR-0003`.
- Policy: `docs/policies/POL-0001`.
- Procedures: `docs/procedures/PROC-0001` through `PROC-0009`.
- Specifications: `SPEC-0001`, `SPEC-0002`, `SPEC-0005`, `SPEC-0006`,
  `SPEC-0007`, `SPEC-0008`, `SPEC-0009`, `SPEC-0010`, `SPEC-0011`,
  `SPEC-0012`, and `SPEC-0014`.
- Standards: `STD-0000` through `STD-0005`.
- Zeus/engineering operational contracts: the authority policy and admission
  schemas, WOP schema/execution interface, authority ownership, repository
  authority model, mission admission runtime, operational runtime, operator
  interface, operational-alpha progress, Development Mode, and execution
  lifecycle procedure.

## Authority ownership result

The current Zeus submission boundary is the identity-bound operator-submitted
WOP. Admission, identity/integrity validation, scope containment, dependency
and prerequisite checks, provider qualification, concurrency/session safety,
baseline verification, lifecycle control, publication, synchronization,
evidence, and closeout remain distinct controls. They are not represented as
generic grants of operator work authority.

## Changed current documents

The full candidate path set is in `PUBLICATION-CANDIDATE-MANIFEST.md`. The
normative convergence edits cover the policy, submission schema, ADR,
architecture/specification/policy/procedure/standard owners, WOP execution
interface, Zeus operational documents, and current EMM source digest.

## Inspected but intentionally unchanged

- `ARCH-0001` and `AQR-0001` remain Draft/Pending assessment artifacts; their
  future qualification and promotion language is not current Zeus runtime
  admission authority.
- `EDR-0002` remains Draft and describes the broader authority model rather
  than the current submitted-WOP runtime boundary.
- `EDR-0003` is persisted historical authorization-transaction evidence and
  was not rewritten.
- Historical WOPs, receipts, completion reports, evidence, and lifecycle
  records were not changed.
- Separate publication, EOS synchronization, provider qualification,
  mission activation, and production dispatch artifacts were retained as
  safety/lifecycle controls.
