# Metadata Versioning Model

Status: `PROPOSED LOGICAL CONTRACT — NON-AUTHORITATIVE`

EMM schema versions use `MAJOR.MINOR.PATCH`. Entity identity remains `entity_type:entity_id:revision`; revision is a monotonic immutable successor and is distinct from the schema version.

| Change | Version increment | Compatibility rule |
|---|---|---|
| Clarification, validation tightening with no representation change | PATCH | existing compatible consumers continue after requalification where required |
| additive optional field, new optional projection | MINOR | older consumers ignore unknown fields; newer consumers tolerate absence where declared |
| removed/renamed meaning, changed identity or required invariant | MAJOR | explicit migration and consumer adoption are required |

Every published revision declares `schema_version`, `compatibility_range`, `canonical_digest`, predecessor reference, and required migration path where its major version differs from an adopted predecessor. Version resolution selects exactly one declared compatible revision; ambiguity is a validation failure, not an implicit fallback.
