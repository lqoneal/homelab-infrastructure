# Repository Information Architecture Report

Result: PASS.

The audited recovery artifacts are in the following authoritative locations:

| Location | Contents | Classification |
|---|---|---|
| `engineering/docs/architecture` | Zeus architecture, runtime, controller, CLI, and invariant documents | Controlled architecture/specification |
| `engineering/docs/cli` | Operator-facing command reference | Controlled operational reference |
| `engineering/docs/operations` | Development Mode and WOP authoring guidance | Controlled procedure/guidance |
| `engineering/evidence/operation-beta` | Qualification, recovery, conformance, and completion evidence | Controlled evidence |
| `engineering/work-orders/WOP-AUTHORING-001` | Immutable generated WOP package | Controlled work order |
| `engineering/evidence/.../fixtures` | Bounded source/package fixtures | Qualification fixture |
| `scripts/tests` and `scripts/tests/fixtures` | Automated tests and disposable fixtures | Test artifact |

The retained BETA-07 DOCX remains at repository root as the source work-order
artifact. No fixture appears in `engineering/work-orders` as an active
canonical work order. No controlled document was placed in a runtime or
temporary state directory.

The repository information architecture and DOC-0001 registry checks pass;
the local Zeus documentation domain remains subordinate to the canonical
`docs/` governance framework.
