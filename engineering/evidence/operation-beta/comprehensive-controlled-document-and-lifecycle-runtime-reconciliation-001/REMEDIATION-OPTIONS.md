# Remediation Options

## Option A — Receipt-chain convergence (preferred)

Make one canonical mission resolver consume P2/P3/P4, provider/session, execution, evidence, publication, EOS, and closeout receipts. Keep provider, session, monitoring, Beta, and autonomous views subordinate. Preserve legacy routes as explicit read-only compatibility. This minimizes redesign and gives replay/idempotency one identity source.

## Option B — Retain parallel lifecycle controllers

Add adapters between current controllers. Lower migration cost, but leaves competing transition ownership and is unsafe for recovery/closeout.

## Option C — Replace with a new monolithic state machine

Could simplify the model, but has high migration risk and threatens immutable historical compatibility. Not recommended.

Option A is recommended because it converges authority without rewriting historical records or changing the already-qualified P2 submission boundary.

