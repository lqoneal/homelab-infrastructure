# Zeus Development WOP Authoring Guide

The canonical authoring workflow uses source documents only:

```text
zeus wop format
zeus wop template --wop-id WOP-EXAMPLE-001 --mission-id EXAMPLE-01 --output WOP-EXAMPLE-001.md
# edit WOP-EXAMPLE-001.md
zeus submit WOP-EXAMPLE-001.md
zeus submit WOP-EXAMPLE-001.md
```

`zeus wop format` is generated from the canonical schema and lists all required
 metadata. `zeus wop template` supports Markdown and DOCX. `zeus wop inspect`
is read-only and reports every unresolved field. `inspect`, `explain`, and
`lint` are read-only previews. Operators do not construct mission files,
manifests, registration, provenance, or runtime state manually.

Submission validates and packages in isolation, preserves the source, and
atomically promotes only a complete immutable package. Failed authoring or
packaging creates no package or runtime state. Only DEVELOPMENT execution and
non-production effect profiles are accepted by this workflow.
## Public workflow

```text
zeus doctor
zeus wop format
zeus wop template --wop-id WOP-EXAMPLE-001 --mission-id EXAMPLE-01
zeus wop init --wop-id WOP-EXAMPLE-001 --mission-id EXAMPLE-01
zeus wop lint WOP-EXAMPLE-001.md
zeus submit WOP-EXAMPLE-001.md
zeus submit WOP-EXAMPLE-001.md
```

`zeus wop init` is an interactive equivalent when IDs are omitted. Use
`zeus wop template --from <SOURCE>` to inherit resolved metadata, gates,
qualification, and completion sections from a prior WOP. `validate`, `lint`,
`inspect`, and `explain` are read-only and create no runtime or repository
state. The canonical contract is emitted by `zeus wop format` from
`scripts/lib/emp/wop_schema.py`; validators and templates consume that same
contract.

Packaging is transactional: source parsing and full package validation occur in
a temporary workspace, then the validated candidate is atomically promoted.
Any failure removes the temporary workspace and leaves no package, registration,
provenance, or Stage 1 state. A changed source never silently replaces an
accepted package.
