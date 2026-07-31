# Canonical Metadata Resolution Specification

Status: `PROPOSED LOGICAL EXECUTION CONTRACT — NON-AUTHORITATIVE`

The Metadata Engine is the canonical resolution service for EMM entity revisions and schema contracts. It is an access/resolution process, not the owner of the facts it resolves.

| Rule | Deterministic requirement |
|---|---|
| Identity | request supplies `entity_type`, `entity_id`, and either exact `revision` or declared `compatibility_range`; identity is HF-007 `entity_type:entity_id:revision` |
| Discovery | resolve only from the canonical registry’s immutable publication index, keyed by owner reference and entity identity |
| Order | exact revision → uniquely compatible published revision → structured failure; never resolve “latest” implicitly |
| Repository context | repository identity/baseline is an explicit input manifest reference; it cannot silently override entity identity |
| Conflict | more than one candidate, digest mismatch, owner mismatch, or schema mismatch returns `AMBIGUOUS_RESOLUTION`/`INTEGRITY_FAILURE` and publishes nothing |
| Missing | no candidate returns `NOT_FOUND` with requested identity/range; consumers stop the dependent operation |
| Verification | response includes resolved identity, owner reference, schema/revision, digest, publication and qualification binding, compatibility decision, and source manifest |

The registry accepts a publication only after schema, identity, owner-directory, lineage, and qualification checks pass. Published revisions are immutable; correction is a successor revision. Retained historical revisions resolve only when a consumer explicitly requests an allowed historical range.
