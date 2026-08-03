# Canonical Automatic Dispatch Contract

The CLI now supplies an executor that reads the existing agent registry,
filters active qualified agents with repository scope, sorts by agent ID, and
creates a dispatch receipt only after deterministic selection. No provider
output or fabricated launch acknowledgement advances execution.
