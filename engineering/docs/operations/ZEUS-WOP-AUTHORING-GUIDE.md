# Zeus Development WOP Authoring Guide

The canonical authoring workflow uses source documents only:

```text
zeus wop format
zeus wop template --wop-id WOP-EXAMPLE-001 --mission-id EXAMPLE-01 --output WOP-EXAMPLE-001.md
# edit WOP-EXAMPLE-001.md
scripts/zeus submit WOP-EXAMPLE-001.md
# if interrupted: scripts/zeus resume EXAMPLE-01
```

`zeus wop format` is generated from the canonical schema and lists all required
 metadata. `zeus wop template` supports Markdown and DOCX. `zeus wop inspect`
is read-only and reports every unresolved field. `inspect`, `explain`, and
`lint` are read-only previews. Operators do not construct mission files,
manifests, registration, provenance, or runtime state manually.

For structured mission intent, Phase 1 also provides the deterministic
authoring boundary:

```text
zeus wop template <MISSION-SOURCE.yaml> --output <WOP-SOURCE.md> --json
zeus wop identity <WOP-SOURCE.md> --json
zeus wop context <WOP-SOURCE.md> --json
zeus wop traceability <WOP-SOURCE.md> --json
zeus wop lint <WOP-SOURCE.md> --json
zeus wop validate <WOP-SOURCE.md> --json
zeus wop readiness <WOP-SOURCE.md> --json
zeus wop next <WOP-SOURCE.md> --json
zeus wop snapshot <WOP-SOURCE.md> --json
zeus wop verify <WOP-SOURCE.md> --json
zeus wop verify <WOP-SOURCE-A.md> --replay-against <WOP-SOURCE-B.md> --json
```

The structured source binds Operation Beta, resolves the canonical repository,
uses the active TPL-0001 template, derives deterministic WOP and Mission IDs,
and writes a traceability sidecar. It reports `ADMISSION_READY` only after
placeholder, lint, validation, and traceability checks pass. The emitted next
submission command is informational; this authoring boundary never submits or
admits the output.

`zeus wop verify` is read-only. It checks the output digest, traceability,
readiness, and unresolved marker-shaped tokens. Replay verification compares
canonical content and preserves repository identity, Mission/WOP IDs, source,
template/context digests, output digest, blockers, and readiness while ignoring
only filesystem-location fields. Ordinary prose containing “placeholder” is
not treated as an unresolved token.

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
scripts/zeus submit WOP-EXAMPLE-001.md
# if interrupted: scripts/zeus resume EXAMPLE-01
```

`zeus wop init` is an interactive equivalent when IDs are omitted. Use
`zeus wop template --from <SOURCE>` to inherit resolved metadata, gates,
qualification, and completion sections from a prior WOP. `validate`, `lint`,
`inspect`, and `explain` are read-only and create no runtime or repository
state. The canonical contract is emitted by `zeus wop format` from
`scripts/lib/emp/wop_schema.py`; validators and templates consume that same
contract.

The generated source includes the execution-bound fields that are checked at
`VALIDATE_WOP`: approval authorization for `Active`, the seven published
procedure/template/standard references, authority-node and authorization-
decision references, and all thirteen required execution sections. Markdown and
DOCX are presentation-equivalent; `--output` selects the exact destination.
`lint` and `validate` report these fields before submission. The package keeps
the same values in `mission.yaml`, so execution does not reconstruct a second
schema.

Packaging is transactional: source parsing and full package validation occur in
a temporary workspace, then the validated candidate is atomically promoted.
Any failure removes the temporary workspace and leaves no package, registration,
provenance, or Stage 1 state. A changed source never silently replaces an
accepted package.
