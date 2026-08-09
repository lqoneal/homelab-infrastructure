# Reprepare Atomicity Assessment

Prepare resolves the canonical current lineage before creating a replacement,
binds the deterministic publication identity to repository/Mission/WOP/cohort,
candidate digest, starting baseline, creation authority, and predecessor, then
persists receipt-backed milestones. Exact replay returns the existing identity
with `publication_replay=IDEMPOTENT`.

Once an integral successor edge exists, derived mission resolution excludes its
predecessor without waiting for a predecessor mutation. A crash before a valid
successor is durable leaves the predecessor current; a malformed, partial, or
receipt-inconsistent successor causes fail-closed integrity resolution. A
stable successful prepare therefore cannot expose two valid current tips.

This is logical atomicity over immutable records. No lock-free filesystem
sequence is claimed to be physically atomic across every receipt write, and a
partial sequence grants no authority.
