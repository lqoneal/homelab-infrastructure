# Phase-1 Authored WOP vs Lifecycle Source Comparison

## Comparison reference

The repository contains executable P1/P2 contract evidence in
`scripts/tests/test-zeus-p1-g1-authoring.py` and
`scripts/tests/test-zeus-p2-g1-submission-boundary.py`. The P1 test creates a
mission source, invokes the structured authoring boundary, and verifies replay
plus `ADMISSION_READY`. The P2 fixture shows the minimum traceability object
consumed by `submit_wop_boundary` and verifies deterministic receipt/replay.

## Contract matrix

| Contract | Valid Phase-1 authored output | Lifecycle `source-wop.md` | Finding |
|---|---|---|---|
| Operation classification | `operation: BETA` in traceability | Semantic source describes Operation Beta, but no trace field | Needs authored projection |
| WOP identity | Trace `wop_id` and generated output identity | `WOP-ZEUS-EXECUTION-LIFECYCLE-COMPLETION-001` in source | Identity exists; must be preserved |
| Mission identity | Trace `mission_id` and generated output identity | `ZEUS-EXECUTION-LIFECYCLE-COMPLETION-01` in source | Identity exists; must be preserved |
| Source provenance | `source.path`, byte digest, normalized digest | No sidecar/source record | Missing |
| Output provenance | `output_digest` over authored Markdown/DOCX | Source digest can be computed, but no output assertion | Missing |
| Template provenance | Template path/digest and `TPL-0001` identity | Only textual authoritative reference | Missing machine binding |
| Context provenance | Operation Beta context identity/digest | No context digest | Missing |
| Repository identity | Canonical repository mapping in trace | Source has repository path | Needs normalized canonical identity record |
| Schema/version | Authoring output uses the shared Development WOP schema and trace contract | Source passes `development-wop/1` validation | Schema-valid, not authoring-complete |
| Readiness | `ADMISSION_READY` | No readiness receipt; `wop readiness` fails | Missing |
| Validation/lint evidence | Embedded in traceability | Standalone read-only commands pass | Must be bound into receipt |
| Source-to-output mapping | Trace maps mission intent to WOP fields/sections | No mapping | Missing |
| Mission-source mapping | Structured mission YAML is normalized to authored output | No structured mission source | Missing; must not be fabricated |
| Required gates | Authored output carries normalized gates | Seven gates are present in source | Semantics exist; bind them |
| Authority wording | Authoring output records submission as the governing act | Explicit authority section says no second generic grant | Compatible with target authority |
| Approval gate | Trace/package declares only explicit in-WOP gate | No approval gate is declared | No WOP approval should be invented |
| Replay identity | Canonical trace content compares equal across replays | Source digest is stable | Promotion must be deterministic |
| Package generation | P2 may later request admission; Stage 1 package is derived | Existing `package_wop` can derive a package | Reuse, do not create a parallel package model |

## Classification conclusion

The lifecycle source is `DEVELOPMENT_SOURCE_PROMOTABLE` in the recommended
future classifier, not `CURRENT_AUTHORED`. It has the complete semantic
Development WOP fields and seven gates, but lacks the P1 provenance envelope.
It is not safe to treat a bare sidecar-shaped file as sufficient: the sidecar
must be generated or verified from source, template, context, repository,
schema, and output digests.

## `wop init` behavior

The CLI's `init` branch calls `markdown_template` or `docx_template` and
returns a source path. It does not call `author()` and does not create a
traceability record. The CLI comment explicitly describes the
`--wop-id/--mission-id` route as compatibility for hand-authored sources.

The structured `wop template <MISSION-SOURCE.yaml>` route calls `author()`.
That service normalizes Operation Beta mission input, resolves the repository,
binds template/context digests, derives hash-based WOP and Mission IDs, writes
the output, and writes `<output>.traceability.json`. It is a valid P1 path for
new structured intent, but it is not a safe transform for the lifecycle source
because it would derive different identities.

## Required promotion rule

An identity-preserving promotion must either accept the existing source as the
immutable authored output and create a complete, cryptographically bound
provenance envelope, or produce a deterministic normalized output whose
identity fields remain exactly the source's declared WOP/Mission IDs. It must
not silently replace them with `MISSION-BETA-*` or another hash-derived ID.
