# Canonical Authority Validation Contract

Resolve one Stage 1 authority-snapshot digest, require all available receipt-backed candidates to agree, then validate predecessor, successor, and execution projection bindings against it. An absent generic field is accepted only when canonical provenance exists. Missing canonical provenance, malformed values, mismatch, unrelated lineage, and ambiguity fail closed.

Submission authority from Engineering Governance is consumed; no authority decision is issued, reinterpreted, or created.

