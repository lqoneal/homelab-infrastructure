# Provider Invocation Contract

Canonical command:

`scripts/zeus provider-invocation create ZEUS-EXECUTION-LIFECYCLE-COMPLETION-01 --json`

The P5-G4 contract resolves the live mission, WOP, submission, admission,
bootstrap, dispatch, provider session, repository identity, and current
baseline before creating a deterministic invocation artifact set. The selected
provider was derived from the live execution-agent registry:
`zeus-local-loneal-01`.

`PROVIDER_INVOCATION_ID=PROVIDER-INVOCATION-ccbf4655-b0f4-57b2-8a1a-3fea9a3d88f9`

`PROVIDER_INVOCATION_MODE=QUALIFICATION_ADAPTER`

The adapter records a provider-bound acknowledgement and is explicitly not a
Codex process launch. It does not begin mission work, mutate the repository,
or cross the execution-start boundary. Its next action is `START_EXECUTION`.
The exact replay returned the same ID, artifact digests, and
`duplicate_provider_invocation=IDEMPOTENT`.
