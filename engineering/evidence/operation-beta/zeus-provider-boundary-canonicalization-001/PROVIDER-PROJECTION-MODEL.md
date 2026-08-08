# Provider Projection Model

The canonical provider boundary is:

```text
live mission/WOP/P2-P4 chain
  -> live execution-agent registry and qualification
  -> one mission-scoped provider-selection set
  -> READY_FOR_PROVIDER_DISPATCH
  -> EVALUATE_PROVIDER_DISPATCH
```

The provider ID is derived from the live registry (`zeus-local-loneal-01` in
this verification), not from a hardcoded provider name. The selected set is
bound to Mission ID, WOP ID, submission, admission, bootstrap, repository
identity, provenance baseline, current published baseline, registry digest,
and provider-selection identity. Two current target sets, digest mismatch,
identity mismatch, or an incomplete target set fails closed. Historical and
cross-mission sets are subordinate evidence.

This boundary does not authorize dispatch or create a provider session.
