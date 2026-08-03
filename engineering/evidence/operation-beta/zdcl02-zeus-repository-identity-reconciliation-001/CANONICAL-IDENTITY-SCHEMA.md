# Canonical Identity Schema

Version `1` fields: `repository_path`, `repository_remote_identity`,
`repository_id`, `repository_fingerprint`, `repository_short_name`,
`repository_identity_source`, and `repository_identity_version`.
`canonical_repository_identity` is the resolved path consumed by Stage 1.

Fingerprint compatibility preserves the existing runtime v2 calculation over
the canonical path and configured remote string.
