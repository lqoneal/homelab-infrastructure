# Implementation Report

The implementation adds an independent native-thread discovery and persistence
projection, including compatibility discovery from a legacy pending request or
app-server log without mutating either source. Status now emits explicit
transport liveness/replacement and thread identity/persistence/resume/fork
fields. The ambiguous reuse/supersession fields are removed from runtime
contracts.

Managed resume now validates current authority and immutable lifecycle
bindings, rejects duplicate ownership, proves native persistence before launch,
and uses the installed app-server `thread/read` and `thread/resume` methods. It
persists the native identity separately from the Zeus wrapper. Explicit fork
uses `thread/fork` and validates lineage. Controlled work reuses an established
thread and creates a thread only when no native thread was ever established.

Mission lifecycle resolution overlays required Codex recovery before exposing
the controlled-work action. Remote reconciliation independently reports
transport and thread state. Event sequencing now excludes non-journal readiness
marker JSON files.

Directly changed implementation surfaces include `scripts/zeus`,
`codex_adapter.py`, `codex_reconciliation.py`, `codex_interactive.py`,
`canonical_lifecycle_resolver.py`, and `operational_beta.py`, plus focused tests
and controlled documents.
