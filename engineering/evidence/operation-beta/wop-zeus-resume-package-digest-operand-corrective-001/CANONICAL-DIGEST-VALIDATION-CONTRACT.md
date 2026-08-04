# Canonical Digest Validation Contract

1. Require a Stage 1 transaction package digest.
2. Require all present package/registration/dispatch receipt package digests
   to equal it.
3. Require every present predecessor and successor package-binding field to
   equal it.
4. Validate source and submission digests independently.
5. Validate projection and runtime-state digests only as their serialized
   object integrity.
6. Fail closed for absent, conflicting, modified, or semantically different
   operands.

The contract performs no persistence and introduces no operator-visible step.
