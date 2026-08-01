# OA-20 Architecture Report

OA-20 adds an EENS-backed provenance-binding layer over the OA-19 append-only evidence owner. It validates the captured evidence checksum and exact repository, commit, mission, WOP, and agent fields, then binds authority, execution, and gate identity in a deterministic manifest. The manifest is append-only, restart-durable, idempotent for exact replay, and conflicting replay fails closed.

No duplicate evidence authority, mission authority, capability authority, or EMM owner was introduced.
