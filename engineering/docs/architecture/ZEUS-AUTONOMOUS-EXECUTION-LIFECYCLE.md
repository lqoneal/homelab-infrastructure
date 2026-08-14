# Zeus Autonomous Execution Lifecycle

Submission hands Zeus an immutable Stage 1 transaction and its receipt chain. The autonomous controller owns derived orchestration from that point until closeout, while Engineering Governance remains the authority source.

The controller is a reconciliation layer over Stage 1, runtime reconciliation, admission supersession, canonical mission activation, EOS validation, and closeout. It does not create authority, rewrite receipts, resubmit a WOP, or approve policy-gated publication.

Every command resolves the exact transaction, computes a deterministic plan, records a receipt-backed snapshot, and either applies lawful derived repairs or exposes a blocker and next action. Missing or stale projections are repairable; conflicting immutable identities fail closed.

The controller's execution envelope may contain multiple sequential roadmap
gates and lifecycle transactions. Gate completion is a transition point, not
an automatic handoff boundary. For each transition the controller resolves
the next action from current canonical authority, checks entry conditions,
retains evidence, independently qualifies where applicable, persists the
receipt/state, and repeats until a real stop condition is reached. Approval is
policy-driven, publication is separately bounded, and provider-session
identity is not gate identity.

### Disposition of adjacent models

- `CURRENT_CANONICAL`: Zeus controller continuation, canonical authority and
  successor resolution, policy-driven operator decisions, independent
  qualification, and Zeus-only protected operations.
- `CURRENT_COMPATIBILITY`: bounded single-gate or single-transaction callers,
  including `max_gates` interruption limits and legacy command spellings.
- `HISTORICAL_FROZEN`: older progressive/manual gate records whose per-gate
  acceptance was part of their original contract.
- `SUPERSEDED`: any caller interpretation that treats a gate completion as an
  automatic handoff termination.
- `REQUIRES_RECONCILIATION`: a current authority or runtime projection that
  cannot identify the next action, approval requirement, or resume position
  uniquely; it must fail closed rather than infer continuation.
