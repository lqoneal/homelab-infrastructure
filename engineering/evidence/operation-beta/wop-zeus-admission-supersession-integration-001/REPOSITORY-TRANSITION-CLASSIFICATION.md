# Repository Transition Classification

The protected transition is `a638ea7221a025789c08c5fc1be4ac466b7041a` to published `a9868c5416b27aa00db0a25c4c32c1a49e631d8a`. It is a single-ancestry descendant transition with published `main` parity. Its intervening commits are the governed Stage 1 resolver publication and its reconciliation package/evidence; paths are limited by the explicit baseline-transition allowlist in `admission_supersession.py`.

The policy rejects dirty trees, local/published divergence, rewinds, ambiguous ancestry, and paths outside the allowlist. Candidate-branch validation is classified `UNPUBLISHED_CANDIDATE` until publication.
