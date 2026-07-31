# Engineering Metadata Lifecycle

Status: `PROPOSED LOGICAL CONTRACT — NON-AUTHORITATIVE`

An EMM entity revision progresses deterministically through `DRAFT → VALIDATED → QUALIFIED → PUBLISHED → ADOPTED → SUPERSEDED | DEPRECATED → RETIRED → ARCHIVED`. A failed validation or qualification returns the candidate to `DRAFT`; it never changes a published immutable revision. `RETIRED` stops new use, while `ARCHIVED` preserves the immutable record and its lineage.

| Stage | Entry criterion | Outcome | Owner responsibility |
|---|---|---|---|
| Create | Identified need and stable identity | candidate fact | declared authoritative owner |
| Validate | complete candidate | structural and semantic result | validation capability |
| Qualify | validation passes | qualified revision/binding | qualification owner |
| Publish | qualification binding exists | immutable discoverable revision | authoritative owner |
| Adopt | compatible consumer accepts published revision | recorded consumer adoption | consuming subsystem |
| Revise | successor is required | new linked candidate revision | authoritative owner |
| Deprecate/retire/archive | replacement or retention policy is met | constrained use, then preserved history | authoritative owner and archive custodian |

Publication is not adoption. Adoption is per consumer and is recorded as an immutable compatibility binding. Synchronization can project a published revision only source-to-target; no projection changes the source revision.
