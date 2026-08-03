# Root Cause Analysis

The parser tracked only the current recognized metadata key. It flushed that
key when it encountered another recognized key, but ignored unrecognized peer
headings. Consequently, `## Scope` and `## Completion Requirements` remained
active while later transaction, authority, architecture, and revision sections
were read as metadata values.

The correction tracks heading level. Nested headings remain within their
metadata section; a peer or higher-level heading flushes the active section,
even when that heading is not a metadata key. Inline metadata labels retain
their existing behavior.

No serializer, manifest schema, authority, runtime, or admission lifecycle
logic was changed.
