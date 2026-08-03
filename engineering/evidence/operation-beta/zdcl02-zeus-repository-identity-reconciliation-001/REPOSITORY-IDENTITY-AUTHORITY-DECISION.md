# Repository Identity Authority Decision

The published runtime/Git repository binding is authoritative. The WOP
`repository_identity` field accepts only the canonical path, normalized remote,
runtime ID, runtime fingerprint, or the path-derived short-name alias. The
resolver returns the canonical repository path to lifecycle consumers.

This is compatibility normalization; it does not weaken fail-closed checks or
fabricate identity.
