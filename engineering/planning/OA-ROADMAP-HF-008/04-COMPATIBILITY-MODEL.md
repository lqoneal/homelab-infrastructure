# Backward and Forward Compatibility Model

Status: `PROPOSED LOGICAL CONTRACT — NON-AUTHORITATIVE`

Compatibility is a declared relation among producer schema, consumer capability, and projection contract. A consumer may read only a version it explicitly supports. Unknown data is preserved by transport/projection layers where required; it is not silently re-authored or discarded.

| Relation | Allowed when | Required behavior |
|---|---|---|
| Backward | new consumer reads old compatible version | apply declared deterministic defaults; surface missing required capability |
| Forward | old consumer reads newer compatible minor version | ignore only declared non-material fields; preserve provenance |
| Cross-major | major versions differ | use qualified migration or reject |
| Repository mixed revision | multiple entity revisions coexist | resolve exact revision through immutable references, never “latest” |
| Downgrade | target has a declared reversible mapping | create a derived compatibility view; never overwrite the newer authoritative fact |

Mismatch drift is detected by comparing source schema/revision, consumer adoption binding, input manifest, and projection digest. A mismatch quarantines the affected derived/runtime view, emits a synchronization discrepancy, and invokes reconciliation at the source boundary.
