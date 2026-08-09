# Provider Qualification Freshness Contract

Provider selection is point-in-time immutable provenance. It records why the
provider was selected and binds the selection to the mission and repository
lineage at that transition.

Dispatch-time provider readiness remains a separate boundary. The dispatch
controller must resolve the live execution-agent registry and revalidate
availability, qualification, repository scope, capability, and trust before
dispatch. A repository descendant publication is not itself a provider-health
change and does not invalidate provider selection.

The current corrective therefore projects selection after publication but does
not authorize dispatch, session creation, provider invocation, or execution.

