# Identity Resolver Implementation Report

Added `scripts/lib/emp/repository_identity.py`. It normalizes remotes,
reproduces the runtime ID/fingerprint, resolves authorized aliases, and
returns a canonical path. WOP validation, packaging, inspection, and Stage 1
submission use the resolver; rejected values remain fail-closed.
