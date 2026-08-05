# Codex Context Injection Contract

The authoritative input is `ZEUS_CODEX_CONTEXT_FILE` plus compact
`ZEUS_CODEX_CONTEXT_JSON`. The payload contains no conversational handoff;
identity and authority are machine fields and are digest-bound. Missing,
malformed, or conflicting fields fail closed.
